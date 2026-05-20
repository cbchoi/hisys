"""Translate structured domain use-case results into existing Hisys schemas.

Traceability: HISYS-DOM-003, HISYS-DOM-009, HISYS-DOM-010, HISYS-DOM-012.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

from hisys.domain.layers import DomainUseCaseResult, LayerTraceStep
from hisys.operations.codebase_analysis import load_codebase_review_bundle
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


CODEBASE_BUNDLE_ROLE_FILENAMES: dict[str, frozenset[str]] = {
    "inventory": frozenset({"inventory.json"}),
    "symbol_index": frozenset({"symbol-index.json", "symbol_index.json"}),
    "scope_map": frozenset({"scope-map.json", "scope_map.json"}),
    "validation_plan": frozenset({"validation-plan.json", "validation_plan.json"}),
    "risk_scan": frozenset({"risk-scan.json", "risk_scan.json"}),
}


def _codebase_artifact_role_for(ref: str) -> str | None:
    filename = ref.rsplit("/", 1)[-1]
    for role, names in CODEBASE_BUNDLE_ROLE_FILENAMES.items():
        if filename in names:
            return role
    return None


def _index_codebase_refs_by_role(refs: list[str]) -> dict[str, str]:
    indexed: dict[str, str] = {}
    for ref in refs:
        role = _codebase_artifact_role_for(ref)
        if role is None or role in indexed:
            continue
        indexed[role] = ref
    return indexed


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
    domain_subtype: str | None
    recommendation_summary: str
    quality_gate: QualityGate
    requires_human_review: bool
    governance_flags: dict[str, bool]
    external_call_made: bool
    mutation_performed: bool
    codebase_artifact_refs: list[str] = field(default_factory=list)
    codebase_bundle_gate: str = "not_applicable"
    codebase_missing_evidence: list[str] = field(default_factory=list)

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
            "domain_subtype": self.domain_subtype,
            "recommendation_summary": self.recommendation_summary,
            "quality_gate": self.quality_gate,
            "requires_human_review": self.requires_human_review,
            "governance_flags": dict(self.governance_flags),
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
            domain_subtype=result.domain_subtype,
            recommendation_summary=result.recommendation_summary,
            quality_gate=result.quality_gate,
            requires_human_review=result.requires_human_review,
            governance_flags=dict(result.governance_flags),
            external_call_made=result.external_call_made,
            mutation_performed=result.mutation_performed,
            codebase_artifact_refs=list(result.investigation.codebase_artifact_refs),
            codebase_bundle_gate=result.investigation.codebase_bundle_gate,
            codebase_missing_evidence=list(result.investigation.codebase_missing_evidence),
        )


@dataclass(frozen=True)
class CodebaseBundleEnrichment:
    """Outcome of loading the codebase-analysis bundle for an enriched result."""

    package: DomainEvidencePackage | None
    override_quality_gate: QualityGate | None


def build_codebase_bundle_enrichment(
    packet: DomainUseCaseArtifactPacket,
    request: DomainInvestigationRequest,
    *,
    instance_root: Path,
) -> CodebaseBundleEnrichment | None:
    """Build an advisory codebase-analysis evidence package from local refs.

    The function reads only through `load_codebase_review_bundle`, which routes
    every ref through `resolve_instance_runtime_ref`. No CLI flag, no network,
    no model, no credential, no destructive Git, and no raw source archival is
    introduced here. Failures map to bounded `needs_more_evidence` evidence
    rather than unhandled exceptions.
    """

    if not packet.codebase_artifact_refs:
        return None

    source_refs = [source.source_id for source in request.sources]
    role_to_ref = _index_codebase_refs_by_role(packet.codebase_artifact_refs)
    package_id = f"DEPKG-CBBUNDLE-{packet.request_id}"

    if packet.codebase_bundle_gate != "candidate_complete":
        missing = list(packet.codebase_missing_evidence)
        limitations = [
            "codebase-analysis bundle is incomplete; advisory evidence only.",
            *[f"missing role: {role}" for role in missing],
        ]
        package = DomainEvidencePackage(
            package_id=package_id,
            domain=request.domain,
            evidence_type="codebase_analysis_bundle",
            summary="Codebase-analysis bundle missing required roles; advisory.",
            evidence_refs=list(packet.codebase_artifact_refs),
            source_refs=source_refs,
            limitations=limitations,
            open_questions=[
                "Provide a complete codebase-analysis bundle before human review.",
            ],
        )
        return CodebaseBundleEnrichment(
            package=package, override_quality_gate="needs_more_evidence"
        )

    ordered_refs = [
        role_to_ref["inventory"],
        role_to_ref["symbol_index"],
        role_to_ref["scope_map"],
        role_to_ref["risk_scan"],
    ]
    try:
        bundle = load_codebase_review_bundle(
            instance_root=instance_root,
            inventory_ref=role_to_ref["inventory"],
            symbol_index_ref=role_to_ref["symbol_index"],
            scope_map_ref=role_to_ref["scope_map"],
            risk_scan_ref=role_to_ref["risk_scan"],
        )
    except (FileNotFoundError, ValueError, OSError) as exc:
        package = DomainEvidencePackage(
            package_id=package_id,
            domain=request.domain,
            evidence_type="codebase_analysis_bundle",
            summary="Codebase-analysis bundle unreadable; advisory.",
            evidence_refs=list(packet.codebase_artifact_refs),
            source_refs=source_refs,
            limitations=[
                "codebase-analysis bundle unreadable; advisory evidence only.",
                f"bundle load failure type: {type(exc).__name__}",
            ],
            open_questions=[
                "Validate codebase artifact files before resubmitting.",
            ],
        )
        return CodebaseBundleEnrichment(
            package=package, override_quality_gate="needs_more_evidence"
        )

    risk_category_count = len(bundle.risk_scan.category_counts)
    scope_count = len(bundle.scope_map.scope_entries)
    inventory_file_count = len(bundle.inventory.files)
    summary = (
        "Codebase-analysis bundle loaded under instance runtime boundary; "
        f"inventory_files={inventory_file_count}, "
        f"scopes={scope_count}, "
        f"risk_categories={risk_category_count}; advisory evidence only."
    )
    package = DomainEvidencePackage(
        package_id=package_id,
        domain=request.domain,
        evidence_type="codebase_analysis_bundle",
        summary=summary,
        evidence_refs=ordered_refs,
        source_refs=source_refs,
        claims=[
            "Codebase-analysis bundle is complete for human review.",
        ],
        limitations=[
            "Advisory bundle evidence requires human review.",
            "No raw source content persisted in this package.",
        ],
    )
    return CodebaseBundleEnrichment(package=package, override_quality_gate=None)


def build_domain_investigation_result(
    packet: DomainUseCaseArtifactPacket,
    request: DomainInvestigationRequest,
    *,
    runtime_boundary_refs: list[str],
    codebase_evidence_package: DomainEvidencePackage | None = None,
    override_quality_gate: QualityGate | None = None,
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
    evidence_packages = [evidence]
    if codebase_evidence_package is not None:
        evidence_packages.append(codebase_evidence_package)
    data = InvestigationDataPackage(
        investigation_id=f"INV-{packet.request_id}",
        request_id=request.request_id,
        domain=request.domain,
        objective=request.objective,
        evidence_packages=evidence_packages,
        runtime_boundary_refs=combined_runtime_refs,
        hisys_mode=HisysMode(level="stone"),
    )
    quality_gate: QualityGate = override_quality_gate or packet.quality_gate
    candidate = CandidateRecord(
        candidate_id=f"CAND-{packet.request_id}",
        candidate_type=f"{packet.domain}_advisory_candidate",
        claim=packet.recommendation_summary,
        evidence_refs=list(dict.fromkeys(packet.evidence_refs + [packet.aggregation_report_ref, packet.decision_ref])),
        value="Preserve structured three-layer analysis for human review.",
        risks=["Advisory result only; human review required."],
        uncertainties=[] if quality_gate == "passed" else ["More evidence may be required."],
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
        quality_gate=quality_gate,
        requires_human_review=packet.requires_human_review,
        external_call_made=packet.external_call_made,
        mutation_performed=packet.mutation_performed,
    )


__all__ = [
    "CodebaseBundleEnrichment",
    "DomainUseCaseArtifactPacket",
    "DomainUseCaseArtifactTranslator",
    "build_codebase_bundle_enrichment",
    "build_domain_investigation_result",
]
