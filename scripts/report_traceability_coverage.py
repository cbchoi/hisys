#!/usr/bin/env python3
"""Write a bounded advisory traceability coverage report.

M21.1 intentionally exposes this as a standalone script rather than a Hisys CLI
subcommand. It uses a small deterministic anchor loader over the existing repo
files and writes only counts/IDs under the runtime boundary.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from hisys.operations.traceability_coverage import (
    TraceabilityAnchors,
    build_traceability_coverage_report,
    write_traceability_coverage_report,
)

ROOT = Path(__file__).resolve().parent.parent
REQ_RE = re.compile(r"HISYS-[A-Z]+-[A-Z0-9]+(?:-\d+)?")
STD_RE = re.compile(r"STD-[A-Z0-9_-]+")


def _ids_from_file(path: Path, pattern: re.Pattern[str]) -> tuple[str, ...]:
    if not path.is_file():
        return ()
    text = path.read_text(encoding="utf-8")
    return tuple(sorted(dict.fromkeys(pattern.findall(text))))


def load_repo_traceability_anchors(root: Path = ROOT) -> TraceabilityAnchors:
    schema_refs: dict[str, list[str]] = {}
    for path in sorted((root / "src" / "hisys" / "schemas").glob("*.py")):
        if path.name in {"__init__.py", "base.py"}:
            continue
        for req_id in _ids_from_file(path, REQ_RE):
            schema_refs.setdefault(req_id, []).append(path.relative_to(root).as_posix())

    traceability_doc = root / "docs" / "traceability" / "README.md"
    design_refs = {
        req_id: (traceability_doc.relative_to(root).as_posix(),)
        for req_id in _ids_from_file(traceability_doc, REQ_RE)
    }
    requirement_ids = tuple(sorted(set(schema_refs) | set(design_refs)))

    trace_test = root / "tests" / "integration" / "test_trace_path.py"
    test_req_ids = _ids_from_file(trace_test, REQ_RE)
    test_ids = _ids_from_file(trace_test, STD_RE) or ("tests/integration/test_trace_path.py",)
    test_requirement_links = {
        test_id: test_req_ids for test_id in test_ids
    }

    return TraceabilityAnchors(
        requirement_ids=requirement_ids,
        design_requirement_refs=design_refs,
        interface_requirement_refs={req_id: tuple(paths) for req_id, paths in schema_refs.items()},
        test_requirement_refs={req_id: (trace_test.relative_to(root).as_posix(),) for req_id in test_req_ids},
        test_ids=test_ids,
        test_requirement_links=test_requirement_links,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance-root", type=Path, default=ROOT)
    parser.add_argument("--date", required=True, help="YYYYMMDD runtime-boundary date")
    args = parser.parse_args()

    anchors = load_repo_traceability_anchors(ROOT)
    report = build_traceability_coverage_report(anchors)
    refs = write_traceability_coverage_report(
        instance_root=args.instance_root, date=args.date, report=report
    )
    print(f"traceability_coverage_json={refs['json_ref']}")
    print(f"traceability_coverage_markdown={refs['markdown_ref']}")
    print(f"coverage_ratio={report.coverage_ratio}")
    print(f"unreferenced_requirements={len(report.unreferenced_requirements)}")
    print(f"orphan_test_ids={len(report.orphan_test_ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
