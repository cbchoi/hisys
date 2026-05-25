"""DARS tag-creation selected-action approval checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "dars-release-tag-creation-selection-approval-v0.0.103.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.103.md"
RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.103.md"
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"


def test_tag_creation_selection_approval_records_selected_set_without_execution() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "task_id=DARS-LIVE-RELEASE-SPECIFIC-ACTION-EXACT-APPROVAL" in text
    assert "accepted_claim=release_specific_action_tag_creation_selected_for_human_review" in text
    assert "operator_instruction=tag creation" in text
    assert "selected_action_set=tag_creation_only" in text
    assert "specific_action_selection_approved=true" in text
    assert "exact_human_approval_provided=true" in text
    assert "tag_creation_selected=true" in text
    assert "tag_creation_authorized=false" in text
    assert "tag_creation_performed=false" in text


def test_tag_creation_selection_approval_keeps_other_actions_locked() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for flag in [
        "release_action_authorized=false",
        "release_action_performed=false",
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
        "mutation_performed=false",
        "publication_performed=false",
        "external_action_performed=false",
        "requires_human_review=true",
    ]:
        assert flag in text


def test_tag_creation_selection_approval_states_execution_is_separate() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "This approval selects only the tag creation action set" in text
    assert "It does not create a tag" in text
    assert "concrete tag creation remains a separate execution decision and action step" in text


def test_tag_creation_selection_notes_record_and_traceability_advance_to_execution_decision() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")

    assert "Tag creation action set selected for human review; tag not created" in notes
    assert "accepted_claim=release_specific_action_tag_creation_selected_for_human_review" in record
    assert "selected_action_set: tag_creation_only" in record
    assert "specific_action_selection_approved: true" in record
    assert "tag_creation_authorized: false" in record
    assert "tag_creation_performed: false" in record
    assert "next_safe_task=DARS-LIVE-RELEASE-TAG-CREATION-EXECUTION-DECISION-PACKET" in record
    assert "DARS-LIVE-RELEASE-SPECIFIC-ACTION-EXACT-APPROVAL — tag creation selected" in trace
    assert "`tag_creation_performed=false`" in trace
