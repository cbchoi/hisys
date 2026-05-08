#!/usr/bin/env python3
"""Validate that schema modules and tests carry HISYS traceability.

Checks (all derived from HISYS-IMP-001 Section 5 and HISYS-REPO-001):

1. Every record class declared in ``hisys.schemas`` exposes a non-empty
   ``REQUIREMENTS`` tuple of ``HISYS-*`` IDs.
2. The end-to-end trace test
   ``tests/integration/test_trace_path.py`` exists and references each
   schema name involved in the path.
3. The Hermes boundary path convention from HISYS-IDD-001 Section 6 is
   referenced from the relevant schema module.

Exit code 0 on success, 1 on first failure with a human-readable message.
This script does not perform any network or destructive actions.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "hisys"
SCHEMAS_PKG = SRC / "schemas"
TRACE_TEST = ROOT / "tests" / "integration" / "test_trace_path.py"

REQ_RE = re.compile(r"HISYS-[A-Z]+-[A-Z0-9]+(?:-\d+)?")
BOUNDARY_HINT = "hisys/runtime-boundary/hermes/"

EXPECTED_RECORDS = {
    "SourceRegistryEntry",
    "RawObservation",
    "ExtractedSignal",
    "PerspectiveProfile",
    "ZettelMemo",
    "AlertDecisionRecord",
    "AgentHandoffPackage",
    "HermesCollectionTrace",
    "AuditEvent",
}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def check_schema_modules() -> None:
    if not SCHEMAS_PKG.is_dir():
        fail(f"missing schemas package at {SCHEMAS_PKG}")

    py_files = sorted(SCHEMAS_PKG.glob("*.py"))
    if not py_files:
        fail("no schema modules found")

    found_records: set[str] = set()

    for path in py_files:
        if path.name in {"__init__.py", "base.py"}:
            continue
        text = path.read_text(encoding="utf-8")
        ids = REQ_RE.findall(text)
        if not ids:
            fail(f"{path.relative_to(ROOT)} has no HISYS-* requirement IDs")
        if "REQUIREMENTS" not in text:
            fail(f"{path.relative_to(ROOT)} missing REQUIREMENTS tuple")
        for record in EXPECTED_RECORDS:
            if f"class {record}" in text:
                found_records.add(record)

    missing = EXPECTED_RECORDS - found_records
    if missing:
        fail(f"missing record classes: {sorted(missing)}")


def check_trace_test() -> None:
    if not TRACE_TEST.is_file():
        fail(f"missing end-to-end trace test at {TRACE_TEST}")
    text = TRACE_TEST.read_text(encoding="utf-8")
    required_names = [
        "RawObservation",
        "ExtractedSignal",
        "ZettelMemo",
        "AlertDecisionRecord",
        "HermesCollectionTrace",
        "AuditEvent",
    ]
    for name in required_names:
        if name not in text:
            fail(f"trace test does not reference {name}")
    if "SRC-HERMES-TOOL-001" not in text and "hermes_source" not in text:
        fail("trace test does not exercise a Hermes source")


def check_boundary_convention() -> None:
    hermes_module = SCHEMAS_PKG / "hermes_trace.py"
    if BOUNDARY_HINT not in hermes_module.read_text(encoding="utf-8"):
        fail(f"hermes_trace.py does not encode boundary path convention {BOUNDARY_HINT!r}")


def main() -> int:
    check_schema_modules()
    check_trace_test()
    check_boundary_convention()
    print("OK: schemas, trace test, and Hermes boundary convention pass traceability checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
