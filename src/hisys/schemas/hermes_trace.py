"""``HermesCollectionTrace`` schema.

Traceability:
- HISYS-FR-DS-006, HISYS-FR-INV-006, HISYS-FR-AGT-005, HISYS-DATA-005
  (Hermes hierarchical collection as a controlled, traceable source).
- HISYS-IDD-001 Section 4 (HermesToolSource subtype) and Section 6
  (Markdown boundary path convention).
- HISYS-SCHEMA-001 Section 10.
- HISYS-T-005A.
"""

from __future__ import annotations

import re
from typing import ClassVar, Literal

from pydantic import Field, field_validator, model_validator

from ..core.ids import IdNamespace, validate_id
from .base import BaseRecord

ApprovalState = Literal[
    "preapproved", "requested", "approved", "rejected", "blocked", "not_required"
]
HermesStatus = Literal[
    "planned",
    "dispatched",
    "delegated",
    "tool_running",
    "completed",
    "partial",
    "failed",
    "blocked",
    "reviewed",
]

# HISYS-IDD-001 Section 6 / HISYS-SCHEMA-001 Section 10:
#   hisys/runtime-boundary/hermes/<YYYYMMDD>/<campaign_id>/<record_kind>-<stable_id>.md
_BOUNDARY_RE = re.compile(
    r"^hisys/runtime-boundary/hermes/\d{8}/[A-Za-z0-9_\-]+/[a-z_]+-[A-Za-z0-9_\-]+\.md$"
)


class HermesCollectionTrace(BaseRecord):
    REQUIREMENTS: ClassVar[tuple[str, ...]] = (
        "HISYS-FR-DS-006",
        "HISYS-FR-INV-006",
        "HISYS-FR-AGT-005",
        "HISYS-DATA-005",
    )

    campaign_id: str
    hermes_parent_run_id: str
    delegated_task_id: str | None = None
    delegated_subagent_preapproval_ref: str | None = None
    tool_invocation_id: str | None = None
    tool_name: str | None = None
    enabled_toolsets: list[str] = Field(default_factory=list)
    source_scope: str
    user_input_ref: str | None = None
    prompt_or_query_ref: str
    tool_output_ref: str
    boundary_record_ref: str
    working_directory: str
    scope_policy_ref: str
    approval_state: ApprovalState
    raw_observation_refs: list[str] = Field(default_factory=list)
    audit_event_refs: list[str] = Field(default_factory=list)
    status: HermesStatus = "planned"

    @field_validator("campaign_id")
    @classmethod
    def _campaign(cls, v: str) -> str:
        validate_id(v)
        if not v.startswith(IdNamespace.CAMPAIGN.value + "-"):
            raise ValueError(f"campaign_id must start with 'CAMP-': {v!r}")
        return v

    @field_validator("boundary_record_ref")
    @classmethod
    def _boundary(cls, v: str) -> str:
        if not _BOUNDARY_RE.match(v):
            raise ValueError(
                "boundary_record_ref must match "
                "hisys/runtime-boundary/hermes/<YYYYMMDD>/<campaign_id>/<record_kind>-<stable_id>.md"
            )
        return v

    @field_validator("raw_observation_refs")
    @classmethod
    def _obs_refs(cls, v: list[str]) -> list[str]:
        for ref in v:
            validate_id(ref)
            if not ref.startswith(IdNamespace.OBSERVATION.value + "-"):
                raise ValueError(f"raw_observation_refs entry must start with 'OBS-': {ref!r}")
        return v

    @model_validator(mode="after")
    def _delegated_consistency(self) -> "HermesCollectionTrace":
        # HISYS-FR-AGT-005: delegated subagent collection requires a
        # preapproval reference once a delegated_task_id is present.
        if self.delegated_task_id and not self.delegated_subagent_preapproval_ref:
            raise ValueError(
                "delegated_task_id requires delegated_subagent_preapproval_ref"
            )
        return self
