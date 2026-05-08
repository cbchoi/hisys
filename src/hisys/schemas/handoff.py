"""``AgentHandoffPackage`` schema.

Traceability:
- HISYS-FR-AGT-001..005 (handoff package, critique ingestion, allowed
  actions, Hermes-delegated collection actors).
- HISYS-DARS-CONTRACT-001 Section 3 (minimum payload).
- HISYS-SCHEMA-001 Section 9; HISYS-IDD-001 Section 5.6.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field, field_validator

from ..core.ids import IdNamespace, validate_id
from .base import BaseRecord

AllowedActions = Literal[
    "advisory_only",
    "propose_change",
    "collect_with_registered_scope",
    "trigger_with_approval",
]
HandoffApprovalState = Literal[
    "not_required", "preapproved", "requested", "approved", "rejected", "blocked"
]
HandoffStatus = Literal[
    "prepared", "dispatched", "received", "linked", "rejected", "closed"
]


class AgentHandoffPackage(BaseRecord):
    REQUIREMENTS: ClassVar[tuple[str, ...]] = (
        "HISYS-FR-AGT-001",
        "HISYS-FR-AGT-002",
        "HISYS-FR-AGT-003",
        "HISYS-FR-AGT-004",
        "HISYS-FR-AGT-005",
    )

    handoff_id: str
    target_agent_system: str
    task: str
    context: str
    evidence_bundle: list[str] = Field(default_factory=list)
    perspective_id: str | None = None
    constraints: list[str] = Field(default_factory=list)
    expected_output: str
    due_condition: str | None = None
    allowed_actions: AllowedActions = "advisory_only"

    # Hermes-delegated actor fields (HISYS-IDD-001 Section 5.6 final paragraph).
    hermes_parent_run_id: str | None = None
    delegated_task_id: str | None = None
    enabled_toolsets: list[str] = Field(default_factory=list)
    source_scope: str | None = None
    preapproval_id: str | None = None
    preapproval_scope: str | None = None
    preapproved_by: str | None = None
    approval_basis: str | None = None
    approval_state: HandoffApprovalState = "not_required"
    source_registry_refs: list[str] = Field(default_factory=list)
    scope_policy_ref: str | None = None
    boundary_record_refs: list[str] = Field(default_factory=list)
    collection_output_refs: list[str] = Field(default_factory=list)
    prohibited_actions: list[str] = Field(default_factory=list)
    escalation_rule: str | None = None
    result_refs: list[str] = Field(default_factory=list)
    status: HandoffStatus = "prepared"

    @field_validator("handoff_id")
    @classmethod
    def _id(cls, v: str) -> str:
        validate_id(v)
        if not v.startswith(IdNamespace.HANDOFF.value + "-"):
            raise ValueError(f"handoff_id must start with 'HANDOFF-': {v!r}")
        return v
