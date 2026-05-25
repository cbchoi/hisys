"""DARS package registry/upload scope discarded by operator decision."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "dars-release-package-registry-upload-scope-discarded-v0.0.117.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.117.md"
RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.117.md"
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"
CHECKLIST = ROOT / "docs" / "release" / "dars-panel-release-candidate-checklist.md"
PROFILE = ROOT / "docs" / "milestone-bootstrap" / "profile.yaml"
RALPH = ROOT / "ralph.md"


def test_registry_upload_scope_is_discarded_without_selecting_a_registry() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "task_id=DARS-LIVE-RELEASE-PACKAGE-REGISTRY-UPLOAD-SCOPE-DISCARDED" in text
    assert "accepted_claim=release_package_registry_upload_scope_discarded" in text
    assert "operator_decision=registry_and_package_upload_not_planned" in text
    assert "registry_policy_details_required=false" in text
    assert "composite_upload_approval_packet_retired=true" in text
    assert "package_upload_scope_retired=true" in text
    assert "pypi_registry_use_planned=false" in text
    assert "testpypi_registry_use_planned=false" in text
    assert "upload_command_scope_retired=true" in text
    assert "package_registry_interaction_scope_retired=true" in text


def test_registry_discard_record_preserves_all_live_external_locks() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for retired_flag in [
        "upload_command_executed=false",
        "package_upload_authorized=false",
        "package_upload_performed=false",
        "package_registry_interaction_performed=false",
    ]:
        assert retired_flag not in text

    for flag in [
        "registry_target_selected=false",
        "registry_url_resolved=false",
        "registry_human_approval_recorded=false",
        "artifact_build_human_approval_recorded=false",
        "version_alignment_human_approval_recorded=false",
        "distribution_artifact_built=false",
        "distribution_artifact_verified=false",
        "distribution_artifact_hash_recorded=false",
        "build_command_executed=false",
        "credential_lookup_by_hisys=false",
        "live_external_action_authorized=false",
        "requires_human_review=true",
    ]:
        assert flag in text


def test_registry_terms_are_not_recast_as_source_or_evidence_registry() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "package distribution registry such as PyPI/TestPyPI" in text
    assert "does not retire Hisys source registries, evidence registries, or fixture registries" in text
    assert "No package distribution registry policy remains pending" in text


def test_release_notes_profile_traceability_and_ralph_advance_to_discard_state() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")
    checklist = CHECKLIST.read_text(encoding="utf-8")
    profile = PROFILE.read_text(encoding="utf-8")
    ralph = RALPH.read_text(encoding="utf-8")

    assert "package distribution registry/upload scope is discarded" in notes
    assert "accepted_claim=release_package_registry_upload_scope_discarded" in record
    assert "registry_policy_details_required: false" in record
    assert "composite_upload_approval_packet_retired: true" in record
    assert "package_upload_scope_retired: true" in record
    assert "DARS-LIVE-RELEASE-PACKAGE-REGISTRY-UPLOAD-SCOPE-DISCARDED — registry/upload scope discarded" in trace
    assert "dars-release-package-registry-upload-scope-discarded-v0.0.117.md" in checklist
    assert "previous_bootstrap_version: v0.0.117" in profile
    assert "formal_hisys_result: local_artifact_release_scope_review_approved" in profile
    assert "next_safe_task: DARS-LIVE-RELEASE-LOCAL-ARTIFACT-INVENTORY-REVIEW" in profile
    assert "Local artifact/release-scope review approved" in ralph
