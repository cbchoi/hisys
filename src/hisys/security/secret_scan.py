"""Secret-like value scanner for product hardening.

Traceability: HISYS-T-021, HISYS-NFR-SEC-001, HISYS-NFR-SEC-002,
HISYS-FR-ADM-001, HISYS-R-008.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel, Field

SKIP_DIR_NAMES = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
}

SECRET_PATTERNS = [
    re.compile(r"(?i)\b(api[_-]?key|token|password|secret)\s*=\s*([^\s,;]+)"),
]

SAFE_REDACTED_VALUES = {"[REDACTED]", "REDACTED", "<REDACTED>"}
SAFE_VALUE_PREFIXES = ("FAKE_", "TEST_", "fixture-", "example-")


class SecretScanHit(BaseModel):
    """A redacted secret-like match found in a scanned text file."""

    path: str
    relative_path: str
    line_number: int = Field(ge=1)
    pattern_name: str
    redacted_excerpt: str


class SecretScanReport(BaseModel):
    """Summary of secret-like scan results."""

    scanned_paths: list[str]
    scanned_files: int
    skipped_files: int
    hits: list[SecretScanHit]

    @property
    def hit_count(self) -> int:
        return len(self.hits)


def _iter_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    for directory, dir_names, file_names in os.walk(root):
        dir_names[:] = [name for name in dir_names if name not in SKIP_DIR_NAMES]
        directory_path = Path(directory)
        for file_name in file_names:
            yield directory_path / file_name


def _is_binary(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return b"\0" in handle.read(2048)
    except OSError:
        return True


def _redact_match(match: re.Match[str]) -> str:
    return f"{match.group(1)}=[REDACTED]"


def _scan_line(path: Path, relative_path: str, line_number: int, line: str) -> list[SecretScanHit]:
    hits: list[SecretScanHit] = []
    for pattern in SECRET_PATTERNS:
        for match in pattern.finditer(line):
            raw_value = match.group(2).strip().strip('"\'')
            if raw_value in SAFE_REDACTED_VALUES or raw_value.startswith(SAFE_VALUE_PREFIXES):
                continue
            hits.append(
                SecretScanHit(
                    path=str(path),
                    relative_path=relative_path,
                    line_number=line_number,
                    pattern_name="assignment_secret_like",
                    redacted_excerpt=pattern.sub(_redact_match, match.group(0)),
                )
            )
    return hits


def _scan_file(path: Path, relative_path: str) -> list[SecretScanHit]:
    hits: list[SecretScanHit] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, start=1):
            hits.extend(_scan_line(path, relative_path, line_number, line.rstrip("\n")))
    return hits


def scan_paths(paths: Iterable[str | Path]) -> SecretScanReport:
    """Scan text files for simple assignment-style secret-like values.

    The scanner intentionally reports only redacted excerpts so validation output
    can be shared without leaking the matched value.
    """

    roots = [Path(path).resolve() for path in paths]
    hits: list[SecretScanHit] = []
    scanned_files = 0
    skipped_files = 0
    for root in roots:
        base = root if root.is_dir() else root.parent
        for file_path in _iter_files(root):
            if _is_binary(file_path):
                skipped_files += 1
                continue
            relative_path = str(file_path.relative_to(base))
            try:
                hits.extend(_scan_file(file_path, relative_path))
            except OSError:
                skipped_files += 1
                continue
            scanned_files += 1
    return SecretScanReport(
        scanned_paths=[str(root) for root in roots],
        scanned_files=scanned_files,
        skipped_files=skipped_files,
        hits=hits,
    )


__all__ = ["SecretScanHit", "SecretScanReport", "scan_paths"]
