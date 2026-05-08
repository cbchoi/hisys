"""Chief Editor product factory.

Traceability: HISYS-FR-CE-001..006, HISYS-CE-POLICY-001,
HISYS-D-015, HISYS-T-025.
"""

from __future__ import annotations

from typing import Literal, Protocol

from ..config import InstanceRoot
from ..editor import MemoReviewReport
from ..schemas import AlertDecisionRecord, ZettelMemo
from .policy import ChiefEditorPolicy
from .runtime import AlertDecisionRunReport, ChiefEditorRuntime

ChiefEditorProductType = Literal["analysis_only", "alert_delivery_dry_run"]


class ChiefEditorProduct(Protocol):
    product_type: ChiefEditorProductType

    def decide_run(
        self,
        memos: list[ZettelMemo],
        *,
        memo_review_report: MemoReviewReport,
        yyyymmdd: str,
    ) -> AlertDecisionRunReport:
        ...


class AlertDeliveryDryRunProduct:
    """Default product: produce alert decisions that may become dry-run send candidates."""

    product_type: ChiefEditorProductType = "alert_delivery_dry_run"

    def __init__(self, runtime: ChiefEditorRuntime) -> None:
        self._runtime = runtime

    def decide_run(
        self,
        memos: list[ZettelMemo],
        *,
        memo_review_report: MemoReviewReport,
        yyyymmdd: str,
    ) -> AlertDecisionRunReport:
        return self._runtime.decide_run(memos, memo_review_report=memo_review_report, yyyymmdd=yyyymmdd)


class AnalysisOnlyProduct:
    """Product variant that records Chief Editor judgment without alert delivery intent."""

    product_type: ChiefEditorProductType = "analysis_only"

    def __init__(self, runtime: ChiefEditorRuntime) -> None:
        self._runtime = runtime

    def decide_run(
        self,
        memos: list[ZettelMemo],
        *,
        memo_review_report: MemoReviewReport,
        yyyymmdd: str,
    ) -> AlertDecisionRunReport:
        report = self._runtime.decide_run(memos, memo_review_report=memo_review_report, yyyymmdd=yyyymmdd)
        for alert_id in report.alert_decision_refs:
            path = self._runtime.instance.root / "data" / "alert-decisions" / yyyymmdd / f"{alert_id}.json"
            decision = AlertDecisionRecord.model_validate_json(path.read_text(encoding="utf-8"))
            if decision.status == "suppressed":
                continue
            analysis_decision = decision.model_copy(
                update={
                    "approval_status": "not_required",
                    "target_channel": None,
                    "status": "closed",
                    "action_taken": "none",
                    "follow_up": (
                        "analysis_only product: Chief Editor judgment recorded; "
                        "no alert delivery candidate should be produced."
                    ),
                }
            )
            self._runtime._write_decision(analysis_decision, yyyymmdd)
        return report


def create_chief_editor_product(
    *,
    product_type: ChiefEditorProductType,
    instance: InstanceRoot,
    policy: ChiefEditorPolicy,
    producer_id: str,
    conflict_severity: str | None = None,
    target_channel: str | None = None,
) -> ChiefEditorProduct:
    policy = ChiefEditorPolicy(
        policy_version=policy.policy_version,
        conflict_severity=conflict_severity or policy.conflict_severity,
        duplicate_severity=policy.duplicate_severity,
        target_channel=target_channel or policy.target_channel,
    )
    runtime = ChiefEditorRuntime(instance=instance, policy=policy, producer_id=producer_id)
    if product_type == "analysis_only":
        return AnalysisOnlyProduct(runtime)
    if product_type == "alert_delivery_dry_run":
        return AlertDeliveryDryRunProduct(runtime)
    raise ValueError(f"unsupported Chief Editor product_type: {product_type}")


__all__ = [
    "AnalysisOnlyProduct",
    "AlertDeliveryDryRunProduct",
    "ChiefEditorProduct",
    "ChiefEditorProductType",
    "create_chief_editor_product",
]
