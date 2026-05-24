"""DARS R7 residual-risk exact approval capture checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APPROVAL = ROOT / "docs" / "release" / "dars-r7-rc-residual-risk-exact-approval-v0.0.95.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.95.md"
CHECKLIST = ROOT / "docs" / "release" / "dars-panel-release-candidate-checklist.md"
READINESS_RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.95.md"
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"


def test_residual_risk_exact_approval_accepts_only_residual_risk_scope() -> None:
    text = APPROVAL.read_text(encoding="utf-8")

    assert "task_id=DARS-LIVE-RELEASE-R7-RC-RESIDUAL-RISK-EXACT-APPROVAL" in text
    assert "accepted_claim=r7_rc_residual_risk_scope_accepted_for_human_review" in text
    assert "operator_approval_utterance=승인" in text
    assert "approval_context=after_residual_risk_explanation" in text
    assert "human_residual_risk_acceptance=accepted" in text
    assert "release_candidate_ready=false" in text
    assert "release_execution_authorized=false" in text


def test_approval_records_accepted_risks_and_keeps_actions_blocked() -> None:
    text = APPROVAL.read_text(encoding="utf-8")

    required = [
        "r5_live_canary_executed=false",
        "bounded_unattended_advisory_operation_ready=false",
        "live_provider_model_call_made=false",
        "raw_provider_api_call_by_hisys=false",
        "credential_lookup_by_hisys=false",
        "adapter_native_real_provider_transport_ready=false",
        "r4c_codex_subprocess_completion_required_for_this_release=false",
        "released_for_controlled_advisory_use=false",
        "live_external_action_authorized=false",
        "live_model_call_authorized=false",
        "standing_unattended_approval_activated=false",
    ]
    for item in required:
        assert item in text


def test_checklist_notes_and_readiness_record_advance_to_rc_readiness_acceptance() -> None:
    checklist = CHECKLIST.read_text(encoding="utf-8")
    notes = NOTES.read_text(encoding="utf-8")
    record = READINESS_RECORD.read_text(encoding="utf-8")

    assert "R7 residual-risk exact approval is recorded" in checklist
    assert "r7_rc_residual_risk_scope_accepted_for_human_review" in checklist
    assert "human_residual_risk_acceptance=accepted" in checklist
    assert "Residual-risk scope accepted for human-reviewed RC readiness consideration" in notes
    assert "accepted_claim=r7_rc_residual_risk_scope_accepted_for_human_review" in record
    assert "human_residual_risk_acceptance=accepted" in record
    assert "next_safe_task=DARS-LIVE-RELEASE-R7-RC-READINESS-ACCEPTANCE-PACKET" in record
    assert "release_action_authorized=false" in record


def test_traceability_records_exact_approval_without_release_upgrade() -> None:
    text = TRACEABILITY.read_text(encoding="utf-8")

    assert "DARS-LIVE-RELEASE-R7-RC-RESIDUAL-RISK-EXACT-APPROVAL" in text
    assert "accepted claim is `r7_rc_residual_risk_scope_accepted_for_human_review`" in text
    assert "`human_residual_risk_acceptance=accepted`" in text
    assert "`release_candidate_ready=false`" in text
