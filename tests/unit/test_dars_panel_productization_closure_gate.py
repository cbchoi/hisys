"""DARS panel productization closure-gate checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "dars-panel-productization-closure-gate-v0.0.124.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.124.md"
RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.124.md"
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"
CHECKLIST = ROOT / "docs" / "release" / "dars-panel-release-candidate-checklist.md"
PROFILE = ROOT / "docs" / "milestone-bootstrap" / "profile.yaml"
RALPH = ROOT / "ralph.md"
README = ROOT / "docs" / "milestone-bootstrap" / "README.md"


def test_closure_gate_records_productization_closure_without_completion_upgrade() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "task_id=DARS-PANEL-PRODUCTIZATION-CLOSURE-GATE" in text
    assert "accepted_claim=dars_panel_productization_closure_gate_recorded" in text
    assert "productization_closure_gate_recorded=true" in text
    assert "post_inventory_recommendation_accepted=true" in text
    assert "active_controlled_record_set_accepted=true" in text
    assert "historical_only_record_set_accepted=true" in text
    assert "dars_completion_upgrade_claimed=false" in text
    assert "bounded_unattended_advisory_operation_ready=false" in text
    assert "released_for_controlled_advisory_use=false" in text


def test_closure_gate_restores_codebase_queue_as_next_safe_task() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "restored_queue=codebase-analysis" in text
    assert "next_safe_task=MB-CODEBASE-M21-6-PREP" in text
    assert "docs/milestone-bootstrap/README.md" in text
    assert "docs/milestone-bootstrap/gates/quality_gate_v0.0.14.md" in text


def test_closure_gate_preserves_external_and_release_boundaries() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for flag in [
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


def test_notes_profile_traceability_and_ralph_record_closure_gate() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")
    checklist = CHECKLIST.read_text(encoding="utf-8")
    profile = PROFILE.read_text(encoding="utf-8")
    ralph = RALPH.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")

    assert "DARS panel productization closure gate is recorded" in notes
    assert "accepted_claim=dars_panel_productization_closure_gate_recorded" in record
    assert "restored_queue: codebase-analysis" in record
    assert "DARS-PANEL-PRODUCTIZATION-CLOSURE-GATE — closure gate recorded" in trace
    assert "dars-panel-productization-closure-gate-v0.0.124.md" in checklist
    assert "version: v0.0.124" in profile
    assert "formal_hisys_result: dars_panel_productization_closure_gate_recorded" in profile
    assert "next_safe_task: MB-CODEBASE-M21-6-PREP" in profile
    assert "DARS-PANEL-PRODUCTIZATION-CLOSURE-GATE" in ralph
    assert "returned to the codebase-analysis queue" in readme
