"""DARS controlled advisory use decision packet checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "dars-controlled-advisory-use-decision-packet-v0.0.97.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.97.md"
RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.97.md"
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"


def test_controlled_advisory_use_is_accepted_without_release_execution() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "task_id=DARS-LIVE-RELEASE-CONTROLLED-ADVISORY-USE-DECISION-PACKET" in text
    assert "accepted_claim=released_for_controlled_advisory_use_with_human_review" in text
    assert "operator_approval_utterance=승인" in text
    assert "released_for_controlled_advisory_use=true" in text
    assert "release_candidate_ready=true" in text
    assert "requires_human_review=true" in text


def test_controlled_advisory_use_keeps_external_and_live_boundaries_locked() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for flag in [
        "release_execution_authorized=false",
        "release_action_authorized=false",
        "live_external_action_authorized=false",
        "live_model_call_authorized=false",
        "bounded_unattended_advisory_operation_ready=false",
        "standing_unattended_approval_activated=false",
        "r5_live_canary_executed=false",
        "live_provider_model_call_made=false",
        "raw_provider_api_call_by_hisys=false",
        "credential_lookup_by_hisys=false",
        "adapter_native_real_provider_transport_ready=false",
        "publication_performed=false",
        "external_action_performed=false",
    ]:
        assert flag in text


def test_notes_record_and_traceability_advance_next_safe_task() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")

    assert "Controlled advisory use accepted with human review" in notes
    assert "accepted_claim=released_for_controlled_advisory_use_with_human_review" in record
    assert "released_for_controlled_advisory_use: true" in record
    assert "release_execution_authorized: false" in record
    assert "next_safe_task=DARS-LIVE-RELEASE-EXECUTION-DECISION-PACKET" in record
    assert "DARS-LIVE-RELEASE-CONTROLLED-ADVISORY-USE-DECISION-PACKET" in trace
    assert "`release_execution_authorized=false`" in trace
