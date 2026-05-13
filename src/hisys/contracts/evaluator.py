"""Pass-contract evidence evaluator.

Traceability: HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001, HISYS-T-024.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .pass_registry import PassContractRegistryEntry


@dataclass(frozen=True)
class EvidenceSummary:
    artifact_refs: list[str] = field(default_factory=list)
    alternative_count: int = 0
    claims_covered: bool = False
    contradiction_checked: bool = False
    dars_critique_refs: list[str] = field(default_factory=list)
    consequential_use: bool = False
    human_approval_ref: str | None = None
    boundary_violation_detected: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceSummary":
        return cls(**{key: data[key] for key in cls.__dataclass_fields__ if key in data})


@dataclass(frozen=True)
class PassContractEvaluationResult:
    contract_id: str
    quality_gate: str
    blockers: list[str]
    human_reviewed_use_only: bool = True
    automatic_promotion_allowed: bool = False
    external_call_made: bool = False
    mutation_performed: bool = False
    publication_or_live_action_approved: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_pass_contract(entry: PassContractRegistryEntry, summary: EvidenceSummary) -> PassContractEvaluationResult:
    blockers: list[str] = []
    minimum = entry.minimum_evidence
    if summary.boundary_violation_detected:
        return PassContractEvaluationResult(entry.contract_id, "failed", ["boundary_violation_detected"])
    if minimum.get("artifact_refs_required") and not summary.artifact_refs:
        blockers.append("no_traceable_artifact_refs")
    if minimum.get("alternative_set_required") and summary.alternative_count < 2:
        blockers.append("alternative_set_incomplete")
    if minimum.get("claim_coverage_required") and not summary.claims_covered:
        blockers.append("claim_coverage_incomplete")
    if minimum.get("contradiction_check_required") and not summary.contradiction_checked:
        blockers.append("contradiction_unchecked")
    if minimum.get("dars_critique_required") and not summary.dars_critique_refs:
        blockers.append("dars_critique_missing")
    if blockers:
        return PassContractEvaluationResult(entry.contract_id, "needs_more_evidence", blockers)
    if summary.consequential_use and not summary.human_approval_ref:
        return PassContractEvaluationResult(entry.contract_id, "human_approval_required", ["human_approval_required"])
    return PassContractEvaluationResult(entry.contract_id, "passed", [])
