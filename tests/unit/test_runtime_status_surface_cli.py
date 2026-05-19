"""Runtime status surface CLI tests.

Traceability: docs/plans/2026-05-19-runtime-status-surface-cli.md.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.cli.main import main


def test_runtime_status_surface_cli_writes_report_and_text(tmp_path: Path, capsys) -> None:
    instance = tmp_path / "instance"
    workdir = tmp_path / "repo"
    instance.mkdir()
    workdir.mkdir()

    result = main(
        [
            "runtime-status-surface",
            "--instance",
            str(instance),
            "--date",
            "20260519",
            "--workdir",
            str(workdir),
            "--model",
            "safe-model",
            "--session",
            "session-secret-123456789",
            "--approval-state",
            "approved:CHERRY-20260519-005",
            "--context-budget",
            "input=12000/output=2000",
            "--format",
            "text",
        ]
    )

    assert result == 0
    out = capsys.readouterr().out
    assert "runtime status:" in out
    assert "external_call_made=false" in out
    assert "session-secret" not in out
    report_path = instance / "reports" / "run-summaries" / "20260519" / "hisys-runtime-status-surface.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["schema_id"] == "hisys.runtime_status_surface"
    assert report["boundary_flags"]["mutation_performed"] is False
    assert report["runtime"]["session"] == "[REDACTED]"


def test_runtime_status_surface_cli_json_output_contains_artifact_refs(tmp_path: Path, capsys) -> None:
    instance = tmp_path / "instance"
    instance.mkdir()

    result = main(
        [
            "runtime-status-surface",
            "--instance",
            str(instance),
            "--date",
            "20260519",
            "--approval-state",
            "pending",
            "--format",
            "json",
        ]
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["packet"]["boundary_flags"]["action_taken"] == "none"
    assert payload["artifacts"]["json_ref"].endswith("hisys-runtime-status-surface.json")
    assert payload["artifacts"]["markdown_ref"].endswith("hisys-runtime-status-surface.md")
