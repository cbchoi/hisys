"""CLI runtime glue tests for the I4 Investigator increment.

Traceability: HISYS-INST-INV-001, HISYS-RUNTIME-DIR-001, HISYS-D-015,
HISYS-D-016, HISYS-T-001, HISYS-T-007, HISYS-T-008, HISYS-T-009,
HISYS-T-010, HISYS-T-011, HISYS-T-012.
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


def test_collect_command_writes_hermes_boundary_markdown_for_hermes_source(
    tmp_path: Path,
    capsys,
):
    result = main(
        [
            "collect",
            "--instance",
            str(tmp_path),
            "--config-from",
            str(EXAMPLE_INSTANCE),
            "--source",
            "SRC-HERMES-TOOL-001",
            "--date",
            "20260508",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "boundary_records: 1" in captured.out
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "collection-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["boundary_record_refs"] == [
        "hisys/runtime-boundary/hermes/20260508/CAMP-HERMES-CLI-001/tool_output-HERMES-CLI-001.md"
    ]
    boundary_path = (
        tmp_path
        / "runtime-boundary"
        / "hermes"
        / "20260508"
        / "CAMP-HERMES-CLI-001"
        / "tool_output-HERMES-CLI-001.md"
    )
    assert boundary_path.exists()
    markdown = boundary_path.read_text(encoding="utf-8")
    assert "record_kind: tool_output" in markdown
    assert "SRC-HERMES-TOOL-001" in markdown
    assert "Fixture Hermes collection output" in markdown


def test_extract_command_writes_signal_report_from_collected_observations(tmp_path: Path, capsys):
    collect_result = main(
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
    assert collect_result == 0
    capsys.readouterr()

    result = main(["extract", "--instance", str(tmp_path), "--date", "20260508"])

    captured = capsys.readouterr()
    assert result == 0
    assert "extraction run" in captured.out
    assert "signals: 1" in captured.out
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "extraction-report.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert len(report["requested_observation_refs"]) == 1
    assert len(report["extracted_signal_refs"]) == 1
    signal_id = report["extracted_signal_refs"][0]
    signal_path = tmp_path / "data" / "extracted-signals" / "20260508" / f"{signal_id}.json"
    assert signal_path.exists()
    signal = json.loads(signal_path.read_text(encoding="utf-8"))
    assert signal["observation_refs"] == report["requested_observation_refs"]
    assert signal["signal_type"] == "anomaly"
    assert "temperature_c" not in signal["claim_or_event"]


def test_draft_memo_command_writes_runtime_local_memo_draft(tmp_path: Path, capsys):
    collect_result = main(
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
    assert collect_result == 0
    extract_result = main(["extract", "--instance", str(tmp_path), "--date", "20260508"])
    assert extract_result == 0
    capsys.readouterr()

    result = main(
        [
            "draft-memo",
            "--instance",
            str(tmp_path),
            "--date",
            "20260508",
            "--perspective",
            "PERSP-OPS-001",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "memo draft run" in captured.out
    assert "drafts: 1" in captured.out
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "memo-draft-report.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["perspective_id"] == "PERSP-OPS-001"
    assert len(report["requested_signal_refs"]) == 1
    assert len(report["draft_memo_refs"]) == 1
    memo_id = report["draft_memo_refs"][0]
    memo_json_path = tmp_path / "data" / "memo-drafts" / "20260508" / f"{memo_id}.json"
    memo_md_path = tmp_path / "data" / "memo-drafts" / "20260508" / f"{memo_id}.md"
    assert memo_json_path.exists()
    assert memo_md_path.exists()
    memo = json.loads(memo_json_path.read_text(encoding="utf-8"))
    assert memo["review_status"] == "draft"
    assert memo["perspective_id"] == "PERSP-OPS-001"
    assert memo["signal_refs"] == report["requested_signal_refs"]
    markdown = memo_md_path.read_text(encoding="utf-8")
    assert "# Operations perspective" in markdown
    assert "temperature_c" not in markdown


def test_extract_command_rejects_missing_observation_partition(tmp_path: Path, capsys):
    result = main(["extract", "--instance", str(tmp_path), "--date", "20260508"])

    captured = capsys.readouterr()
    assert result == 1
    assert "no raw observations found" in captured.err


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
