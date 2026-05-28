"""DARS package-upload registry/artifact human gate checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "dars-release-package-upload-registry-artifact-human-gate-v0.0.113.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.113.md"
RECORD = (
    ROOT
    / "docs"
    / "milestone-bootstrap"
    / "documents"
    / "readiness_decision_record_v0.0.113.md"
)
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"
CHECKLIST = ROOT / "docs" / "release" / "dars-panel-release-candidate-checklist.md"
RALPH = ROOT / "ralph.md"
PROFILE = ROOT / "docs" / "milestone-bootstrap" / "profile.yaml"


def test_registry_artifact_human_gate_records_required_exact_approval_inputs() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "accepted_claim=release_package_upload_registry_artifact_human_gate_entered" in text
    assert "task_id=DARS-LIVE-RELEASE-PACKAGE-UPLOAD-REGISTRY-AND-ARTIFACT-HUMAN-GATE" in text
    assert "operator_instruction=go" in text
    assert "registry_artifact_human_gate_entered=true" in text
    assert "exact_approval_token_for_registry=APPROVE-PACKAGE-UPLOAD-REGISTRY-v0.0.113" in text
    assert "exact_approval_token_for_artifact_build=APPROVE-PACKAGE-UPLOAD-ARTIFACT-BUILD-v0.0.113" in text
    assert "exact_approval_token_for_version_alignment=APPROVE-PACKAGE-UPLOAD-VERSION-ALIGNMENT-v0.0.113" in text


def test_registry_artifact_human_gate_keeps_upload_and_artifact_actions_locked() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for flag in [
        "registry_target_selected=false",
        "registry_url_resolved=false",
        "registry_human_approval_recorded=false",
        "artifact_build_human_approval_recorded=false",
        "version_alignment_human_approval_recorded=false",
        "distribution_artifact_built=false",
        "distribution_artifact_verified=false",
        "distribution_artifact_hash_recorded=false",
        "package_version_alignment_verified=false",
        "build_command_executed=false",
        "upload_command_executed=false",
        "package_upload_authorized=false",
        "package_upload_performed=false",
        "package_registry_interaction_performed=false",
        "credential_lookup_by_hisys=false",
        "deployment_authorized=false",
        "publication_authorized=false",
        "external_notification_authorized=false",
        "live_external_action_authorized=false",
        "live_model_call_authorized=false",
        "raw_provider_api_call_by_hisys=false",
        "standing_unattended_approval_activated=false",
        "human_review_removal_authorized=false",
        "force_push_authorized=false",
        "branch_rewrite_authorized=false",
        "requires_human_review=true",
    ]:
        assert flag in text


def test_registry_artifact_gate_updates_current_state_and_next_task() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")
    checklist = CHECKLIST.read_text(encoding="utf-8")
    ralph = RALPH.read_text(encoding="utf-8")
    profile = PROFILE.read_text(encoding="utf-8")

    assert "Package-upload registry/artifact human gate entered" in notes
    assert "accepted_claim=release_package_upload_registry_artifact_human_gate_entered" in record
    assert "registry_artifact_human_gate_entered: true" in record
    assert "registry_target_selected: false" in record
    assert "distribution_artifact_built: false" in record
    assert "package_version_alignment_verified: false" in record
    assert "next_safe_task=DARS-LIVE-RELEASE-PACKAGE-UPLOAD-REGISTRY-ARTIFACT-EXACT-APPROVAL" in record
    assert "DARS-LIVE-RELEASE-PACKAGE-UPLOAD-REGISTRY-AND-ARTIFACT-HUMAN-GATE" in trace
    assert "dars-release-package-upload-registry-artifact-human-gate-v0.0.113.md" in checklist
    assert "DARS-LIVE-RELEASE-PACKAGE-UPLOAD-REGISTRY-ARTIFACT-EXACT-APPROVAL`" in ralph
    assert "previous_bootstrap_version: v0.0.123" in profile
    assert "next_safe_task: MB-CODEBASE-M21-6-PREP" in profile
