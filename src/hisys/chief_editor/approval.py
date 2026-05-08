"""Chief Editor runtime-local approval transition stub.

Traceability: HISYS-FR-CE-006, HISYS-CE-POLICY-001,
HISYS-D-015, HISYS-T-020.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from ..config import InstanceRoot
from ..schemas import AlertDecisionRecord

ApprovalOutcome = Literal["approved", "rejected"]


@dataclass(frozen=True)
class AlertApprovalTransitionReport:
    """Machine-checkable I7-E approval transition report."""

    alert_decision_ref: str
    previous_approval_status: str
    new_approval_status: str
    previous_status: str
    new_status: str
    action_taken: str
    reviewer_id: str
    rationale: str
    policy_refs: list[str] = field(default_factory=lambda: ["HISYS-FR-CE-006", "HISYS-T-020"])


class AlertApprovalTransitionRuntime:
    """Apply fixture approve/reject transitions to local alert decisions only."""

    def __init__(self, *, instance: InstanceRoot, reviewer_id: str) -> None:
        self.instance = instance
        self.reviewer_id = reviewer_id

    def transition(
        self,
        *,
        yyyymmdd: str,
        alert_id: str,
        outcome: ApprovalOutcome,
        rationale: str,
    ) -> AlertApprovalTransitionReport:
        path = self.instance.root / "data" / "alert-decisions" / yyyymmdd / f"{alert_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"alert decision not found: {path}")
        decision = AlertDecisionRecord.model_validate_json(path.read_text(encoding="utf-8"))
        if decision.approval_status != "requested" or decision.status != "needs_approval":
            raise ValueError(
                "approval transition requires approval_status='requested' and status='needs_approval'"
            )
        previous_approval_status = decision.approval_status
        previous_status = decision.status
        if outcome == "approved":
            updated = decision.model_copy(
                update={
                    "approval_status": "approved",
                    "status": "pending",
                    "action_taken": "none",
                    "follow_up": _append_note(decision.follow_up, f"approval approved by {self.reviewer_id}: {rationale}"),
                }
            )
        else:
            updated = decision.model_copy(
                update={
                    "approval_status": "rejected",
                    "status": "closed",
                    "action_taken": "none",
                    "outcome_feedback": _append_note(
                        decision.outcome_feedback,
                        f"approval rejected by {self.reviewer_id}: {rationale}",
                    ),
                }
            )
        path.write_text(_to_json(updated), encoding="utf-8")
        markdown_path = path.with_suffix(".md")
        markdown_path.write_text(_decision_to_markdown(updated), encoding="utf-8")
        report = AlertApprovalTransitionReport(
            alert_decision_ref=alert_id,
            previous_approval_status=previous_approval_status,
            new_approval_status=updated.approval_status,
            previous_status=previous_status,
            new_status=updated.status,
            action_taken=updated.action_taken,
            reviewer_id=self.reviewer_id,
            rationale=rationale,
        )
        self._write_report(report, yyyymmdd)
        return report

    def _write_report(self, report: AlertApprovalTransitionReport, yyyymmdd: str) -> Path:
        directory = self.instance.root / "reports" / "run-summaries" / yyyymmdd
        directory.mkdir(parents=True, exist_ok=True)
        json_path = directory / "alert-approval-transition-report.json"
        json_path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        markdown_path = directory / "alert-approval-transition-report.md"
        markdown_path.write_text(_report_to_markdown(report), encoding="utf-8")
        return json_path


def _append_note(existing: str | None, note: str) -> str:
    if existing:
        return f"{existing}\n{note}"
    return note


def _to_json(record: BaseModel) -> str:
    return json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True)


def _decision_to_markdown(decision: AlertDecisionRecord) -> str:
    return "\n".join(
        [
            "# Hisys Alert Decision",
            "",
            f"- alert_id: `{decision.alert_id}`",
            f"- trigger_reason: `{decision.trigger_reason}`",
            f"- severity: `{decision.severity}`",
            f"- status: `{decision.status}`",
            f"- action_taken: `{decision.action_taken}`",
            f"- approval_status: `{decision.approval_status}`",
            "",
            f"Follow-up: {decision.follow_up or 'none'}",
            f"Outcome feedback: {decision.outcome_feedback or 'none'}",
            "",
        ]
    )


def _report_to_markdown(report: AlertApprovalTransitionReport) -> str:
    return "\n".join(
        [
            "# Hisys Alert Approval Transition Report",
            "",
            f"- alert_decision_ref: `{report.alert_decision_ref}`",
            f"- previous: `{report.previous_approval_status}/{report.previous_status}`",
            f"- new: `{report.new_approval_status}/{report.new_status}`",
            f"- action_taken: `{report.action_taken}`",
            f"- reviewer_id: `{report.reviewer_id}`",
            f"- rationale: {report.rationale}",
            "",
            "## Policy References",
            *[f"- {ref}" for ref in report.policy_refs],
            "",
        ]
    )


__all__ = ["AlertApprovalTransitionReport", "AlertApprovalTransitionRuntime"]
