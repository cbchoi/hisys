"""DARS local artifact/release-scope review approval checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "dars-release-local-artifact-scope-review-approval-v0.0.118.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.118.md"
RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.118.md"
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"
CHECKLIST = ROOT / "docs" / "release" / "dars-panel-release-candidate-checklist.md"
PROFILE = ROOT / "docs" / "milestone-bootstrap" / "profile.yaml"
RALPH = ROOT / "ralph.md"


def test_local_artifact_scope_review_approval_is_recorded_without_external_authority() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "task_id=DARS-LIVE-RELEASE-LOCAL-ARTIFACT-RELEASE-SCOPE-REVIEW" in text
    assert "accepted_claim=local_artifact_release_scope_review_approved" in text
    assert "operator_approval=APPROVE-LOCAL-ARTIFACT-RELEASE-SCOPE-REVIEW-v0.0.117" in text
    assert "local_artifact_review_scope_approved=true" in text
    assert "repository_record_review_scope_approved=true" in text
    assert "single_operator_dars_panel_scope=true" in text


def test_local_artifact_scope_review_keeps_package_registry_and_external_boundaries_closed() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for flag in [
        "package_upload_scope_retired=true",
        "upload_command_scope_retired=true",
        "package_registry_interaction_scope_retired=true",
        "credential_lookup_by_hisys=false",
        "live_external_action_authorized=false",
        "live_model_call_authorized=false",
        "raw_provider_api_call_by_hisys=false",
        "deployment_authorized=false",
        "publication_authorized=false",
        "external_notification_authorized=false",
        "standing_unattended_approval_activated=false",
        "force_push_authorized=false",
        "branch_rewrite_authorized=false",
        "requires_human_review=true",
    ]:
        assert flag in text


def test_local_artifact_review_scope_names_allowed_and_forbidden_outputs() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "Allowed local-only review outputs" in text
    assert "release-scope inventory" in text
    assert "repository record recommendation" in text
    assert "No artifact build is authorized by this packet" in text
    assert "No package distribution registry or upload path is revived" in text


def test_notes_profile_traceability_and_ralph_advance_to_local_inventory_review() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")
    checklist = CHECKLIST.read_text(encoding="utf-8")
    profile = PROFILE.read_text(encoding="utf-8")
    ralph = RALPH.read_text(encoding="utf-8")

    assert "local artifact/release-scope review is approved" in notes
    assert "accepted_claim=local_artifact_release_scope_review_approved" in record
    assert "local_artifact_review_scope_approved: true" in record
    assert "credential_lookup_by_hisys: false" in record
    assert "live_external_action_authorized: false" in record
    assert "requires_human_review: true" in record
    assert "DARS-LIVE-RELEASE-LOCAL-ARTIFACT-RELEASE-SCOPE-REVIEW — local artifact scope review approved" in trace
    assert "dars-release-local-artifact-scope-review-approval-v0.0.118.md" in checklist
    assert "version: v0.0.122" in profile
    assert "formal_hisys_result: post_inventory_review_exact_approval_missing" in profile
    assert "next_safe_task: DARS-LIVE-RELEASE-POST-INVENTORY-REVIEW-EXACT-APPROVAL" in profile
    assert "Local artifact/release-scope review approved" in ralph
