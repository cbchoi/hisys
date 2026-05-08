"""Chief Editor policy rules.

Traceability: HISYS-FR-CE-001..006, HISYS-CE-POLICY-001,
HISYS-T-014, HISYS-T-015, HISYS-T-016.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..schemas import AlertDecisionRecord, ZettelMemo


@dataclass(frozen=True)
class ChiefEditorPolicy:
    """Deterministic fixture policy for I7 Chief Editor decision tests."""

    policy_version: str
    conflict_severity: str = "medium"
    duplicate_severity: str = "low"
    target_channel: str = "runtime-local"

    @classmethod
    def fixture_default(cls) -> "ChiefEditorPolicy":
        return cls(policy_version="HISYS-CE-POLICY-001.fixture-v0")

    def decide(self, memo: ZettelMemo, *, producer_id: str) -> AlertDecisionRecord | None:
        if memo.review_status == "flagged_conflict":
            return AlertDecisionRecord(
                alert_id=_placeholder_alert_id(),
                memo_refs=[memo.memo_id],
                signal_refs=list(memo.signal_refs),
                policy_version=self.policy_version,
                trigger_reason="memo_conflict_detected",
                severity=self.conflict_severity,  # type: ignore[arg-type]
                confidence=memo.confidence,
                novelty="new_runtime_conflict",
                approval_status="not_required",
                target_channel=self.target_channel,
                action_taken="none",
                suppression_key=_suppression_key("conflict", memo),
                follow_up="Chief Editor review required before external escalation.",
                status="pending",
                producer_id=producer_id,
            )
        if memo.review_status == "flagged_duplicate":
            return AlertDecisionRecord(
                alert_id=_placeholder_alert_id(),
                memo_refs=[memo.memo_id],
                signal_refs=list(memo.signal_refs),
                policy_version=self.policy_version,
                trigger_reason="duplicate_memo_suppressed",
                severity=self.duplicate_severity,  # type: ignore[arg-type]
                confidence=memo.confidence,
                novelty="duplicate_runtime_memo",
                approval_status="not_required",
                target_channel=None,
                action_taken="none",
                suppression_key=_suppression_key("duplicate", memo),
                follow_up="No external alert; preserve decision record for audit.",
                status="suppressed",
                producer_id=producer_id,
            )
        return None


def _suppression_key(kind: str, memo: ZettelMemo) -> str:
    signal_ref = memo.signal_refs[0] if memo.signal_refs else "no-signal"
    return f"{kind}:{memo.perspective_id}:{signal_ref}"


def _placeholder_alert_id() -> str:
    # ChiefEditorRuntime replaces this with a stable generated ALERT-* id before persistence.
    return "ALERT-PLACEHOLDER"


__all__ = ["ChiefEditorPolicy"]
