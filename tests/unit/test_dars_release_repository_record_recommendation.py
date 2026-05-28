"""DARS repository-record recommendation checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "dars-release-repository-record-recommendation-v0.0.120.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.120.md"
RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.120.md"
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"
CHECKLIST = ROOT / "docs" / "release" / "dars-panel-release-candidate-checklist.md"
PROFILE = ROOT / "docs" / "milestone-bootstrap" / "profile.yaml"
RALPH = ROOT / "ralph.md"


def test_repository_record_recommendation_records_active_and_historical_sets() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "task_id=DARS-LIVE-RELEASE-REPOSITORY-RECORD-RECOMMENDATION" in text
    assert "accepted_claim=repository_record_recommendation_recorded_for_human_review" in text
    assert "predecessor_claim=local_artifact_inventory_review_recorded_for_human_review" in text
    assert "active_controlled_record_set_recommended=true" in text
    assert "historical_only_record_set_recommended=true" in text
    assert "docs/reports/dars-r4c-codex-subprocess-panel-smoke-success-2026-05-28.md" in text
    assert "docs/reports/dars-r4-codex-subprocess-panel-smoke-auth-stop-2026-05-24.md" in text


def test_repository_record_recommendation_keeps_r4c_claim_narrow() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "r4c_success_report_recommended_as_active_transport_evidence=true" in text
    assert "r4c_auth_stop_report_recommended_as_historical_only=true" in text
    assert "r4c_codex_subscription_multi_critic_panel_smoke_completed_with_findings" in text
    assert "dars_completion_upgrade_claimed=false" in text
    assert "bounded_unattended_advisory_operation_ready=false" in text
    assert "human_review_removal_authorized=false" in text


def test_repository_record_recommendation_keeps_external_and_release_boundaries_closed() -> None:
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


def test_notes_profile_traceability_and_ralph_advance_to_post_inventory_review_gate() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")
    checklist = CHECKLIST.read_text(encoding="utf-8")
    profile = PROFILE.read_text(encoding="utf-8")
    ralph = RALPH.read_text(encoding="utf-8")

    assert "repository-record recommendation is recorded" in notes
    assert "accepted_claim=repository_record_recommendation_recorded_for_human_review" in record
    assert "active_controlled_record_set_recommended: true" in record
    assert "historical_only_record_set_recommended: true" in record
    assert "DARS-LIVE-RELEASE-REPOSITORY-RECORD-RECOMMENDATION — repository-record recommendation recorded" in trace
    assert "dars-release-repository-record-recommendation-v0.0.120.md" in checklist
    assert "version: v0.0.122" in profile
    assert "formal_hisys_result: post_inventory_review_exact_approval_missing" in profile
    assert "next_safe_task: DARS-LIVE-RELEASE-POST-INVENTORY-REVIEW-EXACT-APPROVAL" in profile
    assert "DARS-LIVE-RELEASE-REPOSITORY-RECORD-RECOMMENDATION" in ralph
