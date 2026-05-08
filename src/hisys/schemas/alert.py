"""``AlertDecisionRecord`` schema.

Traceability:
- HISYS-FR-CE-002..006 (policy evaluation, audit of escalation/non-escalation,
  duplicate suppression, human approval gate).
- HISYS-CE-POLICY-001 Sections 3-5 (decision rules and severity scale).
- HISYS-SCHEMA-001 Section 8; HISYS-IDD-001 Section 5.5.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field, field_validator, model_validator

from ..core.ids import IdNamespace, validate_id
from .base import BaseRecord

Severity = Literal["low", "medium", "high", "critical"]
ApprovalStatus = Literal["not_required", "requested", "approved", "rejected"]
ActionTaken = Literal["none", "sent", "triggered", "handoff", "failed"]
AlertStatus = Literal[
    "pending", "suppressed", "needs_approval", "sent", "failed", "closed", "feedback_received"
]


class AlertDecisionRecord(BaseRecord):
    REQUIREMENTS: ClassVar[tuple[str, ...]] = (
        "HISYS-FR-CE-002",
        "HISYS-FR-CE-003",
        "HISYS-FR-CE-004",
        "HISYS-FR-CE-005",
        "HISYS-FR-CE-006",
        "HISYS-NFR-SEC-004",
    )

    alert_id: str
    memo_refs: list[str] = Field(default_factory=list)
    signal_refs: list[str] = Field(default_factory=list)
    policy_version: str
    trigger_reason: str
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    novelty: str
    approval_status: ApprovalStatus = "not_required"
    target_channel: str | None = None
    action_taken: ActionTaken = "none"
    suppression_key: str | None = None
    follow_up: str | None = None
    outcome_feedback: str | None = None
    status: AlertStatus = "pending"

    @field_validator("alert_id")
    @classmethod
    def _id(cls, v: str) -> str:
        validate_id(v)
        if not v.startswith(IdNamespace.ALERT.value + "-"):
            raise ValueError(f"alert_id must start with 'ALERT-': {v!r}")
        return v

    @model_validator(mode="after")
    def _approval_gate(self) -> "AlertDecisionRecord":
        # HISYS-FR-CE-006 / HISYS-NFR-SEC-004 / HISYS-T-018: high-impact actions
        # cannot be 'sent' or 'triggered' without prior approval.
        if (
            self.severity in ("high", "critical")
            and self.action_taken in ("sent", "triggered")
            and self.approval_status != "approved"
        ):
            raise ValueError(
                "high/critical alert cannot be sent/triggered without approval_status='approved'"
            )
        if not self.memo_refs and not self.signal_refs:
            raise ValueError("AlertDecisionRecord requires at least one memo_ref or signal_ref")
        return self
