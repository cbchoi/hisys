"""DARS package-upload authorization-packet preflight checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = (
    ROOT
    / "docs"
    / "release"
    / "dars-release-package-upload-authorization-preflight-v0.0.107.md"
)
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.107.md"
RECORD = (
    ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.107.md"
)
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"


def test_package_upload_preflight_records_gate_state_without_approval() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "task_id=DARS-LIVE-RELEASE-PACKAGE-UPLOAD-AUTHORIZATION-PACKET-PREFLIGHT" in text
    assert (
        "accepted_claim=release_package_upload_authorization_packet_preflight_recorded_for_human_review"
        in text
    )
    assert "selected_action_set=tag_creation_only" in text
    assert "package_upload_in_selected_action_set=false" in text
    assert "package_upload_authorization_packet_approved=false" in text
    assert "package_upload_authorization_packet_preflight_recorded=true" in text
    assert "operator_instruction_for_package_upload_received=false" in text


def test_package_upload_preflight_keeps_release_actions_locked() -> None:
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


def test_package_upload_preflight_lists_exact_approval_templates() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "APPROVE-PACKAGE-UPLOAD-SCOPE-EXPANSION-v0.0.107" in text
    assert "APPROVE-PACKAGE-UPLOAD-AUTHORIZATION-PACKET-v0.0.107" in text


def test_package_upload_preflight_notes_record_traceability_and_next_gate() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")

    assert "Package-upload authorization-packet preflight recorded" in notes
    assert (
        "accepted_claim=release_package_upload_authorization_packet_preflight_recorded_for_human_review"
        in record
    )
    assert "package_upload_authorization_packet_preflight_recorded: true" in record
    assert "package_upload_authorization_packet_approved: false" in record
    assert "package_upload_in_selected_action_set: false" in record
    assert (
        "next_safe_task=DARS-LIVE-RELEASE-PACKAGE-UPLOAD-AUTHORIZATION-PACKET-EXACT-APPROVAL-GATE"
        in record
    )
    assert (
        "DARS-LIVE-RELEASE-PACKAGE-UPLOAD-AUTHORIZATION-PACKET-PREFLIGHT — preflight recorded"
        in trace
    )
    assert "`package_upload_authorization_packet_approved=false`" in trace
