"""Tests for the completed Obsidian milestone status gate.

Traceability: Obsidian-Milestone-Status, HISYS-FR-INV-001..006,
HISYS-T-024, HISYS-CON-010..012, HISYS-CON-022..023.
"""

from __future__ import annotations

import json

from hisys.config.obsidian_live import build_obsidian_milestone_status_report


def test_obsidian_milestone_status_marks_live_gatekeeper_and_promotion_complete() -> None:
    report = build_obsidian_milestone_status_report(request_id="REQ-OBS-MILESTONE")

    assert report["schema_id"] == "hisys.obsidian.milestone_status"
    assert report["status"] == "complete"
    assert report["obsidian_milestone_complete"] is True
    assert report["open_milestone_count"] == 0
    assert report["completed_milestone_count"] == 4
    assert [item["milestone"] for item in report["milestones"]] == [
        "Live-Obsidian-Config",
        "Topic-Gatekeeper",
        "Obsidian-Evidence-Promotion",
        "Obsidian-Git-Management",
    ]
    assert report["real_obsidian_vault_write_performed"] is False
    assert report["external_call_made"] is False
    assert report["mutation_performed"] is False


def test_obsidian_milestone_status_cli_writes_report(tmp_path, capsys) -> None:
    from hisys.cli.main import main

    instance = tmp_path / "instance"
    exit_code = main([
        "vault-obsidian-milestone-status",
        "--instance", str(instance),
        "--date", "20260510",
        "--request-id", "REQ-OBS-MILESTONE",
    ])

    assert exit_code == 0
    captured = capsys.readouterr().out
    assert "obsidian milestone: complete" in captured
    assert "open_milestone_count: 0" in captured
    report_path = instance / "runtime-boundary" / "obsidian-live" / "20260510" / "obsidian-milestone-status-REQ-OBS-MILESTONE.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["obsidian_milestone_complete"] is True
    assert report["real_obsidian_vault_write_performed"] is False
