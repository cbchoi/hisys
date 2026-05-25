"""DARS package-upload registry/artifact exact approval missing checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "dars-release-package-upload-registry-artifact-exact-approval-missing-v0.0.114.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.114.md"
RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.114.md"
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"


def test_generic_proceed_records_registry_artifact_exact_approval_missing() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "task_id=DARS-LIVE-RELEASE-PACKAGE-UPLOAD-REGISTRY-ARTIFACT-EXACT-APPROVAL" in text
    assert "accepted_claim=release_package_upload_registry_artifact_exact_approval_missing" in text
    assert "operator_instruction=진행" in text
    assert "previous_assistant_presented_single_packet=true" in text
    assert "composite_approval_packet_received=false" in text
    assert "registry_human_approval_recorded=false" in text
    assert "artifact_build_human_approval_recorded=false" in text
    assert "version_alignment_human_approval_recorded=false" in text
    assert "package_upload_authorized=false" in text


def test_missing_packet_repeats_all_required_tokens_and_packet_requirements() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for item in [
        "APPROVE-PACKAGE-UPLOAD-REGISTRY-v0.0.113",
        "APPROVE-PACKAGE-UPLOAD-ARTIFACT-BUILD-v0.0.113",
        "APPROVE-PACKAGE-UPLOAD-VERSION-ALIGNMENT-v0.0.113",
        "target registry policy",
        "artifact build command and output directory",
        "artifact hash recording method",
        "version alignment basis",
        "generic `진행` is not the approval packet",
    ]:
        assert item in text


def test_missing_approval_keeps_build_upload_registry_and_credentials_locked() -> None:
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
        "deployment_authorized=false",
        "publication_authorized=false",
        "external_notification_authorized=false",
        "live_external_action_authorized=false",
        "requires_human_review=true",
    ]:
        assert flag in text


def test_notes_record_and_traceability_keep_same_next_gate() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")

    assert "Generic 진행 did not provide the composite approval packet" in notes
    assert "accepted_claim=release_package_upload_registry_artifact_exact_approval_missing" in record
    assert "composite_approval_packet_received: false" in record
    assert "registry_human_approval_recorded: false" in record
    assert "artifact_build_human_approval_recorded: false" in record
    assert "version_alignment_human_approval_recorded: false" in record
    assert "next_safe_task=DARS-LIVE-RELEASE-PACKAGE-UPLOAD-REGISTRY-ARTIFACT-EXACT-APPROVAL" in record
    assert "DARS-LIVE-RELEASE-PACKAGE-UPLOAD-REGISTRY-ARTIFACT-EXACT-APPROVAL — exact approval missing" in trace
    assert "`composite_approval_packet_received=false`" in trace
