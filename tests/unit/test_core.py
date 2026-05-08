"""Unit tests for core primitives.

Traceability: HISYS-DATA-001 (stable IDs), HISYS-IDD-001 Section 2 (ISO
timestamps, error status), HISYS-SDD-001 Section 8 (failure handling).
"""

from __future__ import annotations

from datetime import timezone

import pytest

from hisys.core import (
    HisysError,
    IdNamespace,
    Result,
    SchemaValidationError,
    iso_now,
    make_id,
    parse_iso,
    utc_now,
    validate_id,
)


def test_make_id_round_trip():
    rid = make_id(IdNamespace.SOURCE, "HW-MOCK-001")
    assert rid == "SRC-HW-MOCK-001"
    assert validate_id(rid) == rid


def test_make_id_default_suffix_is_well_formed():
    rid = make_id(IdNamespace.OBSERVATION)
    assert rid.startswith("OBS-") and len(rid) > 4


def test_validate_id_rejects_lowercase():
    with pytest.raises(ValueError):
        validate_id("src-bad-001")


def test_iso_now_is_timezone_aware():
    now = utc_now()
    assert now.tzinfo is timezone.utc
    parsed = parse_iso(iso_now())
    assert parsed.tzinfo is not None


def test_result_helpers():
    ok: Result[int] = Result.success(42)
    assert ok.ok and ok.value == 42 and ok.error is None
    bad: Result[int] = Result.failure("boom")
    assert not bad.ok and bad.error == "boom"


def test_error_hierarchy():
    assert issubclass(SchemaValidationError, HisysError)
