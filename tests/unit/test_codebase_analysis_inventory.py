from pathlib import Path

from hisys.operations.codebase_analysis import build_codebase_inventory


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
