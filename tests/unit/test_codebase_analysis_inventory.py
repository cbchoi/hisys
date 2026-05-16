import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from hisys.operations.codebase_analysis import (
    PathPolicy,
    build_codebase_inventory,
    write_codebase_inventory,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"


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


def test_write_codebase_inventory_persists_json_and_markdown(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "src.py").write_text("x = 1\n", encoding="utf-8")
    (repo / "image.bin").write_bytes(b"\x00\x01ABC")

    inventory = build_codebase_inventory(repo_root=repo)

    instance = tmp_path / "instance"
    result = write_codebase_inventory(
        instance_root=instance,
        date="20260516",
        request_id="REQ-CODEBASE-001",
        inventory=inventory,
    )

    assert result["external_call_made"] is False
    assert result["mutation_performed"] is False
    assert result["publication_or_live_action_approved"] is False
    assert result["raw_source_content_persisted"] is False
    assert result["json_ref"] == (
        "runtime-boundary/codebase-analysis/20260516/REQ-CODEBASE-001/inventory.json"
    )
    assert result["markdown_ref"] == (
        "runtime-boundary/codebase-analysis/20260516/REQ-CODEBASE-001/inventory.md"
    )

    json_path = instance / result["json_ref"]
    md_path = instance / result["markdown_ref"]
    assert json_path.is_file()
    assert md_path.is_file()

    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    assert loaded["schema_id"] == "hisys.codebase.inventory"
    assert loaded["raw_source_content_persisted"] is False
    assert loaded["files"] == sorted(loaded["files"])

    # JSON is deterministic: re-rendering the same model yields byte-identical
    # content and the same listed refs.
    other_instance = tmp_path / "instance_two"
    other_result = write_codebase_inventory(
        instance_root=other_instance,
        date="20260516",
        request_id="REQ-CODEBASE-001",
        inventory=inventory,
    )
    other_json = (other_instance / other_result["json_ref"]).read_text(encoding="utf-8")
    assert other_json == json_path.read_text(encoding="utf-8")

    markdown = md_path.read_text(encoding="utf-8")
    assert "hisys.codebase.inventory" in markdown
    assert "src.py" in markdown


def test_write_codebase_inventory_rejects_traversal_in_request_id(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "src.py").write_text("x = 1\n", encoding="utf-8")
    inventory = build_codebase_inventory(repo_root=repo)
    instance = tmp_path / "instance"

    for bad in ("../escape", "REQ/with/slash", "REQ\\back", ".."):
        with pytest.raises(ValueError):
            write_codebase_inventory(
                instance_root=instance,
                date="20260516",
                request_id=bad,
                inventory=inventory,
            )

    for bad_date in ("2026/05/16", "..", "20260516/extra"):
        with pytest.raises(ValueError):
            write_codebase_inventory(
                instance_root=instance,
                date=bad_date,
                request_id="REQ-CODEBASE-001",
                inventory=inventory,
            )


def _seed_cli_fixture_repo(repo: Path) -> None:
    (repo / "src" / "pkg").mkdir(parents=True)
    (repo / "src" / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "src" / "pkg" / "module.py").write_text(
        "def hello():\n    return 'hi'\n", encoding="utf-8"
    )
    (repo / "tests").mkdir()
    (repo / "tests" / "test_module.py").write_text(
        "def test_hello():\n    assert True\n", encoding="utf-8"
    )
    (repo / ".git").mkdir()
    (repo / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")


def test_build_codebase_inventory_cli_writes_artifacts(tmp_path: Path):
    fixture_repo = tmp_path / "fixture_repo"
    fixture_repo.mkdir()
    _seed_cli_fixture_repo(fixture_repo)
    instance = tmp_path / "instance"

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{SRC_ROOT}{os.pathsep}{env.get('PYTHONPATH', '')}"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hisys.cli.main",
            "build-codebase-inventory",
            "--repo",
            str(fixture_repo),
            "--instance",
            str(instance),
            "--date",
            "20260516",
            "--request-id",
            "REQ-CODEBASE-001",
            "--format",
            "json",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    payload = json.loads(completed.stdout)
    assert payload["schema_id"] == "hisys.codebase.inventory"
    assert payload["raw_source_content_persisted"] is False
    assert payload["external_call_made"] is False
    assert payload["mutation_performed"] is False
    assert payload["publication_or_live_action_approved"] is False
    assert payload["json_ref"] == (
        "runtime-boundary/codebase-analysis/20260516/REQ-CODEBASE-001/inventory.json"
    )
    assert payload["markdown_ref"] == (
        "runtime-boundary/codebase-analysis/20260516/REQ-CODEBASE-001/inventory.md"
    )

    json_path = instance / payload["json_ref"]
    md_path = instance / payload["markdown_ref"]
    assert json_path.is_file()
    assert md_path.is_file()

    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    assert loaded["files"] == sorted(loaded["files"])
    assert "src/pkg/module.py" in loaded["files"]
    assert "tests/test_module.py" in loaded["files"]
    # .git is a default-excluded directory
    assert any(".git" in entry for entry in loaded["excluded_paths"])


def test_build_codebase_inventory_cli_supports_scope_filter(tmp_path: Path):
    fixture_repo = tmp_path / "fixture_repo"
    fixture_repo.mkdir()
    _seed_cli_fixture_repo(fixture_repo)
    instance = tmp_path / "instance"

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{SRC_ROOT}{os.pathsep}{env.get('PYTHONPATH', '')}"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hisys.cli.main",
            "build-codebase-inventory",
            "--repo",
            str(fixture_repo),
            "--instance",
            str(instance),
            "--date",
            "20260516",
            "--request-id",
            "REQ-CODEBASE-002",
            "--scope",
            "src",
            "--format",
            "json",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, (
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    payload = json.loads(completed.stdout)
    json_path = instance / payload["json_ref"]
    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    assert loaded["analysis_scope"] == "src"
    # scope must filter to only files under src/
    assert all(entry.startswith("src/") for entry in loaded["files"])
    assert "src/pkg/module.py" in loaded["files"]
    assert "tests/test_module.py" not in loaded["files"]
