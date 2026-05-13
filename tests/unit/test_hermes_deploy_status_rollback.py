"""Hermes tool deployment status, report, and rollback behavior.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012, HISYS-CON-022..023.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from hisys.hermes_deploy import deploy_hisys_to_hermes, get_hermes_deployment_status, rollback_hisys_hermes_tool


ROOT = Path(__file__).resolve().parents[2]


def _source_root(tmp_path: Path, name: str) -> Path:
    source_root = tmp_path / name
    (source_root / "src" / "hisys").mkdir(parents=True)
    return source_root


def test_deployment_status_reports_snapshot_safety_and_rollback_availability(tmp_path):
    target_root = tmp_path / ".hermes" / "tools" / "hisys"
    first = deploy_hisys_to_hermes(source_root=_source_root(tmp_path, "repo1"), target_root=target_root)
    second = deploy_hisys_to_hermes(source_root=_source_root(tmp_path, "repo2"), target_root=target_root, force=True)

    status = get_hermes_deployment_status(target_root=target_root)

    assert status["status"] == "deployed"
    assert status["deployment_mode"] == "immutable_snapshot"
    assert status["current_release_id"] == second["release_id"]
    assert first["release_id"] in status["available_release_ids"]
    assert second["release_id"] in status["available_release_ids"]
    assert status["wrapper_points_to_snapshot"] is True
    assert status["wrapper_references_live_source"] is False
    assert status["rollback_available"] is True
    assert status["safe_to_use"] is True


def test_rollback_hisys_hermes_tool_moves_current_release_atomically(tmp_path):
    target_root = tmp_path / ".hermes" / "tools" / "hisys"
    first = deploy_hisys_to_hermes(source_root=_source_root(tmp_path, "repo1"), target_root=target_root)
    second = deploy_hisys_to_hermes(source_root=_source_root(tmp_path, "repo2"), target_root=target_root, force=True)
    assert first["release_id"] != second["release_id"]

    result = rollback_hisys_hermes_tool(target_root=target_root, to_release=first["release_id"])

    assert result["status"] == "rolled_back"
    assert result["previous_release_id"] == second["release_id"]
    assert result["current_release_id"] == first["release_id"]
    assert (target_root / "releases" / "current").readlink() == Path(first["release_id"])
    manifest = json.loads((target_root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["release_id"] == first["release_id"]
    assert manifest["rollback"]["from_release_id"] == second["release_id"]


def test_rollback_hisys_hermes_tool_rejects_unknown_release(tmp_path):
    target_root = tmp_path / ".hermes" / "tools" / "hisys"
    deploy_hisys_to_hermes(source_root=_source_root(tmp_path, "repo1"), target_root=target_root)

    result = rollback_hisys_hermes_tool(target_root=target_root, to_release="missing-release")

    assert result["status"] == "blocked"
    assert result["reason"] == "release_not_found"


def test_deployment_status_and_report_cli(tmp_path):
    target_root = tmp_path / ".hermes" / "tools" / "hisys"
    deploy_hisys_to_hermes(source_root=_source_root(tmp_path, "repo1"), target_root=target_root)
    report_path = tmp_path / "deploy-report.json"

    status_result = subprocess.run(
        [sys.executable, "-m", "hisys.cli.main", "deployment-status", "--target", str(target_root), "--format", "json"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert status_result.returncode == 0, status_result.stdout
    status = json.loads(status_result.stdout)
    assert status["safe_to_use"] is True
    assert status["wrapper_points_to_snapshot"] is True

    report_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "hisys.cli.main",
            "build-hermes-deploy-report",
            "--target",
            str(target_root),
            "--validation",
            "pytest=passed",
            "--validation",
            "traceability=passed",
            "--output",
            str(report_path),
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert report_result.returncode == 0, report_result.stdout
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["schema_id"] == "hisys.hermes_tool_deploy_report"
    assert report["promotion_allowed"] is False
    assert report["human_approval_required_for_host_install"] is True
    assert report["deployment_status"]["safe_to_use"] is True
    assert report["verification"]["pytest"] == "passed"


def test_rollback_cli_rolls_back_to_previous_release(tmp_path):
    target_root = tmp_path / ".hermes" / "tools" / "hisys"
    first = deploy_hisys_to_hermes(source_root=_source_root(tmp_path, "repo1"), target_root=target_root)
    deploy_hisys_to_hermes(source_root=_source_root(tmp_path, "repo2"), target_root=target_root, force=True)

    result = subprocess.run(
        [sys.executable, "-m", "hisys.cli.main", "rollback-hermes-tool", "--target", str(target_root), "--previous", "--format", "json"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    data = json.loads(result.stdout)
    assert data["status"] == "rolled_back"
    assert data["current_release_id"] == first["release_id"]
