"""DARS package-upload authorization-packet approval record checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = (
    ROOT
    / "docs"
    / "release"
    / "dars-release-package-upload-authorization-packet-v0.0.108.md"
)
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.108.md"
RECORD = (
    ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.108.md"
)
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"
TRACEABILITY_README = ROOT / "docs" / "traceability" / "README.md"
RALPH = ROOT / "ralph.md"
PROFILE = ROOT / "docs" / "milestone-bootstrap" / "profile.yaml"


def test_package_upload_authorization_packet_records_exact_approvals() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "task_id=DARS-LIVE-RELEASE-PACKAGE-UPLOAD-AUTHORIZATION-PACKET" in text
    assert (
        "accepted_claim=release_package_upload_authorization_packet_approved_for_human_review"
        in text
    )
    assert "operator_approval_scope_expansion=APPROVE-PACKAGE-UPLOAD-SCOPE-EXPANSION-v0.0.107" in text
    assert (
        "operator_approval_authorization_packet=APPROVE-PACKAGE-UPLOAD-AUTHORIZATION-PACKET-v0.0.107"
        in text
    )
    assert "selected_action_set=tag_creation_and_package_upload" in text
    assert "package_upload_in_selected_action_set=true" in text
    assert "package_upload_authorization_packet_approved=true" in text
    assert "operator_instruction_for_package_upload_received=true" in text


def test_package_upload_authorization_packet_does_not_execute_upload_or_other_actions() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for flag in [
        "package_upload_execution_decision_packet_approved=false",
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


def test_package_upload_authorization_record_traceability_and_next_gate() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")
    trace_readme = TRACEABILITY_README.read_text(encoding="utf-8")
    ralph = RALPH.read_text(encoding="utf-8")

    assert "Package-upload authorization packet approved for human review" in notes
    assert (
        "accepted_claim=release_package_upload_authorization_packet_approved_for_human_review"
        in record
    )
    assert "package_upload_authorization_packet_approved: true" in record
    assert "package_upload_authorized: false" in record
    assert (
        "next_safe_task=DARS-LIVE-RELEASE-PACKAGE-UPLOAD-EXECUTION-DECISION-PACKET"
        in record
    )
    assert "DARS-LIVE-RELEASE-PACKAGE-UPLOAD-AUTHORIZATION-PACKET — authorization packet approved" in trace
    assert "DARS package-upload authorization packet" in trace_readme
    assert "DARS-LIVE-RELEASE-PACKAGE-UPLOAD-AUTHORIZATION-PACKET`" in ralph
