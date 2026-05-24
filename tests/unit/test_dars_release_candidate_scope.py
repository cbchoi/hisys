"""DARS release-candidate scope decision document checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCOPE_DECISION = ROOT / "docs" / "release" / "dars-panel-rc-scope-decision-v0.0.84.md"
CHECKLIST = ROOT / "docs" / "release" / "dars-panel-release-candidate-checklist.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.84.md"
READINESS_RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.84.md"


def test_rc_scope_decision_preserves_claim_ladder_and_blocks_release_actions() -> None:
    text = SCOPE_DECISION.read_text(encoding="utf-8")

    assert "accepted_claim=r7_rc_scope_decision_recorded_for_human_review" in text
    assert "release_candidate_ready=false" in text
    assert "released_for_controlled_advisory_use=false" in text
    assert "bounded_unattended_advisory_operation_ready=false" in text
    assert "r5_action_canary_evidence=missing" in text
    assert "r4c_codex_subprocess_completion=deferred" in text
    assert "raw_provider_api_readiness=false" in text
    assert "adapter_native_readiness=false" in text
    assert "requires_human_review=true" in text
    assert "no release tag, package upload, deployment, publication, or external notification" in text


def test_release_candidate_checklist_requires_prior_live_unattended_and_rollback_evidence() -> None:
    text = CHECKLIST.read_text(encoding="utf-8")

    required_items = [
        "R3 reviewed single-smoke evidence",
        "R4 reviewed multi-critic evidence or accepted scoped substitute",
        "R5 bounded unattended live canary evidence",
        "R6 live operations status report",
        "rollback runbook",
        "full unit gate",
        "traceability validator",
        "secret scan",
        "residual risk acceptance",
        "human release approval",
    ]
    for item in required_items:
        assert item in text

    assert "release_candidate_ready remains false until every required evidence row is accepted" in text
    assert "R4H is a scoped human-review advisory substitute, not R4C Codex subprocess completion" in text


def test_release_notes_and_readiness_record_are_scope_only() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = READINESS_RECORD.read_text(encoding="utf-8")

    assert "Scope decision only" in notes
    assert "No release artifact is produced by this note" in notes
    assert "accepted_claim=r7_rc_scope_decision_recorded_for_human_review" in record
    assert "next_safe_task=DARS-LIVE-RELEASE-R7-RC-PACKET-PREP" in record
    assert "live_model_call_authorized=false" in record
    assert "live_external_action_authorized=false" in record
    assert "release_action_authorized=false" in record
