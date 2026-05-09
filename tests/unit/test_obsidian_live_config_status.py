"""Tests for Live-Obsidian-Config-O completion status report.

Traceability: Live-Obsidian-Config-O, HISYS-FR-INV-001..006,
HISYS-T-024, HISYS-CON-010..012, HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.config.obsidian_live import build_live_obsidian_config_status_report


def test_live_obsidian_config_status_marks_all_stages_complete() -> None:
    report = build_live_obsidian_config_status_report(request_id="REQ-STATUS")

    assert report["schema_id"] == "hisys.obsidian.live_config_status"
    assert report["request_id"] == "REQ-STATUS"
    assert report["status"] == "complete"
    assert report["completed_stage_count"] == 15
    assert report["open_stage_count"] == 0
    assert report["live_obsidian_config_complete"] is True
    assert report["real_obsidian_vault_write_performed"] is False
    assert report["external_call_made"] is False
    assert report["mutation_performed"] is False
    assert [stage["increment"] for stage in report["stages"]] == [f"Live-Obsidian-Config-{letter}" for letter in "ABCDEFGHIJKLMNO"]
    assert report["stages"][-1]["command"] == "vault-live-config-status"


def test_live_obsidian_config_status_cli_writes_report(tmp_path: Path, capsys) -> None:
    from hisys.cli.main import main

    instance = tmp_path / "instance"
    exit_code = main(
        [
            "vault-live-config-status",
            "--instance",
            str(instance),
            "--date",
            "20260510",
            "--request-id",
            "REQ-STATUS",
        ]
    )

    assert exit_code == 0
    assert "vault live config status: complete" in capsys.readouterr().out
    report_path = instance / "runtime-boundary" / "obsidian-live" / "20260510" / "vault-live-config-status-REQ-STATUS.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["live_obsidian_config_complete"] is True
    assert report["open_stage_count"] == 0
    assert report["real_obsidian_vault_write_performed"] is False
