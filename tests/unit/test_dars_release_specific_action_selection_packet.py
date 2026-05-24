"""DARS release specific-action selection packet checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "dars-release-specific-action-selection-packet-v0.0.100.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.100.md"
RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.100.md"
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"


def test_specific_action_selection_records_candidate_set_without_approval() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "task_id=DARS-LIVE-RELEASE-SPECIFIC-ACTION-SELECTION-PACKET" in text
    assert "accepted_claim=release_specific_action_candidate_set_recorded_for_human_review" in text
    assert "operator_instruction=다음" in text
    assert "selected_action_set=none" in text
    assert "specific_action_selection_approved=false" in text
    assert "release_action_authorized=false" in text
    assert "release_action_performed=false" in text


def test_specific_action_selection_keeps_all_candidate_actions_locked() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for flag in [
        "tag_creation_authorized=false",
        "package_upload_authorized=false",
        "deployment_authorized=false",
        "publication_authorized=false",
        "external_notification_authorized=false",
        "live_external_action_authorized=false",
        "live_model_call_authorized=false",
        "raw_provider_api_call_by_hisys=false",
        "credential_lookup_by_hisys=false",
        "standing_unattended_approval_activated=false",
        "human_review_removal_authorized=false",
        "requires_human_review=true",
    ]:
        assert flag in text


def test_specific_action_notes_record_and_traceability_advance_to_approval_gate() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")

    assert "Specific action candidate set recorded for human review" in notes
    assert "accepted_claim=release_specific_action_candidate_set_recorded_for_human_review" in record
    assert "specific_action_selection_approved: false" in record
    assert "next_safe_task=DARS-LIVE-RELEASE-SPECIFIC-ACTION-APPROVAL-GATE" in record
    assert "DARS-LIVE-RELEASE-SPECIFIC-ACTION-SELECTION-PACKET" in trace
    assert "`selected_action_set=none`" in trace
