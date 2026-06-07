"""Hisys MCP subsystem extraction decision packet checks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs" / "release" / "hisys-mcp-subsystem-extraction-decision-packet-v0.0.137.md"
NOTES = ROOT / "docs" / "release" / "hisys-mcp-release-notes-v0.0.137.md"
RECORD = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.137.md"
PROFILE = ROOT / "docs" / "milestone-bootstrap" / "profile.yaml"
TRACEABILITY = ROOT / "docs" / "traceability" / "README.md"
RALPH = ROOT / "ralph.md"


def test_subsystem_extraction_decision_selects_deferred_altas_first_candidate() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "task_id=HISYS-MCP-SUBSYSTEM-EXTRACTION-DECISION-PACKET" in text
    assert "accepted_claim=hisys_mcp_subsystem_extraction_decision_recorded" in text
    assert "gateway_should_remain_lightweight=true" in text
    assert "first_extraction_candidate=altas" in text
    assert "altas_split_decision=defer" in text
    assert "dars_split_decision=defer" in text
    assert "judge_split_decision=no" in text
    assert "actual_subsystem_split_performed=false" in text


def test_decision_packet_keeps_runtime_and_external_boundaries_closed() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for flag in [
        "production_listener_started=false",
        "hermes_config_mutated=false",
        "live_external_action_authorized=false",
        "live_model_call_authorized=false",
        "raw_provider_api_call_by_hisys=false",
        "credential_lookup_by_hisys=false",
        "docker_build_authorized=false",
        "docker_run_authorized=false",
        "deployment_authorized=false",
        "publication_authorized=false",
        "external_notification_authorized=false",
        "remote_push_authorized=false",
        "force_push_authorized=false",
        "branch_rewrite_authorized=false",
        "human_review_removal_authorized=false",
        "requires_human_review=true",
    ]:
        assert flag in text


def test_decision_packet_records_claude_drloo_evidence_and_next_safe_slice() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "claude_read_only_mapper_lane_a=altas" in text
    assert "claude_read_only_mapper_lane_b=dars_judge" in text
    assert "claude_read_only_mapper_lane_c=gateway_sidecar" in text
    assert "next_safe_task=HISYS-MCP-SUBSYSTEM-STATUS-READINESS-WRAPPER-PREFLIGHT" in text
    assert "src/hisys/altas/ package is not present" in text
    assert "do not expose judge_decide" in text


def test_notes_record_and_governance_surfaces_advance() -> None:
    notes = NOTES.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    profile = PROFILE.read_text(encoding="utf-8")
    traceability = TRACEABILITY.read_text(encoding="utf-8")
    ralph = RALPH.read_text(encoding="utf-8")

    assert "hisys_mcp_subsystem_extraction_decision_recorded" in notes
    assert "accepted_claim=hisys_mcp_subsystem_extraction_decision_recorded" in record
    assert "gateway_should_remain_lightweight: true" in record
    assert "actual_subsystem_split_performed: false" in record
    assert "version: v0.0.137" in profile
    assert "formal_hisys_result: hisys_mcp_subsystem_extraction_decision_recorded" in profile
    assert "next_safe_task: HISYS-MCP-SUBSYSTEM-STATUS-READINESS-WRAPPER-PREFLIGHT" in profile
    assert "Hisys MCP subsystem extraction decision" in traceability
    assert "HISYS-MCP-SUBSYSTEM-EXTRACTION-DECISION-PACKET" in ralph
