"""Operational Lapidary governance flow/routing integration tests.

Traceability: HISYS-SCHEMA-001, HISYS-FR-INV-001..006,
HISYS-FR-CE-004, HISYS-DARS-CONTRACT-001, HISYS-T-024.

These tests cover the operational gaps identified after the initial Lapidary
implementation: top-level HisysMode routing, weighted alternative production and
audit persistence, DARS advisory-only application to final packets, and a single
fixture-backed flow from investigation evidence to Chief Editor decision to
investment decision support packet.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from hisys.agents.dars_protocol import (
    DarsAdapterValidation,
    DarsBoundaryEvidence,
    DarsCriticPanelMember,
    DarsDecisionTrace,
    DarsProducer,
    DarsRecommendedAction,
    DarsResponseEnvelope,
    DarsRiskFinding,
    DarsStructuredCritique,
)
from hisys.audit import LapidaryGovernanceAuditWriter
from hisys.chief_editor import ChiefEditorPolicy, ChiefEditorRuntime
from hisys.config import InstanceRoot
from hisys.editor import MemoReviewReport
from hisys.operations.lapidary_flow import (
    apply_dars_advisory_review,
    build_weighted_alternative,
    persist_weighted_alternatives,
    select_hisys_mode,
)
from hisys.schemas import EvidenceChainRecord, HisysMode, SourceRegistryEntry, ZettelMemo
from hisys.schemas.investment import (
    HumanApprovalGate,
    InvestmentDecisionPacket,
    InvestmentSignal,
    ScenarioAssessment,
)
from hisys.schemas.lapidary_governance import WeightedDecisionAlternative

YYYYMMDD = "20260512"
PRODUCER_ID = "operational-governance-flow-test"


def _source() -> SourceRegistryEntry:
    return SourceRegistryEntry(
        source_id="SRC-OPGOV-FLOW-001",
        source_type="agent_system",
        display_name="Operational governance fixture source",
        owner="lab-test",
        lifecycle_state="experimental",
        reliability_class="B",
        access_method="agent_handoff",
        cadence="P1D",
        rate_limit="fixture_only",
        usage_constraints=["test_only"],
        retention_rule="P7D",
        producer_id=PRODUCER_ID,
    )


def _memo(source: SourceRegistryEntry) -> ZettelMemo:
    return ZettelMemo(
        memo_id="MEM-OPGOV-FLOW-001",
        title="Decision-level governance requires weighted alternatives",
        summary="Evidence is sufficient for decision support but requires guarded alternatives.",
        body="Synthetic fixture memo for operational governance routing.",
        source_refs=[source.source_id],
        signal_refs=["SIG-OPGOV-FLOW-001"],
        perspective_id="PERSP-OPGOV-FLOW-001",
        confidence=0.82,
        tags=["hisys", "operational-governance"],
        links=[],
        revision="1",
        review_status="flagged_conflict",
        status="flagged_conflict",
        producer_id=PRODUCER_ID,
    )


def _dars_response(
    *,
    recommended_action_type: str = "escalate_to_human",
    critique_status: str = "received",
    schema_valid: bool = True,
    rejected_fields: list[str] | None = None,
) -> DarsResponseEnvelope:
    return DarsResponseEnvelope(
        schema_id="hisys.dars.response",
        schema_version="0.1.0",
        response_id="DARSRESP-OPGOV-FLOW-001",
        request_id="DARSREQ-OPGOV-FLOW-001",
        handoff_id="HANDOFF-OPGOV-FLOW-001",
        created_at="2026-05-12T00:00:00Z",
        producer=DarsProducer(
            backend_id="fixture-dars",
            backend_kind="fixture_file",
            role_id="risk-reviewer",
            model=None,
            external_call_made=False,
        ),
        critique=DarsStructuredCritique(
            critique_id="CRITIQUE-OPGOV-FLOW-001",
            status=critique_status,
            critique_summary="Advisory critique recommends human review but cannot approve.",
            confidence_assessment="high",
            severity="medium",
            requires_human_review=True,
            risk_findings=[
                DarsRiskFinding(
                    risk_id="RISK-OPGOV-FLOW-001",
                    category="authority_boundary",
                    statement="DARS output must remain advisory and cannot approve publication or execution.",
                    severity="medium",
                    mitigation="Keep human approval pending and preserve DARS as an insight ref only.",
                )
            ],
            recommended_actions=[
                DarsRecommendedAction(
                    action_id="ACT-OPGOV-FLOW-001",
                    action_type=recommended_action_type,
                    statement="Escalate to human rather than approving automatically.",
                    priority="high",
                    requires_approval=True,
                    allowed_to_execute=False,
                )
            ],
        ),
        decision_trace=DarsDecisionTrace(
            process_mode="single_pass_critique",
            round_index=1,
            critic_role_id="risk-reviewer",
            critic_profession="systems_safety_reviewer",
            critic_persona="skeptical_but_constructive",
            prompt_bundle_ref="prompt-bundle/dars-risk-reviewer@0.1.0",
            rubric_refs=["rubric/dars/advisory-only"],
            improvement_direction="escalate_to_human",
            blocks_decision=False,
            unresolved_high_severity_findings=0,
            synthesis_summary="DARS advisory critique linked without authority transfer.",
        ),
        rubric_scores=[],
        validation=DarsAdapterValidation(
            schema_valid=schema_valid,
            warnings=[],
            rejected_fields=rejected_fields or [],
        ),
        boundary=DarsBoundaryEvidence(allowed_actions="advisory_only", action_taken="none"),
    )


def _packet(chain: EvidenceChainRecord, alternative: WeightedDecisionAlternative) -> InvestmentDecisionPacket:
    return InvestmentDecisionPacket(
        packet_id="IDP-OPGOV-FLOW-001",
        producer_id=PRODUCER_ID,
        status="draft",
        asset="Operational governance fixture asset",
        instrument_refs=["FIXTURE-ASSET"],
        time_horizon="review cycle",
        proposed_action="watch",
        recommendation_summary="Watch until human review accepts or rejects the advisory package.",
        confidence=0.61,
        evidence_score=0.76,
        risk_score=0.58,
        contradiction_score=0.22,
        signals=[
            InvestmentSignal(
                signal_id="SIG-OPGOV-FLOW-001",
                name="Operational governance signal",
                direction="mixed",
                strength=0.61,
                evidence_refs=list(chain.evidence_refs),
                interpretation="Evidence supports decision-level review but not autonomous action.",
            )
        ],
        bull_case=ScenarioAssessment(
            case_id="CASE-OPGOV-BULL-001",
            summary="Human review accepts the bounded recommendation.",
            probability=0.3,
            evidence_refs=list(chain.evidence_refs),
        ),
        base_case=ScenarioAssessment(
            case_id="CASE-OPGOV-BASE-001",
            summary="Recommendation stays in watch mode pending more evidence.",
            probability=0.5,
            evidence_refs=list(chain.evidence_refs),
        ),
        bear_case=ScenarioAssessment(
            case_id="CASE-OPGOV-BEAR-001",
            summary="Contradictions force revision before use.",
            probability=0.2,
            evidence_refs=list(chain.evidence_refs),
        ),
        decision_boundary=["No execution or publication without human approval."],
        risk_register=["DARS critique is advisory-only."],
        human_approval=HumanApprovalGate(
            required=True,
            status="pending",
            approver_ref="human:professor",
            responsibility_statement="Human remains responsible for consequential use.",
        ),
        disclaimers=["not financial advice", "no autonomous execution"],
        hisys_mode=HisysMode(level="decision"),
        evidence_chain=chain,
        weighted_alternatives=[alternative],
    )


def test_routing_policy_selects_decision_and_publication_modes_with_reasons() -> None:
    decision_mode = select_hisys_mode(
        evidence_refs=["EV-001"],
        claim_refs=["C-001"],
        synthesis_refs=["SYN-001"],
        decision_requested=True,
        risk_score=0.72,
    )

    assert decision_mode.level == "decision"
    assert decision_mode.routing_policy_ref == "lapidary-routing-policy/operational-governance-v1"
    assert "decision_requested" in decision_mode.upgrade_triggers
    assert "risk_score>=0.70" in decision_mode.upgrade_triggers

    publication_mode = select_hisys_mode(
        evidence_refs=["EV-001"],
        claim_refs=["C-001"],
        synthesis_refs=["SYN-001"],
        decision_requested=True,
        publication_requested=True,
        risk_score=0.2,
    )

    assert publication_mode.level == "publication"
    assert "publication_requested" in publication_mode.upgrade_triggers


def test_weighted_alternative_generation_is_persisted_to_lapidary_audit(tmp_path: Path) -> None:
    chain = EvidenceChainRecord(
        chain_id="CHAIN-OPGOV-FLOW-001",
        producer_id=PRODUCER_ID,
        status="active",
        decision_ref="ALERT-OPGOV-FLOW-001",
        synthesis_refs=["PERSP-OPGOV-FLOW-001"],
        claim_ledger_refs=["MEM-OPGOV-FLOW-001"],
        evidence_refs=["SIG-OPGOV-FLOW-001"],
        source_refs=["SRC-OPGOV-FLOW-001"],
    )
    alternative = build_weighted_alternative(
        alternative_id="ALT-OPGOV-FLOW-001",
        label="Watch pending human-reviewed use",
        claim="Use the decision only as human-reviewed decision support.",
        evidence_chain=chain,
        producer_id=PRODUCER_ID,
        recommended_use="hybrid",
    )

    assert alternative.weighted_score > 0
    assert {weight.evidence_origin for weight in alternative.origin_weights} == {
        "external_source",
        "runtime_observation",
        "agent_synthesis",
    }

    paths = persist_weighted_alternatives(
        LapidaryGovernanceAuditWriter(InstanceRoot(tmp_path)),
        [alternative],
        yyyymmdd=YYYYMMDD,
    )

    assert len(paths) == 1
    audit_path = paths[0]
    assert audit_path.exists()
    assert audit_path.relative_to(tmp_path).as_posix() == (
        "data/audit/20260512/lapidary-governance/weighted-alternatives/ALT-OPGOV-FLOW-001.json"
    )
    roundtrip = WeightedDecisionAlternative.model_validate_json(
        audit_path.read_text(encoding="utf-8")
    )
    assert roundtrip.alternative_id == alternative.alternative_id


def test_full_operational_flow_routes_investigation_to_decision_packet_and_audit(
    tmp_path: Path,
) -> None:
    source = _source()
    memo = _memo(source)
    runtime = ChiefEditorRuntime(
        instance=InstanceRoot(tmp_path),
        policy=ChiefEditorPolicy.fixture_default(),
        producer_id=PRODUCER_ID,
        hisys_mode=select_hisys_mode(
            evidence_refs=memo.signal_refs,
            claim_refs=[memo.memo_id],
            synthesis_refs=[memo.perspective_id],
            decision_requested=True,
            risk_score=0.8,
        ),
    )

    report = runtime.decide_run(
        [memo],
        memo_review_report=MemoReviewReport(
            reviewed_memo_refs=[memo.memo_id],
            conflict_memo_refs=[memo.memo_id],
        ),
        yyyymmdd=YYYYMMDD,
    )

    assert len(report.alert_decision_refs) == 1
    assert len(report.evidence_chain_refs) == 1
    chain_path = (
        tmp_path
        / "data"
        / "alert-decisions"
        / YYYYMMDD
        / f"{report.alert_decision_refs[0]}.evidence_chain.json"
    )
    chain = EvidenceChainRecord.model_validate_json(chain_path.read_text(encoding="utf-8"))
    alternative = build_weighted_alternative(
        alternative_id="ALT-OPGOV-FLOW-002",
        label="Watch pending human-reviewed use",
        claim="Use this flow only after human review accepts the advisory package.",
        evidence_chain=chain,
        producer_id=PRODUCER_ID,
        recommended_use="hybrid",
    )
    persist_weighted_alternatives(
        LapidaryGovernanceAuditWriter(InstanceRoot(tmp_path)),
        [alternative],
        yyyymmdd=YYYYMMDD,
    )

    reviewed_packet = apply_dars_advisory_review(_packet(chain, alternative), _dars_response())

    assert reviewed_packet.hisys_mode.level == "decision"
    assert reviewed_packet.evidence_chain is not None
    assert reviewed_packet.weighted_alternatives[0].alternative_id == "ALT-OPGOV-FLOW-002"
    assert reviewed_packet.dars_review_status == "completed"
    assert "runtime-boundary/dars/DARSRESP-OPGOV-FLOW-001.json" in reviewed_packet.human_insight_refs
    assert reviewed_packet.human_approval.status == "pending"
    assert reviewed_packet.execution_authorized is False
    assert reviewed_packet.publication_or_live_action_approved is False

    alt_path = (
        tmp_path
        / "data"
        / "audit"
        / YYYYMMDD
        / "lapidary-governance"
        / "weighted-alternatives"
        / "ALT-OPGOV-FLOW-002.json"
    )
    assert alt_path.exists()
    raw_alt = json.loads(alt_path.read_text(encoding="utf-8"))
    assert raw_alt["alternative_id"] == "ALT-OPGOV-FLOW-002"


def test_dars_advisory_result_cannot_transfer_approval_or_execution_authority() -> None:
    chain = EvidenceChainRecord(
        chain_id="CHAIN-OPGOV-FLOW-NEG-001",
        producer_id=PRODUCER_ID,
        status="active",
        decision_ref="ALERT-OPGOV-FLOW-NEG-001",
        synthesis_refs=["PERSP-OPGOV-FLOW-001"],
        claim_ledger_refs=["MEM-OPGOV-FLOW-001"],
        evidence_refs=["SIG-OPGOV-FLOW-001"],
        source_refs=["SRC-OPGOV-FLOW-001"],
    )
    alternative = build_weighted_alternative(
        alternative_id="ALT-OPGOV-FLOW-NEG-001",
        label="Reject autonomous approval",
        claim="DARS critique may recommend human review but cannot approve.",
        evidence_chain=chain,
        producer_id=PRODUCER_ID,
        recommended_use="internal_prior",
    )
    packet = _packet(chain, alternative)

    reviewed = apply_dars_advisory_review(
        packet,
        _dars_response(recommended_action_type="escalate_to_human"),
    )

    assert reviewed.dars_review_status == "completed"
    assert reviewed.human_approval.status == "pending"
    assert reviewed.human_approval.approver_ref == "human:professor"
    assert reviewed.execution_authorized is False
    assert reviewed.publication_or_live_action_approved is False
    assert reviewed.order_ticket_draft is None
    assert "no autonomous execution" in reviewed.disclaimers


def test_weighted_alternative_requires_decision_level_evidence_chain() -> None:
    stone_chain = EvidenceChainRecord(
        chain_id="CHAIN-OPGOV-STONE-ONLY-001",
        producer_id=PRODUCER_ID,
        status="active",
        evidence_refs=["SIG-OPGOV-FLOW-001"],
        source_refs=["SRC-OPGOV-FLOW-001"],
    )

    with pytest.raises(ValueError, match="decision-level EvidenceChainRecord"):
        build_weighted_alternative(
            alternative_id="ALT-OPGOV-STONE-ONLY-001",
            label="Invalid lower-mode alternative",
            claim="A Stone-only chain must not become a decision alternative.",
            evidence_chain=stone_chain,
            producer_id=PRODUCER_ID,
            recommended_use="hybrid",
        )


def test_rejected_or_invalid_dars_response_is_not_linked_as_completed_review() -> None:
    chain = EvidenceChainRecord(
        chain_id="CHAIN-OPGOV-FLOW-REJECTED-001",
        producer_id=PRODUCER_ID,
        status="active",
        decision_ref="ALERT-OPGOV-FLOW-REJECTED-001",
        synthesis_refs=["PERSP-OPGOV-FLOW-001"],
        claim_ledger_refs=["MEM-OPGOV-FLOW-001"],
        evidence_refs=["SIG-OPGOV-FLOW-001"],
        source_refs=["SRC-OPGOV-FLOW-001"],
    )
    alternative = build_weighted_alternative(
        alternative_id="ALT-OPGOV-FLOW-REJECTED-001",
        label="Reject invalid DARS response",
        claim="Invalid DARS responses must not complete review.",
        evidence_chain=chain,
        producer_id=PRODUCER_ID,
        recommended_use="hybrid",
    )
    packet = _packet(chain, alternative)

    with pytest.raises(ValueError, match="valid completed advisory"):
        apply_dars_advisory_review(
            packet,
            _dars_response(critique_status="rejected"),
        )

    with pytest.raises(ValueError, match="valid completed advisory"):
        apply_dars_advisory_review(
            packet,
            _dars_response(schema_valid=False, rejected_fields=["approval_ref"]),
        )
