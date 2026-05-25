"""DARS post-tag-push review packet checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "dars-release-post-tag-push-review-packet-v0.0.106.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.106.md"
RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.106.md"
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"


def test_post_tag_push_review_records_remote_tag_evidence_without_new_action() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "task_id=DARS-LIVE-RELEASE-POST-TAG-PUSH-REVIEW-PACKET" in text
    assert "accepted_claim=release_tag_push_reviewed_for_human_review_no_additional_action" in text
    assert "operator_instruction=go" in text
    assert "tag_name=v0.0.103" in text
    assert "tag_target_commit=ea26df6" in text
    assert "remote_tag_ref=refs/tags/v0.0.103" in text
    assert "remote_tag_object=1b94bf8da8d9fdd43201ee05b44558d2c9787789" in text
    assert "remote_tag_peeled_commit=ea26df63f8705faf178b0860ff9f17090ba0b8c3" in text
    assert "tag_push_reviewed=true" in text
    assert "additional_release_action_authorized=false" in text
    assert "additional_release_action_performed=false" in text


def test_post_tag_push_review_keeps_release_actions_locked() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for flag in [
        "package_upload_authorized=false",
        "package_upload_performed=false",
        "deployment_authorized=false",
        "deployment_performed=false",
        "publication_authorized=false",
        "publication_performed=false",
        "external_notification_authorized=false",
        "external_notification_performed=false",
        "live_external_action_authorized=false",
        "live_model_call_authorized=false",
        "raw_provider_api_call_by_hisys=false",
        "credential_lookup_by_hisys=false",
        "standing_unattended_approval_activated=false",
        "human_review_removal_authorized=false",
        "force_push_authorized=false",
        "branch_rewrite_authorized=false",
        "requires_human_review=true",
    ]:
        assert flag in text


def test_post_tag_push_review_notes_record_traceability_and_next_gate() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")

    assert "Post-tag-push review recorded for `v0.0.103`" in notes
    assert "accepted_claim=release_tag_push_reviewed_for_human_review_no_additional_action" in record
    assert "tag_push_reviewed: true" in record
    assert "additional_release_action_authorized: false" in record
    assert "package_upload_authorized: false" in record
    assert "deployment_authorized: false" in record
    assert "next_safe_task=DARS-LIVE-RELEASE-PACKAGE-UPLOAD-AUTHORIZATION-PACKET" in record
    assert "DARS-LIVE-RELEASE-POST-TAG-PUSH-REVIEW-PACKET — tag push reviewed" in trace
    assert "`additional_release_action_performed=false`" in trace
