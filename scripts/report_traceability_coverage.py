#!/usr/bin/env python3
"""Write a bounded advisory traceability coverage report.

M21.1 intentionally exposes this as a standalone script rather than a Hisys CLI
subcommand. It uses a small deterministic anchor loader over the existing repo
files and writes only counts/IDs under the runtime boundary.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from hisys.operations.traceability_coverage import (
    build_traceability_coverage_report,
    load_repo_traceability_anchors,
    write_traceability_coverage_report,
)

ROOT = Path(__file__).resolve().parent.parent


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
