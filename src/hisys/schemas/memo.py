"""``ZettelMemo`` schema.

Traceability:
- HISYS-FR-MEM-001..005 (atomic memo with stable ID, source/signal refs,
  perspective, confidence, tags, links, revision, review status).
- HISYS-SCHEMA-001 Section 7; HISYS-IDD-001 Section 5.4.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field, field_validator

from ..core.ids import IdNamespace, validate_id
from .base import BaseRecord

ReviewStatus = Literal[
    "draft", "published", "revised", "flagged_duplicate", "flagged_conflict", "retired"
]


class ZettelMemo(BaseRecord):
    REQUIREMENTS: ClassVar[tuple[str, ...]] = (
        "HISYS-FR-MEM-001",
        "HISYS-FR-MEM-002",
        "HISYS-FR-MEM-003",
        "HISYS-FR-MEM-004",
        "HISYS-FR-MEM-005",
        "HISYS-DATA-002",
    )

    memo_id: str
    title: str
    summary: str
    body: str
    source_refs: list[str] = Field(min_length=1)
    signal_refs: list[str] = Field(min_length=1)
    perspective_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    revision: str = "1"
    review_status: ReviewStatus = "draft"
    status: ReviewStatus = "draft"

    @field_validator("memo_id")
    @classmethod
    def _id(cls, v: str) -> str:
        validate_id(v)
        if not v.startswith(IdNamespace.MEMO.value + "-"):
            raise ValueError(f"memo_id must start with 'MEM-': {v!r}")
        return v

    @field_validator("source_refs")
    @classmethod
    def _src(cls, v: list[str]) -> list[str]:
        for ref in v:
            validate_id(ref)
            if not ref.startswith(IdNamespace.SOURCE.value + "-"):
                raise ValueError(f"source_refs entry must start with 'SRC-': {ref!r}")
        return v

    @field_validator("signal_refs")
    @classmethod
    def _sig(cls, v: list[str]) -> list[str]:
        for ref in v:
            validate_id(ref)
            if not ref.startswith(IdNamespace.SIGNAL.value + "-"):
                raise ValueError(f"signal_refs entry must start with 'SIG-': {ref!r}")
        return v

    @field_validator("perspective_id")
    @classmethod
    def _persp(cls, v: str) -> str:
        validate_id(v)
        if not v.startswith(IdNamespace.PERSPECTIVE.value + "-"):
            raise ValueError(f"perspective_id must start with 'PERSP-': {v!r}")
        return v
