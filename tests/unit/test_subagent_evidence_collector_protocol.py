"""Subagent evidence collector protocol tests.

Traceability: docs/plans/m21-9-subagent-evidence-collector-protocol-implementation-tasks.md.
"""

from __future__ import annotations

import pytest

from hisys.contracts.subagent_evidence_collector import (
    SubagentEvidenceValidationError,
    validate_subagent_evidence_result_packet,
    validate_subagent_evidence_task_packet,
)


def _task_payload() -> dict[str, object]:
    return {
        "schema_id": "hisys.subagent_evidence.task.v1",
        "task_id": "SUBEVID-TASK-001",
        "parent_request_id": "REQ-CODEBASE-001",
        "objective": "Inspect bounded code-analysis refs for missing traceability anchors.",
        "repo_ref": "repos/hisys",
        "include_refs": ["src/hisys/contracts", "tests/unit/test_pass_contract_evaluator.py"],
        "exclude_refs": ["runtime-boundary/", ".git/"],
        "allowed_read_only_tools": ["read_file", "search_files"],
        "expected_artifact_schema": "hisys.subagent_evidence.result.v1",
        "what_not_to_do": ["do not mutate files", "do not call network tools"],
        "advisory_only": True,
        "requires_human_review": True,
    }


def _result_payload() -> dict[str, object]:
    return {
        "schema_id": "hisys.subagent_evidence.result.v1",
        "task_id": "SUBEVID-TASK-001",
        "summary": "Two bounded refs inspected; no mutation performed.",
        "artifact_refs": ["runtime-boundary/subagent-evidence/20260521/result.json"],
        "source_refs": ["src/hisys/contracts/pass_registry.py"],
        "validation_suggestions": ["PYTHONPATH=src pytest tests/unit/test_pass_contract_evaluator.py -q"],
        "blockers": [],
        "external_call_made": False,
        "mutation_performed": False,
        "raw_source_content_persisted": False,
        "parent_verification_required": True,
    }


def test_subagent_task_packet_accepts_bounded_read_only_scope() -> None:
    packet = validate_subagent_evidence_task_packet(_task_payload())

    assert packet.schema_id == "hisys.subagent_evidence.task.v1"
    assert packet.task_id == "SUBEVID-TASK-001"
    assert packet.allowed_read_only_tools == ("read_file", "search_files")
    assert packet.advisory_only is True
    assert packet.requires_human_review is True


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("repo_ref", "/abs/repo", "unsafe_ref"),
        ("include_refs", ["../escape.py"], "unsafe_ref"),
        ("allowed_read_only_tools", ["terminal"], "mutation_tool_not_allowed"),
        ("allowed_read_only_tools", ["browser_navigate"], "external_call_not_allowed"),
        ("advisory_only", False, "advisory_only_required"),
    ],
)
def test_subagent_task_packet_rejects_unsafe_scope_or_authority(
    field: str, value: object, code: str
) -> None:
    payload = _task_payload()
    payload[field] = value

    with pytest.raises(SubagentEvidenceValidationError) as exc_info:
        validate_subagent_evidence_task_packet(payload)

    assert exc_info.value.code == code


def test_subagent_result_packet_accepts_advisory_refs_and_boundary_flags() -> None:
    task = validate_subagent_evidence_task_packet(_task_payload())

    result = validate_subagent_evidence_result_packet(_result_payload(), task=task)

    assert result.schema_id == "hisys.subagent_evidence.result.v1"
    assert result.task_id == task.task_id
    assert result.artifact_refs == ("runtime-boundary/subagent-evidence/20260521/result.json",)
    assert result.external_call_made is False
    assert result.mutation_performed is False
    assert result.raw_source_content_persisted is False
    assert result.parent_verification_required is True


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("external_call_made", True, "external_call_not_allowed"),
        ("mutation_performed", True, "mutation_not_allowed"),
        ("raw_source_content_persisted", True, "raw_source_persistence_not_allowed"),
        ("parent_verification_required", False, "parent_verification_required_missing"),
        ("artifact_refs", ["/tmp/result.json"], "unsafe_ref"),
    ],
)
def test_subagent_result_packet_rejects_side_effects_or_unverified_refs(
    field: str, value: object, code: str
) -> None:
    payload = _result_payload()
    payload[field] = value

    with pytest.raises(SubagentEvidenceValidationError) as exc_info:
        validate_subagent_evidence_result_packet(payload)

    assert exc_info.value.code == code


def test_subagent_result_packet_rejects_task_mismatch() -> None:
    task = validate_subagent_evidence_task_packet(_task_payload())
    payload = _result_payload()
    payload["task_id"] = "SUBEVID-TASK-OTHER"

    with pytest.raises(SubagentEvidenceValidationError) as exc_info:
        validate_subagent_evidence_result_packet(payload, task=task)

    assert exc_info.value.code == "task_id_mismatch"
