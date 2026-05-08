"""Disabled Chief Editor alert connector execution harness.

Traceability: HISYS-FR-CE-006, HISYS-FR-AGT-004, HISYS-D-015,
HISYS-T-022.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from ..config.instance import InstanceRoot

ExecutionStatus = Literal["blocked"]


class AlertConnectorExecutionRecord(BaseModel):
    execution_id: str
    action_plan_ref: str
    alert_decision_ref: str
    connector_id: str
    target_channel: str | None = None
    would_send: bool
    live_delivery_permitted: bool = False
    execution_status: ExecutionStatus = "blocked"
    blocked_reason: str
    action_taken: Literal["none"] = "none"
    policy_refs: list[str] = Field(default_factory=lambda: ["HISYS-FR-CE-006", "HISYS-FR-AGT-004", "HISYS-T-022"])


@dataclass(frozen=True)
class AlertConnectorExecutionReport:
    report_ref: str
    action_plan_refs: list[str] = field(default_factory=list)
    execution_refs: list[str] = field(default_factory=list)
    sent_refs: list[str] = field(default_factory=list)
    blocked_refs: list[str] = field(default_factory=list)
    skipped_plan_refs: list[str] = field(default_factory=list)
    policy_refs: list[str] = field(default_factory=lambda: ["HISYS-FR-CE-006", "HISYS-FR-AGT-004", "HISYS-T-022"])


class AlertConnectorRuntime:
    """Fixture connector that validates would-send plans but never sends."""

    def __init__(self, *, instance: InstanceRoot, connector_id: str = "disabled-fixture-connector") -> None:
        self.instance = instance
        self.connector_id = connector_id

    def execute_run(self, *, yyyymmdd: str) -> AlertConnectorExecutionReport:
        plans = _load_action_plans(self.instance, yyyymmdd)
        output_dir = self.instance.data_dir / "alert-connector-executions" / yyyymmdd
        output_dir.mkdir(parents=True, exist_ok=True)
        report = AlertConnectorExecutionReport(
            report_ref=str(_report_json_path(self.instance, yyyymmdd).relative_to(self.instance.root))
        )
        for plan in plans:
            plan_id = plan.get("plan_id")
            if not plan_id:
                continue
            report.action_plan_refs.append(plan_id)
            execution = self._execution_for_plan(plan)
            if execution is None:
                report.skipped_plan_refs.append(plan_id)
                continue
            _write_execution(output_dir, execution)
            report.execution_refs.append(execution.execution_id)
            report.blocked_refs.append(execution.execution_id)
        _write_report(self.instance, yyyymmdd, report)
        return report

    def _execution_for_plan(self, plan: dict) -> AlertConnectorExecutionRecord | None:
        if plan.get("action_taken") != "none":
            return None
        plan_id = str(plan["plan_id"])
        blocked_reason = str(plan.get("blocked_reason") or "live_delivery_disabled")
        if plan.get("live_delivery_permitted") is not False:
            blocked_reason = "live_delivery_disabled"
        return AlertConnectorExecutionRecord(
            execution_id=_execution_id_for_plan(plan_id),
            action_plan_ref=plan_id,
            alert_decision_ref=str(plan.get("alert_decision_ref", "")),
            connector_id=self.connector_id,
            target_channel=plan.get("target_channel"),
            would_send=bool(plan.get("would_send")),
            live_delivery_permitted=False,
            execution_status="blocked",
            blocked_reason=blocked_reason,
            action_taken="none",
        )


def _load_action_plans(instance: InstanceRoot, yyyymmdd: str) -> list[dict]:
    plan_dir = instance.data_dir / "alert-action-plans" / yyyymmdd
    if not plan_dir.exists():
        return []
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(plan_dir.glob("*.json"))]


def _write_execution(output_dir: Path, execution: AlertConnectorExecutionRecord) -> None:
    payload = execution.model_dump(mode="json")
    json_path = output_dir / f"{execution.execution_id}.json"
    md_path = output_dir / f"{execution.execution_id}.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(
        "\n".join(
            [
                f"# Alert connector execution {execution.execution_id}",
                "",
                f"- action_plan_ref: {execution.action_plan_ref}",
                f"- alert_decision_ref: {execution.alert_decision_ref}",
                f"- connector_id: {execution.connector_id}",
                f"- would_send: {execution.would_send}",
                f"- live_delivery_permitted: {execution.live_delivery_permitted}",
                f"- execution_status: {execution.execution_status}",
                f"- blocked_reason: {execution.blocked_reason}",
                f"- action_taken: {execution.action_taken}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_report(instance: InstanceRoot, yyyymmdd: str, report: AlertConnectorExecutionReport) -> None:
    report_json = _report_json_path(instance, yyyymmdd)
    report_json.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(report)
    report_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _report_md_path(instance, yyyymmdd).write_text(
        "\n".join(
            [
                "# Alert Connector Execution Report",
                "",
                f"- action_plans: {len(report.action_plan_refs)}",
                f"- executions: {len(report.execution_refs)}",
                f"- sent: {len(report.sent_refs)}",
                f"- blocked: {len(report.blocked_refs)}",
                f"- skipped: {len(report.skipped_plan_refs)}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _report_json_path(instance: InstanceRoot, yyyymmdd: str) -> Path:
    return instance.reports_dir / "run-summaries" / yyyymmdd / "alert-connector-execution-report.json"


def _report_md_path(instance: InstanceRoot, yyyymmdd: str) -> Path:
    return instance.reports_dir / "run-summaries" / yyyymmdd / "alert-connector-execution-report.md"


def _execution_id_for_plan(plan_id: str) -> str:
    return plan_id.replace("PLAN-", "EXEC-", 1)


__all__ = ["AlertConnectorExecutionRecord", "AlertConnectorExecutionReport", "AlertConnectorRuntime"]
