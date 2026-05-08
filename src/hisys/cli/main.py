"""Hisys CLI placeholder.

Traceability: HISYS-PKG-ARCH-001 Section 3 lists the planned CLI surface;
this module only exposes a stub so I0 import-smoke and traceability checks
have a stable entry point.
"""

from __future__ import annotations

import argparse
import sys

from .. import __version__


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="hisys", description="Hisys CLI (I0 stub).")
    p.add_argument("--version", action="version", version=f"hisys {__version__}")
    sub = p.add_subparsers(dest="command")
    sub.add_parser("validate-config", help="not implemented in I0")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    print(f"hisys: '{args.command}' is not implemented yet (I0/I1 only)", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
