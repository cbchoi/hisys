"""Hisys Hermes DARS panel smoke gate checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "hisys-hermes-dars-panel-smoke-gate-v0.0.126.md"
REPORT = ROOT / "docs" / "reports" / "hisys-hermes-dars-panel-readiness-smoke-2026-05-28.md"
NOTES = ROOT / "docs" / "release" / "dars-panel-release-notes-v0.0.126.md"
RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.126.md"
TRACEABILITY = ROOT / "docs" / "traceability" / "dars-critic-panel-runtime-traceability.md"
CHECKLIST = ROOT / "docs" / "release" / "dars-panel-release-candidate-checklist.md"
PROFILE = ROOT / "docs" / "milestone-bootstrap" / "profile.yaml"
RALPH = ROOT / "ralph.md"
README = ROOT / "docs" / "milestone-bootstrap" / "README.md"


def test_hermes_dars_panel_smoke_records_actual_child_session_and_command() -> None:
    text = PACKET.read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")

    assert "task_id=HISYS-HERMES-DARS-PANEL-SMOKE-GATE" in text
    assert "accepted_claim=hermes_dars_panel_readiness_smoke_completed" in text
    assert "hermes_child_session_id=20260528_205103_8880e6" in text
    assert "hermes_terminal_tool_call_verified=true" in text
    assert "hisys_command_exit_code=0" in text
    assert "schema_id: hisys.dars_panel.readiness_status" in report
    assert "Session-store verification shows the child Hermes assistant issued the terminal tool call" in report


def test_hermes_smoke_preserves_hisys_non_actuator_boundaries() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for flag in [
        "hisys_raw_provider_api_readiness=false",
        "hisys_adapter_native_readiness=false",
        "dars_completion_upgrade_claimed=false",
        "bounded_unattended_advisory_operation_ready=false",
        "released_for_controlled_advisory_use=false",
        "release_action_authorized=false",
        "credential_lookup_by_hisys=false",
        "live_external_action_authorized=false",
        "hisys_command_external_call_made=false",
        "hisys_command_mutation_performed=false",
        "hisys_command_publication_performed=false",
        "raw_provider_api_call_by_hisys=false",
        "standing_unattended_approval_activated=false",
        "human_review_removal_authorized=false",
        "requires_human_review=true",
    ]:
        assert flag in text


def test_notes_traceability_checklist_and_profile_record_hermes_smoke_gate() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    trace = TRACEABILITY.read_text(encoding="utf-8")
    checklist = CHECKLIST.read_text(encoding="utf-8")
    profile = PROFILE.read_text(encoding="utf-8")
    ralph = RALPH.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")

    assert "Hisys Hermes DARS panel readiness smoke gate is recorded" in notes
    assert "accepted_claim=hermes_dars_panel_readiness_smoke_completed" in record
    assert "HISYS-HERMES-DARS-PANEL-SMOKE-GATE — Hermes smoke completed" in trace
    assert "hisys-hermes-dars-panel-smoke-gate-v0.0.126.md" in checklist
    assert "version: v0.0.126" in profile
    assert "formal_hisys_result: hermes_dars_panel_readiness_smoke_completed" in profile
    assert "next_safe_task: MB-CODEBASE-M21-6-PREP" in profile
    assert "HISYS-HERMES-DARS-PANEL-SMOKE-GATE" in ralph
    assert "Hermes child-session smoke" in readme
