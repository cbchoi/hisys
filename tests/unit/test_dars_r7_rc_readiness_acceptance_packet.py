"""DARS R7 RC readiness acceptance packet checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "dars-r7-rc-readiness-acceptance-packet-v0.0.96.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.96.md"
CHECKLIST = ROOT / "docs" / "release" / "dars-panel-release-candidate-checklist.md"
READINESS_RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.96.md"
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"


def test_rc_readiness_acceptance_sets_only_human_reviewed_rc_claim() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "task_id=DARS-LIVE-RELEASE-R7-RC-READINESS-ACCEPTANCE-PACKET" in text
    assert "accepted_claim=r7_rc_ready_for_human_review_controlled_scope" in text
    assert "operator_approval_utterance=승인" in text
    assert "approval_context=after_rc_readiness_acceptance_packet_boundary" in text
    assert "release_candidate_ready=true" in text
    assert "human_release_approval_recorded=true" in text
    assert "requires_human_review=true" in text


def test_rc_acceptance_keeps_release_execution_and_live_boundaries_locked() -> None:
    text = PACKET.read_text(encoding="utf-8")

    required_false_flags = [
        "released_for_controlled_advisory_use=false",
        "release_execution_authorized=false",
        "release_action_authorized=false",
        "live_external_action_authorized=false",
        "live_model_call_authorized=false",
        "bounded_unattended_advisory_operation_ready=false",
        "r5_live_canary_executed=false",
        "live_provider_model_call_made=false",
        "raw_provider_api_call_by_hisys=false",
        "credential_lookup_by_hisys=false",
        "adapter_native_real_provider_transport_ready=false",
        "standing_unattended_approval_activated=false",
        "r4c_codex_subprocess_completion_required_for_this_release=false",
    ]
    for flag in required_false_flags:
        assert flag in text


def test_checklist_notes_and_readiness_record_advance_after_rc_acceptance() -> None:
    checklist = CHECKLIST.read_text(encoding="utf-8")
    notes = NOTES.read_text(encoding="utf-8")
    record = READINESS_RECORD.read_text(encoding="utf-8")

    assert "R7 RC readiness acceptance packet records `release_candidate_ready=true`" in checklist
    assert "human release approval is recorded for RC readiness only" in checklist
    assert "RC readiness accepted for human-reviewed controlled scope" in notes
    assert "accepted_claim=r7_rc_ready_for_human_review_controlled_scope" in record
    assert "release_candidate_ready: true" in record
    assert "release_execution_authorized: false" in record
    assert "next_safe_task=DARS-LIVE-RELEASE-CONTROLLED-ADVISORY-USE-DECISION-PACKET" in record


def test_traceability_records_rc_acceptance_without_release_execution() -> None:
    text = TRACEABILITY.read_text(encoding="utf-8")

    assert "DARS-LIVE-RELEASE-R7-RC-READINESS-ACCEPTANCE-PACKET" in text
    assert "accepted claim is `r7_rc_ready_for_human_review_controlled_scope`" in text
    assert "`release_candidate_ready=true`" in text
    assert "`release_execution_authorized=false`" in text
    assert "`released_for_controlled_advisory_use=false`" in text
