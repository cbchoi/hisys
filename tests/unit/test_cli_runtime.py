"""CLI runtime glue tests for the I4 Investigator increment.

Traceability: HISYS-INST-INV-001, HISYS-RUNTIME-DIR-001, HISYS-D-015,
HISYS-D-016, HISYS-T-001, HISYS-T-007, HISYS-T-008.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.cli.main import main


EXAMPLE_INSTANCE = Path(__file__).resolve().parents[2] / "examples" / "instance"


def test_validate_config_accepts_example_instance(capsys):
    result = main(["validate-config", "--instance", str(EXAMPLE_INSTANCE)])

    captured = capsys.readouterr()
    assert result == 0
    assert "config valid" in captured.out
    assert "SRC-HW-MOCK-001" in captured.out
    assert "SRC-HERMES-TOOL-001" in captured.out


def test_collect_command_writes_report_summary_and_runtime_records(tmp_path: Path, capsys):
    result = main(
        [
            "collect",
            "--instance",
            str(tmp_path),
            "--config-from",
            str(EXAMPLE_INSTANCE),
            "--source",
            "SRC-HW-MOCK-001",
            "--date",
            "20260508",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "collection run" in captured.out
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "collection-report.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["requested_source_ids"] == ["SRC-HW-MOCK-001"]
    assert len(report["collected_observation_refs"]) == 1
    assert report["skipped_source_ids"] == []
    obs_id = report["collected_observation_refs"][0]
    assert (tmp_path / "data" / "raw-observations" / "20260508" / f"{obs_id}.json").exists()
    assert (tmp_path / "data" / "audit" / "20260508" / "AUDIT-20260508.jsonl").exists()


def test_collect_command_rejects_unknown_source_without_unhandled_exception(tmp_path: Path, capsys):
    result = main(
        [
            "collect",
            "--instance",
            str(tmp_path),
            "--config-from",
            str(EXAMPLE_INSTANCE),
            "--source",
            "SRC-NOT-REGISTERED-001",
            "--date",
            "20260508",
        ]
    )

    captured = capsys.readouterr()
    assert result == 1
    assert "no observations collected" in captured.err
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "collection-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["skipped_source_ids"] == ["SRC-NOT-REGISTERED-001"]
    assert "SRC-NOT-REGISTERED-001" in report["adapter_errors"]
