"""Formal schemas for governed browser acceptance artifacts.

Traceability:
- HISYS-FR-INV-001..006 (evidence package review and investigation boundaries).
- HISYS-FR-AGT-001..005 (advisory DARS/Devil handoff boundary).
- HISYS-DARS-CONTRACT-001 (DARS remains advisory and non-executable).
- HISYS-SCHEMA-001 (machine-checkable runtime artifacts).
- HISYS-IDD-001 (runtime boundary records and side-effect controls).
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


BrowserRevisionDecision = Literal[
    "ready_for_final_acceptance_review",
    "revision_required_before_final_acceptance",
]
BrowserGateStatus = Literal["complete", "incomplete"]
BrowserCompetitiveSignalStrength = Literal["high", "medium", "low", "unspecified"]
BrowserAcceptanceDecision = Literal["accept_for_human_reviewed_use"]


class BrowserDarsSegmentNormalizationRow(BaseModel):
    """Per-row segment normalization result for Browser-G."""

    model_config = ConfigDict(extra="forbid")

    row_index: int = Field(ge=1)
    company_or_source: str = Field(min_length=1)
    normalized_segment: str = Field(min_length=1)
    basis: Literal["explicit_row_segment", "heuristic_from_row_text"]


class BrowserDarsCorroborationMappingRow(BaseModel):
    """Per-row independent corroboration mapping result for Browser-G."""

    model_config = ConfigDict(extra="forbid")

    row_index: int = Field(ge=1)
    company_or_source: str = Field(min_length=1)
    competitive_signal_strength: BrowserCompetitiveSignalStrength
    corroborating_evidence_class: str = Field(min_length=1)
    independent_corroboration_present: bool
    evidence_refs: list[str] = Field(default_factory=list)


class BrowserDarsRevisionResolution(BaseModel):
    """Formal Browser-G revision-resolution artifact.

    This schema encodes the DARS revision gate only. A ready decision authorizes
    final Chief Editor review, not publication, mutation, or live external action.
    """

    model_config = ConfigDict(extra="forbid")

    REQUIREMENTS: ClassVar[tuple[str, ...]] = (
        "HISYS-FR-INV-001",
        "HISYS-FR-INV-002",
        "HISYS-FR-INV-003",
        "HISYS-FR-INV-004",
        "HISYS-FR-INV-005",
        "HISYS-FR-INV-006",
        "HISYS-FR-AGT-001",
        "HISYS-FR-AGT-002",
        "HISYS-FR-AGT-003",
        "HISYS-FR-AGT-004",
        "HISYS-FR-AGT-005",
        "HISYS-DARS-CONTRACT-001",
        "HISYS-SCHEMA-001",
        "HISYS-IDD-001",
    )

    schema_id: Literal["hisys.browser_dars_revision_resolution"] = "hisys.browser_dars_revision_resolution"
    schema_version: Literal["0.1.0"] = "0.1.0"
    request_id: str = Field(min_length=1)
    dars_review_ref: str = Field(min_length=1)
    chief_editor_review_ref: str = Field(min_length=1)
    competitive_matrix_ref: str = Field(min_length=1)
    decision: BrowserRevisionDecision
    segment_normalization_status: BrowserGateStatus
    corroboration_mapping_status: BrowserGateStatus
    segment_normalization_rows: list[BrowserDarsSegmentNormalizationRow] = Field(min_length=1)
    corroboration_mapping_rows: list[BrowserDarsCorroborationMappingRow] = Field(min_length=1)
    resolved_dars_revision_items: list[str] = Field(default_factory=list)
    remaining_blockers: list[str] = Field(default_factory=list)
    final_acceptance_allowed: bool
    allowed_actions: Literal["advisory_only"] = "advisory_only"
    external_call_made: Literal[False] = False
    mutation_performed: Literal[False] = False
    producer_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def _gate_consistency(self) -> "BrowserDarsRevisionResolution":
        ready = self.decision == "ready_for_final_acceptance_review"
        all_gates_complete = (
            self.segment_normalization_status == "complete"
            and self.corroboration_mapping_status == "complete"
            and not self.remaining_blockers
        )
        if ready and not all_gates_complete:
            raise ValueError("ready_for_final_acceptance_review requires complete gates and no blockers")
        if self.final_acceptance_allowed != (ready and all_gates_complete):
            raise ValueError("final_acceptance_allowed must match Browser-G readiness gates")
        if self.segment_normalization_status == "complete" and any(
            row.normalized_segment == "unknown" for row in self.segment_normalization_rows
        ):
            raise ValueError("complete segment normalization cannot include unknown normalized_segment")
        if self.corroboration_mapping_status == "complete" and any(
            row.competitive_signal_strength == "high" and not row.independent_corroboration_present
            for row in self.corroboration_mapping_rows
        ):
            raise ValueError("complete corroboration mapping cannot include uncorroborated high-strength rows")
        return self


class BrowserDarsRevisionResolutionReport(BaseModel):
    """Run-summary schema for Browser-G."""

    model_config = ConfigDict(extra="forbid")

    REQUIREMENTS: ClassVar[tuple[str, ...]] = BrowserDarsRevisionResolution.REQUIREMENTS

    schema_id: Literal["hisys.browser_dars_revision_resolution.report"] = "hisys.browser_dars_revision_resolution.report"
    schema_version: Literal["0.1.0"] = "0.1.0"
    request_id: str = Field(min_length=1)
    dars_review_ref: str = Field(min_length=1)
    revision_resolution_ref: str = Field(min_length=1)
    decision: BrowserRevisionDecision
    segment_normalization_status: BrowserGateStatus
    corroboration_mapping_status: BrowserGateStatus
    external_call_made: Literal[False] = False
    mutation_performed: Literal[False] = False


class FinalBrowserAcceptanceReview(BaseModel):
    """Formal Browser-H final Chief Editor acceptance artifact.

    This schema accepts a browser package only for controlled human-reviewed use;
    it explicitly does not approve publication, live connector use, vault mutation,
    or consequential external action.
    """

    model_config = ConfigDict(extra="forbid")

    REQUIREMENTS: ClassVar[tuple[str, ...]] = (
        "HISYS-FR-INV-001",
        "HISYS-FR-INV-002",
        "HISYS-FR-INV-003",
        "HISYS-FR-INV-004",
        "HISYS-FR-INV-005",
        "HISYS-FR-INV-006",
        "HISYS-FR-AGT-001",
        "HISYS-FR-AGT-002",
        "HISYS-FR-AGT-003",
        "HISYS-FR-AGT-004",
        "HISYS-FR-AGT-005",
        "HISYS-DARS-CONTRACT-001",
        "HISYS-SCHEMA-001",
        "HISYS-IDD-001",
    )

    schema_id: Literal["hisys.chief_editor.final_browser_acceptance_review"] = "hisys.chief_editor.final_browser_acceptance_review"
    schema_version: Literal["0.1.0"] = "0.1.0"
    request_id: str = Field(min_length=1)
    revision_resolution_ref: str = Field(min_length=1)
    dars_review_ref: str = Field(min_length=1)
    chief_editor_review_ref: str = Field(min_length=1)
    competitive_matrix_ref: str = Field(min_length=1)
    decision: BrowserAcceptanceDecision = "accept_for_human_reviewed_use"
    accepted_conditions: list[Literal[
        "segment_normalization_complete",
        "independent_corroboration_mapping_complete",
    ]] = Field(min_length=2)
    acceptance_scope: Literal[
        "browser_investigation_evidence_package_for_human_reviewed_use"
    ] = "browser_investigation_evidence_package_for_human_reviewed_use"
    dars_role: Literal["advisory_only_non_executable"] = "advisory_only_non_executable"
    publication_or_live_action_approved: Literal[False] = False
    human_approval_required_for_consequential_use: Literal[True] = True
    external_call_made: Literal[False] = False
    mutation_performed: Literal[False] = False
    action_taken: Literal["none"] = "none"
    producer_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def _accepted_conditions_complete(self) -> "FinalBrowserAcceptanceReview":
        required = {"segment_normalization_complete", "independent_corroboration_mapping_complete"}
        if set(self.accepted_conditions) != required:
            raise ValueError("final browser acceptance requires both Browser-G accepted conditions")
        return self


class FinalBrowserAcceptanceReviewReport(BaseModel):
    """Run-summary schema for Browser-H."""

    model_config = ConfigDict(extra="forbid")

    REQUIREMENTS: ClassVar[tuple[str, ...]] = FinalBrowserAcceptanceReview.REQUIREMENTS

    schema_id: Literal[
        "hisys.chief_editor.final_browser_acceptance_review.report"
    ] = "hisys.chief_editor.final_browser_acceptance_review.report"
    schema_version: Literal["0.1.0"] = "0.1.0"
    request_id: str = Field(min_length=1)
    revision_resolution_ref: str = Field(min_length=1)
    final_review_ref: str = Field(min_length=1)
    decision: BrowserAcceptanceDecision = "accept_for_human_reviewed_use"
    publication_or_live_action_approved: Literal[False] = False
    external_call_made: Literal[False] = False
    mutation_performed: Literal[False] = False
