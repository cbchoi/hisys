"""Hisys Altas/DARS/Judge subsystem role-separation gate tests."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCHITECTURE_DOC = ROOT / "docs" / "design" / "hisys-subsystem-architecture.md"
RELEASE_GATE_DOC = ROOT / "docs" / "release" / "hisys-subsystem-role-separation-prep-v0.0.127.md"
RDR_DOC = ROOT / "docs" / "milestone-bootstrap" / "documents" / "readiness_decision_record_v0.0.127.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_subsystem_architecture_defines_altas_dars_judge_roles() -> None:
    text = _read(ARCHITECTURE_DOC)

    assert "Hisys = Altas + DARS + Judge" in text
    assert "Altas finds and projects" in text
    assert "DARS challenges and improves" in text
    assert "Judge decides and bounds" in text
    assert "Altas = Agentic Layered Trace and Search" in text
    assert "Altas may use MCP and web search connectors" in text
    assert "DARS produces developmental opposition" in text
    assert "Judge issues bounded advisory judgments" in text


def test_architecture_preserves_independent_use_and_full_loop_boundaries() -> None:
    text = _read(ARCHITECTURE_DOC)

    assert "altas-only" in text
    assert "dars-only" in text
    assert "judge-only" in text
    assert "Altas -> DARS -> Judge" in text
    assert "Altas does not accept or reject claims" in text
    assert "DARS does not approve, mutate, or execute actions" in text
    assert "Judge does not remove human review" in text
    assert "raw evidence belongs in the evidence store" in text
    assert "vault writes are curated projections" in text


def test_role_separation_gate_records_bounded_dars_completion_claim() -> None:
    gate_text = _read(RELEASE_GATE_DOC)
    rdr_text = _read(RDR_DOC)

    for text in (gate_text, rdr_text):
        assert "accepted_claim=hisys_altas_dars_judge_role_separation_recorded" in text
        assert "dars_bounded_advisory_productized_baseline=true" in text
        assert "dars_completion_upgrade_claimed=false" in text
        assert "bounded_unattended_advisory_operation_ready=false" in text
        assert "raw_provider_api_readiness=false" in text
        assert "adapter_native_readiness=false" in text
        assert "live_external_action_authorized=false" in text
        assert "requires_human_review=true" in text
        assert "next_safe_task=HISYS-ALTAS-DARS-JUDGE-MODULE-SKELETON" in text


def test_release_checklist_records_role_separation_prep_row() -> None:
    checklist = _read(ROOT / "docs" / "release" / "dars-panel-release-candidate-checklist.md")

    assert "Hisys subsystem role-separation prep is recorded" in checklist
    assert "docs/design/hisys-subsystem-architecture.md" in checklist
    assert "Altas/DARS/Judge roles are separated without changing live authority" in checklist
