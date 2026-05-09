"""Tests for keeping traceability docs aligned with implemented Investigator increments.

Traceability: HISYS-T-027, HISYS-T-028, HISYS-T-032, HISYS-INST-INV-001.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TRACEABILITY_DOC = ROOT / "docs" / "traceability" / "README.md"
README = ROOT / "README.md"


def test_traceability_summary_marks_investigator_tasks_as_implemented_not_planned():
    """Implemented Investigator increments must not remain listed as planned work."""

    text = TRACEABILITY_DOC.read_text(encoding="utf-8")

    assert "| HISYS-T-027 Investigator multi-agent fixture research |" in text
    assert "| HISYS-T-028 Selenium read-only research harness |" in text
    assert "| HISYS-T-032 Configurable Investigator connector registry |" in text
    assert "| Planned HISYS-T-027" not in text
    assert "| Planned HISYS-T-028" not in text
    assert "Planned next Investigator work" not in text


def test_readme_status_lists_selenium_harness_as_completed_increment():
    """Top-level status should mention the implemented disabled browser harness."""

    text = README.read_text(encoding="utf-8")

    assert "Increment **HISYS-T-028 Selenium read-only research harness**" in text
    assert "disabled-by-default" in text
    assert "local static" in text
    assert "HTML fixture" in text


def test_live_research_connector_boundary_is_documented():
    """Live source search must be documented as disabled-by-default and governed."""

    live_doc = ROOT / "docs" / "use-cases" / "live-research-connectors.md"
    text = live_doc.read_text(encoding="utf-8")
    investigator = (ROOT / "examples" / "instance" / "harness" / "guidelines" / "investigator.md").read_text(
        encoding="utf-8"
    )
    source_governance = (
        ROOT / "examples" / "instance" / "harness" / "guidelines" / "source-governance.md"
    ).read_text(encoding="utf-8")

    assert "disabled-by-default" in text
    assert "no live external action until harness passes" in text
    assert "forbidden_actions" in text
    assert "approval_ref" in text
    assert "prompt text may not enable live connectors" in investigator
    assert "live connector dispatch decision" in source_governance


def test_live_c_manual_metadata_smoke_boundary_is_documented():
    """Manual metadata smoke must remain approval-gated and outside CI."""

    live_doc = ROOT / "docs" / "use-cases" / "live-research-connectors.md"
    text = live_doc.read_text(encoding="utf-8")

    assert "Live-C manual metadata smoke boundary" in text
    assert "doi_metadata_search" in text
    assert "manual_smoke_only" in text
    assert "not part of CI" in text
    assert "HISYS_ALLOW_LIVE_SMOKE" in text
    assert "dry-run artifact first" in text
