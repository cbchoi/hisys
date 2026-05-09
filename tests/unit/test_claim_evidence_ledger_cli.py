"""CLI tests for quote-to-claim evidence ledger construction.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.cli.main import main
from hisys.connectors.pdf_quote_extractor import SourceQuoteRecord


def _write_source_quote(root: Path) -> str:
    quote_dir = root / "runtime-boundary" / "source-connectors" / "20260509"
    quote_dir.mkdir(parents=True, exist_ok=True)
    quote = SourceQuoteRecord(
        quote_id="QUOTE-HISYS-REQ-LIVE-I-CLI-001-open_access_pdf_fetch-001",
        request_id="HISYS-REQ-LIVE-I-CLI-001",
        connector_id="open_access_pdf_fetch",
        source_access_ref="runtime-boundary/source-connectors/20260509/source-access-ACCESS-HISYS-REQ-LIVE-I-CLI-001-open_access_pdf_fetch.json",
        source_evidence_ref="runtime-boundary/source-connectors/20260509/source-evidence-EVID-HISYS-REQ-LIVE-I-CLI-001-open_access_pdf_fetch.json",
        source_url="https://mdpi.com/fixture/open-access.pdf",
        quote_text="Dynamic structure formalisms explicitly support structure changes.",
        quote_sha256="b" * 64,
    )
    quote_path = quote_dir / f"source-quote-{quote.quote_id}.json"
    quote_path.write_text(quote.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return str(quote_path.relative_to(root))


def test_build_claim_evidence_ledger_cli_writes_report_without_external_call(tmp_path: Path, capsys) -> None:
    quote_ref = _write_source_quote(tmp_path)

    result = main(
        [
            "build-claim-evidence-ledger",
            "--instance",
            str(tmp_path),
            "--date",
            "20260509",
            "--request-id",
            "HISYS-REQ-LIVE-I-CLI-001",
            "--claim-id",
            "CLAIM-HISYS-REQ-LIVE-I-CLI-001-DSDEVS",
            "--claim-text",
            "Dynamic Structure DEVS is relevant to structural change.",
            "--relation",
            "support",
            "--rationale",
            "The quote explicitly mentions structure changes.",
            "--source-quote-ref",
            quote_ref,
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "claim evidence ledger" in captured.out
    report_path = tmp_path / "reports" / "run-summaries" / "20260509" / "claim-evidence-ledger-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "completed"
    assert report["relation"] == "support"
    assert report["ledger_count"] == 1
    assert report["external_call_made"] is False
    assert report["mutation_performed"] is False
    ledger_ref = report["claim_evidence_ledger_refs"][0]
    ledger = json.loads((tmp_path / ledger_ref).read_text(encoding="utf-8"))
    assert ledger["source_quote_ref"] == quote_ref
    assert ledger["quote_text_is_source_evidence"] is True
    assert ledger["claim_mapping_is_interpretation"] is True
