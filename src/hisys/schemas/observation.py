"""``RawObservation`` schema (immutable raw evidence record).

Traceability:
- HISYS-FR-INV-002..005 (raw observation IDs, payload reference, integrity,
  data quality, retention).
- HISYS-DATA-001..004 (stable IDs, evidence/interpretation separation,
  retention).
- HISYS-DATA-005 (Hermes provenance fields when applicable).
- HISYS-SCHEMA-001 Section 4; HISYS-IDD-001 Section 5.2.
"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..core.ids import IdNamespace, validate_id
from .base import BaseRecord

ObservationStatus = Literal[
    "captured", "referenced", "quarantined", "redacted", "retained", "expired"
]
ApprovalState = Literal[
    "preapproved", "requested", "approved", "rejected", "blocked", "not_required"
]


class DataQuality(BaseModel):
    model_config = ConfigDict(extra="forbid")

    completeness: str
    freshness: str
    anomaly_flags: list[str] = Field(default_factory=list)
    source_confidence: float = Field(ge=0.0, le=1.0)


class ProvenanceBundle(BaseModel):
    """Provenance metadata.

    For Hermes collection (HISYS-IDD-001 Section 5.2; HISYS-DATA-005) the
    fields ``campaign_id``, ``hermes_parent_run_id``, ``user_input_ref``,
    ``prompt_or_query_ref``, ``tool_output_ref``, ``boundary_record_ref``,
    ``working_directory``, ``scope_policy_ref``, ``approval_state`` and
    ``audit_event_refs`` are required and validated at construction time.
    """

    model_config = ConfigDict(extra="forbid")

    collector_kind: Literal[
        "hardware_sensor", "web_news", "agent_system", "hermes_tool"
    ]

    # Generic provenance (all collector kinds may populate these).
    method: str | None = None
    device_identity: str | None = None
    calibration_ref: str | None = None
    citation_url: str | None = None
    citation_title: str | None = None
    fetch_method: str | None = None
    agent_identity: str | None = None
    agent_advisory_label: str | None = None

    # Hermes hierarchical collection fields (HISYS-IDD-001 5.2, HISYS-SCHEMA-001 10).
    campaign_id: str | None = None
    hermes_parent_run_id: str | None = None
    user_input_ref: str | None = None
    delegated_task_id: str | None = None
    delegated_subagent_preapproval_ref: str | None = None
    tool_invocation_id: str | None = None
    tool_name: str | None = None
    enabled_toolsets: list[str] = Field(default_factory=list)
    prompt_or_query_ref: str | None = None
    tool_output_ref: str | None = None
    boundary_record_ref: str | None = None
    working_directory: str | None = None
    scope_policy_ref: str | None = None
    approval_state: ApprovalState | None = None
    audit_event_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _hermes_required_fields(self) -> "ProvenanceBundle":
        if self.collector_kind == "hermes_tool":
            required = {
                "campaign_id": self.campaign_id,
                "hermes_parent_run_id": self.hermes_parent_run_id,
                "user_input_ref": self.user_input_ref,
                "prompt_or_query_ref": self.prompt_or_query_ref,
                "tool_output_ref": self.tool_output_ref,
                "boundary_record_ref": self.boundary_record_ref,
                "working_directory": self.working_directory,
                "scope_policy_ref": self.scope_policy_ref,
                "approval_state": self.approval_state,
            }
            missing = [k for k, v in required.items() if not v]
            if missing:
                raise ValueError(
                    "hermes_tool provenance missing required fields: "
                    + ", ".join(missing)
                )
        return self


class RawObservation(BaseRecord):
    REQUIREMENTS: ClassVar[tuple[str, ...]] = (
        "HISYS-FR-INV-002",
        "HISYS-FR-INV-003",
        "HISYS-FR-INV-004",
        "HISYS-FR-INV-005",
        "HISYS-FR-INV-006",
        "HISYS-DATA-001",
        "HISYS-DATA-002",
        "HISYS-DATA-003",
        "HISYS-DATA-004",
        "HISYS-DATA-005",
    )

    observation_id: str
    source_id: str
    collection_run_id: str
    collected_at: datetime
    collector_id: str
    payload_ref: str
    payload_hash: str
    provenance_bundle: ProvenanceBundle
    data_quality: DataQuality
    usage_constraints: list[str] = Field(default_factory=list)
    retention_rule: str
    status: ObservationStatus = "captured"

    @field_validator("observation_id")
    @classmethod
    def _obs_id(cls, v: str) -> str:
        validate_id(v)
        if not v.startswith(IdNamespace.OBSERVATION.value + "-"):
            raise ValueError(f"observation_id must start with 'OBS-': {v!r}")
        return v

    @field_validator("source_id")
    @classmethod
    def _src_id(cls, v: str) -> str:
        validate_id(v)
        if not v.startswith(IdNamespace.SOURCE.value + "-"):
            raise ValueError(f"source_id must start with 'SRC-': {v!r}")
        return v
