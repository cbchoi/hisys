"""DARS package-upload registry/artifact policy details partial approval checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "dars-release-package-upload-registry-artifact-policy-details-partial-v0.0.116.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.116.md"
RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.116.md"
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"
CHECKLIST = ROOT / "docs" / "release" / "dars-panel-release-candidate-checklist.md"
PROFILE = ROOT / "docs" / "milestone-bootstrap" / "profile.yaml"


def test_partial_policy_details_record_artifact_and_version_details_without_build() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "task_id=DARS-LIVE-RELEASE-PACKAGE-UPLOAD-REGISTRY-ARTIFACT-EXACT-APPROVAL" in text
    assert "accepted_claim=release_package_upload_registry_artifact_policy_details_partial" in text
    assert "approval_tokens_received=true" in text
    assert "artifact_build_policy_details_received=true" in text
    assert "version_alignment_policy_details_received=true" in text
    assert "execution_boundary_details_received=true" in text
    assert "registry_policy_details_received=false" in text
    assert "composite_approval_packet_complete=false" in text


def test_partial_policy_details_name_the_remaining_missing_registry_policy() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for item in [
        "target registry policy is still missing",
        "TestPyPI-only pre-upload preparation",
        "https://test.pypi.org/legacy/",
        "credential-reference handling",
        "artifact build remains blocked until registry policy is recorded",
    ]:
        assert item in text


def test_partial_policy_details_keep_runtime_actions_locked() -> None:
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
        "requires_human_review=true",
    ]:
        assert flag in text


def test_notes_record_traceability_and_profile_keep_exact_approval_gate() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")
    checklist = CHECKLIST.read_text(encoding="utf-8")
    profile = PROFILE.read_text(encoding="utf-8")

    assert "artifact/version policy details were received, but registry policy details are still missing" in notes
    assert "accepted_claim=release_package_upload_registry_artifact_policy_details_partial" in record
    assert "registry_policy_details_received: false" in record
    assert "artifact_build_policy_details_received: true" in record
    assert "version_alignment_policy_details_received: true" in record
    assert "next_safe_task=DARS-LIVE-RELEASE-PACKAGE-UPLOAD-REGISTRY-ARTIFACT-EXACT-APPROVAL" in record
    assert "DARS-LIVE-RELEASE-PACKAGE-UPLOAD-REGISTRY-ARTIFACT-EXACT-APPROVAL — policy details partial" in trace
    assert "dars-release-package-upload-registry-artifact-policy-details-partial-v0.0.116.md" in checklist
    assert "previous_bootstrap_version: v0.0.123" in profile
    assert "next_safe_task: MB-CODEBASE-M21-6-PREP" in profile
