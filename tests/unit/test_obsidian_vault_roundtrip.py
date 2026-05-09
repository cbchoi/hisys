"""Tests for Live-Obsidian-Config-H fixture vault roundtrip validation.

Traceability: Live-Obsidian-Config-H, HISYS-FR-INV-001..006,
HISYS-T-024, HISYS-CON-010..012, HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.config.obsidian_live import (
    apply_vault_plan_to_fixture,
    build_vault_plan,
    validate_fixture_vault_roundtrip,
)

EXAMPLES = Path("examples/obsidian-live")


def _applied_fixture(tmp_path: Path) -> tuple[dict, Path, dict]:
    plan = build_vault_plan(
        registry_path=EXAMPLES / "registry.json",
        request_id="REQ-ROUNDTRIP-1",
        submitted_title="DEVS Structural Change Formalism",
        domain="research",
        objective="roundtrip validation",
        yyyymmdd="20260509",
        hhmm="2101",
        dry_run=True,
    )
    target = tmp_path / "fixture-vault"
    apply_report = apply_vault_plan_to_fixture(
        plan=plan,
        target_vault_root=target,
        approval_ref="APPROVAL-roundtrip-001",
        fixture_vault_only=True,
    )
    return plan, target, apply_report


def test_validate_fixture_vault_roundtrip_accepts_applied_plan(tmp_path: Path) -> None:
    plan, target, apply_report = _applied_fixture(tmp_path)

    report = validate_fixture_vault_roundtrip(plan=plan, fixture_vault_root=target, apply_report=apply_report)

    assert report["valid"] is True
    assert report["status"] == "valid"
    assert report["checked_file_count"] == len(plan["planned_files"])
    assert report["missing_file_count"] == 0
    assert report["unexpected_file_count"] == 0
    assert report["projection_metadata_valid"] is True
    assert report["apply_report_matches_fixture"] is True
    assert report["real_obsidian_vault_write_performed"] is False
    assert report["external_call_made"] is False


def test_validate_fixture_vault_roundtrip_rejects_missing_planned_file(tmp_path: Path) -> None:
    plan, target, apply_report = _applied_fixture(tmp_path)
    (target / plan["planned_files"][0]).unlink()

    report = validate_fixture_vault_roundtrip(plan=plan, fixture_vault_root=target, apply_report=apply_report)

    assert report["valid"] is False
    assert report["missing_file_count"] == 1
    assert any(issue["code"] == "missing_planned_file" for issue in report["issues"])


def test_validate_fixture_vault_roundtrip_rejects_unexpected_file(tmp_path: Path) -> None:
    plan, target, apply_report = _applied_fixture(tmp_path)
    extra = target / "topics" / "unexpected.md"
    extra.parent.mkdir(parents=True, exist_ok=True)
    extra.write_text("unexpected", encoding="utf-8")

    report = validate_fixture_vault_roundtrip(plan=plan, fixture_vault_root=target, apply_report=apply_report)

    assert report["valid"] is False
    assert report["unexpected_file_count"] == 1
    assert any(issue["code"] == "unexpected_fixture_file" for issue in report["issues"])


def test_vault_roundtrip_validate_cli_writes_report(tmp_path: Path, capsys) -> None:
    from hisys.cli.main import main

    plan, target, apply_report = _applied_fixture(tmp_path)
    instance = tmp_path / "instance"
    plan_path = tmp_path / "plan.json"
    apply_report_path = tmp_path / "apply-report.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    apply_report_path.write_text(json.dumps(apply_report), encoding="utf-8")

    exit_code = main(
        [
            "vault-roundtrip-validate",
            "--instance",
            str(instance),
            "--date",
            "20260509",
            "--plan",
            str(plan_path),
            "--fixture-vault-root",
            str(target),
            "--apply-report",
            str(apply_report_path),
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr().out
    assert "vault roundtrip validation: valid" in captured
    report_path = instance / "runtime-boundary" / "obsidian-live" / "20260509" / "vault-roundtrip-report-REQ-ROUNDTRIP-1.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["valid"] is True
    assert report["real_obsidian_vault_write_performed"] is False
