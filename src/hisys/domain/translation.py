"""Translate structured domain use-case results into existing Hisys schemas.

Traceability: HISYS-DOM-003, HISYS-DOM-009, HISYS-DOM-010, HISYS-DOM-012.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

from hisys.domain.layers import DomainUseCaseResult, LayerTraceStep
from hisys.schemas.domain_investigation import (
    AlternativeDecisionSet,
    CandidateRecord,
    DomainEvidencePackage,
    DomainInvestigationRequest,
    DomainInvestigationResult,
    InvestigationDataPackage,
)
from hisys.schemas.lapidary_governance import HisysMode

QualityGate = Literal["passed", "needs_more_evidence", "failed"]


@dataclass(frozen=True)
class DomainUseCaseArtifactPacket:
    """Intermediate structured packet before existing Pydantic schema projection."""

    request_id: str
    domain: str
    layer_trace: list[LayerTraceStep]
    investigation_ref: str
    aggregation_report_ref: str
    decision_ref: str
    memo_refs: list[str]
    evidence_refs: list[str]
    runtime_boundary_refs: list[str]
    config_snapshot_refs: list[str]
    prompt_bundle_refs: list[str]
    traceability_ids: tuple[str, ...]
    recommendation_summary: str
    quality_gate: QualityGate
    requires_human_review: bool
    external_call_made: bool
    mutation_performed: bool

    def to_runtime_record(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "domain": self.domain,
            "layer_trace": [asdict(step) for step in self.layer_trace],
            "artifact_refs": {
                "investigation_ref": self.investigation_ref,
                "aggregation_report_ref": self.aggregation_report_ref,
                "decision_ref": self.decision_ref,
                "memo_refs": self.memo_refs,
                "evidence_refs": self.evidence_refs,
                "runtime_boundary_refs": self.runtime_boundary_refs,
            },
            "config_snapshot_refs": self.config_snapshot_refs,
            "prompt_bundle_refs": self.prompt_bundle_refs,
            "traceability_ids": list(self.traceability_ids),
            "recommendation_summary": self.recommendation_summary,
            "quality_gate": self.quality_gate,
            "requires_human_review": self.requires_human_review,
            "external_call_made": self.external_call_made,
            "mutation_performed": self.mutation_performed,
        }


class DomainUseCaseArtifactTranslator:
    """Translate a three-layer use-case result into a stable artifact packet."""

    def translate(
        self,
        result: DomainUseCaseResult,
        *,
        request: DomainInvestigationRequest,
        traceability_ids: tuple[str, ...],
    ) -> DomainUseCaseArtifactPacket:
        return DomainUseCaseArtifactPacket(
            request_id=result.request_id,
            domain=result.domain,
            layer_trace=list(result.layer_trace),
            investigation_ref=result.investigation.work_product_id,
            aggregation_report_ref=result.aggregation.report_ref,
            decision_ref=result.decision.decision_ref,
            memo_refs=list(result.investigation.memo_refs),
            evidence_refs=list(result.investigation.evidence_refs),
            runtime_boundary_refs=[],
            config_snapshot_refs=list(request.config_snapshot_refs),
            prompt_bundle_refs=list(request.prompt_bundle_refs),
            traceability_ids=traceability_ids,
            recommendation_summary=result.recommendation_summary,
            quality_gate=result.quality_gate,
            requires_human_review=result.requires_human_review,
            external_call_made=result.external_call_made,
            mutation_performed=result.mutation_performed,
        )


def build_domain_investigation_result(
    packet: DomainUseCaseArtifactPacket,
    request: DomainInvestigationRequest,
    *,
    runtime_boundary_refs: list[str],
) -> DomainInvestigationResult:
    """Project a structured packet into the existing Hisys result schema."""

    combined_runtime_refs = list(dict.fromkeys([*packet.runtime_boundary_refs, *runtime_boundary_refs]))
    evidence = DomainEvidencePackage(
        package_id=f"DEPKG-{packet.request_id}",
        domain=request.domain,
        evidence_type=f"{packet.domain}_structured_evidence",
        summary=f"Structured {packet.domain} investigation packet.",
        evidence_refs=list(dict.fromkeys(packet.evidence_refs + [packet.investigation_ref])),
        source_refs=[source.source_id for source in request.sources],
        claims=[packet.recommendation_summary],
        limitations=["Structured adapter bridge uses governed local artifacts only."],
        external_call_made=packet.external_call_made,
        mutation_performed=packet.mutation_performed,
    )
    data = InvestigationDataPackage(
        investigation_id=f"INV-{packet.request_id}",
        request_id=request.request_id,
        domain=request.domain,
        objective=request.objective,
        evidence_packages=[evidence],
        runtime_boundary_refs=combined_runtime_refs,
        hisys_mode=HisysMode(level="stone"),
    )
    candidate = CandidateRecord(
        candidate_id=f"CAND-{packet.request_id}",
        candidate_type=f"{packet.domain}_advisory_candidate",
        claim=packet.recommendation_summary,
        evidence_refs=list(dict.fromkeys(packet.evidence_refs + [packet.aggregation_report_ref, packet.decision_ref])),
        value="Preserve structured three-layer analysis for human review.",
        risks=["Advisory result only; human review required."],
        uncertainties=[] if packet.quality_gate == "passed" else ["More evidence may be required."],
        next_increment="human_review",
    )
    alternatives = AlternativeDecisionSet(
        alternative_set_id=f"ALT-{packet.request_id}",
        request_id=request.request_id,
        candidates=[candidate],
        recommended_candidate_id=candidate.candidate_id,
    )
    return DomainInvestigationResult(
        result_id=f"RESULT-{packet.request_id}",
        request_id=request.request_id,
        domain=request.domain,
        investigation_data=data,
        alternative_decision_set=alternatives,
        recommendation_summary=packet.recommendation_summary,
        dars_refs=[packet.decision_ref],
        runtime_boundary_refs=combined_runtime_refs,
        quality_gate=packet.quality_gate,
        requires_human_review=packet.requires_human_review,
        external_call_made=packet.external_call_made,
        mutation_performed=packet.mutation_performed,
    )


__all__ = [
    "DomainUseCaseArtifactPacket",
    "DomainUseCaseArtifactTranslator",
    "build_domain_investigation_result",
]
