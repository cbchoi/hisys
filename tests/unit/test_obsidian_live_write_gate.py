"""Tests for Live-Obsidian-Config-K live vault write gate.

Traceability: Live-Obsidian-Config-K, HISYS-FR-INV-001..006,
HISYS-T-024, HISYS-CON-010..012, HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.config.obsidian_live import build_live_vault_write_gate_report


def _approval_package() -> dict:
    return {
        "schema_id": "hisys.obsidian.live_vault_approval_package",
        "schema_version": "0.1.0",
        "request_id": "REQ-LIVE-APPROVAL",
        "status": "approval_required",
        "approval_required": True,
        "required_approvals": [
            "human_live_vault_write_approval",
            "clean_git_status_confirmation",
            "rollback_plan_acknowledgement",
        ],
        "planned_writes": [
            {"vault_relative_ref": "registry.json", "operation": "create_or_update_after_separate_approval"},
            {"vault_relative_ref": "topics/TOPIC-20260509-AAAAAA__demo/index.md", "operation": "create_or_update_after_separate_approval"},
        ],
        "planned_write_count": 2,
        "live_write_enabled": False,
        "real_obsidian_vault_write_performed": False,
    }


def test_live_vault_write_gate_blocks_without_explicit_enablement() -> None:
    report = build_live_vault_write_gate_report(
        request_id="REQ-WRITE-GATE",
        approval_package=_approval_package(),
        approval_ref="APPROVAL-20260509-PROFESSOR",
        explicit_live_write_enable=False,
        clean_git_status=True,
    )

    assert report["status"] == "blocked"
    assert report["reason_code"] == "live_write_not_enabled"
    assert report["approved_for_future_live_write"] is True
    assert report["planned_write_count"] == 2
    assert report["live_write_enabled"] is False
    assert report["real_obsidian_vault_write_performed"] is False
    assert report["mutation_performed"] is False


def test_live_vault_write_gate_does_not_write_even_when_enabled_flag_is_present() -> None:
    report = build_live_vault_write_gate_report(
        request_id="REQ-WRITE-GATE-ENABLED",
        approval_package=_approval_package(),
        approval_ref="APPROVAL-20260509-PROFESSOR",
        explicit_live_write_enable=True,
        clean_git_status=True,
    )

    assert report["status"] == "blocked"
    assert report["reason_code"] == "live_writer_not_implemented"
    assert report["implementation_boundary"] == "gate_only_no_writer"
    assert report["live_write_enabled"] is False
    assert report["real_obsidian_vault_write_performed"] is False
    assert report["planned_writes_preview"][0]["vault_relative_ref"] == "registry.json"


def test_live_vault_write_gate_blocks_dirty_git_status() -> None:
    report = build_live_vault_write_gate_report(
        request_id="REQ-WRITE-GATE-DIRTY",
        approval_package=_approval_package(),
        approval_ref="APPROVAL-20260509-PROFESSOR",
        explicit_live_write_enable=True,
        clean_git_status=False,
    )

    assert report["status"] == "blocked"
    assert report["reason_code"] == "git_status_not_clean"
    assert report["real_obsidian_vault_write_performed"] is False


def test_live_vault_write_gate_cli_writes_blocked_runtime_report(tmp_path: Path, capsys) -> None:
    from hisys.cli.main import main

    instance = tmp_path / "instance"
    package_path = tmp_path / "approval-package.json"
    package_path.write_text(json.dumps(_approval_package()), encoding="utf-8")

    exit_code = main(
        [
            "vault-live-write-gate",
            "--instance",
            str(instance),
            "--date",
            "20260509",
            "--request-id",
            "REQ-WRITE-GATE-CLI",
            "--approval-package",
            str(package_path),
            "--approval-ref",
            "APPROVAL-20260509-PROFESSOR",
            "--clean-git-status",
        ]
    )

    assert exit_code == 1
    captured = capsys.readouterr().out
    assert "vault live write gate: blocked" in captured
    report_path = instance / "runtime-boundary" / "obsidian-live" / "20260509" / "vault-live-write-gate-REQ-WRITE-GATE-CLI.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["reason_code"] == "live_write_not_enabled"
    assert report["real_obsidian_vault_write_performed"] is False
