"""I6 editorial runtime tests.

Traceability: HISYS-FR-PER-001..004, HISYS-FR-MEM-001..005,
HISYS-DATA-002, HISYS-T-011, HISYS-T-012, HISYS-T-013.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.config import InstanceRoot
from hisys.editor import EditorialRuntime, FixtureMemoDrafter, MemoReviewRuntime
from hisys.schemas import ExtractedSignal, PerspectiveProfile, RawObservation, ZettelMemo


def test_fixture_memo_drafter_creates_atomic_draft_with_signal_and_source_refs(
    hardware_adapter,
):
    result = hardware_adapter.collect()
    observation = hardware_adapter.to_observation(result, producer_id="editor-test")
    signal = ExtractedSignal(
        signal_id="SIG-EDITOR-001",
        observation_refs=[observation.observation_id],
        signal_type="anomaly",
        claim_or_event="hardware_sensor reported over_threshold anomaly",
        entities=[observation.source_id],
        confidence=0.82,
        uncertainty="bounded_by_fixture_rules",
        contradictions=[],
        extraction_method="fixture-rule-v0",
        producer_id="editor-test",
        status="proposed",
    )
    perspective = PerspectiveProfile(
        perspective_id="PERSP-OPS-001",
        title="Operations perspective",
        owner="hisys-fixture",
        lifecycle_state="active",
        intent="Surface operational anomalies for review.",
        focus_areas=["thermal anomalies"],
        producer_id="editor-test",
        status="active",
    )
    drafter = FixtureMemoDrafter(template_id="fixture-zettel-v0")

    memo = drafter.draft(signal, perspective=perspective, observations=[observation])

    assert memo.review_status == "draft"
    assert memo.status == "draft"
    assert memo.signal_refs == [signal.signal_id]
    assert memo.source_refs == [observation.source_id]
    assert memo.perspective_id == perspective.perspective_id
    assert memo.confidence == signal.confidence
    assert "# Operations perspective" in memo.body
    assert signal.signal_id in memo.body
    assert observation.observation_id in memo.body
    assert "temperature_c" not in memo.body
    assert "hisys" in memo.tags
    assert "perspective:PERSP-OPS-001" in memo.tags


def test_editorial_runtime_persists_memo_json_and_markdown_under_instance_root(
    tmp_path: Path,
    hardware_adapter,
):
    result = hardware_adapter.collect()
    observation = hardware_adapter.to_observation(result, producer_id="editor-test")
    signal = ExtractedSignal(
        signal_id="SIG-EDITOR-002",
        observation_refs=[observation.observation_id],
        signal_type="anomaly",
        claim_or_event="hardware_sensor reported over_threshold anomaly",
        entities=[observation.source_id],
        confidence=0.77,
        uncertainty="bounded_by_fixture_rules",
        contradictions=[],
        extraction_method="fixture-rule-v0",
        producer_id="editor-test",
        status="proposed",
    )
    runtime = EditorialRuntime(
        instance=InstanceRoot(tmp_path),
        drafter=FixtureMemoDrafter(template_id="fixture-zettel-v0"),
        producer_id="editor-runtime-test",
    )

    report = runtime.draft_run(
        [signal],
        observations=[observation],
        perspective=_active_perspective(),
        yyyymmdd="20260508",
    )

    assert report.requested_signal_refs == [signal.signal_id]
    assert len(report.draft_memo_refs) == 1
    memo_id = report.draft_memo_refs[0]
    json_path = tmp_path / "data" / "memo-drafts" / "20260508" / f"{memo_id}.json"
    markdown_path = tmp_path / "data" / "memo-drafts" / "20260508" / f"{memo_id}.md"
    assert json_path.exists()
    assert markdown_path.exists()
    memo_json = json.loads(json_path.read_text(encoding="utf-8"))
    assert memo_json["signal_refs"] == [signal.signal_id]
    assert memo_json["source_refs"] == [observation.source_id]
    markdown = markdown_path.read_text(encoding="utf-8")
    assert f"memo_id: {memo_id}" in markdown
    assert "signal_refs:" in markdown
    assert signal.signal_id in markdown
    assert "temperature_c" not in markdown
    assert report.policy_refs == ["HISYS-FR-MEM-001", "HISYS-DATA-002"]


def test_editorial_runtime_rejects_retired_perspective(tmp_path: Path):
    runtime = EditorialRuntime(
        instance=InstanceRoot(tmp_path),
        drafter=FixtureMemoDrafter(template_id="fixture-zettel-v0"),
        producer_id="editor-runtime-test",
    )
    retired = _active_perspective().model_copy(update={"lifecycle_state": "retired", "status": "retired"})

    report = runtime.draft_run([], observations=[], perspective=retired, yyyymmdd="20260508")

    assert report.draft_memo_refs == []
    assert report.skipped_signal_refs == []
    assert report.policy_refs == ["HISYS-FR-MEM-001", "HISYS-DATA-002"]
    assert report.perspective_state == "retired"


def test_memo_review_runtime_flags_duplicate_drafts_and_persists_report(
    tmp_path: Path,
    hardware_adapter,
):
    result = hardware_adapter.collect()
    observation = hardware_adapter.to_observation(result, producer_id="editor-test")
    signal = ExtractedSignal(
        signal_id="SIG-EDITOR-DUP-001",
        observation_refs=[observation.observation_id],
        signal_type="anomaly",
        claim_or_event="hardware_sensor reported over_threshold anomaly",
        entities=[observation.source_id],
        confidence=0.77,
        uncertainty="bounded_by_fixture_rules",
        contradictions=[],
        extraction_method="fixture-rule-v0",
        producer_id="editor-test",
        status="proposed",
    )
    drafter = FixtureMemoDrafter(template_id="fixture-zettel-v0")
    memo_a = drafter.draft(signal, perspective=_active_perspective(), observations=[observation])
    memo_b = drafter.draft(signal, perspective=_active_perspective(), observations=[observation])
    runtime = MemoReviewRuntime(instance=InstanceRoot(tmp_path), producer_id="memo-review-test")

    report = runtime.review_run([memo_a, memo_b], yyyymmdd="20260508")

    assert sorted(report.reviewed_memo_refs) == sorted([memo_a.memo_id, memo_b.memo_id])
    assert sorted(report.duplicate_memo_refs) == sorted([memo_a.memo_id, memo_b.memo_id])
    assert report.conflict_memo_refs == []
    assert report.policy_refs == ["HISYS-FR-MEM-004", "HISYS-T-013"]
    report_path = tmp_path / "reports" / "run-summaries" / "20260508" / "memo-review-report.json"
    assert report_path.exists()
    report_json = json.loads(report_path.read_text(encoding="utf-8"))
    assert sorted(report_json["duplicate_memo_refs"]) == sorted([memo_a.memo_id, memo_b.memo_id])
    for memo_id in [memo_a.memo_id, memo_b.memo_id]:
        memo_path = tmp_path / "data" / "memo-drafts" / "20260508" / f"{memo_id}.json"
        memo_json = json.loads(memo_path.read_text(encoding="utf-8"))
        assert memo_json["review_status"] == "flagged_duplicate"
        assert memo_json["status"] == "flagged_duplicate"


def test_memo_review_runtime_flags_conflict_drafts(tmp_path: Path):
    base = _memo_for_review("MEM-CONFLICT-A", summary="temperature trend high", body="temperature trend high")
    conflicting = _memo_for_review("MEM-CONFLICT-B", summary="temperature trend normal", body="temperature trend normal")
    runtime = MemoReviewRuntime(instance=InstanceRoot(tmp_path), producer_id="memo-review-test")

    report = runtime.review_run([base, conflicting], yyyymmdd="20260508")

    assert sorted(report.conflict_memo_refs) == ["MEM-CONFLICT-A", "MEM-CONFLICT-B"]
    assert report.duplicate_memo_refs == []
    for memo_id in report.conflict_memo_refs:
        memo_path = tmp_path / "data" / "memo-drafts" / "20260508" / f"{memo_id}.json"
        memo_json = json.loads(memo_path.read_text(encoding="utf-8"))
        assert memo_json["review_status"] == "flagged_conflict"
        assert memo_json["status"] == "flagged_conflict"

def _active_perspective() -> PerspectiveProfile:
    return PerspectiveProfile(
        perspective_id="PERSP-OPS-001",
        title="Operations perspective",
        owner="hisys-fixture",
        lifecycle_state="active",
        intent="Surface operational anomalies for review.",
        focus_areas=["thermal anomalies"],
        producer_id="editor-test",
        status="active",
    )


def _memo_for_review(memo_id: str, *, summary: str, body: str) -> ZettelMemo:
    return ZettelMemo(
        memo_id=memo_id,
        title=summary.title(),
        summary=summary,
        body=body,
        source_refs=["SRC-HW-MOCK-001"],
        signal_refs=["SIG-EDITOR-REVIEW-001"],
        perspective_id="PERSP-OPS-001",
        confidence=0.75,
        tags=["hisys", "zettel-draft"],
        links=["OBS-EDITOR-REVIEW-001"],
        revision="1",
        review_status="draft",
        status="draft",
        producer_id="editor-test",
    )
