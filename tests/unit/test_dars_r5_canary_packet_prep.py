"""DARS R5 canary packet-prep document tests.

Traceability: HISYS-FR-DARS-CP-013, HISYS-FR-DARS-CP-015,
DARS-LIVE-RELEASE-R5-CANARY-PACKET-PREP.

These tests validate controlled documents only. They perform no live provider/model
call, no Codex subprocess call, no raw provider API call, no credential lookup,
no standing unattended approval activation, and no external action.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "dars-r5-canary-packet-prep-v0.0.86.md"
RDR = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.86.md"
CHECKLIST = ROOT / "docs" / "release" / "dars-panel-release-candidate-checklist.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.86.md"
SCOPE_DECISION = ROOT / "docs" / "release" / "dars-r5-canary-scope-decision-v0.0.85.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_r5_canary_packet_prep_records_required_packet_sections_and_flags() -> None:
    text = _read(PACKET)

    assert "accepted_claim=r5_canary_packet_prepared_for_human_review" in text
    assert "next_safe_task: `DARS-LIVE-RELEASE-R5-CANARY-ACTION-DECISION-PACKET`" in text

    required_sections = {
        "Standing approval references",
        "Request-class scope",
        "Budget, rate, prompt, and output caps",
        "Kill-switch reference",
        "Audit-retention reference",
        "Post-run human review",
        "Stop conditions",
        "R6 status and rollback references",
    }
    for section in required_sections:
        assert section in text, f"missing section: {section}"

    required_flags = {
        "r5_canary_packet_prepared=true",
        "r5_live_canary_executed=false",
        "standing_unattended_approval_activated=false",
        "live_provider_model_call_made=false",
        "codex_cli_subprocess_call=false",
        "raw_provider_api_call_by_hisys=false",
        "credential_lookup_by_hisys=false",
        "mutation_performed=false",
        "publication_performed=false",
        "bounded_unattended_advisory_operation_ready=false",
        "release_candidate_ready=false",
        "requires_human_review=true",
    }
    for flag in required_flags:
        assert flag in text, f"missing flag: {flag}"


def test_r5_canary_packet_prep_references_existing_r5_prep_and_r6_anchors() -> None:
    text = _read(PACKET)

    expected_refs = {
        "docs/runbooks/dars-unattended-advisory-operation.md",
        "docs/examples/dars/unattended-standing-approval.example.json",
        "src/hisys/agents/dars_unattended_policy.py",
        "src/hisys/operations/dars_unattended_runner.py",
        "docs/runbooks/dars-live-operations.md",
        "docs/runbooks/dars-live-rollback.md",
        "docs/release/dars-r5-canary-scope-decision-v0.0.85.md",
    }
    for ref in expected_refs:
        assert ref in text, f"missing anchor reference: {ref}"


def test_r5_canary_packet_prep_excludes_live_execution_and_r4c_reactivation() -> None:
    text = _read(PACKET)

    assert "R4C is excluded from this release scope" in text
    assert "does not by itself authorize" in text
    assert "no live provider/model call" in text
    assert "no Codex subprocess call" in text
    assert "no credential lookup" in text
    assert "no mutation outside repository docs/tests/control files" in text


def test_readiness_record_v0086_matches_packet_prep_boundary() -> None:
    text = _read(RDR)

    assert "formal_hisys_result=r5_canary_packet_prepared_for_human_review" in text
    assert "next_safe_task=DARS-LIVE-RELEASE-R5-CANARY-ACTION-DECISION-PACKET" in text
    assert "r5_canary_packet_prepared=true" in text
    assert "r5_live_canary_executed=false" in text
    assert "standing_unattended_approval_activated=false" in text
    assert "release_candidate_ready=false" in text
    assert "bounded_unattended_advisory_operation_ready=false" in text
    assert "requires_human_review=true" in text
    assert "live_model_call_authorized=false" in text
    assert "live_external_action_authorized=false" in text
    assert "release_action_authorized=false" in text


def test_release_notes_v0086_record_packet_prep_scope_only() -> None:
    text = _read(NOTES)

    assert "R5 canary packet preparation" in text
    assert "release_candidate_ready=false" in text
    assert "r5_live_canary_executed=false" in text
    assert "No release artifact is produced by this note" in text
    assert "R4C is excluded from this release scope" in text


def test_release_candidate_checklist_marks_r5_canary_packet_prep_present() -> None:
    text = _read(CHECKLIST)

    assert "R5 bounded unattended canary packet prep document is present" in text
    assert "docs/release/dars-r5-canary-packet-prep-v0.0.86.md" in text
    assert "R5 bounded unattended canary action decision packet is reviewed" in text
    assert "R5 bounded unattended live canary evidence" in text
    assert "release_candidate_ready remains false until every required evidence row is accepted" in text


def test_scope_decision_v0085_remains_unchanged_and_consistent() -> None:
    """Ensure the prior scope decision still names the packet-prep task we are now executing."""

    text = _read(SCOPE_DECISION)
    assert "next_safe_task: `DARS-LIVE-RELEASE-R5-CANARY-PACKET-PREP`" in text
    assert "r4c_in_this_release=false" in text
