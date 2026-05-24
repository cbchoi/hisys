"""DARS R7 RC residual-risk human gate checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / "docs" / "release" / "dars-r7-rc-residual-risk-human-gate-v0.0.94.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.94.md"
CHECKLIST = ROOT / "docs" / "release" / "dars-panel-release-candidate-checklist.md"
READINESS_RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.94.md"
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"


def test_residual_risk_gate_records_gate_entered_without_approval_substitution() -> None:
    text = GATE.read_text(encoding="utf-8")

    assert "task_id=DARS-LIVE-RELEASE-R7-RC-RESIDUAL-RISK-HUMAN-GATE" in text
    assert "accepted_claim=r7_rc_residual_risk_human_gate_entered" in text
    assert "human_residual_risk_acceptance=not_recorded" in text
    assert "exact_human_approval_required=true" in text
    assert "release_candidate_ready=false" in text
    assert "release_execution_authorized=false" in text
    assert "released_for_controlled_advisory_use=false" in text


def test_residual_risk_gate_lists_exact_approval_text_and_scope() -> None:
    text = GATE.read_text(encoding="utf-8")

    required = [
        "APPROVE-R7-RC-RESIDUAL-RISK-SCOPE-v0.0.94",
        "r7_rc_readiness_decision_packet_recorded_for_human_review",
        "r4h_hermes_mediated_request_response_harness_closed_for_human_review",
        "r5_fake_transport_canary_post_run_review_accepted",
        "r5_live_canary_executed=false",
        "bounded_unattended_advisory_operation_ready=false",
        "live_provider_model_call_made=false",
        "raw_provider_api_call_by_hisys=false",
        "credential_lookup_by_hisys=false",
        "adapter_native_real_provider_transport_ready=false",
    ]
    for item in required:
        assert item in text


def test_checklist_notes_and_readiness_record_keep_rc_not_ready() -> None:
    checklist = CHECKLIST.read_text(encoding="utf-8")
    notes = NOTES.read_text(encoding="utf-8")
    record = READINESS_RECORD.read_text(encoding="utf-8")

    assert "R7 residual-risk human gate is entered" in checklist
    assert "r7_rc_residual_risk_human_gate_entered" in checklist
    assert "residual risk acceptance is still not recorded" in checklist
    assert "Residual-risk human gate entered; exact approval text is required" in notes
    assert "accepted_claim=r7_rc_residual_risk_human_gate_entered" in record
    assert "human_residual_risk_acceptance=not_recorded" in record
    assert "next_safe_task=DARS-LIVE-RELEASE-R7-RC-RESIDUAL-RISK-EXACT-APPROVAL" in record
    assert "live_model_call_authorized=false" in record
    assert "live_external_action_authorized=false" in record
    assert "release_action_authorized=false" in record


def test_traceability_records_residual_risk_gate_without_readiness_upgrade() -> None:
    text = TRACEABILITY.read_text(encoding="utf-8")

    assert "DARS-LIVE-RELEASE-R7-RC-RESIDUAL-RISK-HUMAN-GATE" in text
    assert "accepted claim is `r7_rc_residual_risk_human_gate_entered`" in text
    assert "`human_residual_risk_acceptance=not_recorded`" in text
    assert "`release_candidate_ready=false`" in text
