"""Tests for Live-Obsidian-Config-M live transaction fixture rehearsal.

Traceability: Live-Obsidian-Config-M, HISYS-FR-INV-001..006,
HISYS-T-024, HISYS-CON-010..012, HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.config.obsidian_live import rehearse_live_vault_transaction_in_fixture


def _transaction_plan() -> dict:
    return {
        "schema_id": "hisys.obsidian.live_vault_transaction_plan",
        "request_id": "REQ-TXN",
        "status": "planned_not_executable",
        "implementation_boundary": "transaction_manifest_only_no_writer",
        "planned_operations": [
            {"operation_id": "live-vault-op-0001", "operation": "create_or_update_after_separate_approval", "vault_relative_ref": "registry.json"},
            {"operation_id": "live-vault-op-0002", "operation": "create_or_update_after_separate_approval", "vault_relative_ref": "topics/TOPIC-20260509-AAAAAA__demo/index.md"},
        ],
        "planned_operation_count": 2,
        "live_write_enabled": False,
        "real_obsidian_vault_write_performed": False,
    }


def test_transaction_rehearsal_writes_fixture_only(tmp_path: Path) -> None:
    fixture_root = tmp_path / "fixture-vault"
    report = rehearse_live_vault_transaction_in_fixture(
        transaction_plan=_transaction_plan(),
        fixture_vault_root=fixture_root,
        approval_ref="APPROVAL-REHEARSE-ONLY",
        fixture_vault_only=True,
    )

    assert report["status"] == "rehearsed_fixture_only"
    assert report["source_transaction_request_id"] == "REQ-TXN"
    assert report["fixture_vault_only"] is True
    assert report["operation_count"] == 2
    assert report["real_obsidian_vault_write_performed"] is False
    assert report["mutation_performed"] is False
    assert (fixture_root / "registry.json").exists()
    projected = json.loads((fixture_root / "registry.json").read_text(encoding="utf-8"))
    assert projected["fixture_projection_only"] is True
    assert projected["source_transaction_request_id"] == "REQ-TXN"
    assert projected["approval_ref"] == "APPROVAL-REHEARSE-ONLY"


def test_transaction_rehearsal_refuses_real_obsidian_vault() -> None:
    report = rehearse_live_vault_transaction_in_fixture(
        transaction_plan=_transaction_plan(),
        fixture_vault_root=Path("/home/cbchoi/obsidian"),
        approval_ref="APPROVAL-REHEARSE-ONLY",
        fixture_vault_only=True,
    )

    assert report["status"] == "blocked"
    assert report["reason_code"] == "real_obsidian_vault_blocked"
    assert report["real_obsidian_vault_write_performed"] is False


def test_transaction_rehearsal_requires_fixture_flag_and_approval(tmp_path: Path) -> None:
    report = rehearse_live_vault_transaction_in_fixture(
        transaction_plan=_transaction_plan(),
        fixture_vault_root=tmp_path / "fixture-vault",
        approval_ref=None,
        fixture_vault_only=False,
    )

    assert report["status"] == "blocked"
    assert report["reason_code"] == "fixture_rehearsal_gate_not_satisfied"
    assert report["real_obsidian_vault_write_performed"] is False


def test_transaction_rehearsal_cli_writes_report(tmp_path: Path, capsys) -> None:
    from hisys.cli.main import main

    instance = tmp_path / "instance"
    fixture_root = tmp_path / "fixture-vault"
    plan_path = tmp_path / "transaction-plan.json"
    plan_path.write_text(json.dumps(_transaction_plan()), encoding="utf-8")

    exit_code = main(
        [
            "vault-live-transaction-rehearse",
            "--instance",
            str(instance),
            "--date",
            "20260509",
            "--transaction-plan",
            str(plan_path),
            "--fixture-vault-root",
            str(fixture_root),
            "--approval-ref",
            "APPROVAL-REHEARSE-ONLY",
            "--fixture-vault-only",
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr().out
    assert "vault live transaction rehearsal: rehearsed_fixture_only" in captured
    report_path = instance / "runtime-boundary" / "obsidian-live" / "20260509" / "vault-live-transaction-rehearsal-REQ-TXN.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["real_obsidian_vault_write_performed"] is False
