"""``PerspectiveProfile`` schema.

Traceability:
- HISYS-FR-PER-001..004 (versioned perspective profiles, lifecycle).
- HISYS-SCHEMA-001 Section 6.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field, field_validator

from ..core.ids import IdNamespace, validate_id
from .base import BaseRecord

PerspectiveLifecycle = Literal["draft", "active", "retired", "superseded"]


class PerspectiveProfile(BaseRecord):
    REQUIREMENTS: ClassVar[tuple[str, ...]] = (
        "HISYS-FR-PER-001",
        "HISYS-FR-PER-002",
        "HISYS-FR-PER-003",
        "HISYS-FR-PER-004",
    )

    perspective_id: str
    title: str
    owner: str
    version: str = "1"
    lifecycle_state: PerspectiveLifecycle = "draft"
    intent: str
    scope: list[str] = Field(default_factory=list)
    focus_areas: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    bias_controls: list[str] = Field(default_factory=list)
    review_cadence: str = "TBD"
    status: PerspectiveLifecycle = "draft"

    @field_validator("perspective_id")
    @classmethod
    def _id(cls, v: str) -> str:
        validate_id(v)
        if not v.startswith(IdNamespace.PERSPECTIVE.value + "-"):
            raise ValueError(f"perspective_id must start with 'PERSP-': {v!r}")
        return v
