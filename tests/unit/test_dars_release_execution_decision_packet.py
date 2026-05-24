"""DARS release execution decision packet checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "dars-release-execution-decision-packet-v0.0.98.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.98.md"
RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.98.md"
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"


def test_release_execution_decision_is_approved_without_performing_release_action() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "task_id=DARS-LIVE-RELEASE-EXECUTION-DECISION-PACKET" in text
    assert "accepted_claim=release_execution_decision_approved_for_human_reviewed_docs_only" in text
    assert "operator_approval_utterance=승인" in text
    assert "release_execution_decision_authorized=true" in text
    assert "release_action_authorized=false" in text
    assert "release_action_performed=false" in text
    assert "requires_human_review=true" in text


def test_release_execution_decision_keeps_live_publication_and_deploy_boundaries_locked() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for flag in [
        "tag_creation_authorized=false",
        "package_upload_authorized=false",
        "deployment_authorized=false",
        "publication_authorized=false",
        "external_notification_authorized=false",
        "live_external_action_authorized=false",
        "live_model_call_authorized=false",
        "raw_provider_api_call_by_hisys=false",
        "credential_lookup_by_hisys=false",
        "standing_unattended_approval_activated=false",
        "human_review_removal_authorized=false",
    ]:
        assert flag in text


def test_release_execution_notes_record_and_traceability_advance_next_safe_task() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")

    assert "Release execution decision approved for docs-only human-reviewed scope" in notes
    assert "accepted_claim=release_execution_decision_approved_for_human_reviewed_docs_only" in record
    assert "release_execution_decision_authorized: true" in record
    assert "release_action_authorized: false" in record
    assert "next_safe_task=DARS-LIVE-RELEASE-ACTION-AUTHORIZATION-PACKET" in record
    assert "DARS-LIVE-RELEASE-EXECUTION-DECISION-PACKET" in trace
    assert "`release_action_authorized=false`" in trace
