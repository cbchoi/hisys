"""Security hardening helpers.

Traceability: HISYS-T-021, HISYS-NFR-SEC-001, HISYS-NFR-SEC-002.
"""

from .secret_scan import SecretScanHit, SecretScanReport, scan_paths

__all__ = ["SecretScanHit", "SecretScanReport", "scan_paths"]
