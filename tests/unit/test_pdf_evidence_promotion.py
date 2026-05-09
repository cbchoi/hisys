"""Tests for promoting approved OA PDF evidence refs into investigations.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.connectors.open_access_pdf import OpenAccessPdfConnector
from hisys.connectors.pdf_evidence_promotion import PdfEvidencePromotionLoader


def test_pdf_evidence_promotion_loader_accepts_explicit_oa_pdf_refs(tmp_path: Path) -> None:
    fixture = tmp_path / "approved.pdf"
    fixture.write_bytes(b"%PDF-1.7\nApproved manual smoke bytes.\n%%EOF\n")
    package = OpenAccessPdfConnector().collect_fixture(
        request_id="HISYS-REQ-LIVE-G-001",
        fixture_path=fixture,
        source_url="https://mdpi.com/fixture/approved.pdf",
        license_signal="open_access",
        output_root=tmp_path,
        yyyymmdd="20260509",
    )

    promoted = PdfEvidencePromotionLoader(root=tmp_path).promote(
        source_access_refs=[package.access_ref],
        source_evidence_refs=[package.evidence_ref],
    )

    assert promoted.status == "promoted"
    assert promoted.promoted_pdf_evidence_refs == [package.evidence_ref]
    assert promoted.source_access_refs == [package.access_ref]
    assert promoted.pdf_downloaded is True
    assert promoted.external_call_made is False
    assert promoted.mutation_performed is False
    assert promoted.source_urls == ["https://mdpi.com/fixture/approved.pdf"]


def test_pdf_evidence_promotion_loader_rejects_non_pdf_access_ref(tmp_path: Path) -> None:
    access_ref = "runtime-boundary/source-connectors/20260509/source-access-ACCESS-HISYS-REQ-LIVE-G-002-doi_metadata_search.json"
    evidence_ref = "runtime-boundary/source-connectors/20260509/source-evidence-EVID-HISYS-REQ-LIVE-G-002-doi_metadata_search.json"
    access_path = tmp_path / access_ref
    evidence_path = tmp_path / evidence_ref
    access_path.parent.mkdir(parents=True)
    access_path.write_text(
        json.dumps(
            {
                "schema_id": "hisys.source_connector.source_access",
                "schema_version": "0.1.0",
                "access_id": "ACCESS-HISYS-REQ-LIVE-G-002-doi_metadata_search",
                "request_id": "HISYS-REQ-LIVE-G-002",
                "connector_id": "doi_metadata_search",
                "source_url": "https://api.crossref.org/works/10.0000/fixture",
                "accessed_at": "20260509T00:00:00Z",
                "http_status": 200,
                "content_type": "application/json",
                "license_signal": "open_access",
                "sha256": "a" * 64,
                "pdf_downloaded": False,
                "external_call_made": True,
                "mutation_performed": False,
                "policy_refs": ["docs/use-cases/live-research-connectors.md"],
            }
        ),
        encoding="utf-8",
    )
    evidence_path.write_text(
        json.dumps(
            {
                "schema_id": "hisys.source_connector.evidence_item",
                "schema_version": "0.1.0",
                "evidence_id": "EVID-HISYS-REQ-LIVE-G-002-doi_metadata_search",
                "access_ref": access_ref,
                "quoted_text": "metadata says OA",
                "interpretation": "metadata candidate only",
                "claim_type": "source_evidence",
                "confidence": "medium",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="open_access_pdf_fetch"):
        PdfEvidencePromotionLoader(root=tmp_path).promote(
            source_access_refs=[access_ref],
            source_evidence_refs=[evidence_ref],
        )
