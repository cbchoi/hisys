"""CLI tests for promoted OA PDF quote extraction.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.cli.main import main
from hisys.connectors.open_access_pdf import OpenAccessPdfConnector
from hisys.connectors.pdf_evidence_promotion import PdfEvidencePromotionLoader


def _promoted_pdf_refs(tmp_path: Path):
    fixture = tmp_path / "manual-smoke.pdf"
    fixture.write_bytes(b"%PDF-1.7\nCLI quote extraction fixture.\n%%EOF\n")
    package = OpenAccessPdfConnector().collect_fixture(
        request_id="HISYS-REQ-LIVE-H-CLI-001",
        fixture_path=fixture,
        source_url="https://mdpi.com/fixture/live-h-cli.pdf",
        license_signal="open_access",
        output_root=tmp_path,
        yyyymmdd="20260509",
    )
    promoted = PdfEvidencePromotionLoader(root=tmp_path).promote(
        source_access_refs=[package.access_ref],
        source_evidence_refs=[package.evidence_ref],
    )
    return package, promoted


def test_extract_pdf_quotes_cli_writes_quote_artifacts_and_report(tmp_path: Path, capsys) -> None:
    package, promoted = _promoted_pdf_refs(tmp_path)

    result = main(
        [
            "extract-pdf-quotes",
            "--instance",
            str(tmp_path),
            "--date",
            "20260509",
            "--request-id",
            "HISYS-REQ-LIVE-H-CLI-001",
            "--promoted-pdf-evidence-ref",
            promoted.promoted_pdf_evidence_refs[0],
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "pdf quote extraction" in captured.out
    report_path = tmp_path / "reports" / "run-summaries" / "20260509" / "pdf-quote-extraction-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "completed"
    assert report["request_id"] == "HISYS-REQ-LIVE-H-CLI-001"
    assert report["external_call_made"] is False
    assert report["mutation_performed"] is False
    assert report["source_quote_refs"] == [
        "runtime-boundary/source-connectors/20260509/source-quote-QUOTE-HISYS-REQ-LIVE-H-CLI-001-open_access_pdf_fetch-001.json"
    ]
    quote = json.loads((tmp_path / report["source_quote_refs"][0]).read_text(encoding="utf-8"))
    assert quote["source_evidence_ref"] == package.evidence_ref
    assert quote["interpretation"] is None
