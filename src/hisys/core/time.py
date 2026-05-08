"""ISO timestamp helpers.

Traceability: HISYS-IDD-001 Section 2 (ISO timestamp fields are a common
interface rule for all operational interfaces).
"""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Timezone-aware UTC ``datetime``."""
    return datetime.now(timezone.utc)


def iso_now() -> str:
    """ISO 8601 UTC timestamp string."""
    return utc_now().isoformat()


def parse_iso(value: str) -> datetime:
    """Parse an ISO 8601 timestamp; trailing ``Z`` accepted."""
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)
