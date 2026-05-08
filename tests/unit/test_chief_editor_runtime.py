"""I7 Chief Editor runtime tests.

Traceability: HISYS-FR-CE-001..006, HISYS-CE-POLICY-001,
HISYS-D-015, HISYS-T-014, HISYS-T-015, HISYS-T-016.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.chief_editor import ChiefEditorPolicy, ChiefEditorRuntime
from hisys.config import InstanceRoot
from hisys.editor import MemoReviewReport
from hisys.schemas import ZettelMemo


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
