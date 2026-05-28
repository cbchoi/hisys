"""DARS post-inventory review gate checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "dars-release-post-inventory-review-gate-v0.0.121.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.121.md"
RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.121.md"
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"
CHECKLIST = ROOT / "docs" / "release" / "dars-panel-release-candidate-checklist.md"
PROFILE = ROOT / "docs" / "milestone-bootstrap" / "profile.yaml"
RALPH = ROOT / "ralph.md"


def test_post_inventory_review_gate_enters_human_review_without_acceptance() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "task_id=DARS-LIVE-RELEASE-POST-INVENTORY-REVIEW-GATE" in text
    assert "predecessor_claim=repository_record_recommendation_recorded_for_human_review" in text
    assert "accepted_claim=post_inventory_review_gate_entered_for_human_review" in text
    assert "post_inventory_review_gate_entered=true" in text
    assert "active_controlled_record_set_accepted=false" in text
    assert "historical_only_record_set_accepted=false" in text
    assert "exact_human_approval_required=true" in text


def test_post_inventory_review_gate_preserves_r4c_and_release_boundaries() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for flag in [
        "r4c_success_report_recommended_as_active_transport_evidence=true",
        "r4c_auth_stop_report_recommended_as_historical_only=true",
        "dars_completion_upgrade_claimed=false",
        "bounded_unattended_advisory_operation_ready=false",
        "release_action_authorized=false",
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
        "human_review_removal_authorized=false",
        "force_push_authorized=false",
        "branch_rewrite_authorized=false",
        "requires_human_review=true",
    ]:
        assert flag in text


def test_post_inventory_review_gate_names_exact_approval_token_and_next_task() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "required_exact_approval=APPROVE-POST-INVENTORY-REVIEW-v0.0.121" in text
    assert "next_safe_task=DARS-LIVE-RELEASE-POST-INVENTORY-REVIEW-EXACT-APPROVAL" in text
    assert "docs/release/dars-release-repository-record-recommendation-v0.0.120.md" in text
    assert "docs/reports/dars-r4c-codex-subprocess-panel-smoke-success-2026-05-28.md" in text


def test_notes_profile_traceability_and_ralph_advance_to_exact_approval() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")
    checklist = CHECKLIST.read_text(encoding="utf-8")
    profile = PROFILE.read_text(encoding="utf-8")
    ralph = RALPH.read_text(encoding="utf-8")

    assert "post-inventory review gate is entered" in notes
    assert "accepted_claim=post_inventory_review_gate_entered_for_human_review" in record
    assert "post_inventory_review_gate_entered: true" in record
    assert "active_controlled_record_set_accepted: false" in record
    assert "DARS-LIVE-RELEASE-POST-INVENTORY-REVIEW-GATE — post-inventory review gate entered" in trace
    assert "dars-release-post-inventory-review-gate-v0.0.121.md" in checklist
    assert "version: v0.0.121" in profile
    assert "formal_hisys_result: post_inventory_review_gate_entered_for_human_review" in profile
    assert "next_safe_task: DARS-LIVE-RELEASE-POST-INVENTORY-REVIEW-EXACT-APPROVAL" in profile
    assert "DARS-LIVE-RELEASE-POST-INVENTORY-REVIEW-GATE" in ralph
