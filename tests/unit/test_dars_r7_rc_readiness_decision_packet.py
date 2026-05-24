"""DARS R7 release-candidate readiness decision packet checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "dars-r7-rc-readiness-decision-packet-v0.0.93.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.93.md"
CHECKLIST = ROOT / "docs" / "release" / "dars-panel-release-candidate-checklist.md"
READINESS_RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.93.md"
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"


def test_rc_readiness_packet_records_no_go_claim_boundary() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "task_id=DARS-LIVE-RELEASE-R7-RC-READINESS-DECISION-PACKET" in text
    assert "accepted_claim=r7_rc_readiness_decision_packet_recorded_for_human_review" in text
    assert "release_candidate_ready=false" in text
    assert "released_for_controlled_advisory_use=false" in text
    assert "release_execution_authorized=false" in text
    assert "requires_human_review=true" in text
    assert "no release tag, package upload, deployment, publication, or external notification" in text


def test_rc_readiness_packet_links_r4h_r5_and_preserves_live_blockers() -> None:
    text = PACKET.read_text(encoding="utf-8")

    required = [
        "r4h_hermes_mediated_request_response_harness_closed_for_human_review",
        "r5_fake_transport_canary_post_run_review_accepted",
        "r4c_codex_subprocess_completion_required_for_this_release=false",
        "r5_live_canary_executed=false",
        "live_provider_model_call_made=false",
        "raw_provider_api_call_by_hisys=false",
        "credential_lookup_by_hisys=false",
        "adapter_native_real_provider_transport_ready=false",
        "bounded_unattended_advisory_operation_ready=false",
        "human_residual_risk_acceptance=missing",
    ]
    for item in required:
        assert item in text


def test_checklist_and_notes_reflect_rc_readiness_decision_packet() -> None:
    checklist = CHECKLIST.read_text(encoding="utf-8")
    notes = NOTES.read_text(encoding="utf-8")
    record = READINESS_RECORD.read_text(encoding="utf-8")

    assert "R7 RC readiness decision packet" in checklist
    assert "r7_rc_readiness_decision_packet_recorded_for_human_review" in checklist
    assert "release_candidate_ready remains false" in checklist
    assert "RC readiness decision packet recorded; no release artifact is produced" in notes
    assert "accepted_claim=r7_rc_readiness_decision_packet_recorded_for_human_review" in record
    assert "next_safe_task=DARS-LIVE-RELEASE-R7-RC-RESIDUAL-RISK-HUMAN-GATE" in record
    assert "live_model_call_authorized=false" in record
    assert "live_external_action_authorized=false" in record
    assert "release_action_authorized=false" in record


def test_traceability_records_r7_readiness_packet_without_readiness_upgrade() -> None:
    text = TRACEABILITY.read_text(encoding="utf-8")

    assert "DARS-LIVE-RELEASE-R7-RC-READINESS-DECISION-PACKET" in text
    assert "accepted claim is `r7_rc_readiness_decision_packet_recorded_for_human_review`" in text
    assert "`release_candidate_ready=false`" in text
    assert "`r5_fake_transport_canary_post_run_review_accepted`" in text
