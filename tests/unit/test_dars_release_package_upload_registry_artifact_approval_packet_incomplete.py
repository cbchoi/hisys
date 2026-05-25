"""DARS package-upload registry/artifact approval packet incomplete checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "dars-release-package-upload-registry-artifact-approval-packet-incomplete-v0.0.115.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.115.md"
RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.115.md"
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"
CHECKLIST = ROOT / "docs" / "release" / "dars-panel-release-candidate-checklist.md"
PROFILE = ROOT / "docs" / "milestone-bootstrap" / "profile.yaml"


def test_tokens_only_packet_is_recorded_as_incomplete_without_build() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "task_id=DARS-LIVE-RELEASE-PACKAGE-UPLOAD-REGISTRY-ARTIFACT-EXACT-APPROVAL" in text
    assert "accepted_claim=release_package_upload_registry_artifact_approval_packet_incomplete" in text
    assert "approval_tokens_received=true" in text
    assert "approval_policy_details_received=false" in text
    assert "composite_approval_packet_complete=false" in text
    assert "registry_human_approval_recorded=false" in text
    assert "artifact_build_human_approval_recorded=false" in text
    assert "version_alignment_human_approval_recorded=false" in text


def test_incomplete_packet_names_missing_required_details() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for item in [
        "target registry policy",
        "artifact build command and output directory",
        "artifact hash recording method",
        "version alignment basis",
        "tokens alone are not the composite approval packet",
    ]:
        assert item in text


def test_incomplete_packet_keeps_all_runtime_actions_locked() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for flag in [
        "registry_target_selected=false",
        "registry_url_resolved=false",
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
        "requires_human_review=true",
    ]:
        assert flag in text


def test_notes_record_traceability_and_profile_keep_same_gate() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")
    checklist = CHECKLIST.read_text(encoding="utf-8")
    profile = PROFILE.read_text(encoding="utf-8")

    assert "approval tokens were received, but required policy details were not" in notes
    assert "accepted_claim=release_package_upload_registry_artifact_approval_packet_incomplete" in record
    assert "approval_tokens_received: true" in record
    assert "approval_policy_details_received: false" in record
    assert "next_safe_task=DARS-LIVE-RELEASE-PACKAGE-UPLOAD-REGISTRY-ARTIFACT-EXACT-APPROVAL" in record
    assert "DARS-LIVE-RELEASE-PACKAGE-UPLOAD-REGISTRY-ARTIFACT-EXACT-APPROVAL — approval packet incomplete" in trace
    assert "dars-release-package-upload-registry-artifact-approval-packet-incomplete-v0.0.115.md" in checklist
    assert "version: v0.0.115" in profile
    assert "next_safe_task: DARS-LIVE-RELEASE-PACKAGE-UPLOAD-REGISTRY-ARTIFACT-EXACT-APPROVAL" in profile
