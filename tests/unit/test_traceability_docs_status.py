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
