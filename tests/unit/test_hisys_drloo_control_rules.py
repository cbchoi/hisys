"""Hisys DRLOO control-rule adoption checks."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RALPH = ROOT / "ralph.md"
CONTROL_RULES = ROOT / "docs" / "plans" / "hisys-drloo-control-rules.md"


def test_hisys_drloo_control_rules_document_exists_with_scope_and_boundaries() -> None:
    content = CONTROL_RULES.read_text(encoding="utf-8")

    assert "# Hisys DRLOO Control Rules" in content
    assert "HISYS-DRLOO-ADAPT-1-CONTROL-RULES" in content
    assert "DRLOO-derived" in content
    assert "candidate-state reconciliation" in content
    assert "queue-end refill" in content
    assert "cleaned active surface" in content
    assert "local-safe documentation/control" in content
    assert "fixture-only" in content

    locked_boundaries = [
        "live provider/model call",
        "credential lookup",
        "standing unattended approval activation",
        "release tag/package/upload/deploy/publication",
        "external notification",
        "raw provider API",
        "requires_human_review=false",
    ]
    for boundary in locked_boundaries:
        assert boundary in content


def test_root_ralph_adopts_drloo_queue_semantics_without_relaxing_hisys_boundaries() -> None:
    content = RALPH.read_text(encoding="utf-8")

    assert "### DRLOO-derived continuation and queue-end control" in content
    assert "HISYS-DRLOO-ADAPT-1-CONTROL-RULES" in content
    assert "docs/plans/hisys-drloo-control-rules.md" in content
    assert "candidate-state reconciliation" in content
    assert "cleaned active surface" in content
    assert "queue-end refill checkpoint" in content
    assert "No active implementation row may be derived from historical/completed" in content

    locked_boundaries = [
        "live provider/model call",
        "credential, token, keychain, or secret lookup",
        "standing unattended approval",
        "release tag/package/upload/deploy/publication",
        "external notification",
        "raw provider API",
        "removal of `requires_human_review=true`",
    ]
    for boundary in locked_boundaries:
        assert boundary in content


def test_ralph_reflection_records_drloo_adoption_as_docs_control_only() -> None:
    content = RALPH.read_text(encoding="utf-8")

    assert "2026-06-06 — `HISYS-DRLOO-ADAPT-1-CONTROL-RULES`" in content
    assert "docs/control only" in content
    assert "no production code" in content
    assert "no live provider/model call" in content
    assert "Next safe task remains `JUDGE-SUBSYSTEM-READINESS-PACKET-CONTINUATION`" in content
