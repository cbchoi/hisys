"""Hisys typed errors.

Traceability: HISYS-SDD-001 Section 8 (failure handling design),
HISYS-IDD-001 Section 2 (error status reporting).
"""

from __future__ import annotations


class HisysError(Exception):
    """Base for all Hisys-typed errors."""


class SchemaValidationError(HisysError):
    """Raised when a record fails its declared schema rules."""


class RegistryError(HisysError):
    """Raised on source registry / lifecycle violations."""


class ComplianceError(HisysError):
    """Raised when a web/news compliance gate denies an operation."""
