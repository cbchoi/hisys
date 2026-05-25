"""DARS release specific-action exact approval missing checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "dars-release-specific-action-exact-approval-missing-v0.0.102.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.102.md"
RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.102.md"
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"


def test_generic_go_records_exact_approval_missing_without_selection() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "task_id=DARS-LIVE-RELEASE-SPECIFIC-ACTION-EXACT-APPROVAL" in text
    assert "accepted_claim=release_specific_action_exact_approval_missing" in text
    assert "operator_instruction=go" in text
    assert "selected_action_set=none" in text
    assert "specific_action_selection_approved=false" in text
    assert "exact_human_approval_required=true" in text
    assert "exact_human_approval_provided=false" in text
    assert "release_action_authorized=false" in text
    assert "release_action_performed=false" in text


def test_exact_approval_missing_lists_required_approval_texts_again() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for item in [
        "APPROVE-DARS-RELEASE-ACTION-SET-TAG-CREATION-ONLY-v0.0.101",
        "APPROVE-DARS-RELEASE-ACTION-SET-PACKAGE-UPLOAD-ONLY-v0.0.101",
        "APPROVE-DARS-RELEASE-ACTION-SET-DEPLOYMENT-ONLY-v0.0.101",
        "APPROVE-DARS-RELEASE-ACTION-SET-PUBLICATION-ONLY-v0.0.101",
        "APPROVE-DARS-RELEASE-ACTION-SET-EXTERNAL-NOTIFICATION-ONLY-v0.0.101",
        "generic `go` is not an explicitly scoped equivalent approval",
    ]:
        assert item in text


def test_exact_approval_missing_keeps_all_release_actions_locked() -> None:
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
        "mutation_performed=false",
        "publication_performed=false",
        "external_action_performed=false",
        "requires_human_review=true",
    ]:
        assert flag in text


def test_exact_approval_missing_notes_record_and_traceability_keep_same_next_gate() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")

    assert "Generic go did not provide exact selected-action approval" in notes
    assert "accepted_claim=release_specific_action_exact_approval_missing" in record
    assert "exact_human_approval_provided: false" in record
    assert "selected_action_set: none" in record
    assert "specific_action_selection_approved: false" in record
    assert "next_safe_task=DARS-LIVE-RELEASE-SPECIFIC-ACTION-EXACT-APPROVAL" in record
    assert "DARS-LIVE-RELEASE-SPECIFIC-ACTION-EXACT-APPROVAL — exact approval missing" in trace
    assert "`exact_human_approval_provided=false`" in trace
