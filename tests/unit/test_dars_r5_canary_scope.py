"""DARS R5 canary scope and R4C release exclusion tests.

Traceability: HISYS-FR-DARS-CP-013, HISYS-FR-DARS-CP-015,
DARS-LIVE-RELEASE-R5-CANARY-SCOPE-DECISION.

These tests validate controlled documents only. They perform no live provider/model
call, no Codex subprocess call, no credential lookup, and no external action.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DECISION = ROOT / "docs" / "release" / "dars-r5-canary-scope-decision-v0.0.85.md"
RDR = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.85.md"
CHECKLIST = ROOT / "docs" / "release" / "dars-panel-release-candidate-checklist.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.85.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_r5_canary_scope_decision_records_operator_instruction_and_excludes_r4c() -> None:
    text = _read(DECISION)

    assert "R5진행 R4C는 이번 release에서 제외" in text
    assert "accepted_claim=r5_canary_scope_selected_with_r4c_excluded_from_this_release" in text
    assert "next_safe_task: `DARS-LIVE-RELEASE-R5-CANARY-PACKET-PREP`" in text
    assert "r4c_in_this_release=false" in text
    assert "r4c_future_work_allowed=true" in text
    assert "r4c_codex_subprocess_completion_required_for_this_release=false" in text


def test_r5_canary_scope_preserves_non_action_boundaries() -> None:
    text = _read(DECISION)

    required_flags = {
        "r5_live_canary_executed=false",
        "bounded_unattended_advisory_operation_ready=false",
        "release_candidate_ready=false",
        "released_for_controlled_advisory_use=false",
        "standing_unattended_approval_activated=false",
        "live_provider_model_call_made=false",
        "codex_cli_subprocess_call=false",
        "raw_provider_api_call_by_hisys=false",
        "credential_lookup_by_hisys=false",
        "mutation_performed=false",
        "publication_performed=false",
        "requires_human_review=true",
    }
    for flag in required_flags:
        assert flag in text


def test_release_checklist_and_notes_use_r5_canary_without_r4c_blocker() -> None:
    checklist = _read(CHECKLIST)
    notes = _read(NOTES)

    assert "R5 bounded unattended canary packet prep" in checklist
    assert "R5 bounded unattended canary action decision packet is reviewed" in checklist
    assert "R4C is excluded from this release scope" in checklist
    assert "R4C Codex subprocess completion is not a release blocker for v0.0.85" in notes
    assert "R5 canary has not executed in this decision increment" in notes
    assert "release_candidate_ready=false" in notes


def test_readiness_record_matches_r5_scope_boundary() -> None:
    text = _read(RDR)

    assert "R5 canary scope selected; R4C excluded from this release" in text
    assert "formal_hisys_result=r5_canary_scope_selected_with_r4c_excluded_from_this_release" in text
    assert "next_safe_task=DARS-LIVE-RELEASE-R5-CANARY-PACKET-PREP" in text
    assert "r4c_in_this_release=false" in text
    assert "r5_live_canary_executed=false" in text
    assert "requires_human_review=true" in text
