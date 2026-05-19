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
from pathlib import Path


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
