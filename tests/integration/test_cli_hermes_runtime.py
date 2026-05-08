"""Hermes CLI runtime integration test.

Traceability: HISYS-INST-INV-001, HISYS-RUNTIME-DIR-001, HISYS-D-015,
HISYS-D-016, HISYS-T-005A, HISYS-T-007, HISYS-T-008, HISYS-T-024.

This test executes the real CLI module as a subprocess against the controlled
example instance. It verifies the local fixture-only runtime path:

    validate-config
      -> collect SRC-HERMES-TOOL-001
      -> RawObservation JSON
      -> HermesCollectionTrace JSON
      -> Hermes Markdown boundary record
      -> Audit JSONL
      -> collection-report JSON/Markdown
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_INSTANCE = REPO_ROOT / "examples" / "instance"


def _run_cli(args: list[str], *, output_root: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "hisys.cli.main", *args],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_hermes_collect_cli_writes_full_runtime_boundary_path(tmp_path: Path):
    validate = _run_cli(["validate-config", "--instance", str(EXAMPLE_INSTANCE)])
    assert validate.returncode == 0, validate.stderr
    assert "SRC-HERMES-TOOL-001" in validate.stdout

    collect = _run_cli(
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
    assert collect.returncode == 0, collect.stderr
    assert "boundary_records: 1" in collect.stdout

    report_json = tmp_path / "reports" / "run-summaries" / "20260508" / "collection-report.json"
    report_md = tmp_path / "reports" / "run-summaries" / "20260508" / "collection-report.md"
    audit_jsonl = tmp_path / "data" / "audit" / "20260508" / "AUDIT-20260508.jsonl"
    trace_dir = tmp_path / "data" / "hermes-traces" / "20260508"
    boundary_path = (
        tmp_path
        / "runtime-boundary"
        / "hermes"
        / "20260508"
        / "CAMP-HERMES-CLI-001"
        / "tool_output-HERMES-CLI-001.md"
    )

    assert report_json.exists()
    assert report_md.exists()
    assert audit_jsonl.exists()
    assert boundary_path.exists()
    trace_files = sorted(trace_dir.glob("HTRACE-*.json"))
    assert len(trace_files) == 1

    report = json.loads(report_json.read_text(encoding="utf-8"))
    assert report["requested_source_ids"] == ["SRC-HERMES-TOOL-001"]
    assert len(report["collected_observation_refs"]) == 1
    assert report["skipped_source_ids"] == []
    assert report["boundary_record_refs"] == [
        "hisys/runtime-boundary/hermes/20260508/CAMP-HERMES-CLI-001/tool_output-HERMES-CLI-001.md"
    ]

    obs_id = report["collected_observation_refs"][0]
    observation_json = tmp_path / "data" / "raw-observations" / "20260508" / f"{obs_id}.json"
    assert observation_json.exists()
    observation = json.loads(observation_json.read_text(encoding="utf-8"))
    assert observation["source_id"] == "SRC-HERMES-TOOL-001"
    provenance = observation["provenance_bundle"]
    assert provenance["campaign_id"] == "CAMP-HERMES-CLI-001"
    assert provenance["boundary_record_ref"].endswith("tool_output-HERMES-CLI-001.md")
    assert provenance["approval_state"] == "preapproved"

    trace = json.loads(trace_files[0].read_text(encoding="utf-8"))
    assert trace["campaign_id"] == "CAMP-HERMES-CLI-001"
    assert trace["raw_observation_refs"] == [obs_id]
    assert trace["boundary_record_ref"].endswith("tool_output-HERMES-CLI-001.md")

    boundary_markdown = boundary_path.read_text(encoding="utf-8")
    assert "record_kind: tool_output" in boundary_markdown
    assert "SRC-HERMES-TOOL-001" in boundary_markdown
    assert "Fixture Hermes collection output" in boundary_markdown

    audit_lines = [json.loads(line) for line in audit_jsonl.read_text(encoding="utf-8").splitlines()]
    assert audit_lines
    assert any(event["result"] == "success" for event in audit_lines)
