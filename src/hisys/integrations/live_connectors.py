"""Disabled-by-default live connector execution controls.

Traceability: HISYS-FR-AGT-004, HISYS-T-020, HISYS-T-022,
HISYS-CON-010, HISYS-CON-012, HISYS-CON-022..023.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

ExecutionStatus = Literal["blocked"]
ActionTaken = Literal["none"]


class LiveConnectorRequest(BaseModel):
    """Requested live connector action before safety evaluation."""

    connector_id: str
    connector_type: str
    target: str
    requested_action: str
    payload_summary: str
    approval_ref: str | None = None
    policy_refs: list[str] = Field(default_factory=list)


class LiveConnectorDecision(BaseModel):
    """Runtime-boundary decision for a live connector request.

    This baseline never performs the external call; it only records the blocked
    decision so later adapters can be gated without changing downstream evidence.
    """

    connector_id: str
    connector_type: str
    target: str
    requested_action: str
    payload_summary: str
    approval_ref: str | None
    execution_status: ExecutionStatus
    blocked_reason: str
    live_execution_permitted: bool = False
    external_call_made: bool = False
    action_taken: ActionTaken = "none"
    report_path: str
    policy_refs: list[str] = Field(default_factory=list)
    requirement_refs: list[str] = Field(
        default_factory=lambda: [
            "HISYS-FR-AGT-004",
            "HISYS-T-020",
            "HISYS-T-022",
            "HISYS-CON-010",
            "HISYS-CON-012",
            "HISYS-CON-022",
            "HISYS-CON-023",
        ]
    )


def evaluate_live_connector_request(
    *,
    request: LiveConnectorRequest,
    runtime_root: str | Path,
    yyyymmdd: str,
    enabled_connectors: dict[str, dict[str, Any]],
) -> LiveConnectorDecision:
    """Evaluate and persist a blocked live connector decision.

    The function intentionally has no transport implementation. Even configured
    connectors are blocked unless their action is allow-listed and approval is
    present; this first safety increment still records `action_taken=none` and
    `external_call_made=false`.
    """

    connector_config = enabled_connectors.get(request.connector_id)
    blocked_reason = _blocked_reason(request, connector_config)
    report_path = (
        Path(runtime_root)
        / "runtime-boundary"
        / "live-connectors"
        / yyyymmdd
        / f"live-connector-decision-{_safe_ref(request.connector_id)}.md"
    )
    decision = LiveConnectorDecision(
        connector_id=request.connector_id,
        connector_type=request.connector_type,
        target=request.target,
        requested_action=request.requested_action,
        payload_summary=request.payload_summary,
        approval_ref=request.approval_ref,
        execution_status="blocked",
        blocked_reason=blocked_reason,
        live_execution_permitted=False,
        external_call_made=False,
        action_taken="none",
        report_path=str(report_path),
        policy_refs=list(request.policy_refs),
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_format_decision_report(decision), encoding="utf-8")
    return decision


def _blocked_reason(request: LiveConnectorRequest, connector_config: dict[str, Any] | None) -> str:
    if connector_config is None:
        return "connector_disabled"
    allowed_actions = set(connector_config.get("allowed_actions") or [])
    if request.requested_action not in allowed_actions:
        return "action_not_allowed"
    if not request.approval_ref:
        return "approval_required"
    return "live_execution_not_enabled_in_baseline"


def _safe_ref(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-." else "-" for ch in value).strip("-.") or "connector"


def _format_decision_report(decision: LiveConnectorDecision) -> str:
    return "\n".join(
        [
            "# Live Connector Execution Decision",
            "",
            f"connector_id: `{decision.connector_id}`",
            f"connector_type: `{decision.connector_type}`",
            f"target: `{decision.target}`",
            f"requested_action: `{decision.requested_action}`",
            f"execution_status: `{decision.execution_status}`",
            f"blocked_reason: `{decision.blocked_reason}`",
            f"live_execution_permitted: `{decision.live_execution_permitted}`",
            f"external_call_made: `{decision.external_call_made}`",
            f"action_taken: `{decision.action_taken}`",
            "",
            "## Policy References",
            *[f"- {ref}" for ref in decision.policy_refs],
            "",
            "## Requirement References",
            *[f"- {ref}" for ref in decision.requirement_refs],
            "",
            "## Payload Summary",
            "",
            decision.payload_summary,
            "",
        ]
    )


__all__ = ["LiveConnectorDecision", "LiveConnectorRequest", "evaluate_live_connector_request"]
