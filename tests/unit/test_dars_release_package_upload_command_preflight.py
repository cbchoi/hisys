"""DARS package-upload command-boundary preflight checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "dars-release-package-upload-command-preflight-v0.0.112.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.112.md"
RECORD = (
    ROOT
    / "docs"
    / "milestone-bootstrap"
    / "documents"
    / "readiness_decision_record_v0.0.112.md"
)
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"
CHECKLIST = ROOT / "docs" / "release" / "dars-panel-release-candidate-checklist.md"
RALPH = ROOT / "ralph.md"
PROFILE = ROOT / "docs" / "milestone-bootstrap" / "profile.yaml"


def test_package_upload_command_preflight_records_candidate_commands_without_execution() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "accepted_claim=release_package_upload_command_preflight_recorded_for_human_review" in text
    assert "task_id=DARS-LIVE-RELEASE-PACKAGE-UPLOAD-COMMAND-PREFLIGHT" in text
    assert "candidate_build_command=python -m build" in text
    assert "candidate_upload_command=python -m twine upload <registry> dist/*" in text
    assert "upload_command_executed=false" in text
    assert "package_registry_interaction_performed=false" in text
    assert "credential_lookup_by_hisys=false" in text


def test_package_upload_command_preflight_identifies_blockers_before_upload() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for flag in [
        "package_upload_command_preflight_recorded=true",
        "package_upload_execution_instruction_received=true",
        "registry_target_selected=false",
        "registry_url_resolved=false",
        "distribution_artifact_built=false",
        "distribution_artifact_verified=false",
        "package_version_alignment_verified=false",
        "package_upload_authorized=false",
        "package_upload_performed=false",
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


def test_package_upload_command_preflight_updates_current_state_and_next_gate() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")
    checklist = CHECKLIST.read_text(encoding="utf-8")
    ralph = RALPH.read_text(encoding="utf-8")
    profile = PROFILE.read_text(encoding="utf-8")

    assert "Package-upload command preflight recorded" in notes
    assert "accepted_claim=release_package_upload_command_preflight_recorded_for_human_review" in record
    assert "package_upload_command_preflight_recorded: true" in record
    assert "registry_target_selected: false" in record
    assert "distribution_artifact_built: false" in record
    assert "package_upload_performed: false" in record
    assert "next_safe_task=DARS-LIVE-RELEASE-PACKAGE-UPLOAD-REGISTRY-AND-ARTIFACT-HUMAN-GATE" in record
    assert "DARS-LIVE-RELEASE-PACKAGE-UPLOAD-COMMAND-PREFLIGHT" in trace
    assert "dars-release-package-upload-command-preflight-v0.0.112.md" in checklist
    assert "DARS-LIVE-RELEASE-PACKAGE-UPLOAD-REGISTRY-AND-ARTIFACT-HUMAN-GATE`" in ralph
    assert "next_safe_task: MB-CODEBASE-M21-6-PREP" in profile
