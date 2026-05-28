"""DARS local artifact inventory review checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "dars-release-local-artifact-inventory-review-v0.0.119.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.119.md"
RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.119.md"
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"
CHECKLIST = ROOT / "docs" / "release" / "dars-panel-release-candidate-checklist.md"
PROFILE = ROOT / "docs" / "milestone-bootstrap" / "profile.yaml"
RALPH = ROOT / "ralph.md"


def test_local_artifact_inventory_review_records_controlled_evidence_set() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "task_id=DARS-LIVE-RELEASE-LOCAL-ARTIFACT-INVENTORY-REVIEW" in text
    assert "accepted_claim=local_artifact_inventory_review_recorded_for_human_review" in text
    assert "predecessor_claim=local_artifact_release_scope_review_approved" in text
    assert "docs/reports/dars-r4c-codex-subprocess-panel-smoke-success-2026-05-28.md" in text
    assert "docs/release/dars-release-local-artifact-scope-review-approval-v0.0.118.md" in text
    assert "docs/release/dars-panel-release-candidate-checklist.md" in text
    assert "docs/traceability/dars-critic-panel-runtime-traceability.md" in text


def test_local_artifact_inventory_review_marks_transient_evidence_as_reference_only() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "transient_runtime_evidence_reference_only=true" in text
    assert "/tmp/hisys-r4c-codex-panel-smoke-20260528-002-r049wku8" in text
    assert "copy_transient_runtime_payloads_into_repo=false" in text
    assert "raw_provider_output_persisted=false" in text
    assert "credential_or_token_material_recorded=false" in text


def test_local_artifact_inventory_review_keeps_external_and_release_boundaries_closed() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for flag in [
        "package_upload_scope_retired=true",
        "upload_command_scope_retired=true",
        "package_registry_interaction_scope_retired=true",
        "artifact_build_authorized=false",
        "build_command_executed=false",
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


def test_notes_profile_traceability_and_ralph_advance_to_repository_record_recommendation() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")
    checklist = CHECKLIST.read_text(encoding="utf-8")
    profile = PROFILE.read_text(encoding="utf-8")
    ralph = RALPH.read_text(encoding="utf-8")

    assert "local artifact inventory review is recorded" in notes
    assert "accepted_claim=local_artifact_inventory_review_recorded_for_human_review" in record
    assert "local_artifact_inventory_review_recorded: true" in record
    assert "transient_runtime_evidence_reference_only: true" in record
    assert "copy_transient_runtime_payloads_into_repo: false" in record
    assert "DARS-LIVE-RELEASE-LOCAL-ARTIFACT-INVENTORY-REVIEW — local artifact inventory review recorded" in trace
    assert "dars-release-local-artifact-inventory-review-v0.0.119.md" in checklist
    assert "version: v0.0.123" in profile
    assert "formal_hisys_result: post_inventory_review_recommendation_accepted_by_operator_override" in profile
    assert "next_safe_task: DARS-PANEL-PRODUCTIZATION-CLOSURE-GATE" in profile
    assert "DARS-LIVE-RELEASE-LOCAL-ARTIFACT-INVENTORY-REVIEW" in ralph
