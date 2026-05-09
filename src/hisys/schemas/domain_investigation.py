"""Domain-general Hisys investigation schemas.

Traceability: HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001, HISYS-T-024,
HISYS-CON-010..012.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .base import BaseRecord

DomainName = Literal["codebase", "research", "business", "investment", "iso_process", "general"]
AccessMode = Literal["read_only"]
SourceType = Literal[
    "current_artifact",
    "open_source_reference",
    "previous_project_result",
    "publisher_source",
    "fixture",
    "runtime_record",
]


class DomainInvestigationConstraints(BaseModel):
    """Non-overridable safety defaults for Hermes-facing Hisys requests."""

    model_config = ConfigDict(extra="forbid")

    external_calls_allowed: bool = False
    mutation_allowed: bool = False
    credential_use_allowed: bool = False
    max_rounds: int = Field(default=3, ge=1, le=10)


class DomainOutputContract(BaseModel):
    """Compact output expectations for a Hisys tool result."""

    model_config = ConfigDict(extra="forbid")

    include_summary: bool = True
    include_recommended_alternative: bool = True
    include_runtime_boundary_refs: bool = True
    include_quality_gate: bool = True


class DomainSourceRef(BaseModel):
    """Source reference allowed into a domain investigation."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    source_type: SourceType
    ref: str
    access_mode: AccessMode = "read_only"
    sensitivity: str = "normal"
    license_status: str | None = None
    provenance_ref: str | None = None


class DomainInvestigationRequest(BaseRecord):
    """Hermes-facing request envelope for domain-general investigation."""

    REQUIREMENTS = (
        "HISYS-FR-INV-001",
        "HISYS-FR-INV-002",
        "HISYS-FR-INV-003",
        "HISYS-CON-010",
        "HISYS-CON-011",
        "HISYS-CON-012",
    )

    request_id: str
    domain: DomainName
    objective: str
    sources: list[DomainSourceRef]
    constraints: DomainInvestigationConstraints = Field(default_factory=DomainInvestigationConstraints)
    output_contract: DomainOutputContract = Field(default_factory=DomainOutputContract)
    user_focus: str | None = None
    config_snapshot_refs: list[str] = Field(default_factory=list)
    prompt_bundle_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _enforce_safe_defaults(self) -> "DomainInvestigationRequest":
        if self.constraints.mutation_allowed:
            raise ValueError("Domain investigation MVP requests must keep mutation_allowed=false")
        if self.constraints.credential_use_allowed:
            raise ValueError("Domain investigation MVP requests must keep credential_use_allowed=false")
        return self


class DomainEvidencePackage(BaseModel):
    """Normalized evidence package produced by a domain adapter."""

    model_config = ConfigDict(extra="forbid")

    package_id: str
    domain: DomainName
    evidence_type: str
    summary: str
    evidence_refs: list[str]
    source_refs: list[str]
    claims: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    external_call_made: bool = False
    mutation_performed: bool = False

    @model_validator(mode="after")
    def _evidence_is_boundary_safe(self) -> "DomainEvidencePackage":
        if self.external_call_made:
            raise ValueError("DomainEvidencePackage cannot report external_call_made=true in MVP")
        if self.mutation_performed:
            raise ValueError("DomainEvidencePackage cannot report mutation_performed=true")
        return self


class InvestigationDataPackage(BaseModel):
    """System-of-record bundle for evidence gathered for one investigation."""

    model_config = ConfigDict(extra="forbid")

    investigation_id: str
    request_id: str
    domain: DomainName
    objective: str
    evidence_packages: list[DomainEvidencePackage]
    source_governance_refs: list[str] = Field(default_factory=list)
    runtime_boundary_refs: list[str] = Field(default_factory=list)


class CandidateRecord(BaseModel):
    """A possible direction, design, or decision candidate with evidence links."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str
    candidate_type: str
    claim: str
    evidence_refs: list[str]
    value: str
    costs: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    next_increment: str | None = None


class AlternativeDecisionSet(BaseModel):
    """Explicit alternative set prepared for DARS critique and human review."""

    model_config = ConfigDict(extra="forbid")

    alternative_set_id: str
    request_id: str
    candidates: list[CandidateRecord]
    baseline_option: str = "request_more_evidence"
    recommended_candidate_id: str | None = None

    @model_validator(mode="after")
    def _recommended_candidate_must_exist(self) -> "AlternativeDecisionSet":
        if self.recommended_candidate_id is None:
            return self
        candidate_ids = {candidate.candidate_id for candidate in self.candidates}
        if self.recommended_candidate_id not in candidate_ids:
            raise ValueError("recommended_candidate_id must reference a candidate")
        return self


class DomainInvestigationResult(BaseModel):
    """Full local Hisys result before compact Hermes-facing projection."""

    model_config = ConfigDict(extra="forbid")

    result_id: str
    request_id: str
    domain: DomainName
    investigation_data: InvestigationDataPackage
    alternative_decision_set: AlternativeDecisionSet
    recommendation_summary: str
    dars_refs: list[str] = Field(default_factory=list)
    runtime_boundary_refs: list[str] = Field(default_factory=list)
    quality_gate: Literal["passed", "needs_more_evidence", "failed"] = "passed"
    requires_human_review: bool = True
    external_call_made: bool = False
    mutation_performed: bool = False

    @property
    def recommended_alternative_id(self) -> str | None:
        return self.alternative_decision_set.recommended_candidate_id


class HisysToolResult(BaseModel):
    """Compact result intended for Hermes after Hisys preserves full evidence."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["completed", "needs_more_evidence", "failed"]
    domain: DomainName
    summary: str
    recommended_alternative_id: str | None = None
    requires_human_review: bool
    external_call_made: bool
    mutation_performed: bool
    runtime_boundary_refs: list[str]
    quality_gate: str

    @classmethod
    def from_domain_result(cls, result: DomainInvestigationResult) -> "HisysToolResult":
        status = "completed" if result.quality_gate == "passed" else result.quality_gate
        return cls(
            status=status,
            domain=result.domain,
            summary=result.recommendation_summary,
            recommended_alternative_id=result.recommended_alternative_id,
            requires_human_review=result.requires_human_review,
            external_call_made=result.external_call_made,
            mutation_performed=result.mutation_performed,
            runtime_boundary_refs=result.runtime_boundary_refs,
            quality_gate=result.quality_gate,
        )


__all__ = [
    "AlternativeDecisionSet",
    "CandidateRecord",
    "DomainEvidencePackage",
    "DomainInvestigationConstraints",
    "DomainInvestigationRequest",
    "DomainInvestigationResult",
    "DomainOutputContract",
    "DomainSourceRef",
    "HisysToolResult",
    "InvestigationDataPackage",
]
