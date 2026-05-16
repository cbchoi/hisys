import os
from pathlib import Path

import pytest

from hisys.operations.codebase_analysis import (
    PathPolicy,
    build_codebase_inventory,
)


def _seed_fixture_repo(repo: Path) -> None:
    (repo / "src" / "pkg").mkdir(parents=True)
    (repo / "src" / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "src" / "pkg" / "module.py").write_text("x = 1\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_module.py").write_text(
        "def test_x():\n    assert True\n", encoding="utf-8"
    )
    (repo / "docs").mkdir()
    (repo / "docs" / "readme.md").write_text("# fixture\n", encoding="utf-8")

    (repo / ".git" / "objects").mkdir(parents=True)
    (repo / ".git" / "objects" / "deadbeef").write_text("noise\n", encoding="utf-8")
    (repo / ".venv" / "lib").mkdir(parents=True)
    (repo / ".venv" / "lib" / "noise.py").write_text("noise\n", encoding="utf-8")
    (repo / "src" / "pkg" / "__pycache__").mkdir()
    (repo / "src" / "pkg" / "__pycache__" / "module.cpython-310.pyc").write_text(
        "", encoding="utf-8"
    )
    (repo / "build" / "lib").mkdir(parents=True)
    (repo / "build" / "lib" / "noise.py").write_text("", encoding="utf-8")
    (repo / ".pytest_cache").mkdir()
    (repo / ".pytest_cache" / "log").write_text("", encoding="utf-8")
    (repo / ".mypy_cache").mkdir()
    (repo / ".mypy_cache" / "cache.json").write_text("", encoding="utf-8")
    (repo / "node_modules").mkdir()
    (repo / "node_modules" / "x.js").write_text("", encoding="utf-8")
    (repo / "dist").mkdir()
    (repo / "dist" / "wheel.whl").write_text("", encoding="utf-8")


def test_inventory_excludes_transient_and_generated_paths(tmp_path: Path):
    repo = tmp_path / "fixture_repo"
    repo.mkdir()
    _seed_fixture_repo(repo)

    inventory = build_codebase_inventory(repo_root=repo)

    assert inventory.schema_id == "hisys.codebase.inventory"
    assert inventory.raw_source_content_persisted is False

    expected_kept = {
        "docs/readme.md",
        "src/pkg/__init__.py",
        "src/pkg/module.py",
        "tests/test_module.py",
    }
    assert set(inventory.files) == expected_kept
    assert inventory.files == sorted(inventory.files), "file list must be sorted"

    excluded = set(inventory.excluded_paths)
    for transient in (
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "build",
        "dist",
        "node_modules",
    ):
        assert any(transient in entry for entry in excluded), (
            f"expected an excluded_paths entry referencing {transient!r}; got {sorted(excluded)!r}"
        )

    twice = build_codebase_inventory(repo_root=repo)
    assert twice.model_dump() == inventory.model_dump(), "inventory must be deterministic"


def test_path_policy_records_safety_counts_and_skip_reasons(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    outside_target = outside / "outside_file.txt"
    outside_target.write_text("not part of repo\n", encoding="utf-8")

    (repo / "src.py").write_text("x = 1\n", encoding="utf-8")
    (repo / "image.bin").write_bytes(b"\x00\x01\x02ABC\x00\xff")
    (repo / "huge.dat").write_bytes(b"A" * (1_048_576 + 16))
    (repo / "bundle.min.js").write_text("var a=1;", encoding="utf-8")
    (repo / "auto.py").write_text("# @generated\nx = 2\n", encoding="utf-8")

    sym = repo / "leak"
    symlink_supported = True
    try:
        os.symlink(outside_target, sym)
    except (OSError, NotImplementedError):
        symlink_supported = False

    inventory = build_codebase_inventory(repo_root=repo)

    assert inventory.raw_source_content_persisted is False
    assert isinstance(inventory.path_policy, PathPolicy)
    assert inventory.path_policy.follow_symlinks is False
    assert inventory.path_policy.reject_outside_repo is True
    assert inventory.path_policy.max_file_size_bytes == 1_048_576

    assert inventory.binary_file_count == 1
    assert inventory.large_file_count == 1
    assert inventory.generated_file_count == 2

    expected_files = {"src.py", "image.bin", "huge.dat", "bundle.min.js", "auto.py"}
    assert set(inventory.files) == expected_files
    assert inventory.file_count == len(inventory.files)

    if symlink_supported:
        skipped_map = {entry.path: entry.reason for entry in inventory.skipped_paths}
        assert skipped_map.get("leak") == "outside_repo_symlink"
        assert "leak" not in inventory.files
    else:  # pragma: no cover - platform without symlink support
        pytest.skip("platform does not support symlinks")


def test_inventory_records_realpath_anchors(tmp_path: Path):
    repo = tmp_path / "via_symlink_root"
    real = tmp_path / "real_root"
    real.mkdir()
    (real / "a.py").write_text("a = 1\n", encoding="utf-8")
    try:
        os.symlink(real, repo, target_is_directory=True)
    except (OSError, NotImplementedError):  # pragma: no cover - platform skip
        pytest.skip("platform does not support symlinks")

    inventory = build_codebase_inventory(repo_root=repo)

    assert inventory.repo_root == str(repo)
    assert inventory.repo_root_realpath == os.path.realpath(repo)
    assert inventory.repo_root_realpath == str(real)
