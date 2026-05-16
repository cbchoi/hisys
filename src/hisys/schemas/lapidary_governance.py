"""Hisys Lapidary governance schemas.

Traceability:
- HISYS-SCHEMA-001: machine-readable governed record shapes.
- HISYS-FR-INV-001..006 and HISYS-T-024: evidence-backed domain investigation.
- HISYS-DARS-CONTRACT-001: DARS/Devil remains advisory and separated.
- HISYS-CON-010..012: runtime/evidence boundary preservation.

These schemas encode the Stone/Gem/Jewel-oriented governance layer without
renaming Hisys core. Metaphor names are display/role-layer metadata; structured
Hisys links remain the source of truth.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

from ..core.ids import validate_id
from .base import BaseRecord

HisysModeLevel = Literal["none", "stone", "claim", "synthesis", "decision", "publication"]
LapidaryMetaphor = Literal["Miner", "Cutter", "Artisan", "Appraiser", "Jeweler", "Curator", "Vault Steward"]
EvidenceOrigin = Literal[
    "external_source",
    "internal_prior",
    "human_decision",
    "agent_synthesis",
    "runtime_observation",
]
DecisionUse = Literal["internal_prior", "external_evidence", "hybrid", "conditional_decision", "request_more_evidence"]
TemporalDecayStage = Literal[
    "fresh",
    "aging",
    "stale",
    "deprecated",
    "archive_candidate",
    "archive",
]


class HisysMode(BaseModel):
    """Selective Hisys governance mode for a note, request, or artifact.

    Hisys governance is intentionally opt-in by consequence level. The default is
    no Hisys governance, and agents may upgrade artifacts when evidence, claim,
    synthesis, decision, or publication consequences justify the overhead.
    """

    model_config = ConfigDict(extra="forbid")

    level: HisysModeLevel = "none"
    selective_governance: bool = True
    applies_to_all_notes: bool = False
    upgrade_triggers: list[str] = Field(default_factory=list)
    routing_policy_ref: str | None = None

    @model_validator(mode="after")
    def _must_remain_selective(self) -> "HisysMode":
        if not self.selective_governance or self.applies_to_all_notes:
            raise ValueError("Hisys mode must preserve selective governance; it must not apply to all notes")
        return self


class EvidenceChainRecord(BaseRecord):
    """Downward evidence-chain record for Jewel-to-Stone traceability.

    The intended traversal is:
    decision/Jewel -> synthesis/Gem -> claim ledger -> evidence/Stone -> attachment/source.
    Obsidian wikilinks may project this relation for people, but Hisys structured
    links remain the governance source of truth.
    """

    REQUIREMENTS: ClassVar[tuple[str, ...]] = (
        "HISYS-SCHEMA-001",
        "HISYS-FR-INV-001",
        "HISYS-FR-INV-003",
        "HISYS-T-024",
    )

    chain_id: str
    decision_ref: str | None = None
    synthesis_refs: list[str] = Field(default_factory=list)
    claim_ledger_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    attachment_refs: list[str] = Field(default_factory=list)
    structured_links_source_of_truth: bool = True
    wikilinks_are_projection: bool = True

    @field_validator("chain_id")
    @classmethod
    def _chain_id(cls, value: str) -> str:
        validate_id(value)
        if not value.startswith("CHAIN-"):
            raise ValueError(f"chain_id must start with 'CHAIN-': {value!r}")
        return value

    @field_validator("decision_ref")
    @classmethod
    def _non_blank_decision_ref(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("decision_ref must not be blank")
        return value

    @field_validator(
        "synthesis_refs",
        "claim_ledger_refs",
        "evidence_refs",
        "source_refs",
        "attachment_refs",
    )
    @classmethod
    def _non_blank_ref_lists(cls, value: list[str]) -> list[str]:
        for ref in value:
            if not ref or not ref.strip():
                raise ValueError("evidence chain refs must not be blank")
        return value

    @model_validator(mode="after")
    def _requires_downward_trace(self) -> "EvidenceChainRecord":
        if not self.evidence_refs:
            raise ValueError("evidence chains require evidence_refs")
        if not self.source_refs:
            raise ValueError("evidence chains require source_refs")
        if self.decision_ref is not None:
            if not self.synthesis_refs:
                raise ValueError("decision/Jewel evidence chains require synthesis_refs")
            if not self.claim_ledger_refs:
                raise ValueError("decision/Jewel evidence chains require claim_ledger_refs")
        if not self.structured_links_source_of_truth:
            raise ValueError("structured links must remain the governance source of truth")
        if not self.wikilinks_are_projection:
            raise ValueError("wikilinks must remain human-navigation projections")
        return self

    @computed_field(exclude_if=lambda _: True)  # type: ignore[misc]
    @property
    def path_summary(self) -> str:
        return "decision/Jewel -> synthesis/Gem -> claim ledger -> evidence/Stone -> attachment/source"


class LapidaryRoleAssignment(BaseRecord):
    """Role-layer mapping that keeps metaphor labels separate from technical schema."""

    REQUIREMENTS: ClassVar[tuple[str, ...]] = ("HISYS-SCHEMA-001", "HISYS-DARS-CONTRACT-001")

    role_id: str
    agent_role: str
    function: str
    display_metaphor: LapidaryMetaphor
    technical_type: str

    @field_validator("role_id")
    @classmethod
    def _role_id(cls, value: str) -> str:
        validate_id(value)
        if not value.startswith("ROLE-"):
            raise ValueError(f"role_id must start with 'ROLE-': {value!r}")
        return value


class TemporalArchivePolicy(BaseRecord):
    """Temporal decay policy for time-sensitive artifacts.

    Time-sensitive evidence may become stale, but it remains historical evidence.
    The policy therefore archives instead of deleting.
    """

    REQUIREMENTS: ClassVar[tuple[str, ...]] = ("HISYS-SCHEMA-001", "HISYS-FR-INV-003")

    policy_id: str
    temporal_class: str
    current_stage: TemporalDecayStage
    next_stage: TemporalDecayStage
    delete_allowed: bool = False
    preserve_historical_evidence: bool = True
    review_due: str

    @field_validator("policy_id")
    @classmethod
    def _policy_id(cls, value: str) -> str:
        validate_id(value)
        if not value.startswith("ARCHIVE-POLICY-"):
            raise ValueError(f"policy_id must start with 'ARCHIVE-POLICY-': {value!r}")
        return value

    @model_validator(mode="after")
    def _archive_not_delete(self) -> "TemporalArchivePolicy":
        if self.delete_allowed or not self.preserve_historical_evidence:
            raise ValueError("TemporalArchivePolicy must keep delete_allowed=false and archive historical evidence")
        return self


class EvidenceOriginWeight(BaseModel):
    """Weight dimensions for one internal/external evidence origin."""

    model_config = ConfigDict(extra="forbid")

    evidence_origin: EvidenceOrigin
    ref: str
    origin_weight: float = Field(ge=0.0, le=1.0)
    source_quality: float = Field(ge=0.0, le=1.0)
    verification_status: float = Field(ge=0.0, le=1.0)
    recency: float = Field(ge=0.0, le=1.0)
    independence: float = Field(ge=0.0, le=1.0)
    contradiction_status: float = Field(ge=0.0, le=1.0)
    domain_fit: float = Field(ge=0.0, le=1.0)

    @computed_field  # type: ignore[misc]
    @property
    def score(self) -> float:
        return round(
            (
                self.source_quality
                + self.verification_status
                + self.recency
                + self.independence
                + self.contradiction_status
                + self.domain_fit
            )
            / 6,
            4,
        )


class WeightedDecisionAlternative(BaseRecord):
    """Decision alternative that makes internal/external evidence weighting explicit."""

    REQUIREMENTS: ClassVar[tuple[str, ...]] = (
        "HISYS-SCHEMA-001",
        "HISYS-FR-INV-003",
        "HISYS-DARS-CONTRACT-001",
    )

    alternative_id: str
    label: str
    claim: str
    origin_weights: list[EvidenceOriginWeight]
    recommended_use: DecisionUse
    limitations: list[str] = Field(default_factory=list)

    @field_validator("alternative_id")
    @classmethod
    def _alternative_id(cls, value: str) -> str:
        validate_id(value)
        if not value.startswith("ALT-"):
            raise ValueError(f"alternative_id must start with 'ALT-': {value!r}")
        return value

    @model_validator(mode="after")
    def _requires_weights(self) -> "WeightedDecisionAlternative":
        if not self.origin_weights:
            raise ValueError("WeightedDecisionAlternative requires origin_weights")
        if sum(weight.origin_weight for weight in self.origin_weights) <= 0:
            raise ValueError("WeightedDecisionAlternative requires positive total origin_weight")
        return self

    @computed_field  # type: ignore[misc]
    @property
    def origin_summary(self) -> list[EvidenceOrigin]:
        return [weight.evidence_origin for weight in self.origin_weights]

    @computed_field  # type: ignore[misc]
    @property
    def weighted_score(self) -> float:
        total = sum(weight.origin_weight for weight in self.origin_weights)
        weighted_sum = sum(weight.origin_weight * weight.score for weight in self.origin_weights)
        return round(weighted_sum / total, 4)


class AppraiserSeparationPolicy(BaseRecord):
    """DARS/Devil separation policy.

    DARS/Devil may critique and recommend revisions, but Hisys preserves it
    as advisory-only and separate from Chief Editor/Jeweler decision authority.
    """

    REQUIREMENTS: ClassVar[tuple[str, ...]] = ("HISYS-DARS-CONTRACT-001", "HISYS-SCHEMA-001")

    policy_id: str
    appraiser_role: str
    separate_from_roles: list[str]
    advisory_only: bool = True
    may_approve_decision: bool = False
    may_execute_action: bool = False
    checks: list[str] = Field(default_factory=list)

    @field_validator("policy_id")
    @classmethod
    def _policy_id(cls, value: str) -> str:
        validate_id(value)
        if not value.startswith("APPRAISER-POLICY-"):
            raise ValueError(f"policy_id must start with 'APPRAISER-POLICY-': {value!r}")
        return value

    @model_validator(mode="after")
    def _advisory_separate_only(self) -> "AppraiserSeparationPolicy":
        if not self.advisory_only or self.may_approve_decision or self.may_execute_action:
            raise ValueError("Devil/DARS policy must remain advisory only and cannot approve or execute")
        if not self.separate_from_roles:
            raise ValueError("Devil/DARS policy must list separated decision roles")
        return self


__all__ = [
    "AppraiserSeparationPolicy",
    "EvidenceChainRecord",
    "EvidenceOriginWeight",
    "HisysMode",
    "LapidaryRoleAssignment",
    "TemporalArchivePolicy",
    "WeightedDecisionAlternative",
]
