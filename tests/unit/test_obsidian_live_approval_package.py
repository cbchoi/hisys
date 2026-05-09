"""Tests for Live-Obsidian-Config-J live vault approval package planning.

Traceability: Live-Obsidian-Config-J, HISYS-FR-INV-001..006,
HISYS-T-024, HISYS-CON-010..012, HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.config.obsidian_live import build_live_vault_approval_package


def _preflight() -> dict:
    return {
        "schema_id": "hisys.obsidian.live_vault_preflight_report",
        "schema_version": "0.1.0",
        "request_id": "REQ-PREFLIGHT",
        "status": "ready_for_approval_package",
        "valid": True,
        "vault_root": "/home/cbchoi/obsidian",
        "live_write_enabled": False,
        "write_probe_performed": False,
        "real_obsidian_vault_write_performed": False,
    }


def _plan() -> dict:
    return {
        "schema_id": "hisys.obsidian.vault_plan",
        "schema_version": "0.1.0",
        "request_id": "REQ-LIVE-APPROVAL",
        "topic_uid": "TOPIC-20260509-AAAAAA",
        "investigation_id": "INV-20260509-2101-AAAA",
        "planned_files": ["registry.json", "topics/TOPIC-20260509-AAAAAA__demo/index.md"],
        "dry_run": True,
        "vault_write_attempted": False,
    }


def test_live_vault_approval_package_lists_required_approvals_and_no_writes() -> None:
    package = build_live_vault_approval_package(
        request_id="REQ-LIVE-APPROVAL",
        preflight_report=_preflight(),
        vault_plan=_plan(),
        operator_id="professor",
        rationale="first live vault write review",
    )

    assert package["status"] == "approval_required"
    assert package["live_write_enabled"] is False
    assert package["real_obsidian_vault_write_performed"] is False
    assert package["approval_required"] is True
    assert package["required_approvals"] == ["human_live_vault_write_approval", "clean_git_status_confirmation", "rollback_plan_acknowledgement"]
    assert package["planned_write_count"] == 2
    assert package["planned_writes"][0]["vault_relative_ref"] == "registry.json"
    assert package["rollback_plan"]["strategy"] == "git_revert_or_delete_new_files_after_review"
    assert package["final_gate_before_live_write"] == ["vault-live-preflight", "vault-roundtrip-validate", "git status --short"]


def test_live_vault_approval_package_blocks_failed_preflight() -> None:
    preflight = _preflight()
    preflight["valid"] = False
    preflight["status"] = "blocked"

    package = build_live_vault_approval_package(
        request_id="REQ-LIVE-BLOCKED",
        preflight_report=preflight,
        vault_plan=_plan(),
        operator_id="professor",
        rationale="first live vault write review",
    )

    assert package["status"] == "blocked"
    assert package["reason_code"] == "preflight_not_ready"
    assert package["planned_writes"] == []
    assert package["real_obsidian_vault_write_performed"] is False


def test_live_vault_approval_package_cli_writes_json_and_markdown(tmp_path: Path, capsys) -> None:
    from hisys.cli.main import main

    instance = tmp_path / "instance"
    preflight_path = tmp_path / "preflight.json"
    plan_path = tmp_path / "plan.json"
    preflight_path.write_text(json.dumps(_preflight()), encoding="utf-8")
    plan_path.write_text(json.dumps(_plan()), encoding="utf-8")

    exit_code = main(
        [
            "vault-live-approval-package",
            "--instance",
            str(instance),
            "--date",
            "20260509",
            "--request-id",
            "REQ-LIVE-APPROVAL-CLI",
            "--preflight-report",
            str(preflight_path),
            "--plan",
            str(plan_path),
            "--operator-id",
            "professor",
            "--rationale",
            "first live vault write review",
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr().out
    assert "vault live approval package: approval_required" in captured
    package_path = instance / "runtime-boundary" / "obsidian-live" / "20260509" / "vault-live-approval-package-REQ-LIVE-APPROVAL-CLI.json"
    markdown_path = instance / "runtime-boundary" / "obsidian-live" / "20260509" / "vault-live-approval-package-REQ-LIVE-APPROVAL-CLI.md"
    assert package_path.exists()
    assert markdown_path.exists()
    package = json.loads(package_path.read_text(encoding="utf-8"))
    assert package["approval_required"] is True
    assert package["live_write_enabled"] is False
