"""Investigator evidence validation and merge helpers.

Traceability: HISYS-T-027, HISYS-INST-INV-001, HISYS-FR-INV-001..006,
HISYS-FR-MEM-001..005, HISYS-DATA-002.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .research import ClaimRecord, EvidenceItem, EvidencePackage


class EvidenceValidationError(ValueError):
    """Raised when an EvidencePackage violates HISYS-T-027 safety rules."""


class MergedEvidence(BaseModel):
    """Validated evidence merged across multiple research agents."""

    package_refs: list[str]
    task_refs: list[str]
    agent_ids: list[str]
    claims: list[ClaimRecord]
    evidence: list[EvidenceItem]
    limitations: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


def validate_evidence_package(package: EvidencePackage) -> None:
    """Validate a research agent evidence package before memo synthesis."""

    if package.external_side_effects:
        raise EvidenceValidationError(
            f"EvidencePackage {package.package_id} reports external side effects"
        )
    evidence_ids = {item.evidence_id for item in package.evidence}
    for claim in package.claims:
        if not claim.evidence_refs:
            raise EvidenceValidationError(
                f"Claim {claim.claim_id} in {package.package_id} is without evidence_refs"
            )
        missing = [ref for ref in claim.evidence_refs if ref not in evidence_ids]
        if missing:
            raise EvidenceValidationError(
                f"Claim {claim.claim_id} in {package.package_id} references missing evidence: {missing}"
            )


def _append_unique(items: list[str], values: list[str]) -> None:
    for value in values:
        if value not in items:
            items.append(value)


def merge_evidence_packages(packages: list[EvidencePackage]) -> MergedEvidence:
    """Validate and merge evidence packages from multiple research agents."""

    package_refs: list[str] = []
    task_refs: list[str] = []
    agent_ids: list[str] = []
    claims: list[ClaimRecord] = []
    evidence: list[EvidenceItem] = []
    limitations: list[str] = []
    open_questions: list[str] = []
    for package in packages:
        validate_evidence_package(package)
        package_refs.append(package.package_id)
        _append_unique(task_refs, [package.task_id])
        _append_unique(agent_ids, [package.agent_id])
        claims.extend(package.claims)
        evidence.extend(package.evidence)
        _append_unique(limitations, package.limitations)
        _append_unique(open_questions, package.open_questions)
    return MergedEvidence(
        package_refs=package_refs,
        task_refs=task_refs,
        agent_ids=agent_ids,
        claims=claims,
        evidence=evidence,
        limitations=limitations,
        open_questions=open_questions,
    )
