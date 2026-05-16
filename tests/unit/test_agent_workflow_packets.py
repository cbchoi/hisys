import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from hisys.operations.agent_workflow import (
    FinishPacket,
    SpecFirstRunPacket,
    build_finish_packet,
    build_spec_first_run_packet,
    write_finish_packet,
    write_spec_first_run_packet,
)


def test_spec_first_packet_requires_scope_and_preserves_no_live_action_boundary():
    with pytest.raises(ValidationError):
        SpecFirstRunPacket(
            packet_id="SPEC-EMPTY",
            objective="Improve governed agent workflow",
            scope=[],
            allowed_actions=["read_only_local_files"],
            evidence_contract=["each claim cites an artifact ref"],
            gate_criteria=["focused tests pass"],
            human_approval_boundary="Required before live external action or mutation.",
        )

    packet = build_spec_first_run_packet(
        packet_id="SPEC-HISYS-SUPERPOWERS-001",
        objective="Apply Superpowers workflow lessons without copying plugin assumptions.",
        scope=["spec-first packet", "finish packet", "Hermes skill reference"],
        non_goals=["install Superpowers automatically", "weaken needs_more_evidence gates"],
        allowed_actions=["read_only_local_files", "fixture_only_tests"],
        evidence_contract=["each implementation claim has a test/doc/artifact ref"],
        expected_artifacts=["runtime-boundary/agent-workflows/<date>/SPEC-HISYS-SUPERPOWERS-001.json"],
        gate_criteria=["focused tests pass", "git diff --check passes"],
        human_approval_boundary="Human approval required before live external action, publication, vault mutation, or governance-gate weakening.",
    )

    assert packet.workflow_model == "spec_first_plan_execute_review_finish"
    assert packet.external_call_made is False
    assert packet.mutation_performed is False
    assert packet.publication_or_live_action_approved is False
    assert "weaken needs_more_evidence gates" in packet.non_goals


def test_write_spec_first_packet_persists_json_and_markdown(tmp_path: Path):
    packet = build_spec_first_run_packet(
        packet_id="SPEC-TEST-001",
        objective="Test packet persistence.",
        scope=["packet schema"],
        non_goals=["live action"],
        allowed_actions=["fixture_only_tests"],
        evidence_contract=["test asserts json and markdown refs"],
        expected_artifacts=["json", "markdown"],
        gate_criteria=["pytest passes"],
        human_approval_boundary="Required before mutation.",
    )

    result = write_spec_first_run_packet(tmp_path, "20260516", packet)

    assert result["json_ref"] == "runtime-boundary/agent-workflows/20260516/SPEC-TEST-001.json"
    assert result["markdown_ref"] == "runtime-boundary/agent-workflows/20260516/SPEC-TEST-001.md"
    data = json.loads((tmp_path / result["json_ref"]).read_text())
    assert data["packet_id"] == "SPEC-TEST-001"
    assert data["mutation_performed"] is False
    assert "# SPEC-TEST-001" in (tmp_path / result["markdown_ref"]).read_text()


def test_finish_packet_records_review_gate_without_authorizing_live_action(tmp_path: Path):
    packet = build_finish_packet(
        packet_id="FINISH-SPEC-TEST-001",
        spec_packet_ref="runtime-boundary/agent-workflows/20260516/SPEC-TEST-001.json",
        completed_tasks=["added spec packet schema", "added finish packet writer"],
        validation_results=["pytest tests/unit/test_agent_workflow_packets.py -q: passed"],
        review_findings=["subagents remain evidence collectors, not decision owners"],
        unresolved_blockers=["full Superpowers repo audit not performed"],
        next_actions=["map detailed skill files before deeper adoption"],
        human_gate_state="required_before_live_external_action",
    )

    assert packet.decision == "complete_for_human_review"
    assert packet.action_taken == "none"
    assert packet.external_call_made is False
    assert packet.mutation_performed is False
    assert packet.publication_or_live_action_approved is False

    result = write_finish_packet(tmp_path, "20260516", packet)
    data = json.loads((tmp_path / result["json_ref"]).read_text())
    assert data["human_gate_state"] == "required_before_live_external_action"
    assert data["unresolved_blockers"] == ["full Superpowers repo audit not performed"]


def test_cli_builds_spec_and_finish_packets(tmp_path: Path):
    spec_cmd = [
        sys.executable,
        "-m",
        "hisys.cli.main",
        "build-spec-first-packet",
        "--instance",
        str(tmp_path),
        "--date",
        "20260516",
        "--packet-id",
        "SPEC-CLI-001",
        "--objective",
        "Apply workflow safely.",
        "--scope",
        "spec packet",
        "--non-goal",
        "automatic plugin install",
        "--allowed-action",
        "read_only_local_files",
        "--evidence-contract",
        "claim refs required",
        "--expected-artifact",
        "runtime-boundary/agent-workflows/20260516/SPEC-CLI-001.json",
        "--gate-criterion",
        "focused tests pass",
        "--human-approval-boundary",
        "Required before live action.",
        "--format",
        "json",
    ]
    spec = subprocess.run(spec_cmd, check=True, text=True, capture_output=True)
    spec_result = json.loads(spec.stdout)
    assert spec_result["json_ref"].endswith("SPEC-CLI-001.json")

    finish_cmd = [
        sys.executable,
        "-m",
        "hisys.cli.main",
        "build-finish-packet",
        "--instance",
        str(tmp_path),
        "--date",
        "20260516",
        "--packet-id",
        "FINISH-CLI-001",
        "--spec-packet-ref",
        spec_result["json_ref"],
        "--completed-task",
        "added CLI packet command",
        "--validation-result",
        "focused tests pass",
        "--review-finding",
        "no live action authorized",
        "--unresolved-blocker",
        "full repo audit pending",
        "--next-action",
        "inspect Superpowers skill files",
        "--human-gate-state",
        "required_before_live_external_action",
        "--format",
        "json",
    ]
    finish = subprocess.run(finish_cmd, check=True, text=True, capture_output=True)
    finish_result = json.loads(finish.stdout)
    assert finish_result["json_ref"].endswith("FINISH-CLI-001.json")
    assert (tmp_path / finish_result["markdown_ref"]).exists()
