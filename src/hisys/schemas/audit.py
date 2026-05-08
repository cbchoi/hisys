"""``AuditEvent`` schema.

Traceability:
- HISYS-FR-ADM-002 (audit log of source changes, runs, memo writes,
  alerts, approvals, handoffs, failures).
- HISYS-SCHEMA-001 Section 11; HISYS-IDD-001 HISYS-IF-014.
"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar, Literal

from pydantic import Field, field_validator

from ..core.ids import IdNamespace, validate_id
from ..core.time import utc_now
from .base import BaseRecord

EventType = Literal[
    "source_change",
    "collection_run",
    "hermes_collection_run",
    "memo_write",
    "alert_decision",
    "approval",
    "handoff",
    "failure",
]
AuditResult = Literal["success", "failure", "partial", "skipped"]


class AuditEvent(BaseRecord):
    REQUIREMENTS: ClassVar[tuple[str, ...]] = (
        "HISYS-FR-ADM-002",
        "HISYS-DATA-003",
    )

    audit_id: str
    event_type: EventType
    actor_id: str
    record_refs: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=utc_now)
    summary: str
    result: AuditResult = "success"
    status: AuditResult = "success"

    @field_validator("audit_id")
    @classmethod
    def _id(cls, v: str) -> str:
        validate_id(v)
        if not v.startswith(IdNamespace.AUDIT.value + "-"):
            raise ValueError(f"audit_id must start with 'AUDIT-': {v!r}")
        return v
