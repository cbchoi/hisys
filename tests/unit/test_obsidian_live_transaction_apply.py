"""Tests for Live-Obsidian-Config-N approved live transaction apply boundary.

Traceability: Live-Obsidian-Config-N, HISYS-FR-INV-001..006,
HISYS-T-024, HISYS-CON-010..012, HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.config.obsidian_live import apply_live_vault_transaction


def _transaction_plan() -> dict:
    return {
        "schema_id": "hisys.obsidian.live_vault_transaction_plan",
        "request_id": "REQ-APPLY",
        "status": "planned_not_executable",
        "planned_operations": [
            {"operation_id": "live-vault-op-0001", "vault_relative_ref": "registry.json"},
            {"operation_id": "live-vault-op-0002", "vault_relative_ref": "topics/TOPIC-20260509-AAAAAA__demo/index.md"},
        ],
        "planned_operation_count": 2,
    }


def test_apply_live_transaction_writes_to_candidate_vault_with_required_approval(tmp_path: Path) -> None:
    vault_root = tmp_path / "candidate-vault"
    report = apply_live_vault_transaction(
        transaction_plan=_transaction_plan(),
        vault_root=vault_root,
        approval_ref="APPROVAL-LIVE-APPLY-TEST",
        explicit_live_write_enable=True,
        allow_real_obsidian_vault=False,
        clean_git_status=True,
    )

    assert report["status"] == "applied"
    assert report["source_transaction_request_id"] == "REQ-APPLY"
    assert report["operation_count"] == 2
    assert report["mutation_performed"] is True
    assert report["external_call_made"] is False
    assert report["real_obsidian_vault_write_performed"] is False
    assert (vault_root / "registry.json").exists()
    payload = json.loads((vault_root / "registry.json").read_text(encoding="utf-8"))
    assert payload["live_transaction_projection"] is True
    assert payload["approval_ref"] == "APPROVAL-LIVE-APPLY-TEST"
    assert payload["source_transaction_request_id"] == "REQ-APPLY"
    assert report["applied_operations"][0]["pre_write_hash"] == "missing"
    assert len(report["applied_operations"][0]["post_write_hash"]) == 64


def test_apply_live_transaction_refuses_real_obsidian_without_real_flag() -> None:
    report = apply_live_vault_transaction(
        transaction_plan=_transaction_plan(),
        vault_root=Path("/home/cbchoi/obsidian"),
        approval_ref="APPROVAL-LIVE-APPLY-TEST",
        explicit_live_write_enable=True,
        allow_real_obsidian_vault=False,
        clean_git_status=True,
    )

    assert report["status"] == "blocked"
    assert report["reason_code"] == "real_obsidian_vault_requires_explicit_flag"
    assert report["real_obsidian_vault_write_performed"] is False
    assert report["mutation_performed"] is False


def test_apply_live_transaction_requires_approval_enable_and_clean_git(tmp_path: Path) -> None:
    report = apply_live_vault_transaction(
        transaction_plan=_transaction_plan(),
        vault_root=tmp_path / "candidate-vault",
        approval_ref=None,
        explicit_live_write_enable=False,
        allow_real_obsidian_vault=False,
        clean_git_status=False,
    )

    assert report["status"] == "blocked"
    assert report["reason_code"] == "live_apply_gate_not_satisfied"
    assert report["mutation_performed"] is False


def test_apply_live_transaction_cli_writes_report(tmp_path: Path, capsys) -> None:
    from hisys.cli.main import main

    instance = tmp_path / "instance"
    vault_root = tmp_path / "candidate-vault"
    plan_path = tmp_path / "transaction-plan.json"
    plan_path.write_text(json.dumps(_transaction_plan()), encoding="utf-8")

    exit_code = main(
        [
            "vault-live-transaction-apply",
            "--instance",
            str(instance),
            "--date",
            "20260509",
            "--transaction-plan",
            str(plan_path),
            "--vault-root",
            str(vault_root),
            "--approval-ref",
            "APPROVAL-LIVE-APPLY-TEST",
            "--explicit-live-write-enable",
            "--clean-git-status",
        ]
    )

    assert exit_code == 0
    assert "vault live transaction apply: applied" in capsys.readouterr().out
    report_path = instance / "runtime-boundary" / "obsidian-live" / "20260509" / "vault-live-transaction-apply-REQ-APPLY.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["mutation_performed"] is True
    assert report["real_obsidian_vault_write_performed"] is False
