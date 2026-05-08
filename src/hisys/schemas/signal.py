"""``ExtractedSignal`` schema (interpretation; not raw evidence).

Traceability:
- HISYS-FR-EXT-001..005 (signal references evidence; preserves confidence,
  uncertainty, contradiction; method and version metadata).
- HISYS-DATA-002 (evidence/interpretation separation).
- HISYS-SCHEMA-001 Section 5; HISYS-IDD-001 Section 5.3.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field, field_validator

from ..core.ids import IdNamespace, validate_id
from .base import BaseRecord

SignalType = Literal[
    "fact", "claim", "anomaly", "event", "relationship", "trend", "uncertainty"
]
SignalStatus = Literal[
    "proposed", "accepted", "uncertain", "contradicted", "superseded", "rejected"
]


class ExtractedSignal(BaseRecord):
    REQUIREMENTS: ClassVar[tuple[str, ...]] = (
        "HISYS-FR-EXT-001",
        "HISYS-FR-EXT-002",
        "HISYS-FR-EXT-003",
        "HISYS-FR-EXT-004",
        "HISYS-FR-EXT-005",
        "HISYS-DATA-002",
    )

    signal_id: str
    observation_refs: list[str] = Field(min_length=1)
    signal_type: SignalType
    claim_or_event: str
    entities: list[str] = Field(default_factory=list)
    time_scope: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    uncertainty: str
    contradictions: list[str] = Field(default_factory=list)
    extraction_method: str
    version: str = "1"
    status: SignalStatus = "proposed"

    @field_validator("signal_id")
    @classmethod
    def _id(cls, v: str) -> str:
        validate_id(v)
        if not v.startswith(IdNamespace.SIGNAL.value + "-"):
            raise ValueError(f"signal_id must start with 'SIG-': {v!r}")
        return v

    @field_validator("observation_refs")
    @classmethod
    def _obs_refs(cls, v: list[str]) -> list[str]:
        for ref in v:
            validate_id(ref)
            if not ref.startswith(IdNamespace.OBSERVATION.value + "-"):
                raise ValueError(f"observation_refs entry must start with 'OBS-': {ref!r}")
        return v
