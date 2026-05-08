"""I7 Chief Editor runtime tests.

Traceability: HISYS-FR-CE-001..006, HISYS-CE-POLICY-001,
HISYS-D-015, HISYS-T-014, HISYS-T-015, HISYS-T-016, HISYS-T-017,
HISYS-T-018, HISYS-T-019, HISYS-T-020, HISYS-T-021, HISYS-T-025.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.chief_editor import (
    AlertActionPlanRuntime,
    AlertApprovalTransitionRuntime,
    ChiefEditorPolicy,
    ChiefEditorRuntime,
    create_chief_editor_product,
)
from hisys.config import InstanceRoot
from hisys.editor import MemoReviewReport
from hisys.schemas import ZettelMemo


def test_chief_editor_product_factory_analysis_only_closes_decision_without_alert_target(tmp_path: Path):
    memo = _memo_for_decision(
        "MEM-CE-ANALYSIS-001",
        review_status="flagged_conflict",
        summary="temperature trend high but monitor only",
    )
    report = MemoReviewReport(
        reviewed_memo_refs=[memo.memo_id],
        conflict_memo_refs=[memo.memo_id],
    )
    product = create_chief_editor_product(
        product_type="analysis_only",
        instance=InstanceRoot(tmp_path),
        policy=ChiefEditorPolicy.fixture_default(),
        producer_id="chief-editor-analysis-test",
        conflict_severity="high",
        target_channel="discord:#ops",
    )

    decision_report = product.decide_run([memo], memo_review_report=report, yyyymmdd="20260508")

    assert len(decision_report.alert_decision_refs) == 1
    alert_id = decision_report.alert_decision_refs[0]
    decision = json.loads((tmp_path / "data" / "alert-decisions" / "20260508" / f"{alert_id}.json").read_text(encoding="utf-8"))
    assert decision["severity"] == "high"
    assert decision["target_channel"] is None
    assert decision["approval_status"] == "not_required"
    assert decision["status"] == "closed"
    assert decision["action_taken"] == "none"
    assert "analysis_only" in decision["follow_up"]

    action_plan_report = AlertActionPlanRuntime(
        instance=InstanceRoot(tmp_path),
        producer_id="alert-action-plan-test",
    ).plan_run(yyyymmdd="20260508")
    assert action_plan_report.action_plan_refs == [alert_id.replace("ALERT-", "PLAN-", 1)]
    plan = json.loads((tmp_path / "data" / "alert-action-plans" / "20260508" / f"{action_plan_report.action_plan_refs[0]}.json").read_text(encoding="utf-8"))
    assert plan["would_send"] is False
    assert plan["blocked_reason"] == "no_target_channel"
    assert plan["live_delivery_permitted"] is False



def test_chief_editor_runtime_creates_alert_decision_for_conflict_memo(tmp_path: Path):
    memo = _memo_for_decision(
        "MEM-CE-CONFLICT-001",
        review_status="flagged_conflict",
        summary="temperature trend high",
    )
    report = MemoReviewReport(
        reviewed_memo_refs=[memo.memo_id],
        conflict_memo_refs=[memo.memo_id],
    )
    runtime = ChiefEditorRuntime(
        instance=InstanceRoot(tmp_path),
        policy=ChiefEditorPolicy.fixture_default(),
        producer_id="chief-editor-test",
    )

    decision_report = runtime.decide_run([memo], memo_review_report=report, yyyymmdd="20260508")

    assert decision_report.reviewed_memo_refs == [memo.memo_id]
    assert len(decision_report.alert_decision_refs) == 1
    assert decision_report.suppressed_memo_refs == []
    alert_id = decision_report.alert_decision_refs[0]
    decision_path = tmp_path / "data" / "alert-decisions" / "20260508" / f"{alert_id}.json"
    markdown_path = tmp_path / "data" / "alert-decisions" / "20260508" / f"{alert_id}.md"
    assert decision_path.exists()
    assert markdown_path.exists()
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    assert decision["memo_refs"] == [memo.memo_id]
    assert decision["signal_refs"] == memo.signal_refs
    assert decision["policy_version"] == "HISYS-CE-POLICY-001.fixture-v0"
    assert decision["trigger_reason"] == "memo_conflict_detected"
    assert decision["severity"] == "medium"
    assert decision["approval_status"] == "not_required"
    assert decision["action_taken"] == "none"
    assert decision["status"] == "pending"
    assert decision["suppression_key"] == f"conflict:{memo.perspective_id}:{memo.signal_refs[0]}"
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# Hisys Alert Decision" in markdown
    assert memo.memo_id in markdown
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "alert-decision-report.json"
    assert report_path.exists()


def test_chief_editor_runtime_records_suppressed_decision_for_duplicate_memo(tmp_path: Path):
    memo = _memo_for_decision(
        "MEM-CE-DUP-001",
        review_status="flagged_duplicate",
        summary="temperature trend high",
    )
    report = MemoReviewReport(
        reviewed_memo_refs=[memo.memo_id],
        duplicate_memo_refs=[memo.memo_id],
    )
    runtime = ChiefEditorRuntime(
        instance=InstanceRoot(tmp_path),
        policy=ChiefEditorPolicy.fixture_default(),
        producer_id="chief-editor-test",
    )

    decision_report = runtime.decide_run([memo], memo_review_report=report, yyyymmdd="20260508")

    assert decision_report.alert_decision_refs == []
    assert decision_report.suppressed_memo_refs == [memo.memo_id]
    assert len(decision_report.non_escalation_decision_refs) == 1
    alert_id = decision_report.non_escalation_decision_refs[0]
    decision_path = tmp_path / "data" / "alert-decisions" / "20260508" / f"{alert_id}.json"
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    assert decision["trigger_reason"] == "duplicate_memo_suppressed"
    assert decision["severity"] == "low"
    assert decision["status"] == "suppressed"
    assert decision["action_taken"] == "none"


def test_chief_editor_runtime_suppresses_repeated_alert_by_suppression_key(tmp_path: Path):
    first_memo = _memo_for_decision(
        "MEM-CE-CONFLICT-001",
        review_status="flagged_conflict",
        summary="temperature trend high",
    )
    second_memo = _memo_for_decision(
        "MEM-CE-CONFLICT-002",
        review_status="flagged_conflict",
        summary="temperature trend high again",
    )
    runtime = ChiefEditorRuntime(
        instance=InstanceRoot(tmp_path),
        policy=ChiefEditorPolicy.fixture_default(),
        producer_id="chief-editor-test",
    )
    first_report = MemoReviewReport(
        reviewed_memo_refs=[first_memo.memo_id],
        conflict_memo_refs=[first_memo.memo_id],
    )
    second_report = MemoReviewReport(
        reviewed_memo_refs=[second_memo.memo_id],
        conflict_memo_refs=[second_memo.memo_id],
    )

    first_decision_report = runtime.decide_run(
        [first_memo], memo_review_report=first_report, yyyymmdd="20260508"
    )
    second_decision_report = runtime.decide_run(
        [second_memo], memo_review_report=second_report, yyyymmdd="20260508"
    )

    assert len(first_decision_report.alert_decision_refs) == 1
    assert second_decision_report.alert_decision_refs == []
    assert second_decision_report.suppressed_memo_refs == [second_memo.memo_id]
    assert len(second_decision_report.non_escalation_decision_refs) == 1
    alert_id = second_decision_report.non_escalation_decision_refs[0]
    decision_path = tmp_path / "data" / "alert-decisions" / "20260508" / f"{alert_id}.json"
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    assert decision["trigger_reason"] == "suppression_window_duplicate_alert"
    assert decision["status"] == "suppressed"
    assert decision["action_taken"] == "none"
    assert decision["suppression_key"] == f"conflict:{second_memo.perspective_id}:{second_memo.signal_refs[0]}"



def test_chief_editor_runtime_requests_approval_for_high_impact_alert(tmp_path: Path):
    memo = _memo_for_decision(
        "MEM-CE-HIGH-001",
        review_status="flagged_conflict",
        summary="critical temperature trend high",
    )
    report = MemoReviewReport(
        reviewed_memo_refs=[memo.memo_id],
        conflict_memo_refs=[memo.memo_id],
    )
    runtime = ChiefEditorRuntime(
        instance=InstanceRoot(tmp_path),
        policy=ChiefEditorPolicy(
            policy_version="HISYS-CE-POLICY-001.fixture-v0",
            conflict_severity="high",
            target_channel="discord:#ops",
        ),
        producer_id="chief-editor-test",
    )

    decision_report = runtime.decide_run([memo], memo_review_report=report, yyyymmdd="20260508")

    assert len(decision_report.alert_decision_refs) == 1
    alert_id = decision_report.alert_decision_refs[0]
    decision_path = tmp_path / "data" / "alert-decisions" / "20260508" / f"{alert_id}.json"
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    assert decision["severity"] == "high"
    assert decision["approval_status"] == "requested"
    assert decision["status"] == "needs_approval"
    assert decision["action_taken"] == "none"
    assert decision["target_channel"] == "discord:#ops"
    assert "approval" in decision["follow_up"].lower()



def test_alert_approval_transition_runtime_approves_requested_decision(tmp_path: Path):
    alert_id = _write_high_impact_approval_request(tmp_path)

    report = AlertApprovalTransitionRuntime(
        instance=InstanceRoot(tmp_path),
        reviewer_id="chief-editor-reviewer-test",
    ).transition(
        yyyymmdd="20260508",
        alert_id=alert_id,
        outcome="approved",
        rationale="fixture human approval granted",
    )

    assert report.alert_decision_ref == alert_id
    assert report.previous_approval_status == "requested"
    assert report.new_approval_status == "approved"
    assert report.previous_status == "needs_approval"
    assert report.new_status == "pending"
    assert report.action_taken == "none"
    decision_path = tmp_path / "data" / "alert-decisions" / "20260508" / f"{alert_id}.json"
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    assert decision["approval_status"] == "approved"
    assert decision["status"] == "pending"
    assert decision["action_taken"] == "none"
    assert "fixture human approval granted" in decision["follow_up"]
    assert (tmp_path / "data" / "alert-decisions" / "20260508" / f"{alert_id}.md").exists()
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "alert-approval-transition-report.json"
    report_json = json.loads(report_path.read_text(encoding="utf-8"))
    assert report_json["alert_decision_ref"] == alert_id
    assert report_json["new_approval_status"] == "approved"


def test_alert_approval_transition_runtime_rejects_requested_decision(tmp_path: Path):
    alert_id = _write_high_impact_approval_request(tmp_path)

    report = AlertApprovalTransitionRuntime(
        instance=InstanceRoot(tmp_path),
        reviewer_id="chief-editor-reviewer-test",
    ).transition(
        yyyymmdd="20260508",
        alert_id=alert_id,
        outcome="rejected",
        rationale="fixture human approval rejected",
    )

    assert report.alert_decision_ref == alert_id
    assert report.previous_approval_status == "requested"
    assert report.new_approval_status == "rejected"
    assert report.previous_status == "needs_approval"
    assert report.new_status == "closed"
    assert report.action_taken == "none"
    decision_path = tmp_path / "data" / "alert-decisions" / "20260508" / f"{alert_id}.json"
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    assert decision["approval_status"] == "rejected"
    assert decision["status"] == "closed"
    assert decision["action_taken"] == "none"
    assert "fixture human approval rejected" in decision["outcome_feedback"]



def test_alert_action_plan_runtime_writes_dry_run_plan_for_approval_request(tmp_path: Path):
    memo = _memo_for_decision(
        "MEM-CE-HIGH-PLAN-001",
        review_status="flagged_conflict",
        summary="critical temperature trend high",
    )
    review_report = MemoReviewReport(
        reviewed_memo_refs=[memo.memo_id],
        conflict_memo_refs=[memo.memo_id],
    )
    decision_runtime = ChiefEditorRuntime(
        instance=InstanceRoot(tmp_path),
        policy=ChiefEditorPolicy(
            policy_version="HISYS-CE-POLICY-001.fixture-v0",
            conflict_severity="high",
            target_channel="discord:#ops",
        ),
        producer_id="chief-editor-test",
    )
    decision_report = decision_runtime.decide_run([memo], memo_review_report=review_report, yyyymmdd="20260508")
    alert_id = decision_report.alert_decision_refs[0]

    plan_report = AlertActionPlanRuntime(
        instance=InstanceRoot(tmp_path),
        producer_id="action-plan-test",
    ).plan_run(yyyymmdd="20260508")

    assert plan_report.alert_decision_refs == [alert_id]
    assert plan_report.action_plan_refs == [f"PLAN-{alert_id[6:]}"]
    assert plan_report.would_send_refs == []
    assert plan_report.blocked_refs == [f"PLAN-{alert_id[6:]}"]
    plan_path = tmp_path / "data" / "alert-action-plans" / "20260508" / f"PLAN-{alert_id[6:]}.json"
    markdown_path = tmp_path / "data" / "alert-action-plans" / "20260508" / f"PLAN-{alert_id[6:]}.md"
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "alert-action-plan-report.json"
    assert plan_path.exists()
    assert markdown_path.exists()
    assert report_path.exists()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    assert plan["alert_decision_ref"] == alert_id
    assert plan["target_channel"] == "discord:#ops"
    assert plan["approval_required"] is True
    assert plan["would_send"] is False
    assert plan["blocked_reason"] == "approval_required"
    assert plan["live_delivery_permitted"] is False
    assert plan["action_taken"] == "none"
    assert "discord:#ops" in markdown_path.read_text(encoding="utf-8")



def test_alert_action_plan_runtime_marks_approved_decision_as_dry_run_send_candidate(tmp_path: Path):
    alert_id = _write_high_impact_approval_request(tmp_path)
    AlertApprovalTransitionRuntime(
        instance=InstanceRoot(tmp_path),
        reviewer_id="chief-editor-reviewer-test",
    ).transition(
        yyyymmdd="20260508",
        alert_id=alert_id,
        outcome="approved",
        rationale="fixture approval for send candidate",
    )

    plan_report = AlertActionPlanRuntime(
        instance=InstanceRoot(tmp_path),
        producer_id="action-plan-test",
    ).plan_run(yyyymmdd="20260508")

    plan_id = f"PLAN-{alert_id[6:]}"
    assert plan_report.alert_decision_refs == [alert_id]
    assert plan_report.action_plan_refs == [plan_id]
    assert plan_report.would_send_refs == [plan_id]
    assert plan_report.blocked_refs == [plan_id]
    plan_path = tmp_path / "data" / "alert-action-plans" / "20260508" / f"{plan_id}.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    assert plan["alert_decision_ref"] == alert_id
    assert plan["approval_required"] is False
    assert plan["would_send"] is True
    assert plan["blocked_reason"] == "live_delivery_disabled"
    assert plan["live_delivery_permitted"] is False
    assert plan["action_taken"] == "none"



def _write_high_impact_approval_request(tmp_path: Path) -> str:
    memo = _memo_for_decision(
        "MEM-CE-APPROVAL-001",
        review_status="flagged_conflict",
        summary="critical temperature trend high",
    )
    review_report = MemoReviewReport(
        reviewed_memo_refs=[memo.memo_id],
        conflict_memo_refs=[memo.memo_id],
    )
    decision_runtime = ChiefEditorRuntime(
        instance=InstanceRoot(tmp_path),
        policy=ChiefEditorPolicy(
            policy_version="HISYS-CE-POLICY-001.fixture-v0",
            conflict_severity="high",
            target_channel="discord:#ops",
        ),
        producer_id="chief-editor-test",
    )
    decision_report = decision_runtime.decide_run([memo], memo_review_report=review_report, yyyymmdd="20260508")
    return decision_report.alert_decision_refs[0]



def _memo_for_decision(memo_id: str, *, review_status: str, summary: str) -> ZettelMemo:
    return ZettelMemo(
        memo_id=memo_id,
        title=summary.title(),
        summary=summary,
        body=f"# Fixture memo\n\n{summary}\n",
        source_refs=["SRC-HW-MOCK-001"],
        signal_refs=["SIG-CE-001"],
        perspective_id="PERSP-OPS-001",
        confidence=0.82,
        tags=["hisys", "zettel-draft"],
        links=["OBS-CE-001"],
        revision="1",
        review_status=review_status,
        status=review_status,
        producer_id="chief-editor-test",
    )
