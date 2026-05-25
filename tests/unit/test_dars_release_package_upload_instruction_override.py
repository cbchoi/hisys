"""DARS package-upload instruction override checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = (
    ROOT
    / "docs"
    / "release"
    / "dars-release-package-upload-instruction-override-v0.0.111.md"
)
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.111.md"
RECORD = (
    ROOT
    / "docs"
    / "milestone-bootstrap"
    / "documents"
    / "readiness_decision_record_v0.0.111.md"
)
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"
RALPH = ROOT / "ralph.md"
PROFILE = ROOT / "docs" / "milestone-bootstrap" / "profile.yaml"


def test_package_upload_instruction_override_accepts_prior_natural_language_scope() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "accepted_claim=release_package_upload_instruction_override_accepted_for_command_preflight" in text
    assert "override_operator_instruction=override" in text
    assert "overridden_prior_instruction=execute package upload v0.0.110" in text
    assert "operator_override_exact_token_requirement=true" in text
    assert "package_upload_execution_instruction_received=true" in text
    assert "package_upload_command_preflight_required=true" in text


def test_package_upload_instruction_override_keeps_external_boundaries_locked_before_preflight() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for flag in [
        "package_upload_performed=false",
        "package_registry_interaction_performed=false",
        "credential_lookup_by_hisys=false",
        "deployment_authorized=false",
        "deployment_performed=false",
        "publication_authorized=false",
        "publication_performed=false",
        "external_notification_authorized=false",
        "external_notification_performed=false",
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


def test_package_upload_instruction_override_updates_current_state_and_next_task() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")
    ralph = RALPH.read_text(encoding="utf-8")
    profile = PROFILE.read_text(encoding="utf-8")

    assert "Package-upload instruction override accepted for command preflight" in notes
    assert "accepted_claim=release_package_upload_instruction_override_accepted_for_command_preflight" in record
    assert "package_upload_command_preflight_required: true" in record
    assert "package_upload_performed: false" in record
    assert "package_registry_interaction_performed: false" in record
    assert "credential_lookup_by_hisys: false" in record
    assert "next_safe_task=DARS-LIVE-RELEASE-PACKAGE-UPLOAD-COMMAND-PREFLIGHT" in record
    assert "DARS-LIVE-RELEASE-PACKAGE-UPLOAD-INSTRUCTION-OVERRIDE" in trace
    assert "DARS-LIVE-RELEASE-PACKAGE-UPLOAD-COMMAND-PREFLIGHT`" in ralph
    assert "version:" in profile
