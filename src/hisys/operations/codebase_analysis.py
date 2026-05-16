"""Deterministic, fixture-local codebase inventory.

The inventory builder is the first increment of the codebase-analysis surface
(`SPEC-HISYS-CODEBASE-ANALYSIS-001`). It performs a pure local repository walk
under an explicit caller-supplied root and excludes transient/generated paths
so downstream analyses operate on a stable file set without depending on the
working-directory state of CI runners or developer machines.

M15.1 introduced the deterministic walk and transient-path exclusion. M15.2
adds the path policy contract, safety classifications (binary / large /
generated), skip-reason recording, and realpath anchors. Subsequent
milestones add the JSON/Markdown writer (M15.3), CLI wrapper (M15.4), and
docs/traceability rows (M15.5). The schema_id remains `hisys.codebase.inventory`
across those increments.
"""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field

# Directories whose contents are transient build/cache/VCS state and never
# represent reviewable source. The exclusion is purely name-based so the walk
# stays deterministic and free of host-specific lookups.
DEFAULT_EXCLUDED_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".cache",
        ".eggs",
        "build",
        "dist",
        "htmlcov",
        "node_modules",
    }
)

# Substrings that indicate a text file is machine-generated. Matched against
# the first `binary_null_byte_probe_bytes` of file content so the probe stays
# bounded and deterministic.
DEFAULT_GENERATED_MARKERS: tuple[str, ...] = (
    "@generated",
    "DO NOT EDIT",
    "Auto-generated",
    "AUTO-GENERATED",
)

# Filename suffixes that are conventionally machine-produced artifacts.
DEFAULT_GENERATED_SUFFIXES: tuple[str, ...] = (
    ".min.js",
    ".min.css",
    ".lock",
    ".lockb",
)


class PathPolicy(BaseModel):
    follow_symlinks: bool = False
    reject_outside_repo: bool = True
    max_file_size_bytes: int = 1_048_576
    binary_null_byte_probe_bytes: int = 8192
    excluded_dirs: list[str] = Field(
        default_factory=lambda: sorted(DEFAULT_EXCLUDED_DIRS)
    )
    generated_marker_substrings: list[str] = Field(
        default_factory=lambda: list(DEFAULT_GENERATED_MARKERS)
    )
    generated_suffixes: list[str] = Field(
        default_factory=lambda: list(DEFAULT_GENERATED_SUFFIXES)
    )


class SkippedPath(BaseModel):
    path: str
    reason: str


class CodebaseInventory(BaseModel):
    schema_id: str = "hisys.codebase.inventory"
    repo_root: str
    repo_root_realpath: str | None = None
    analysis_scope: str | None = None
    files: list[str] = Field(default_factory=list)
    excluded_paths: list[str] = Field(default_factory=list)
    skipped_paths: list[SkippedPath] = Field(default_factory=list)
    path_policy: PathPolicy = Field(default_factory=PathPolicy)
    file_count: int = 0
    binary_file_count: int = 0
    large_file_count: int = 0
    generated_file_count: int = 0
    raw_source_content_persisted: bool = False


def _classify_file(
    path: Path, policy: PathPolicy
) -> tuple[bool, bool, bool]:
    try:
        size = path.stat().st_size
    except OSError:
        size = 0
    try:
        with path.open("rb") as handle:
            head = handle.read(policy.binary_null_byte_probe_bytes)
    except OSError:
        head = b""

    is_binary = b"\x00" in head
    is_large = size > policy.max_file_size_bytes

    if any(path.name.endswith(suffix) for suffix in policy.generated_suffixes):
        is_generated = True
    elif is_binary:
        is_generated = False
    else:
        # `errors='ignore'` keeps the marker scan deterministic on partial
        # multi-byte boundaries — generated markers are ASCII so the scan
        # cannot miss them through codec failure.
        text = head.decode("utf-8", errors="ignore")
        is_generated = any(
            marker in text for marker in policy.generated_marker_substrings
        )
    return is_binary, is_large, is_generated


def build_codebase_inventory(
    repo_root: Path,
    *,
    analysis_scope: str | None = None,
    path_policy: PathPolicy | None = None,
) -> CodebaseInventory:
    root = Path(repo_root)
    if not root.is_dir():
        raise NotADirectoryError(f"repo_root is not a directory: {root}")

    policy = path_policy or PathPolicy()
    excluded_dirs = set(policy.excluded_dirs)
    real_root = Path(os.path.realpath(root))

    files: list[str] = []
    excluded: list[str] = []
    skipped: list[SkippedPath] = []
    counters = {"binary": 0, "large": 0, "generated": 0}

    def is_outside_repo(symlink_path: Path) -> bool:
        try:
            target_real = Path(os.path.realpath(symlink_path))
            target_real.relative_to(real_root)
        except ValueError:
            return True
        return False

    def walk(current: Path) -> None:
        try:
            entries = sorted(current.iterdir(), key=lambda p: p.name)
        except PermissionError:
            return
        for entry in entries:
            rel = entry.relative_to(root).as_posix()
            if entry.is_symlink():
                if policy.reject_outside_repo and is_outside_repo(entry):
                    skipped.append(
                        SkippedPath(path=rel, reason="outside_repo_symlink")
                    )
                else:
                    skipped.append(SkippedPath(path=rel, reason="symlink_skipped"))
                continue
            if entry.is_dir():
                if entry.name in excluded_dirs:
                    excluded.append(rel)
                    continue
                walk(entry)
            elif entry.is_file():
                files.append(rel)
                is_binary, is_large, is_generated = _classify_file(entry, policy)
                if is_binary:
                    counters["binary"] += 1
                if is_large:
                    counters["large"] += 1
                if is_generated:
                    counters["generated"] += 1

    walk(root)

    return CodebaseInventory(
        repo_root=str(root),
        repo_root_realpath=str(real_root),
        analysis_scope=analysis_scope,
        files=sorted(files),
        excluded_paths=sorted(excluded),
        skipped_paths=sorted(skipped, key=lambda s: s.path),
        path_policy=policy,
        file_count=len(files),
        binary_file_count=counters["binary"],
        large_file_count=counters["large"],
        generated_file_count=counters["generated"],
        raw_source_content_persisted=False,
    )


__all__ = [
    "CodebaseInventory",
    "DEFAULT_EXCLUDED_DIRS",
    "DEFAULT_GENERATED_MARKERS",
    "DEFAULT_GENERATED_SUFFIXES",
    "PathPolicy",
    "SkippedPath",
    "build_codebase_inventory",
]
