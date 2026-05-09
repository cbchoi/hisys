"""Canonical Hisys ↔ DARS protocol envelope models.

The models in this module validate the JSON-first boundary contract documented in
``docs/contracts/dars-data-format.md``. They intentionally preserve the current
safety posture: DARS may critique and recommend, but it cannot execute, mutate,
approve, block, or perform external side effects.

Traceability: HISYS-DARS-CONTRACT-001, HISYS-FR-AGT-001..005,
HISYS-T-019, HISYS-T-020, HISYS-T-024, HISYS-CON-010, HISYS-CON-011,
HISYS-CON-012.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Severity = Literal["none", "low", "medium", "high", "critical"]
Confidence = Literal["low", "medium", "high", "mixed", "insufficient_evidence"]


class DarsRequestContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    output_schema_id: Literal["hisys.dars.critique"]
    output_schema_version: Literal["0.1.0"]
    allowed_actions: Literal["advisory_only"]
    external_side_effects_allowed: Literal[False]
    mutation_allowed: Literal[False]
    requires_structured_output: Literal[True]


class DarsPromptBundleRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt_bundle_id: str
    prompt_bundle_version: str
    registry_backend: Literal["file", "database"]
    tenant_scope: str
    status: Literal["approved"]
    sha256: str


class DarsRolePrompt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objective: str
    focus: str | None = None


class DarsRoleProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_id: str
    kind: str
    profession: str
    persona: str
    knowledge_scope: list[str] = Field(default_factory=list)
    stance: str
    strictness: Literal["low", "medium", "high"]
    creativity: Literal["low", "medium", "high"]
    verbosity: Literal["concise_structured", "detailed_structured"]
    critique_dimensions: list[str] = Field(default_factory=list)
    prompt: DarsRolePrompt


class DarsSampling(BaseModel):
    model_config = ConfigDict(extra="forbid")

    temperature: float = Field(ge=0, le=1)
    top_p: float = Field(gt=0, le=1)
    max_output_tokens: int = Field(ge=1, le=32000)


class DarsDecisionProcess(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["progressive_adversarial", "single_pass_critique", "human_review_assist"]
    objective: str
    blocking_policy: Literal["advisory_only"]
    round_index: int = Field(ge=1)
    max_rounds: int = Field(ge=1)
    stop_condition: str

    @model_validator(mode="after")
    def _round_within_bounds(self) -> "DarsDecisionProcess":
        if self.round_index > self.max_rounds:
            raise ValueError("round_index must be less than or equal to max_rounds")
        return self


class DarsRubricRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rubric_id: str
    rubric_version: str
    artifact_ref: str
    sha256: str
    applies_to_roles: list[str] = Field(default_factory=list)


class DarsCriticPanelMember(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_id: str
    profession: str
    persona: str
    knowledge_scope: list[str] = Field(default_factory=list)


class DarsHandoffContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    handoff_type: Literal["critique", "risk_review", "requirements_review", "evidence_gap_review"]
    requester: str
    task: str
    context_summary: str
    expected_output: Literal["DarsCritiqueRecord"]
    due_condition: str | None = None


class DarsRecordRefs(BaseModel):
    model_config = ConfigDict(extra="allow")

    sources: list[str] = Field(default_factory=list)
    observations: list[str] = Field(default_factory=list)
    signals: list[str] = Field(default_factory=list)
    memos: list[str] = Field(default_factory=list)
    alerts: list[str] = Field(default_factory=list)
    handoffs: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    runtime_boundary: list[str] = Field(default_factory=list)


class DarsEvidenceBundleRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_ref: str
    artifact_ref: str
    sha256: str
    summary: str
    relevance: Literal["primary", "secondary", "context", "limitation"]


class DarsEvidenceRefs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bundles: list[DarsEvidenceBundleRef] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class DarsRequestConstraints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_refs: list[str] = Field(default_factory=list)
    policy_refs: list[str] = Field(default_factory=list)
    prohibited_actions: list[Literal["external_call", "file_write", "alert_send", "software_trigger"]] = Field(default_factory=list)
    approval_state: Literal["not_required", "pending", "approved", "rejected"]
    approval_ref: str | None = None


class DarsUserFocus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str | None = None


class DarsRequestEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_id: Literal["hisys.dars.request"]
    schema_version: Literal["0.1.0"]
    request_id: str
    handoff_id: str
    created_at: str
    contract: DarsRequestContract
    prompt_bundle_ref: DarsPromptBundleRef
    role: DarsRoleProfile
    sampling: DarsSampling
    decision_process: DarsDecisionProcess
    rubric_refs: list[DarsRubricRef]
    critic_panel: list[DarsCriticPanelMember] = Field(default_factory=list)
    handoff: DarsHandoffContext
    record_refs: DarsRecordRefs
    evidence: DarsEvidenceRefs
    constraints: DarsRequestConstraints
    user_focus: DarsUserFocus | None = None


class DarsProducer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    backend_id: str
    backend_kind: str
    role_id: str
    model: str | None = None
    external_call_made: bool = False


class DarsUnsupportedClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_ref: str
    statement: str
    reason: str
    evidence_refs: list[str] = Field(default_factory=list)
    severity: Severity


class DarsCounterargument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    argument_id: str
    statement: str
    evidence_refs: list[str] = Field(default_factory=list)
    strength: Literal["low", "medium", "high"]


class DarsRiskFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risk_id: str
    category: str
    statement: str
    severity: Severity
    mitigation: str | None = None


class DarsRecommendedAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_id: str
    action_type: Literal[
        "request_more_evidence",
        "revise_memo",
        "revise_alert",
        "open_review_item",
        "open_capa_candidate",
        "reject_claim",
        "lower_confidence",
        "escalate_to_human",
    ]
    statement: str
    priority: Literal["low", "medium", "high", "critical"]
    requires_approval: bool = True
    allowed_to_execute: Literal[False] = False


class DarsStructuredCritique(BaseModel):
    model_config = ConfigDict(extra="forbid")

    critique_id: str
    status: Literal["received", "linked", "rejected", "closed"]
    critique_summary: str
    confidence_assessment: Confidence
    severity: Severity
    requires_human_review: bool = True
    unsupported_claims: list[DarsUnsupportedClaim] = Field(default_factory=list)
    counterarguments: list[DarsCounterargument] = Field(default_factory=list)
    risk_findings: list[DarsRiskFinding] = Field(default_factory=list)
    recommended_actions: list[DarsRecommendedAction] = Field(default_factory=list)
    linked_record_refs: DarsRecordRefs = Field(default_factory=DarsRecordRefs)


class DarsDecisionTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    process_mode: Literal["progressive_adversarial", "single_pass_critique", "human_review_assist"]
    round_index: int = Field(ge=1)
    critic_role_id: str
    critic_profession: str
    critic_persona: str
    prompt_bundle_ref: str
    rubric_refs: list[str] = Field(default_factory=list)
    improvement_direction: Literal[
        "accept_candidate",
        "revise_candidate",
        "request_more_evidence",
        "lower_confidence",
        "split_decision",
        "escalate_to_human",
    ]
    blocks_decision: Literal[False] = False
    unresolved_high_severity_findings: int = Field(ge=0)
    synthesis_summary: str


class DarsRubricScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    axis_id: str
    score: int = Field(ge=0)
    max_score: int = Field(ge=1)
    severity: Severity
    confidence: Confidence
    rationale: str
    evidence_refs: list[str] = Field(default_factory=list)
    improvement_recommendation: str | None = None

    @model_validator(mode="after")
    def _score_within_bounds(self) -> "DarsRubricScore":
        if self.score > self.max_score:
            raise ValueError("score must be less than or equal to max_score")
        return self


class DarsAdapterValidation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_valid: bool
    warnings: list[str] = Field(default_factory=list)
    rejected_fields: list[str] = Field(default_factory=list)


class DarsBoundaryEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allowed_actions: Literal["advisory_only"]
    action_taken: Literal["none"] = "none"
    mutation_requested: bool = False
    mutation_performed: Literal[False] = False
    external_side_effects_requested: bool = False
    external_side_effects_performed: Literal[False] = False

    @field_validator("mutation_requested", "external_side_effects_requested")
    @classmethod
    def _requests_remain_false(cls, value: bool) -> bool:
        if value:
            raise ValueError("DARS responses may not request mutation or external side effects")
        return value


class DarsResponseEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_id: Literal["hisys.dars.response"]
    schema_version: Literal["0.1.0"]
    response_id: str
    request_id: str
    handoff_id: str
    created_at: str
    producer: DarsProducer
    critique: DarsStructuredCritique
    decision_trace: DarsDecisionTrace
    rubric_scores: list[DarsRubricScore]
    validation: DarsAdapterValidation
    boundary: DarsBoundaryEvidence


__all__ = [
    "DarsRequestEnvelope",
    "DarsResponseEnvelope",
    "DarsRequestContract",
    "DarsStructuredCritique",
    "DarsRecommendedAction",
    "DarsBoundaryEvidence",
]
