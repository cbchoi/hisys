"""Release operations CLI tests.

Traceability: HISYS-T-023, HISYS-T-024, HISYS-FR-ADM-003..004.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.cli.main import main


def test_health_status_cli_writes_local_report_without_external_probe(tmp_path: Path, capsys) -> None:
    for name in ("config", "data", "reports", "runtime-boundary"):
        (tmp_path / name).mkdir(parents=True)

    result = main(["health-status", "--instance", str(tmp_path), "--date", "20260512", "--format", "json"])

    assert result == 0
    report = json.loads(capsys.readouterr().out)
    assert report["schema_id"] == "hisys.health_status_report"
    assert report["overall_status"] == "ok"
    assert report["external_call_made"] is False
    assert report["mutation_performed"] is False
    assert (tmp_path / "reports" / "run-summaries" / "20260512" / "hisys-health-status.json").exists()


def test_backup_and_restore_dry_run_cli_write_gate_evidence(tmp_path: Path, capsys) -> None:
    report_dir = tmp_path / "reports" / "run-summaries" / "20260512"
    report_dir.mkdir(parents=True)
    report_dir.joinpath("collection-report.json").write_text('{"ok": true}', encoding="utf-8")

    backup_result = main(
        [
            "backup-runtime",
            "--instance",
            str(tmp_path),
            "--date",
            "20260512",
            "--backup-id",
            "BKP-REL-001",
            "--format",
            "json",
        ]
    )
    assert backup_result == 0
    backup_report = json.loads(capsys.readouterr().out)
    assert backup_report["schema_id"] == "hisys.backup_report"
    assert backup_report["external_call_made"] is False
    assert backup_report["mutation_performed"] is False

    restore_result = main(
        [
            "restore-backup-dry-run",
            "--archive",
            backup_report["archive_path"],
            "--restore-target",
            str(tmp_path / "restore-target"),
            "--date",
            "20260512",
            "--report-root",
            str(tmp_path),
            "--format",
            "json",
        ]
    )
    assert restore_result == 0
    restore_report = json.loads(capsys.readouterr().out)
    assert restore_report["schema_id"] == "hisys.restore_dry_run_report"
    assert restore_report["verified"] is True
    assert restore_report["mutation_performed"] is False
    assert not (tmp_path / "restore-target").exists()
    assert (tmp_path / "reports" / "run-summaries" / "20260512" / "hisys-restore-dry-run.json").exists()
