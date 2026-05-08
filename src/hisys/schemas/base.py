"""Base record with common fields.

Traceability: HISYS-SCHEMA-001 Section 2 (common fields), HISYS-IDD-001
Section 2 (common interface rules: stable IDs, ISO timestamps,
producer/consumer identity, schema version, audit events).
"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field

from ..core.time import utc_now

SCHEMA_VERSION = "0.2.2"


class BaseRecord(BaseModel):
    """Common record fields per HISYS-SCHEMA-001 Section 2."""

    model_config = ConfigDict(extra="forbid", frozen=False)

    REQUIREMENTS: ClassVar[tuple[str, ...]] = ()

    schema_version: str = SCHEMA_VERSION
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    producer_id: str
    status: str
    audit_refs: list[str] = Field(default_factory=list)
