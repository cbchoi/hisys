"""Hisys core primitives: stable IDs, time, errors, and result types.

Implements common-field requirements from HISYS-SCHEMA-001 Section 2 and
HISYS-IDD-001 Section 2 (stable record IDs, ISO timestamps, error status).
"""

from .ids import IdNamespace, make_id, validate_id
from .time import iso_now, parse_iso, utc_now
from .errors import HisysError, SchemaValidationError, RegistryError, ComplianceError
from .result import Result

__all__ = [
    "IdNamespace",
    "make_id",
    "validate_id",
    "iso_now",
    "parse_iso",
    "utc_now",
    "HisysError",
    "SchemaValidationError",
    "RegistryError",
    "ComplianceError",
    "Result",
]
