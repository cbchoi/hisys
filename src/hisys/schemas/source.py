"""``SourceRegistryEntry`` schema.

Traceability:
- HISYS-FR-SRC-001..005 (source identity, lifecycle, reliability, cadence,
  rate limit, usage constraints, retention, approval).
- HISYS-NFR-SEC-003, HISYS-NFR-SEC-005 (compliance review and access
  control non-bypass for web/news sources).
- HISYS-SCHEMA-001 Section 3.
- HISYS-IDD-001 Section 5.1.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field, field_validator, model_validator

from ..core.ids import IdNamespace, validate_id
from .base import BaseRecord

SourceType = Literal["hardware_sensor", "web_news", "agent_system", "hermes_tool"]
LifecycleState = Literal[
    "proposed", "experimental", "approved", "suspended", "retired", "blocked"
]
ReliabilityClass = Literal["A", "B", "C", "D", "X", "TBD"]
AccessMethod = Literal[
    "api",
    "rss",
    "file",
    "device",
    "webhook",
    "agent_handoff",
    "hermes_user_input",
    "hermes_tool",
    "hermes_cron",
    "hermes_delegate",
    "manual",
]
HighImpactClass = Literal[
    "none", "communication", "software_trigger", "public_or_irreversible", "TBD"
]


class SourceRegistryEntry(BaseRecord):
    REQUIREMENTS: ClassVar[tuple[str, ...]] = (
        "HISYS-FR-SRC-001",
        "HISYS-FR-SRC-002",
        "HISYS-FR-SRC-003",
        "HISYS-FR-SRC-004",
        "HISYS-FR-SRC-005",
        "HISYS-NFR-SEC-003",
        "HISYS-NFR-SEC-005",
        "HISYS-DATA-001",
    )

    source_id: str
    source_type: SourceType
    display_name: str
    owner: str
    lifecycle_state: LifecycleState = "proposed"
    reliability_class: ReliabilityClass = "TBD"
    reliability_evidence: list[str] = Field(default_factory=list)
    access_method: AccessMethod
    cadence: str
    rate_limit: str
    usage_constraints: list[str] = Field(default_factory=list)
    retention_rule: str
    credential_ref: str | None = None
    compliance_review_ref: str | None = None
    approved_by: str | None = None
    delegated_subagent_preapproval_ref: str | None = None
    scope_policy_ref: str | None = None
    high_impact_external_action_class: HighImpactClass = "none"
    chief_editor_policy_ref: str | None = None

    status: LifecycleState = "proposed"

    @field_validator("source_id")
    @classmethod
    def _id_shape(cls, v: str) -> str:
        return validate_id(v) if v.startswith(IdNamespace.SOURCE.value + "-") else (_ for _ in ()).throw(
            ValueError(f"source_id must start with '{IdNamespace.SOURCE.value}-': {v!r}")
        )

    @model_validator(mode="after")
    def _compliance_gate(self) -> "SourceRegistryEntry":
        # HISYS-NFR-SEC-005 / HISYS-IDD-001 Section 6: web/news cannot be
        # 'approved' without a compliance review reference.
        if (
            self.source_type == "web_news"
            and self.lifecycle_state == "approved"
            and not self.compliance_review_ref
        ):
            raise ValueError(
                "web_news source cannot be 'approved' without compliance_review_ref"
            )
        # HISYS-FR-DS-006 / HISYS-T-005A: Hermes tool sources require a
        # scope policy reference once they leave the 'proposed' state.
        if (
            self.source_type == "hermes_tool"
            and self.lifecycle_state in ("experimental", "approved")
            and not self.scope_policy_ref
        ):
            raise ValueError(
                "hermes_tool source past 'proposed' requires scope_policy_ref"
            )
        return self
