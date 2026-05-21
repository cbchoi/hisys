"""Subagent evidence collector protocol models and validators.

Traceability: docs/plans/m21-9-subagent-evidence-collector-protocol-implementation-tasks.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, NoReturn

_TASK_SCHEMA_ID = "hisys.subagent_evidence.task.v1"
_RESULT_SCHEMA_ID = "hisys.subagent_evidence.result.v1"
_ALLOWED_READ_ONLY_TOOLS = frozenset({"read_file", "search_files"})
_MUTATION_OR_PROCESS_TOOLS = frozenset({
    "terminal",
    "process",
    "patch",
    "write_file",
    "rhwp_convert",
    "skill_manage",
    "memory",
    "send_message",
})
_EXTERNAL_OR_AGENT_TOOLS = frozenset({
    "browser_navigate",
    "browser_click",
    "browser_type",
    "browser_press",
    "browser_scroll",
    "browser_snapshot",
    "browser_console",
    "browser_get_images",
    "browser_vision",
    "delegate_task",
    "web_search",
    "x_search",
    "cronjob",
})


class SubagentEvidenceValidationError(ValueError):
    """Deterministic validation failure for subagent evidence packets."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class SubagentEvidenceTaskPacket:
    schema_id: str
    task_id: str
    parent_request_id: str
    objective: str
    repo_ref: str
    include_refs: tuple[str, ...]
    exclude_refs: tuple[str, ...]
    allowed_read_only_tools: tuple[str, ...]
    expected_artifact_schema: str
    what_not_to_do: tuple[str, ...]
    advisory_only: bool = True
    requires_human_review: bool = True


@dataclass(frozen=True)
class SubagentEvidenceResultPacket:
    schema_id: str
    task_id: str
    summary: str
    artifact_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    validation_suggestions: tuple[str, ...]
    blockers: tuple[str, ...]
    external_call_made: bool = False
    mutation_performed: bool = False
    raw_source_content_persisted: bool = False
    parent_verification_required: bool = True


def validate_subagent_evidence_task_packet(
    payload: dict[str, Any]
) -> SubagentEvidenceTaskPacket:
    """Validate a bounded read-only subagent task packet."""

    if payload.get("schema_id") != _TASK_SCHEMA_ID:
        _fail("schema_id_mismatch", "task packet schema_id mismatch")
    task_id = _required_text(payload, "task_id")
    parent_request_id = _required_text(payload, "parent_request_id")
    objective = _required_text(payload, "objective")
    repo_ref = _required_text(payload, "repo_ref")
    _validate_safe_ref(repo_ref)
    include_refs = _text_tuple(payload, "include_refs")
    exclude_refs = _text_tuple(payload, "exclude_refs")
    for ref in (*include_refs, *exclude_refs):
        _validate_safe_ref(ref)
    allowed_tools = _text_tuple(payload, "allowed_read_only_tools")
    if not allowed_tools:
        _fail("read_only_tool_required", "at least one read-only tool is required")
    for tool in allowed_tools:
        if tool in _MUTATION_OR_PROCESS_TOOLS:
            _fail("mutation_tool_not_allowed", f"tool is not read-only: {tool}")
        if tool in _EXTERNAL_OR_AGENT_TOOLS:
            _fail("external_call_not_allowed", f"tool requires external or agent authority: {tool}")
        if tool not in _ALLOWED_READ_ONLY_TOOLS:
            _fail("tool_not_allowed", f"tool is not in the allowed read-only set: {tool}")
    expected_schema = _required_text(payload, "expected_artifact_schema")
    what_not_to_do = _text_tuple(payload, "what_not_to_do")
    if payload.get("advisory_only") is not True:
        _fail("advisory_only_required", "task packets must be advisory-only")
    if payload.get("requires_human_review") is not True:
        _fail("human_review_required", "task packets require human review")
    return SubagentEvidenceTaskPacket(
        schema_id=_TASK_SCHEMA_ID,
        task_id=task_id,
        parent_request_id=parent_request_id,
        objective=objective,
        repo_ref=repo_ref,
        include_refs=include_refs,
        exclude_refs=exclude_refs,
        allowed_read_only_tools=allowed_tools,
        expected_artifact_schema=expected_schema,
        what_not_to_do=what_not_to_do,
        advisory_only=True,
        requires_human_review=True,
    )


def validate_subagent_evidence_result_packet(
    payload: dict[str, Any], *, task: SubagentEvidenceTaskPacket | None = None
) -> SubagentEvidenceResultPacket:
    """Validate a subagent result packet without verifying artifact existence."""

    if payload.get("schema_id") != _RESULT_SCHEMA_ID:
        _fail("schema_id_mismatch", "result packet schema_id mismatch")
    task_id = _required_text(payload, "task_id")
    if task is not None and task_id != task.task_id:
        _fail("task_id_mismatch", "result packet task_id does not match task packet")
    summary = _required_text(payload, "summary")
    artifact_refs = _text_tuple(payload, "artifact_refs")
    source_refs = _text_tuple(payload, "source_refs")
    for ref in (*artifact_refs, *source_refs):
        _validate_safe_ref(ref)
    validation_suggestions = _text_tuple(payload, "validation_suggestions")
    blockers = _text_tuple(payload, "blockers")
    if payload.get("external_call_made") is not False:
        _fail("external_call_not_allowed", "result packets must record no external calls")
    if payload.get("mutation_performed") is not False:
        _fail("mutation_not_allowed", "result packets must record no mutation")
    if payload.get("raw_source_content_persisted") is not False:
        _fail(
            "raw_source_persistence_not_allowed",
            "result packets must not persist raw source content",
        )
    if payload.get("parent_verification_required") is not True:
        _fail(
            "parent_verification_required_missing",
            "parent verification is required before reporting success",
        )
    return SubagentEvidenceResultPacket(
        schema_id=_RESULT_SCHEMA_ID,
        task_id=task_id,
        summary=summary,
        artifact_refs=artifact_refs,
        source_refs=source_refs,
        validation_suggestions=validation_suggestions,
        blockers=blockers,
        external_call_made=False,
        mutation_performed=False,
        raw_source_content_persisted=False,
        parent_verification_required=True,
    )


def _required_text(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        _fail("required_field_missing", f"{field} must be a non-empty string")
    return value


def _text_tuple(payload: dict[str, Any], field: str) -> tuple[str, ...]:
    value = payload.get(field)
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        _fail("required_field_missing", f"{field} must be a list of non-empty strings")
    return tuple(value)


def _validate_safe_ref(ref: str) -> None:
    path = PurePosixPath(ref)
    if path.is_absolute() or ".." in path.parts:
        _fail("unsafe_ref", f"unsafe filesystem ref: {ref}")


def _fail(code: str, message: str) -> NoReturn:
    raise SubagentEvidenceValidationError(code, message)
