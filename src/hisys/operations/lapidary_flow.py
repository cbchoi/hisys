"""Operational Lapidary governance flow helpers.

Traceability: HISYS-SCHEMA-001, HISYS-FR-INV-001..006,
HISYS-FR-CE-004, HISYS-DARS-CONTRACT-001, HISYS-T-024.

This module connects the already-governed schema/runtime records into small,
fixture-safe operational routing helpers. It does not perform live external
calls, mutation outside the provided audit writer, or authority transfer from
Devil/DARS reviewer advisory roles to decision roles.
"""

from __future__ import annotations

from collections.abc import Iterable
from math import isfinite
from pathlib import Path
from typing import Literal

from ..agents.dars_protocol import DarsResponseEnvelope
from ..audit import LapidaryGovernanceAuditWriter
from ..schemas.investment import InvestmentDecisionPacket
from ..schemas.lapidary_governance import (
    EvidenceChainRecord,
    EvidenceOriginWeight,
    HisysMode,
    WeightedDecisionAlternative,
)

RoutingLevel = Literal["none", "stone", "claim", "synthesis", "decision", "publication"]
RecommendedUse = Literal["external_source", "internal_prior", "hybrid"]

ROUTING_POLICY_REF = "lapidary-routing-policy/operational-governance-v1"
DARS_RESPONSE_REF_PREFIX = "runtime-boundary/dars"


def select_hisys_mode(
    *,
    evidence_refs: Iterable[str] = (),
    claim_refs: Iterable[str] = (),
    synthesis_refs: Iterable[str] = (),
    decision_requested: bool = False,
    publication_requested: bool = False,
    risk_score: float = 0.0,
) -> HisysMode:
    """Select the minimum selective-governance level required by runtime context.

    The function is intentionally deterministic and conservative: explicit
    publication/decision requests dominate, high risk upgrades to decision, and
    the presence of synthesis/claim/evidence refs selects the corresponding
    lower governance level. It only returns selective HisysMode records; it does
    not apply governance globally to every note.
    """

    evidence = [ref for ref in evidence_refs if ref]
    claims = [ref for ref in claim_refs if ref]
    syntheses = [ref for ref in synthesis_refs if ref]
    if not isfinite(risk_score) or not 0.0 <= risk_score <= 1.0:
        raise ValueError("risk_score must be a finite value between 0.0 and 1.0")
    triggers: list[str] = []

    if publication_requested:
        level: RoutingLevel = "publication"
        triggers.append("publication_requested")
    elif decision_requested or risk_score >= 0.70:
        level = "decision"
        if decision_requested:
            triggers.append("decision_requested")
        if risk_score >= 0.70:
            triggers.append("risk_score>=0.70")
    elif syntheses:
        level = "synthesis"
        triggers.append("synthesis_refs_present")
    elif claims:
        level = "claim"
        triggers.append("claim_refs_present")
    elif evidence:
        level = "stone"
        triggers.append("evidence_refs_present")
    else:
        level = "none"
        triggers.append("no_governed_refs")

    return HisysMode(
        level=level,
        routing_policy_ref=ROUTING_POLICY_REF,
        upgrade_triggers=triggers,
    )


def build_weighted_alternative(
    *,
    alternative_id: str,
    label: str,
    claim: str,
    evidence_chain: EvidenceChainRecord,
    producer_id: str,
    recommended_use: RecommendedUse,
) -> WeightedDecisionAlternative:
    """Build a decision alternative from a validated evidence chain.

    The resulting weights deliberately separate source/evidence/synthesis
    origins. This keeps external/raw provenance, runtime observation, and agent
    synthesis visible instead of collapsing them into a single confidence score.
    """

    if not (
        evidence_chain.decision_ref
        and evidence_chain.synthesis_refs
        and evidence_chain.claim_ledger_refs
        and evidence_chain.evidence_refs
        and evidence_chain.source_refs
    ):
        raise ValueError(
            "weighted alternatives require a decision-level EvidenceChainRecord "
            "with decision_ref, synthesis_refs, claim_ledger_refs, evidence_refs, and source_refs"
        )

    origin_weights: list[EvidenceOriginWeight] = []
    if evidence_chain.source_refs:
        origin_weights.append(
            EvidenceOriginWeight(
                evidence_origin="external_source",
                ref=evidence_chain.source_refs[0],
                origin_weight=0.45,
                source_quality=0.80,
                verification_status=0.75,
                recency=0.70,
                independence=0.80,
                contradiction_status=0.65,
                domain_fit=0.80,
            )
        )
    if evidence_chain.evidence_refs:
        origin_weights.append(
            EvidenceOriginWeight(
                evidence_origin="runtime_observation",
                ref=evidence_chain.evidence_refs[0],
                origin_weight=0.35,
                source_quality=0.75,
                verification_status=0.70,
                recency=0.85,
                independence=0.65,
                contradiction_status=0.60,
                domain_fit=0.75,
            )
        )
    if evidence_chain.synthesis_refs:
        origin_weights.append(
            EvidenceOriginWeight(
                evidence_origin="agent_synthesis",
                ref=evidence_chain.synthesis_refs[0],
                origin_weight=0.20,
                source_quality=0.65,
                verification_status=0.65,
                recency=0.75,
                independence=0.55,
                contradiction_status=0.60,
                domain_fit=0.70,
            )
        )
    if not origin_weights and evidence_chain.claim_ledger_refs:
        origin_weights.append(
            EvidenceOriginWeight(
                evidence_origin="internal_prior",
                ref=evidence_chain.claim_ledger_refs[0],
                origin_weight=0.25,
                source_quality=0.55,
                verification_status=0.50,
                recency=0.50,
                independence=0.45,
                contradiction_status=0.50,
                domain_fit=0.60,
            )
        )

    return WeightedDecisionAlternative(
        alternative_id=alternative_id,
        producer_id=producer_id,
        status="active",
        label=label,
        claim=claim,
        origin_weights=origin_weights,
        recommended_use=recommended_use,
        limitations=[
            "Generated from bounded evidence-chain refs; requires human review before consequential use."
        ],
    )


def persist_weighted_alternatives(
    writer: LapidaryGovernanceAuditWriter,
    alternatives: Iterable[WeightedDecisionAlternative],
    *,
    yyyymmdd: str,
) -> list[Path]:
    """Persist weighted alternatives through the Lapidary governance audit writer."""

    return [writer.append(alternative, yyyymmdd=yyyymmdd) for alternative in alternatives]


def apply_dars_advisory_review(
    packet: InvestmentDecisionPacket,
    response: DarsResponseEnvelope,
) -> InvestmentDecisionPacket:
    """Link a DARS response to a packet without transferring authority.

    DARS may add critique context and recommended human-review actions. It may
    not approve, publish, execute, mutate, or override the packet's human gate.
    The returned packet records the DARS response as a human-insight reference
    and marks the DARS review completed while preserving all authority fields.
    """

    _ensure_dars_response_is_valid_completed_advisory(response)
    _ensure_dars_response_is_advisory_only(response)
    response_ref = f"{DARS_RESPONSE_REF_PREFIX}/{response.response_id}.json"
    insight_refs = list(packet.human_insight_refs)
    if response_ref not in insight_refs:
        insight_refs.append(response_ref)

    return packet.model_copy(
        update={
            "dars_review_status": "completed",
            "human_insight_refs": insight_refs,
            "human_approval": packet.human_approval,
            "execution_authorized": False,
            "publication_or_live_action_approved": False,
            "order_ticket_draft": packet.order_ticket_draft,
        }
    )


def _ensure_dars_response_is_valid_completed_advisory(response: DarsResponseEnvelope) -> None:
    if not response.validation.schema_valid or response.validation.rejected_fields:
        raise ValueError("DARS response must be a valid completed advisory before linking")
    if response.critique.status == "rejected":
        raise ValueError("DARS response must be a valid completed advisory before linking")


def _ensure_dars_response_is_advisory_only(response: DarsResponseEnvelope) -> None:
    boundary = response.boundary
    if boundary.allowed_actions != "advisory_only":
        raise ValueError("DARS response must remain advisory_only")
    if boundary.action_taken != "none":
        raise ValueError("DARS response must not take action")
    if boundary.mutation_performed or boundary.external_side_effects_performed:
        raise ValueError("DARS response must not mutate or perform external side effects")
    for action in response.critique.recommended_actions:
        if action.allowed_to_execute:
            raise ValueError("DARS recommended actions must not be executable")


__all__ = [
    "DARS_RESPONSE_REF_PREFIX",
    "ROUTING_POLICY_REF",
    "apply_dars_advisory_review",
    "build_weighted_alternative",
    "persist_weighted_alternatives",
    "select_hisys_mode",
]
