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


def test_live_d_open_access_pdf_boundary_is_documented():
    """OA PDF collection must start fixture-only and require license evidence."""

    live_doc = ROOT / "docs" / "use-cases" / "live-research-connectors.md"
    text = live_doc.read_text(encoding="utf-8")

    assert "Live-D open-access PDF collector boundary" in text
    assert "open_access_pdf_fetch" in text
    assert "fixture-only first" in text
    assert "license_signal=open_access" in text
    assert "HISYS_ALLOW_LIVE_PDF_SMOKE" in text
    assert "not part of CI" in text


def test_live_e_pdf_candidate_planning_boundary_is_documented():
    """DOI metadata OA hints may plan candidates but must not fetch PDF bytes."""

    live_doc = ROOT / "docs" / "use-cases" / "live-research-connectors.md"
    text = live_doc.read_text(encoding="utf-8")

    assert "Live-E DOI metadata to OA PDF candidate planning boundary" in text
    assert "pdf_candidate" in text
    assert "DOI metadata OA hints" in text
    assert "must not fetch PDF bytes" in text
    assert "candidate_plan_only" in text


def test_live_f_manual_oa_pdf_smoke_boundary_is_documented():
    """Manual OA PDF smoke may fetch bytes only through approved, injectable boundary."""

    live_doc = ROOT / "docs" / "use-cases" / "live-research-connectors.md"
    text = live_doc.read_text(encoding="utf-8")

    assert "Live-F approved manual OA PDF fetch smoke boundary" in text
    assert "injectable transport" in text
    assert "manual live smoke only" in text
    assert "approval ref" in text
    assert "HISYS_ALLOW_LIVE_PDF_SMOKE" in text
    assert "CI must still use fake transport only" in text


def test_live_g_manual_pdf_evidence_promotion_boundary_is_documented():
    """Manual PDF evidence can be promoted only by explicit refs and preserved boundary records."""

    live_doc = ROOT / "docs" / "use-cases" / "live-research-connectors.md"
    text = live_doc.read_text(encoding="utf-8")

    assert "Live-G evidence promotion boundary" in text
    assert "explicit source-access and source-evidence refs" in text
    assert "promoted_pdf_evidence_refs" in text
    assert "no implicit PDF discovery" in text
    assert "DARS trace" in text
    assert "Chief Editor" in text


def test_live_h_pdf_quote_extraction_boundary_is_documented():
    """Promoted OA PDF quotes must be extracted only from explicit refs and separated from claims."""

    live_doc = ROOT / "docs" / "use-cases" / "live-research-connectors.md"
    text = live_doc.read_text(encoding="utf-8")

    assert "Live-H PDF quote extraction boundary" in text
    assert "explicit promoted_pdf_evidence_refs" in text
    assert "source_quote_refs" in text
    assert "quote-vs-interpretation separation" in text
    assert "no OCR or PDF parsing in CI" in text
    assert "Chief Editor novelty claims remain conditional" in text


def test_live_i_quote_to_claim_ledger_boundary_is_documented():
    """Quote-to-claim ledger must map quotes to claims without merging source and interpretation."""

    live_doc = ROOT / "docs" / "use-cases" / "live-research-connectors.md"
    text = live_doc.read_text(encoding="utf-8")

    assert "Live-I quote-to-claim evidence ledger boundary" in text
    assert "source_quote_refs" in text
    assert "claim_evidence_ledger_refs" in text
    assert "support/contradict/needs_evidence" in text
    assert "quote text remains source evidence" in text
    assert "claim mapping remains interpretation" in text
    assert "Chief Editor claims remain conditional" in text


def test_live_j_claim_evidence_summary_boundary_is_documented():
    """Claim ledger aggregation must stay advisory and not prove novelty."""

    live_doc = ROOT / "docs" / "use-cases" / "live-research-connectors.md"
    text = live_doc.read_text(encoding="utf-8")

    assert "Live-J claim ledger aggregation boundary" in text
    assert "claim_evidence_summary_refs" in text
    assert "claim_evidence_ledger_refs" in text
    assert "support/contradict/needs_evidence balance" in text
    assert "advisory confidence only" in text
    assert "does not prove novelty" in text
    assert "Chief Editor confidence remains conditional" in text


def test_live_d_open_access_pdf_status_and_traceability_are_documented():
    """README and traceability docs must mention the implemented Live-D connector."""

    readme = README.read_text(encoding="utf-8")
    trace = TRACEABILITY_DOC.read_text(encoding="utf-8")

    assert "Increment **Live-D legal open-access PDF collector boundary**" in readme
    assert "hisys.connectors.open_access_pdf" in readme
    assert "HISYS_ALLOW_LIVE_PDF_SMOKE" in readme
    assert "| Live-D Legal open-access PDF collector boundary |" in trace
    assert "`hisys.connectors.open_access_pdf`" in trace
    assert "tests/unit/test_open_access_pdf_connector.py" in trace


def test_live_e_pdf_candidate_planning_status_and_traceability_are_documented():
    """README and traceability docs must mention the implemented Live-E planner."""

    readme = README.read_text(encoding="utf-8")
    trace = TRACEABILITY_DOC.read_text(encoding="utf-8")

    assert "Increment **Live-E DOI metadata to OA PDF candidate planning**" in readme
    assert "hisys.connectors.pdf_candidate_planner" in readme
    assert "hisys plan-pdf-candidates" in readme
    assert "| Live-E DOI metadata to OA PDF candidate planning |" in trace
    assert "`hisys.connectors.pdf_candidate_planner`" in trace
    assert "tests/unit/test_pdf_candidate_planner.py" in trace


def test_live_f_manual_oa_pdf_smoke_status_and_traceability_are_documented():
    """README and traceability docs must mention the implemented Live-F manual smoke path."""

    readme = README.read_text(encoding="utf-8")
    trace = TRACEABILITY_DOC.read_text(encoding="utf-8")

    assert "Increment **Live-F approved manual OA PDF fetch smoke**" in readme
    assert "collect_manual_smoke" in readme
    assert "--transport-fixture-pdf" in readme
    assert "| Live-F Approved manual OA PDF fetch smoke |" in trace
    assert "manual_pdf_smoke_completed" in trace
    assert "tests/unit/test_source_connector_cli.py" in trace


def test_live_g_pdf_evidence_promotion_status_and_traceability_are_documented():
    """README and traceability docs must mention implemented Live-G promotion path."""

    readme = README.read_text(encoding="utf-8")
    trace = TRACEABILITY_DOC.read_text(encoding="utf-8")

    assert "Increment **Live-G manual OA PDF evidence promotion**" in readme
    assert "PdfEvidencePromotionLoader" in readme
    assert "--promote-pdf-source-access-ref" in readme
    assert "| Live-G Manual OA PDF evidence promotion |" in trace
    assert "`hisys.connectors.pdf_evidence_promotion`" in trace
    assert "tests/unit/test_pdf_evidence_promotion.py" in trace


def test_live_h_pdf_quote_extraction_status_and_traceability_are_documented():
    """README and traceability docs must mention implemented Live-H quote extraction path."""

    readme = README.read_text(encoding="utf-8")
    trace = TRACEABILITY_DOC.read_text(encoding="utf-8")

    assert "Increment **Live-H PDF quote extraction from promoted OA evidence**" in readme
    assert "PdfQuoteExtractor" in readme
    assert "hisys extract-pdf-quotes" in readme
    assert "--source-quote-ref" in readme
    assert "| Live-H PDF quote extraction from promoted OA evidence |" in trace
    assert "`hisys.connectors.pdf_quote_extractor`" in trace
    assert "tests/unit/test_pdf_quote_extractor.py" in trace


def test_live_i_claim_evidence_ledger_status_and_traceability_are_documented():
    """README and traceability docs must mention implemented Live-I claim ledger path."""

    readme = README.read_text(encoding="utf-8")
    trace = TRACEABILITY_DOC.read_text(encoding="utf-8")

    assert "Live-I quote-to-claim evidence ledger" in readme
    assert "ClaimEvidenceLedgerBuilder" in readme
    assert "build-claim-evidence-ledger" in readme
    assert "--claim-evidence-ledger-ref" in readme
    assert "claim_evidence_ledger_refs" in readme
    assert "claim_evidence_ledger_present" in readme
    assert "support/contradict/needs-evidence" in readme
    assert "quote text remains source evidence" in readme
    assert "claim mapping remains interpretation" in readme

    assert "Live-I Quote-to-claim evidence ledger" in trace
    assert "hisys.connectors.claim_evidence_ledger" in trace
    assert "tests/unit/test_claim_evidence_ledger.py" in trace
    assert "tests/unit/test_claim_evidence_ledger_cli.py" in trace
    assert "tests/unit/test_domain_cli.py" in trace
    assert "claim_evidence_ledger_refs" in trace
    assert "claim_evidence_ledger_present" in trace


def test_live_j_claim_evidence_summary_status_and_traceability_are_documented():
    """README and traceability docs must mention implemented Live-J claim summary path."""

    readme = README.read_text(encoding="utf-8")
    trace = TRACEABILITY_DOC.read_text(encoding="utf-8")

    assert "Live-J claim evidence summary" in readme
    assert "ClaimEvidenceSummaryBuilder" in readme
    assert "build-claim-evidence-summary" in readme
    assert "--claim-evidence-summary-ref" in readme
    assert "claim_evidence_summary_refs" in readme
    assert "claim_evidence_summary_present" in readme
    assert "advisory confidence only" in readme
    assert "does not prove novelty" in readme

    assert "Live-J Claim evidence summary" in trace
    assert "hisys.connectors.claim_evidence_summary" in trace
    assert "tests/unit/test_claim_evidence_summary.py" in trace
    assert "tests/unit/test_claim_evidence_summary_cli.py" in trace
    assert "tests/unit/test_domain_cli.py" in trace
    assert "claim_evidence_summary_refs" in trace
    assert "claim_evidence_summary_present" in trace
