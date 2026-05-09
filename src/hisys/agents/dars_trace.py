"""DARS end-to-end trace-link records.

Traceability: HISYS-DARS-CONTRACT-001, HISYS-T-024, HISYS-FR-AGT-001..005,
HISYS-FR-INV-001..006, HISYS-FR-MEM-001..005.
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict

from ..config.instance import InstanceRoot
from .dars_protocol import DarsRequestEnvelope, DarsResponseEnvelope


class DarsTraceLink(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_id: Literal["hisys.dars.trace_link"] = "hisys.dars.trace_link"
    schema_version: Literal["0.1.0"] = "0.1.0"
    trace_id: str
    request_id: str
    response_id: str
    handoff_id: str
    source_refs: list[str]
    observation_refs: list[str]
    signal_refs: list[str]
    memo_refs: list[str]
    alert_refs: list[str]
    evidence_refs: list[str]
    critique_id: str
    recommended_action_ids: list[str]
    runtime_boundary_refs: list[str]
    requirement_refs: list[str]
    policy_refs: list[str]
    trace_complete: bool
    gaps: list[str]
    external_call_made: bool = False
    mutation_performed: bool = False
    action_taken: Literal["none"] = "none"


class DarsTraceLinker:
    """Build and persist source/memo/alert → DARS critique trace links."""

    def __init__(self, *, instance: InstanceRoot) -> None:
        self.instance = instance

    def write_trace_link(
        self,
        *,
        yyyymmdd: str,
        request: DarsRequestEnvelope,
        response: DarsResponseEnvelope,
        dispatch_decision_ref: str,
        validation_ref: str,
        response_ref: str,
    ) -> DarsTraceLink:
        request_refs = request.record_refs
        response_refs = response.critique.linked_record_refs
        source_refs = _merge_unique(request_refs.sources, response_refs.sources)
        observation_refs = _merge_unique(request_refs.observations, response_refs.observations)
        signal_refs = _merge_unique(request_refs.signals, response_refs.signals)
        memo_refs = _merge_unique(request_refs.memos, response_refs.memos)
        alert_refs = _merge_unique(request_refs.alerts, response_refs.alerts)
        runtime_boundary_refs = _merge_unique(
            [dispatch_decision_ref, validation_ref, response_ref],
            request_refs.runtime_boundary,
            response_refs.runtime_boundary,
        )
        evidence_refs = [bundle.evidence_ref for bundle in request.evidence.bundles]
        gaps = _trace_gaps(source_refs=source_refs, memo_refs=memo_refs, alert_refs=alert_refs, evidence_refs=evidence_refs)
        trace = DarsTraceLink(
            trace_id=f"DARSTRACE-{request.request_id}",
            request_id=request.request_id,
            response_id=response.response_id,
            handoff_id=request.handoff_id,
            source_refs=source_refs,
            observation_refs=observation_refs,
            signal_refs=signal_refs,
            memo_refs=memo_refs,
            alert_refs=alert_refs,
            evidence_refs=evidence_refs,
            critique_id=response.critique.critique_id,
            recommended_action_ids=[action.action_id for action in response.critique.recommended_actions],
            runtime_boundary_refs=runtime_boundary_refs,
            requirement_refs=_merge_unique(request_refs.requirements, request.constraints.requirement_refs),
            policy_refs=list(request.constraints.policy_refs),
            trace_complete=not gaps,
            gaps=gaps,
            external_call_made=response.producer.external_call_made,
            mutation_performed=response.boundary.mutation_performed,
            action_taken=response.boundary.action_taken,
        )
        _write_trace(self.instance, yyyymmdd, trace)
        return trace


def _merge_unique(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for item in group:
            if item and item not in seen:
                merged.append(item)
                seen.add(item)
    return merged


def _trace_gaps(*, source_refs: list[str], memo_refs: list[str], alert_refs: list[str], evidence_refs: list[str]) -> list[str]:
    gaps: list[str] = []
    if not (source_refs or memo_refs or alert_refs):
        gaps.append("no source/memo/alert refs")
    if not evidence_refs:
        gaps.append("no evidence bundle refs")
    return gaps


def _write_trace(instance: InstanceRoot, yyyymmdd: str, trace: DarsTraceLink) -> None:
    output_dir = instance.runtime_boundary_dir / "dars" / yyyymmdd
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = trace.model_dump(mode="json")
    json_path = output_dir / f"dars-trace-{trace.trace_id}.json"
    md_path = output_dir / f"dars-trace-{trace.trace_id}.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(_trace_markdown(trace), encoding="utf-8")


def _trace_markdown(trace: DarsTraceLink) -> str:
    return "\n".join(
        [
            f"# DARS trace {trace.trace_id}",
            "",
            f"- request_id: {trace.request_id}",
            f"- response_id: {trace.response_id}",
            f"- handoff_id: {trace.handoff_id}",
            f"- critique_id: {trace.critique_id}",
            f"- trace_complete: {trace.trace_complete}",
            f"- external_call_made: {trace.external_call_made}",
            f"- mutation_performed: {trace.mutation_performed}",
            "",
            "## Runtime Boundary Refs",
            *[f"- {ref}" for ref in trace.runtime_boundary_refs],
            "",
        ]
    )


__all__ = ["DarsTraceLink", "DarsTraceLinker"]
