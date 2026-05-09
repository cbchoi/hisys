"""Tests for promoted OA PDF source quote extraction.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.connectors.open_access_pdf import OpenAccessPdfConnector
from hisys.connectors.pdf_evidence_promotion import PdfEvidencePromotionLoader
from hisys.connectors.pdf_quote_extractor import PdfQuoteExtractor


def _promoted_pdf_fixture(tmp_path: Path):
    fixture = tmp_path / "manual-smoke.pdf"
    fixture.write_bytes(b"%PDF-1.7\nLocal quote extraction fixture.\n%%EOF\n")
    package = OpenAccessPdfConnector().collect_fixture(
        request_id="HISYS-REQ-LIVE-H-001",
        fixture_path=fixture,
        source_url="https://mdpi.com/fixture/live-h.pdf",
        license_signal="open_access",
        output_root=tmp_path,
        yyyymmdd="20260509",
    )
    promoted = PdfEvidencePromotionLoader(root=tmp_path).promote(
        source_access_refs=[package.access_ref],
        source_evidence_refs=[package.evidence_ref],
    )
    return package, promoted


def test_pdf_quote_extractor_writes_source_quote_from_promoted_evidence(tmp_path: Path) -> None:
    package, promoted = _promoted_pdf_fixture(tmp_path)

    result = PdfQuoteExtractor(root=tmp_path).extract(
        request_id="HISYS-REQ-LIVE-H-001",
        promoted_pdf_evidence_refs=promoted.promoted_pdf_evidence_refs,
        yyyymmdd="20260509",
    )

    assert result.external_call_made is False
    assert result.mutation_performed is False
    assert result.source_quote_refs == [
        "runtime-boundary/source-connectors/20260509/source-quote-QUOTE-HISYS-REQ-LIVE-H-001-open_access_pdf_fetch-001.json"
    ]
    quote_path = tmp_path / result.source_quote_refs[0]
    quote = json.loads(quote_path.read_text(encoding="utf-8"))
    assert quote["schema_id"] == "hisys.source_connector.source_quote"
    assert quote["source_evidence_ref"] == package.evidence_ref
    assert quote["source_access_ref"] == package.access_ref
    assert quote["source_url"] == "https://mdpi.com/fixture/live-h.pdf"
    assert quote["connector_id"] == "open_access_pdf_fetch"
    assert quote["quote_text"].startswith("PDF bytes collected from legal open-access fixture")
    assert quote["interpretation"] is None
    assert quote["claim_type"] == "source_quote"
    assert quote["external_call_made"] is False
    assert quote["mutation_performed"] is False


def test_pdf_quote_extractor_rejects_unpromoted_evidence_ref(tmp_path: Path) -> None:
    package, _promoted = _promoted_pdf_fixture(tmp_path)

    with pytest.raises(ValueError, match="promoted_pdf_evidence_refs"):
        PdfQuoteExtractor(root=tmp_path).extract(
            request_id="HISYS-REQ-LIVE-H-001",
            promoted_pdf_evidence_refs=[],
            yyyymmdd="20260509",
        )

    with pytest.raises(ValueError, match="source-evidence ref must point under runtime-boundary"):
        PdfQuoteExtractor(root=tmp_path).extract(
            request_id="HISYS-REQ-LIVE-H-001",
            promoted_pdf_evidence_refs=[package.evidence_ref.replace("runtime-boundary/", "")],
            yyyymmdd="20260509",
        )
