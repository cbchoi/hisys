"""DARS critic panel CLI tests.

Traceability:
- HISYS-FR-DARS-CP-001
- HISYS-FR-DARS-CP-003
- HISYS-FR-DARS-CP-007
- HISYS-NFR-DARS-CP-001
- M-CP-EXT-6 in docs/plans/dars-critic-panel-platform-runtime-next.md
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from helpers.fake_openai_server import FakeOpenAIServer


# DARS-CLOSE-1: checked-in deterministic golden fixture for the operator-report
# closure path. The directory and contents are loaded by
# ``test_run_dars_panel_cli_golden_fixture_writes_stable_operator_report``;
# changing the fixture files changes the golden contract.
GOLDEN_FIXTURE_DIR = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "dars_panel"
    / "golden_basic"
)


def _candidate_fixture(tmp_path: Path) -> tuple[str, list[str], str]:
    data_dir = tmp_path / "data" / "dars-panel-fixtures" / "20260520"
    data_dir.mkdir(parents=True)
    candidate = data_dir / "candidate-001.json"
    evidence = data_dir / "evidence-001.json"
    rubric = data_dir / "rubric-001.md"
    candidate.write_text('{"candidate_id":"candidate-001"}\n', encoding="utf-8")
    evidence.write_text('{"evidence_id":"evidence-001"}\n', encoding="utf-8")
    rubric.write_text("# Rubric\n", encoding="utf-8")
    return (
        str(candidate.relative_to(tmp_path)),
        [str(evidence.relative_to(tmp_path))],
        str(rubric.relative_to(tmp_path)),
    )


def test_run_dars_panel_cli_persists_fixture_round_and_prints_json(tmp_path: Path, capsys):
    """M-CP-EXT-6: CLI wraps the fixture-local advisory panel runtime."""

    from hisys.cli.main import main

    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    config_path = tmp_path / "panel-config.json"
    config_path.write_text(
        json.dumps(
            {
                "panel_id": "PANEL-DARS-CP-EXT-6",
                "max_parallel_critics": 1,
                "critics": [
                    {
                        "critic_id": "logical-devil",
                        "critic_role": "logical_devil",
                        "backend_id": "fixture-logical-cli-001",
                        "rubric_ref": rubric_ref,
                        "critique_dimensions": ["logical_validity"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "run-dars-panel",
            "--instance",
            str(tmp_path),
            "--date",
            "20260520",
            "--request-id",
            "REQ-DARS-CP-EXT-6",
            "--panel-config",
            str(config_path),
            "--candidate-ref",
            candidate_ref,
            "--evidence-ref",
            evidence_refs[0],
            "--format",
            "json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["request_id"] == "REQ-DARS-CP-EXT-6"
    assert payload["panel_id"] == "PANEL-DARS-CP-EXT-6"
    assert payload["execution_mode"] == "serial"
    # Task id format is TASK-{request_id}-{index:02d}-{critic_id} per
    # DarsCriticPanelRuntime.build_round_plan.
    assert payload["task_statuses"] == {
        "TASK-REQ-DARS-CP-EXT-6-00-logical-devil": "completed"
    }
    assert len(payload["critique_refs"]) == 1
    # Synthesis / round-trace refs use SYNTH-{request_id}.json / TRACE-{request_id}.json
    # per DarsCriticPanelRuntime._write_synthesis / _write_round_trace.
    assert payload["synthesis_ref"].endswith("SYNTH-REQ-DARS-CP-EXT-6.json")
    assert payload["round_trace_ref"].endswith("TRACE-REQ-DARS-CP-EXT-6.json")
    assert len(payload["execution_boundary_refs"]) == 1

    for ref in (
        payload["critique_refs"]
        + [payload["synthesis_ref"], payload["round_trace_ref"]]
        + payload["execution_boundary_refs"]
    ):
        assert (tmp_path / ref).exists()


def test_run_dars_panel_cli_writes_operator_report_without_live_actions(tmp_path: Path, capsys):
    """DARS productization: persist an operator-facing advisory report."""

    from hisys.cli.main import main

    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    config_path = tmp_path / "panel-config.json"
    config_path.write_text(
        json.dumps(
            {
                "panel_id": "PANEL-DARS-PRODUCT-REPORT",
                "max_parallel_critics": 1,
                "critics": [
                    {
                        "critic_id": "logical-devil",
                        "critic_role": "logical_devil",
                        "backend_id": "fixture-logical-report-001",
                        "rubric_ref": rubric_ref,
                        "critique_dimensions": ["logical_validity"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "run-dars-panel",
            "--instance",
            str(tmp_path),
            "--date",
            "20260520",
            "--request-id",
            "REQ-DARS-PRODUCT-REPORT",
            "--panel-config",
            str(config_path),
            "--candidate-ref",
            candidate_ref,
            "--evidence-ref",
            evidence_refs[0],
            "--write-report",
            "--format",
            "json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["report_ref"] == "reports/run-summaries/20260520/dars-panel-round-report.json"

    report_path = tmp_path / payload["report_ref"]
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["schema_id"] == "hisys.dars_panel.round_report"
    assert report["request_id"] == "REQ-DARS-PRODUCT-REPORT"
    assert report["panel_id"] == "PANEL-DARS-PRODUCT-REPORT"
    assert report["execution_mode"] == "serial"
    assert report["task_statuses"] == {
        "TASK-REQ-DARS-PRODUCT-REPORT-00-logical-devil": "completed"
    }
    assert len(report["critique_refs"]) == 1
    assert report["synthesis_ref"].endswith("SYNTH-REQ-DARS-PRODUCT-REPORT.json")
    assert report["round_trace_ref"].endswith("TRACE-REQ-DARS-PRODUCT-REPORT.json")
    assert len(report["execution_boundary_refs"]) == 1
    assert report["advisory_only"] is True
    assert report["requires_human_review"] is True
    assert report["external_call_made"] is False
    assert report["mutation_performed"] is False
    assert report["publication_performed"] is False
    assert report["live_external_action_authorized"] is False

    report_md = report_path.with_suffix(".md").read_text(encoding="utf-8")
    assert "# DARS panel round report" in report_md
    assert "REQ-DARS-PRODUCT-REPORT" in report_md
    assert "live_external_action_authorized: false" in report_md


def test_run_dars_panel_cli_golden_fixture_writes_stable_operator_report(
    tmp_path: Path, capsys
):
    """DARS-CLOSE-1: deterministic golden scenario for the operator report.

    The checked-in fixture under ``tests/fixtures/dars_panel/golden_basic``
    pins the end-to-end operator-report contract for a fixture-local panel
    round. The test fails if the golden fixture files are missing or if the
    advisory safety fields, schema id, or task plan drift.
    """

    from hisys.cli.main import main

    data_dir = tmp_path / "data" / "dars-panel-fixtures" / "20260521"
    data_dir.mkdir(parents=True)
    shutil.copy(GOLDEN_FIXTURE_DIR / "candidate-001.json", data_dir / "candidate-001.json")
    shutil.copy(GOLDEN_FIXTURE_DIR / "evidence-001.json", data_dir / "evidence-001.json")
    shutil.copy(GOLDEN_FIXTURE_DIR / "rubric-001.md", data_dir / "rubric-001.md")

    config_path = tmp_path / "panel-config.json"
    config_blueprint = json.loads(
        (GOLDEN_FIXTURE_DIR / "panel-config.json").read_text(encoding="utf-8")
    )
    # Rewrite the rubric ref so the checked-in blueprint stays
    # instance-relocatable; the rest of the config is the locked contract.
    rubric_ref = "data/dars-panel-fixtures/20260521/rubric-001.md"
    for critic in config_blueprint["critics"]:
        critic["rubric_ref"] = rubric_ref
    config_path.write_text(json.dumps(config_blueprint), encoding="utf-8")

    exit_code = main(
        [
            "run-dars-panel",
            "--instance",
            str(tmp_path),
            "--date",
            "20260521",
            "--request-id",
            "REQ-DARS-GOLDEN-BASIC",
            "--panel-config",
            str(config_path),
            "--candidate-ref",
            "data/dars-panel-fixtures/20260521/candidate-001.json",
            "--evidence-ref",
            "data/dars-panel-fixtures/20260521/evidence-001.json",
            "--write-report",
            "--format",
            "json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert (
        payload["report_ref"]
        == "reports/run-summaries/20260521/dars-panel-round-report.json"
    )

    report_path = tmp_path / payload["report_ref"]
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["schema_id"] == "hisys.dars_panel.round_report"
    assert report["request_id"] == "REQ-DARS-GOLDEN-BASIC"
    assert report["panel_id"] == config_blueprint["panel_id"]
    assert report["execution_mode"] == "serial"
    assert report["task_statuses"] == {
        f"TASK-REQ-DARS-GOLDEN-BASIC-00-{config_blueprint['critics'][0]['critic_id']}": "completed"
    }
    assert len(report["critique_refs"]) == 1
    assert report["synthesis_ref"].endswith("SYNTH-REQ-DARS-GOLDEN-BASIC.json")
    assert report["round_trace_ref"].endswith("TRACE-REQ-DARS-GOLDEN-BASIC.json")
    assert len(report["execution_boundary_refs"]) == 1
    assert report["advisory_only"] is True
    assert report["requires_human_review"] is True
    assert report["external_call_made"] is False
    assert report["mutation_performed"] is False
    assert report["publication_performed"] is False
    assert report["live_external_action_authorized"] is False

    report_md = report_path.with_suffix(".md").read_text(encoding="utf-8")
    assert "# DARS panel round report" in report_md
    assert "REQ-DARS-GOLDEN-BASIC" in report_md
    assert "live_external_action_authorized: false" in report_md


def test_run_dars_panel_cli_blocks_external_backend_without_live_dispatch(
    tmp_path: Path, capsys
):
    """M-CP-EXT-6: an external-prefixed backend is blocked, never dispatched.

    Characterization of the safety boundary: the default fixture policy treats
    any ``external-*`` backend as ``adapter_class="external"`` and the registry
    blocks the dispatch because no external dispatch is enabled. The CLI
    surfaces a typed ``blocked`` task status with a persisted boundary record
    showing the locked advisory envelope, while still exiting 0.
    """

    from hisys.cli.main import main

    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    config_path = tmp_path / "panel-config.json"
    config_path.write_text(
        json.dumps(
            {
                "panel_id": "PANEL-DARS-CP-EXT-6",
                "max_parallel_critics": 1,
                "critics": [
                    {
                        "critic_id": "logical-devil",
                        "critic_role": "logical_devil",
                        "backend_id": "external-cli-backend",
                        "rubric_ref": rubric_ref,
                        "critique_dimensions": ["logical_validity"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "run-dars-panel",
            "--instance",
            str(tmp_path),
            "--date",
            "20260520",
            "--request-id",
            "REQ-DARS-CP-EXT-6-EXT",
            "--panel-config",
            str(config_path),
            "--candidate-ref",
            candidate_ref,
            "--evidence-ref",
            evidence_refs[0],
            "--format",
            "json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["task_statuses"] == {
        "TASK-REQ-DARS-CP-EXT-6-EXT-00-logical-devil": "blocked"
    }
    assert payload["critique_refs"] == []
    assert len(payload["execution_boundary_refs"]) == 1

    boundary_ref = payload["execution_boundary_refs"][0]
    boundary = json.loads((tmp_path / boundary_ref).read_text(encoding="utf-8"))
    assert boundary["dispatch_decision"] == "blocked"
    assert boundary["external_call_made"] is False
    assert boundary["mutation_performed"] is False
    assert boundary["action_authorized"] is False
    assert boundary["advisory_only"] is True
    assert boundary["requires_human_review"] is True
    assert boundary["adapter_class"] == "unresolved"


def _activation_packet_file(tmp_path: Path) -> Path:
    path = tmp_path / "activation-packet.json"
    path.write_text(
        json.dumps(
            {
                "activation_id": "ACT-DARS-LIVE-3",
                "approval_ref": "APPROVAL-DARS-LIVE-LOCALHOST-ONLY",
                "operator_id": "operator-professor",
                "approved_endpoint_scope": "localhost_only",
                "allowed_actions": "advisory_only",
                "human_approved": True,
                "expires_at": "2026-05-21T00:00:00Z",
                "requested_backend_id": "local-fake-openai",
                "requested_adapter_class": "local_model",
            }
        ),
        encoding="utf-8",
    )
    return path


def _local_model_panel_config(tmp_path: Path, rubric_ref: str) -> Path:
    path = tmp_path / "local-model-panel-config.json"
    path.write_text(
        json.dumps(
            {
                "panel_id": "PANEL-DARS-LIVE-3",
                "max_parallel_critics": 1,
                "critics": [
                    {
                        "critic_id": "logical-devil",
                        "critic_role": "logical_devil",
                        "backend_id": "local-fake-openai",
                        "rubric_ref": rubric_ref,
                        "critique_dimensions": ["logical_validity", "missing_evidence"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_run_dars_panel_cli_requires_activation_packet_for_local_model_mode(
    tmp_path: Path, capsys
):
    """M-CP-LIVE-3: local-model CLI mode fails closed without activation."""

    from hisys.cli.main import main

    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    config_path = _local_model_panel_config(tmp_path, rubric_ref)

    with FakeOpenAIServer() as server:
        with pytest.raises(SystemExit) as excinfo:
            main(
                [
                    "run-dars-panel",
                    "--instance",
                    str(tmp_path),
                    "--date",
                    "20260520",
                    "--request-id",
                    "REQ-DARS-LIVE-3-MISSING-ACTIVATION",
                    "--panel-config",
                    str(config_path),
                    "--candidate-ref",
                    candidate_ref,
                    "--evidence-ref",
                    evidence_refs[0],
                    "--local-model-endpoint",
                    server.endpoint,
                    "--local-model",
                    "fake-local-dars",
                    "--format",
                    "json",
                ]
            )

    assert excinfo.value.code == 2
    assert "--activation-packet is required" in capsys.readouterr().err
    assert server.contacted is False


def test_run_dars_panel_cli_rehearses_local_model_with_activation_packet(
    tmp_path: Path, capsys
):
    """M-CP-LIVE-3: approved CLI local mode uses only the localhost fake server."""

    from hisys.cli.main import main

    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    config_path = _local_model_panel_config(tmp_path, rubric_ref)
    activation_path = _activation_packet_file(tmp_path)

    with FakeOpenAIServer(response_content="local cli fake critique") as server:
        exit_code = main(
            [
                "run-dars-panel",
                "--instance",
                str(tmp_path),
                "--date",
                "20260520",
                "--request-id",
                "REQ-DARS-LIVE-3",
                "--panel-config",
                str(config_path),
                "--candidate-ref",
                candidate_ref,
                "--evidence-ref",
                evidence_refs[0],
                "--local-model-endpoint",
                server.endpoint,
                "--local-model",
                "fake-local-dars",
                "--activation-packet",
                str(activation_path),
                "--format",
                "json",
            ]
        )
        server_host = server.host

    assert exit_code == 0
    assert server_host == "127.0.0.1"
    assert server.contacted is True
    payload = json.loads(capsys.readouterr().out)
    assert payload["request_id"] == "REQ-DARS-LIVE-3"
    assert payload["panel_id"] == "PANEL-DARS-LIVE-3"
    assert payload["execution_mode"] == "local_model_rehearsal"
    assert payload["model_boundary_crossed"] is True
    assert payload["local_model_call_made"] is True
    assert payload["external_call_made"] is False
    assert payload["mutation_performed"] is False
    assert payload["publication_performed"] is False
    assert payload["allowed_actions"] == "advisory_only"
    assert payload["task_statuses"] == {"TASK-REQ-DARS-LIVE-3-00-logical-devil": "completed"}
    assert len(payload["local_model_boundary_refs"]) == 1

    boundary = json.loads((tmp_path / payload["local_model_boundary_refs"][0]).read_text(encoding="utf-8"))
    assert boundary["approval_ref"] == "APPROVAL-DARS-LIVE-LOCALHOST-ONLY"
    assert boundary["adapter_class"] == "local_model"
    assert boundary["endpoint_scope"] == "localhost_only"
    assert boundary["model_boundary_crossed"] is True
    assert boundary["local_model_call_made"] is True
    assert boundary["external_call_made"] is False
    assert boundary["mutation_performed"] is False
    assert boundary["publication_performed"] is False
