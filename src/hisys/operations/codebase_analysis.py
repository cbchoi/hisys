"""Deterministic, fixture-local codebase inventory.

The inventory builder is the first increment of the codebase-analysis surface
(`SPEC-HISYS-CODEBASE-ANALYSIS-001`). It performs a pure local repository walk
under an explicit caller-supplied root and excludes transient/generated paths
so downstream analyses operate on a stable file set without depending on the
working-directory state of CI runners or developer machines.

Out of scope for M15.1: path policy (M15.2), JSON/Markdown writer (M15.3),
CLI wrapper (M15.4), and docs/traceability rows (M15.5). Subsequent
milestones extend `CodebaseInventory` with policy and counts; the schema_id
remains `hisys.codebase.inventory` across those increments.
"""

from __future__ import annotations

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


class CodebaseInventory(BaseModel):
    schema_id: str = "hisys.codebase.inventory"
    repo_root: str
    analysis_scope: str | None = None
    files: list[str] = Field(default_factory=list)
    excluded_paths: list[str] = Field(default_factory=list)
    raw_source_content_persisted: bool = False


def build_codebase_inventory(
    repo_root: Path,
    *,
    analysis_scope: str | None = None,
) -> CodebaseInventory:
    root = Path(repo_root)
    if not root.is_dir():
        raise NotADirectoryError(f"repo_root is not a directory: {root}")

    files: list[str] = []
    excluded: list[str] = []

    def walk(current: Path) -> None:
        try:
            entries = sorted(current.iterdir(), key=lambda p: p.name)
        except PermissionError:
            return
        for entry in entries:
            if entry.is_symlink():
                # Symlinks may escape the repo root; M15.2 will record them as a
                # path-policy event. For M15.1 they are skipped silently to keep
                # the inventory deterministic without following them.
                continue
            if entry.is_dir():
                if entry.name in DEFAULT_EXCLUDED_DIRS:
                    excluded.append(entry.relative_to(root).as_posix())
                    continue
                walk(entry)
            elif entry.is_file():
                files.append(entry.relative_to(root).as_posix())

    walk(root)

    return CodebaseInventory(
        repo_root=str(root),
        analysis_scope=analysis_scope,
        files=sorted(files),
        excluded_paths=sorted(excluded),
        raw_source_content_persisted=False,
    )


__all__ = ["CodebaseInventory", "DEFAULT_EXCLUDED_DIRS", "build_codebase_inventory"]
