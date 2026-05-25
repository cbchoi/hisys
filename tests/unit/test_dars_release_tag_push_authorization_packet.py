"""DARS tag-push authorization packet checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "dars-release-tag-push-authorization-packet-v0.0.105.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.105.md"
RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.105.md"
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"
TAG_NAME = "v0.0.103"
TAG_TARGET = "ea26df6"


def test_tag_push_packet_authorizes_only_remote_tag_push() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "task_id=DARS-LIVE-RELEASE-TAG-PUSH-AUTHORIZATION-PACKET" in text
    assert "accepted_claim=release_tag_pushed_to_origin_only" in text
    assert "operator_instruction=push" in text
    assert f"tag_name={TAG_NAME}" in text
    assert f"tag_target_commit={TAG_TARGET}" in text
    assert "tag_kind=annotated" in text
    assert "tag_creation_performed=true" in text
    assert "tag_push_authorized=true" in text
    assert "tag_push_performed=true" in text
    assert "tag_push_remote=origin" in text
    assert "tag_push_refspec=refs/tags/v0.0.103:refs/tags/v0.0.103" in text


def test_tag_push_packet_keeps_non_tag_actions_locked() -> None:
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
        "requires_human_review=true",
    ]:
        assert flag in text


def test_tag_push_notes_record_traceability_and_next_gate() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")

    assert "Remote tag `v0.0.103` pushed to `origin`" in notes
    assert "accepted_claim=release_tag_pushed_to_origin_only" in record
    assert "tag_push_authorized: true" in record
    assert "tag_push_performed: true" in record
    assert "package_upload_authorized: false" in record
    assert "deployment_authorized: false" in record
    assert "next_safe_task=DARS-LIVE-RELEASE-POST-TAG-PUSH-REVIEW-PACKET" in record
    assert "DARS-LIVE-RELEASE-TAG-PUSH-AUTHORIZATION-PACKET — remote tag pushed" in trace
    assert "`tag_push_performed=true`" in trace
