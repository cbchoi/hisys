"""Stable record IDs.

Traceability:
- HISYS-DATA-001 (stable IDs across record types)
- HISYS-IDD-001 Section 2 (common interface rule: stable record IDs)

The controlled namespace format is an open issue (HISYS-IDD-001 Section 7
item 3); this module enforces a permissive but explicit prefix-based form
that all current fixtures and tests use.
"""

from __future__ import annotations

import re
import uuid
from enum import Enum


class IdNamespace(str, Enum):
    """Prefix tokens for the kinds of records in HISYS-SCHEMA-001."""

    SOURCE = "SRC"
    OBSERVATION = "OBS"
    SIGNAL = "SIG"
    PERSPECTIVE = "PERSP"
    MEMO = "MEM"
    ALERT = "ALERT"
    HANDOFF = "HANDOFF"
    HERMES_TRACE = "HTRACE"
    AUDIT = "AUDIT"
    COLLECTION_RUN = "RUN"
    CAMPAIGN = "CAMP"


_ID_RE = re.compile(r"^[A-Z][A-Z0-9_]*-[A-Z0-9][A-Z0-9_\-]*$")


def make_id(namespace: IdNamespace | str, suffix: str | None = None) -> str:
    """Build an ID like ``SRC-HW-MOCK-001`` or ``OBS-<uuid8>``."""
    ns = namespace.value if isinstance(namespace, IdNamespace) else namespace
    if suffix is None:
        suffix = uuid.uuid4().hex[:8].upper()
    suffix = suffix.upper()
    candidate = f"{ns}-{suffix}"
    validate_id(candidate)
    return candidate


def validate_id(value: str) -> str:
    """Validate the ID shape; return the value to enable inline use."""
    if not isinstance(value, str) or not _ID_RE.match(value):
        raise ValueError(f"invalid hisys id: {value!r}")
    return value
