"""Tests for Live-Obsidian-Config-L live vault transaction plan.

Traceability: Live-Obsidian-Config-L, HISYS-FR-INV-001..006,
HISYS-T-024, HISYS-CON-010..012, HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.config.obsidian_live import build_live_vault_transaction_plan


def _approval_package() -> dict:
    return {
        "schema_id": "hisys.obsidian.live_vault_approval_package",
        "request_id": "REQ-LIVE-APPROVAL",
        "status": "approval_required",
        "vault_root": "/home/cbchoi/obsidian",
        "planned_writes": [
            {"vault_relative_ref": "registry.json", "operation": "create_or_update_after_separate_approval"},
            {"vault_relative_ref": "topics/TOPIC-20260509-AAAAAA__demo/index.md", "operation": "create_or_update_after_separate_approval"},
        ],
        "planned_write_count": 2,
        "rollback_plan": {"strategy": "git_revert_or_delete_new_files_after_review"},
        "live_write_enabled": False,
        "real_obsidian_vault_write_performed": False,
    }


def _write_gate(reason_code: str = "live_writer_not_implemented") -> dict:
    return {
        "schema_id": "hisys.obsidian.live_vault_write_gate_report",
        "request_id": "REQ-WRITE-GATE",
        "status": "blocked",
        "reason_code": reason_code,
        "implementation_boundary": "gate_only_no_writer",
        "approved_for_future_live_write": True,
        "planned_write_count": 2,
        "live_write_enabled": False,
        "real_obsidian_vault_write_performed": False,
    }


def test_live_vault_transaction_plan_is_no_write_manifest() -> None:
    plan = build_live_vault_transaction_plan(
        request_id="REQ-TXN-PLAN",
        approval_package=_approval_package(),
        write_gate_report=_write_gate(),
    )

    assert plan["status"] == "planned_not_executable"
    assert plan["implementation_boundary"] == "transaction_manifest_only_no_writer"
    assert plan["source_approval_package_request_id"] == "REQ-LIVE-APPROVAL"
    assert plan["source_write_gate_request_id"] == "REQ-WRITE-GATE"
    assert plan["planned_operation_count"] == 2
    assert plan["planned_operations"][0]["vault_relative_ref"] == "registry.json"
    assert plan["planned_operations"][0]["pre_write_hash"] == "not_read_no_live_write"
    assert plan["planned_operations"][0]["post_write_hash"] == "not_written_no_live_write"
    assert plan["requires_followup_writer_implementation"] is True
    assert plan["live_write_enabled"] is False
    assert plan["real_obsidian_vault_write_performed"] is False
    assert plan["mutation_performed"] is False


def test_live_vault_transaction_plan_blocks_if_write_gate_is_not_final_boundary() -> None:
    plan = build_live_vault_transaction_plan(
        request_id="REQ-TXN-PLAN-BLOCKED",
        approval_package=_approval_package(),
        write_gate_report=_write_gate(reason_code="git_status_not_clean"),
    )

    assert plan["status"] == "blocked"
    assert plan["reason_code"] == "write_gate_not_at_writer_boundary"
    assert plan["planned_operation_count"] == 0
    assert plan["real_obsidian_vault_write_performed"] is False


def test_live_vault_transaction_plan_cli_writes_manifest(tmp_path: Path, capsys) -> None:
    from hisys.cli.main import main

    instance = tmp_path / "instance"
    approval_package_path = tmp_path / "approval-package.json"
    write_gate_path = tmp_path / "write-gate.json"
    approval_package_path.write_text(json.dumps(_approval_package()), encoding="utf-8")
    write_gate_path.write_text(json.dumps(_write_gate()), encoding="utf-8")

    exit_code = main(
        [
            "vault-live-transaction-plan",
            "--instance",
            str(instance),
            "--date",
            "20260509",
            "--request-id",
            "REQ-TXN-CLI",
            "--approval-package",
            str(approval_package_path),
            "--write-gate-report",
            str(write_gate_path),
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr().out
    assert "vault live transaction plan: planned_not_executable" in captured
    report_path = instance / "runtime-boundary" / "obsidian-live" / "20260509" / "vault-live-transaction-plan-REQ-TXN-CLI.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["implementation_boundary"] == "transaction_manifest_only_no_writer"
    assert report["real_obsidian_vault_write_performed"] is False
