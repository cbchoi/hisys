"""Spec-first agent workflow packets for governed Hisys/Hermes work.

Traceability: HISYS-T-024, HISYS-CON-010..012, HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


WorkflowModel = Literal["spec_first_plan_execute_review_finish"]


class SpecFirstRunPacket(BaseModel):
    """Pre-run design packet for bounded agentic development/investigation."""

    model_config = ConfigDict(extra="forbid")

    schema_id: str = "hisys.agent_workflow.spec_first_run_packet.v1"
    packet_id: str
    workflow_model: WorkflowModel = "spec_first_plan_execute_review_finish"
    objective: str
    scope: list[str]
    non_goals: list[str] = Field(default_factory=list)
    allowed_actions: list[str]
    evidence_contract: list[str]
    expected_artifacts: list[str] = Field(default_factory=list)
    gate_criteria: list[str]
    human_approval_boundary: str
    external_call_made: bool = False
    mutation_performed: bool = False
    publication_or_live_action_approved: bool = False
    action_taken: Literal["none"] = "none"

    @field_validator(
        "packet_id",
        "objective",
        "human_approval_boundary",
    )
    @classmethod
    def _non_empty_string(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must be non-empty")
        return value.strip()

    @field_validator("scope", "allowed_actions", "evidence_contract", "gate_criteria")
    @classmethod
    def _non_empty_string_list(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("must contain at least one non-empty item")
        return cleaned

    @field_validator("non_goals", "expected_artifacts")
    @classmethod
    def _clean_optional_string_list(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]


class FinishPacket(BaseModel):
    """Run/branch closure packet that separates completion from live approval."""

    model_config = ConfigDict(extra="forbid")

    schema_id: str = "hisys.agent_workflow.finish_packet.v1"
    packet_id: str
    workflow_model: WorkflowModel = "spec_first_plan_execute_review_finish"
    spec_packet_ref: str
    decision: Literal["complete_for_human_review", "blocked_needs_more_evidence"] = "complete_for_human_review"
    completed_tasks: list[str]
    validation_results: list[str]
    review_findings: list[str]
    unresolved_blockers: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    human_gate_state: str
    external_call_made: bool = False
    mutation_performed: bool = False
    publication_or_live_action_approved: bool = False
    action_taken: Literal["none"] = "none"

    @field_validator("packet_id", "spec_packet_ref", "human_gate_state")
    @classmethod
    def _non_empty_string(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must be non-empty")
        return value.strip()

    @field_validator("completed_tasks", "validation_results", "review_findings")
    @classmethod
    def _non_empty_string_list(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("must contain at least one non-empty item")
        return cleaned

    @field_validator("unresolved_blockers", "next_actions")
    @classmethod
    def _clean_optional_string_list(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]


def build_spec_first_run_packet(
    *,
    packet_id: str,
    objective: str,
    scope: list[str],
    non_goals: list[str] | None = None,
    allowed_actions: list[str],
    evidence_contract: list[str],
    expected_artifacts: list[str] | None = None,
    gate_criteria: list[str],
    human_approval_boundary: str,
) -> SpecFirstRunPacket:
    return SpecFirstRunPacket(
        packet_id=packet_id,
        objective=objective,
        scope=scope,
        non_goals=non_goals or [],
        allowed_actions=allowed_actions,
        evidence_contract=evidence_contract,
        expected_artifacts=expected_artifacts or [],
        gate_criteria=gate_criteria,
        human_approval_boundary=human_approval_boundary,
    )


def build_finish_packet(
    *,
    packet_id: str,
    spec_packet_ref: str,
    completed_tasks: list[str],
    validation_results: list[str],
    review_findings: list[str],
    unresolved_blockers: list[str] | None = None,
    next_actions: list[str] | None = None,
    human_gate_state: str,
    decision: Literal["complete_for_human_review", "blocked_needs_more_evidence"] = "complete_for_human_review",
) -> FinishPacket:
    return FinishPacket(
        packet_id=packet_id,
        spec_packet_ref=spec_packet_ref,
        decision=decision,
        completed_tasks=completed_tasks,
        validation_results=validation_results,
        review_findings=review_findings,
        unresolved_blockers=unresolved_blockers or [],
        next_actions=next_actions or [],
        human_gate_state=human_gate_state,
    )


def _packet_dir(instance_root: Path, date: str) -> Path:
    return instance_root / "runtime-boundary" / "agent-workflows" / date


def _relative_to_instance(instance_root: Path, path: Path) -> str:
    return path.relative_to(instance_root).as_posix()


def _write_packet(instance_root: Path, date: str, packet: BaseModel, markdown: str) -> dict[str, object]:
    out_dir = _packet_dir(instance_root, date)
    out_dir.mkdir(parents=True, exist_ok=True)
    packet_id = str(packet.model_dump()["packet_id"])
    json_path = out_dir / f"{packet_id}.json"
    md_path = out_dir / f"{packet_id}.md"
    json_path.write_text(json.dumps(packet.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    return {
        "packet_id": packet_id,
        "json_ref": _relative_to_instance(instance_root, json_path),
        "markdown_ref": _relative_to_instance(instance_root, md_path),
        "external_call_made": False,
        "mutation_performed": False,
        "publication_or_live_action_approved": False,
    }


def _bullet(items: list[str]) -> str:
    if not items:
        return "- None\n"
    return "".join(f"- {item}\n" for item in items)


def render_spec_first_packet_markdown(packet: SpecFirstRunPacket) -> str:
    return f"""# {packet.packet_id}

## Objective
{packet.objective}

## Scope
{_bullet(packet.scope)}
## Non-goals
{_bullet(packet.non_goals)}
## Allowed actions
{_bullet(packet.allowed_actions)}
## Evidence contract
{_bullet(packet.evidence_contract)}
## Expected artifacts
{_bullet(packet.expected_artifacts)}
## Gate criteria
{_bullet(packet.gate_criteria)}
## Human approval boundary
{packet.human_approval_boundary}

## Safety boundary
- external_call_made: false
- mutation_performed: false
- publication_or_live_action_approved: false
- action_taken: none
"""


def render_finish_packet_markdown(packet: FinishPacket) -> str:
    return f"""# {packet.packet_id}

## Spec packet ref
{packet.spec_packet_ref}

## Decision
{packet.decision}

## Completed tasks
{_bullet(packet.completed_tasks)}
## Validation results
{_bullet(packet.validation_results)}
## Review findings
{_bullet(packet.review_findings)}
## Unresolved blockers
{_bullet(packet.unresolved_blockers)}
## Next actions
{_bullet(packet.next_actions)}
## Human gate state
{packet.human_gate_state}

## Safety boundary
- external_call_made: false
- mutation_performed: false
- publication_or_live_action_approved: false
- action_taken: none
"""


def write_spec_first_run_packet(instance_root: Path, date: str, packet: SpecFirstRunPacket) -> dict[str, object]:
    return _write_packet(instance_root, date, packet, render_spec_first_packet_markdown(packet))


def write_finish_packet(instance_root: Path, date: str, packet: FinishPacket) -> dict[str, object]:
    return _write_packet(instance_root, date, packet, render_finish_packet_markdown(packet))
