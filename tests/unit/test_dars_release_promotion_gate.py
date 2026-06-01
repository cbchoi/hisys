"""DARS release promotion gate tests."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROMOTION_DOC = ROOT / "docs" / "release" / "dars-release-promotion-v0.0.128.md"
RELEASE_NOTES_DOC = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.128.md"
RDR_DOC = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.128.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_dars_release_promotion_records_operator_instruction_and_claim() -> None:
    promotion_text = _read(PROMOTION_DOC)
    rdr_text = _read(RDR_DOC)

    for text in (promotion_text, rdr_text):
        assert "operator_instruction=dars release로 승격" in text
        assert "accepted_claim=dars_released_for_controlled_advisory_use" in text
        assert "dars_release_promoted=true" in text
        assert "released_for_controlled_advisory_use=true" in text
        assert "dars_bounded_advisory_productized_baseline=true" in text
        assert "single_operator_dars_panel_usable=true" in text
        assert "requires_human_review=true" in text
        assert "next_safe_task=JUDGE-SUBSYSTEM-READINESS-PACKET-CONTINUATION" in text


def test_dars_release_promotion_preserves_external_action_boundaries() -> None:
    promotion_text = _read(PROMOTION_DOC)
    rdr_text = _read(RDR_DOC)

    for text in (promotion_text, rdr_text):
        assert "tag_creation_authorized=false" in text
        assert "tag_push_authorized=false" in text
        assert "package_upload_authorized=false" in text
        assert "deployment_authorized=false" in text
        assert "publication_authorized=false" in text
        assert "external_notification_authorized=false" in text
        assert "live_external_action_authorized=false" in text
        assert "live_model_call_authorized=false" in text
        assert "raw_provider_api_call_by_hisys=false" in text
        assert "credential_lookup_by_hisys=false" in text
        assert "standing_unattended_approval_activated=false" in text
        assert "human_review_removal_authorized=false" in text


def test_release_notes_and_checklist_record_dars_release_promotion() -> None:
    notes_text = _read(RELEASE_NOTES_DOC)
    checklist = _read(ROOT / "docs" / "release" / "dars-panel-release-candidate-checklist.md")

    assert "accepted_claim=dars_released_for_controlled_advisory_use" in notes_text
    assert "DARS release promotion is recorded for controlled advisory use" in checklist
    assert "docs/release/dars-release-promotion-v0.0.128.md" in checklist
    assert "No tag, push, package upload, deployment, publication, or external notification is authorized" in checklist
