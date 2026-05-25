"""DARS package-upload scoped execution instruction gate checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = (
    ROOT
    / "docs"
    / "release"
    / "dars-release-package-upload-scoped-execution-instruction-missing-v0.0.110.md"
)
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.110.md"
RECORD = (
    ROOT
    / "docs"
    / "milestone-bootstrap"
    / "documents"
    / "readiness_decision_record_v0.0.110.md"
)
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"
TRACEABILITY_README = ROOT / "docs" / "traceability" / "README.md"
RALPH = ROOT / "ralph.md"
PROFILE = ROOT / "docs" / "milestone-bootstrap" / "profile.yaml"


def test_scoped_execution_instruction_gate_records_generic_go_as_missing_instruction() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "task_id=DARS-LIVE-RELEASE-PACKAGE-UPLOAD-SCOPED-EXECUTION-INSTRUCTION-GATE" in text
    assert "accepted_claim=release_package_upload_scoped_execution_instruction_missing" in text
    assert "operator_instruction=go" in text
    assert "scoped_package_upload_execution_instruction_required=true" in text
    assert "scoped_package_upload_execution_instruction_received=false" in text
    assert "required_exact_execution_instruction=EXECUTE-PACKAGE-UPLOAD-v0.0.110" in text


def test_scoped_execution_instruction_gate_records_unscoped_execute_as_missing_instruction() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "followup_operator_instruction=execute" in text
    assert "followup_instruction_scoped_package_upload_execution=false" in text
    assert "followup_package_upload_authorized=false" in text
    assert "followup_package_registry_interaction_performed=false" in text
    assert "followup_credential_lookup_by_hisys=false" in text


def test_scoped_execution_instruction_gate_records_natural_language_package_upload_as_missing_exact_token() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "second_followup_operator_instruction=execute package upload v0.0.110" in text
    assert "second_followup_exact_required_instruction_matched=false" in text
    assert "second_followup_instruction_scoped_package_upload_execution=false" in text
    assert "second_followup_package_upload_authorized=false" in text
    assert "second_followup_package_upload_performed=false" in text
    assert "second_followup_package_registry_interaction_performed=false" in text
    assert "second_followup_credential_lookup_by_hisys=false" in text


def test_scoped_execution_instruction_gate_keeps_upload_and_external_actions_blocked() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for flag in [
        "package_upload_execution_decision_packet_approved=true",
        "package_upload_execution_instruction_received=false",
        "package_upload_authorized=false",
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


def test_scoped_execution_instruction_missing_record_traceability_and_next_gate() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")
    trace_readme = TRACEABILITY_README.read_text(encoding="utf-8")
    ralph = RALPH.read_text(encoding="utf-8")
    profile = PROFILE.read_text(encoding="utf-8")

    assert "Package-upload scoped execution instruction missing" in notes
    assert "accepted_claim=release_package_upload_scoped_execution_instruction_missing" in record
    assert "required_exact_execution_instruction: EXECUTE-PACKAGE-UPLOAD-v0.0.110" in record
    assert "package_upload_authorized: false" in record
    assert "package_upload_performed: false" in record
    assert (
        "next_safe_task=DARS-LIVE-RELEASE-PACKAGE-UPLOAD-SCOPED-EXECUTION-INSTRUCTION-GATE"
        in record
    )
    assert (
        "DARS-LIVE-RELEASE-PACKAGE-UPLOAD-SCOPED-EXECUTION-INSTRUCTION-GATE — scoped instruction missing"
        in trace
    )
    assert "DARS package-upload scoped execution instruction missing" in trace_readme
    assert "DARS-LIVE-RELEASE-PACKAGE-UPLOAD-SCOPED-EXECUTION-INSTRUCTION-GATE`" in ralph
    assert "version: v0.0.110" in profile
    assert (
        "next_safe_task: DARS-LIVE-RELEASE-PACKAGE-UPLOAD-SCOPED-EXECUTION-INSTRUCTION-GATE"
        in profile
    )
