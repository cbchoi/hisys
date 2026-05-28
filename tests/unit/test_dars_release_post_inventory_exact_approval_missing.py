"""DARS post-inventory exact-approval missing checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "dars-release-post-inventory-exact-approval-missing-v0.0.122.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.122.md"
RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.122.md"
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"
CHECKLIST = ROOT / "docs" / "release" / "dars-panel-release-candidate-checklist.md"
PROFILE = ROOT / "docs" / "milestone-bootstrap" / "profile.yaml"
RALPH = ROOT / "ralph.md"


def test_generic_acceptance_does_not_match_exact_approval() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "task_id=DARS-LIVE-RELEASE-POST-INVENTORY-REVIEW-EXACT-APPROVAL" in text
    assert "operator_instruction=수락" in text
    assert "required_exact_approval=APPROVE-POST-INVENTORY-REVIEW-v0.0.121" in text
    assert "exact_human_approval_matched=false" in text
    assert "accepted_claim=post_inventory_review_exact_approval_missing" in text


def test_recommendation_remains_unaccepted_and_boundaries_closed() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for flag in [
        "active_controlled_record_set_accepted=false",
        "historical_only_record_set_accepted=false",
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


def test_exact_approval_gate_remains_next_safe_task() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "next_safe_task=DARS-LIVE-RELEASE-POST-INVENTORY-REVIEW-EXACT-APPROVAL" in text
    assert "APPROVE-POST-INVENTORY-REVIEW-v0.0.121" in text


def test_notes_profile_traceability_and_ralph_keep_exact_approval_gate() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")
    checklist = CHECKLIST.read_text(encoding="utf-8")
    profile = PROFILE.read_text(encoding="utf-8")
    ralph = RALPH.read_text(encoding="utf-8")

    assert "post-inventory exact approval is missing" in notes
    assert "accepted_claim=post_inventory_review_exact_approval_missing" in record
    assert "exact_human_approval_matched: false" in record
    assert "active_controlled_record_set_accepted: false" in record
    assert "DARS-LIVE-RELEASE-POST-INVENTORY-REVIEW-EXACT-APPROVAL — exact approval missing" in trace
    assert "dars-release-post-inventory-exact-approval-missing-v0.0.122.md" in checklist
    assert "version: v0.0.123" in profile
    assert "formal_hisys_result: post_inventory_review_recommendation_accepted_by_operator_override" in profile
    assert "next_safe_task: DARS-PANEL-PRODUCTIZATION-CLOSURE-GATE" in profile
    assert "DARS-LIVE-RELEASE-POST-INVENTORY-REVIEW-EXACT-APPROVAL" in ralph
