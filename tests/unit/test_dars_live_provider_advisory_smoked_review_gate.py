"""DARS live-provider advisory smoked current-state review gate checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "dars-live-provider-advisory-smoked-review-gate-v0.0.125.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.125.md"
RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.125.md"
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"
CHECKLIST = ROOT / "docs" / "release" / "dars-panel-release-candidate-checklist.md"
PROFILE = ROOT / "docs" / "milestone-bootstrap" / "profile.yaml"
RALPH = ROOT / "ralph.md"
README = ROOT / "docs" / "milestone-bootstrap" / "README.md"


def test_review_gate_answers_current_live_provider_advisory_smoked_scope() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "task_id=DARS-LIVE-PROVIDER-ADVISORY-SMOKED-REVIEW-GATE" in text
    assert "accepted_claim=live_provider_advisory_smoked_current_state_reviewed" in text
    assert "live_provider_advisory_smoked: usable_with_scoped_human_review" in text
    assert "scope=codex_subscription_subprocess_transport_only" in text
    assert "single_operator_dars_panel_usable=true" in text
    assert "active_transport_evidence_ref=docs/reports/dars-r4c-codex-subprocess-panel-smoke-success-2026-05-28.md" in text


def test_review_gate_preserves_raw_provider_unattended_and_completion_boundaries() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for flag in [
        "raw_provider_api_readiness=false",
        "adapter_native_readiness=false",
        "dars_completion_upgrade_claimed=false",
        "bounded_unattended_advisory_operation_ready=false",
        "released_for_controlled_advisory_use=false",
        "release_action_authorized=false",
        "credential_lookup_by_hisys=false",
        "live_external_action_authorized=false",
        "live_model_call_authorized=false",
        "raw_provider_api_call_by_hisys=false",
        "standing_unattended_approval_activated=false",
        "human_review_removal_authorized=false",
        "requires_human_review=true",
    ]:
        assert flag in text


def test_notes_traceability_checklist_and_profile_record_review_gate() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")
    checklist = CHECKLIST.read_text(encoding="utf-8")
    profile = PROFILE.read_text(encoding="utf-8")
    ralph = RALPH.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")

    assert "DARS live-provider advisory smoked current-state review gate is recorded" in notes
    assert "accepted_claim=live_provider_advisory_smoked_current_state_reviewed" in record
    assert "DARS-LIVE-PROVIDER-ADVISORY-SMOKED-REVIEW-GATE — current state reviewed" in trace
    assert "dars-live-provider-advisory-smoked-review-gate-v0.0.125.md" in checklist
    assert "version: v0.0.125" in profile
    assert "formal_hisys_result: live_provider_advisory_smoked_current_state_reviewed" in profile
    assert "next_safe_task: MB-CODEBASE-M21-6-PREP" in profile
    assert "DARS-LIVE-PROVIDER-ADVISORY-SMOKED-REVIEW-GATE" in ralph
    assert "live_provider_advisory_smoked is usable only under scoped human review" in readme
