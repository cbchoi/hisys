#!/usr/bin/env python3
"""Run the Hisys secret-like value scan.

Traceability: HISYS-T-021, HISYS-NFR-SEC-001, HISYS-NFR-SEC-002.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from hisys.security.secret_scan import scan_paths  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan paths for secret-like assignment values.")
    parser.add_argument("paths", nargs="*", default=[str(REPO_ROOT)], help="Files or directories to scan")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = scan_paths(args.paths)
    payload = report.model_dump()
    payload["hit_count"] = report.hit_count
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(
            f"secret_scan: scanned_files={report.scanned_files} "
            f"skipped_files={report.skipped_files} hit_count={report.hit_count}"
        )
        for hit in report.hits:
            print(f"{hit.relative_path}:{hit.line_number}: {hit.redacted_excerpt}")
    return 1 if report.hit_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
