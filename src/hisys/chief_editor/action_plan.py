"""Chief Editor dry-run alert action plan runtime.

Traceability: HISYS-FR-CE-001..006, HISYS-CE-POLICY-001,
HISYS-D-015, HISYS-T-019.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from ..config import InstanceRoot
from ..schemas import AlertDecisionRecord

BlockedReason = Literal["approval_required", "suppressed", "no_target_channel", "live_delivery_disabled"]


class AlertActionPlanRecord(BaseModel):
    """Dry-run action plan for one alert decision.

    This is intentionally not a live connector request. It records what would be
    considered and why delivery is blocked in the fixture harness.
    """

    plan_id: str
    alert_decision_ref: str
    target_channel: str | None = None
    approval_required: bool = False
    would_send: bool = False
    blocked_reason: BlockedReason | None = None
    live_delivery_permitted: bool = False
    action_taken: Literal["none"] = "none"
    producer_id: str
    policy_refs: list[str] = Field(default_factory=lambda: ["HISYS-FR-CE-006", "HISYS-T-019"])


@dataclass(frozen=True)
class AlertActionPlanRunReport:
    """Machine-checkable I7-D dry-run action planning report."""

    alert_decision_refs: list[str]
    action_plan_refs: list[str] = field(default_factory=list)
    would_send_refs: list[str] = field(default_factory=list)
    blocked_refs: list[str] = field(default_factory=list)
    skipped_decision_refs: list[str] = field(default_factory=list)
    policy_refs: list[str] = field(default_factory=lambda: ["HISYS-FR-CE-006", "HISYS-T-019"])


class AlertActionPlanRuntime:
    """Persist dry-run action plans for existing alert decisions."""

    def __init__(self, *, instance: InstanceRoot, producer_id: str) -> None:
        self.instance = instance
        self.producer_id = producer_id

    def plan_run(self, *, yyyymmdd: str) -> AlertActionPlanRunReport:
        decisions = _load_alert_decisions(self.instance, yyyymmdd)
        action_plan_refs: list[str] = []
        would_send_refs: list[str] = []
        blocked_refs: list[str] = []
        skipped_refs: list[str] = []
        for decision in decisions:
            plan = self._plan_for_decision(decision)
            if plan is None:
                skipped_refs.append(decision.alert_id)
                continue
            self._write_plan(plan, yyyymmdd)
            action_plan_refs.append(plan.plan_id)
            if plan.would_send:
                would_send_refs.append(plan.plan_id)
            if plan.blocked_reason is not None:
                blocked_refs.append(plan.plan_id)
        report = AlertActionPlanRunReport(
            alert_decision_refs=[decision.alert_id for decision in decisions],
            action_plan_refs=action_plan_refs,
            would_send_refs=would_send_refs,
            blocked_refs=blocked_refs,
            skipped_decision_refs=skipped_refs,
        )
        self._write_report(report, yyyymmdd)
        return report

    def _plan_for_decision(self, decision: AlertDecisionRecord) -> AlertActionPlanRecord | None:
        if decision.action_taken != "none":
            return None
        approval_required = decision.approval_status == "requested" or decision.status == "needs_approval"
        blocked_reason: BlockedReason | None = None
        if approval_required:
            blocked_reason = "approval_required"
        elif decision.status == "suppressed":
            blocked_reason = "suppressed"
        elif not decision.target_channel:
            blocked_reason = "no_target_channel"
        else:
            blocked_reason = "live_delivery_disabled"
        return AlertActionPlanRecord(
            plan_id=_plan_id_for_alert(decision.alert_id),
            alert_decision_ref=decision.alert_id,
            target_channel=decision.target_channel,
            approval_required=approval_required,
            would_send=False,
            blocked_reason=blocked_reason,
            live_delivery_permitted=False,
            action_taken="none",
            producer_id=self.producer_id,
        )

    def _write_plan(self, plan: AlertActionPlanRecord, yyyymmdd: str) -> tuple[Path, Path]:
        directory = self.instance.root / "data" / "alert-action-plans" / yyyymmdd
        directory.mkdir(parents=True, exist_ok=True)
        json_path = directory / f"{plan.plan_id}.json"
        markdown_path = directory / f"{plan.plan_id}.md"
        json_path.write_text(_to_json(plan), encoding="utf-8")
        markdown_path.write_text(_plan_to_markdown(plan), encoding="utf-8")
        return json_path, markdown_path

    def _write_report(self, report: AlertActionPlanRunReport, yyyymmdd: str) -> Path:
        directory = self.instance.root / "reports" / "run-summaries" / yyyymmdd
        directory.mkdir(parents=True, exist_ok=True)
        json_path = directory / "alert-action-plan-report.json"
        json_path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        markdown_path = directory / "alert-action-plan-report.md"
        markdown_path.write_text(_report_to_markdown(report), encoding="utf-8")
        return json_path


def _load_alert_decisions(instance: InstanceRoot, yyyymmdd: str) -> list[AlertDecisionRecord]:
    directory = instance.root / "data" / "alert-decisions" / yyyymmdd
    if not directory.exists():
        return []
    decisions: list[AlertDecisionRecord] = []
    for path in sorted(directory.glob("ALERT-*.json")):
        decisions.append(AlertDecisionRecord.model_validate_json(path.read_text(encoding="utf-8")))
    return decisions


def _plan_id_for_alert(alert_id: str) -> str:
    suffix = alert_id.removeprefix("ALERT-")
    return f"PLAN-{suffix}"


def _to_json(record: BaseModel) -> str:
    return json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True)


def _plan_to_markdown(plan: AlertActionPlanRecord) -> str:
    return "\n".join(
        [
            "# Hisys Alert Action Plan",
            "",
            f"- plan_id: `{plan.plan_id}`",
            f"- alert_decision_ref: `{plan.alert_decision_ref}`",
            f"- target_channel: `{plan.target_channel or 'none'}`",
            f"- approval_required: `{plan.approval_required}`",
            f"- would_send: `{plan.would_send}`",
            f"- blocked_reason: `{plan.blocked_reason or 'none'}`",
            f"- live_delivery_permitted: `{plan.live_delivery_permitted}`",
            f"- action_taken: `{plan.action_taken}`",
            "",
        ]
    )


def _report_to_markdown(report: AlertActionPlanRunReport) -> str:
    return "\n".join(
        [
            "# Hisys Alert Action Plan Report",
            "",
            f"- alert_decisions: {len(report.alert_decision_refs)}",
            f"- action_plans: {len(report.action_plan_refs)}",
            f"- would_send: {len(report.would_send_refs)}",
            f"- blocked: {len(report.blocked_refs)}",
            f"- skipped_decisions: {len(report.skipped_decision_refs)}",
            "",
            "## Action Plans",
            *[f"- {ref}" for ref in report.action_plan_refs],
            "",
            "## Policy References",
            *[f"- {ref}" for ref in report.policy_refs],
            "",
        ]
    )


__all__ = ["AlertActionPlanRecord", "AlertActionPlanRunReport", "AlertActionPlanRuntime"]
