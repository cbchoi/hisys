"""Tests for live source evidence provenance records.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from hisys.connectors.live_source_evidence import SourceAccessRecord, SourceEvidenceItem


def test_source_access_record_requires_url_time_hash_and_license_signal():
    record = SourceAccessRecord.model_validate(
        {
            "access_id": "ACCESS-001",
            "request_id": "HISYS-REQ-LIVE-001",
            "connector_id": "publisher_web_search",
            "source_url": "https://arxiv.org/abs/0000.00000",
            "accessed_at": "2026-05-09T16:30:00Z",
            "http_status": 200,
            "content_type": "text/html",
            "title": "Fixture title",
            "license_signal": "open_access",
            "sha256": "a" * 64,
            "external_call_made": True,
        }
    )

    assert record.mutation_performed is False
    assert record.license_signal == "open_access"
    assert record.sha256 == "a" * 64


def test_source_evidence_item_separates_quote_from_interpretation():
    item = SourceEvidenceItem.model_validate(
        {
            "evidence_id": "EVID-LIVE-001",
            "access_ref": "runtime-boundary/source-connectors/20260509/source-access-ACCESS-001.json",
            "quoted_text": "The paper states a limitation about topology change.",
            "interpretation": "This supports the research-gap criterion for topology/behavior co-evolution.",
            "claim_type": "source_evidence",
            "confidence": "medium",
        }
    )

    assert item.quoted_text != item.interpretation
    assert item.claim_type == "source_evidence"


def test_source_evidence_item_rejects_interpretation_without_quote():
    with pytest.raises(ValidationError, match="quoted_text"):
        SourceEvidenceItem.model_validate(
            {
                "evidence_id": "EVID-LIVE-002",
                "access_ref": "runtime-boundary/source-connectors/20260509/source-access-ACCESS-001.json",
                "quoted_text": "",
                "interpretation": "Unsupported interpretation.",
                "claim_type": "interpreted_gap",
            }
        )


def test_source_access_record_blocks_pdf_download_without_open_access_signal():
    with pytest.raises(ValidationError, match="open_access"):
        SourceAccessRecord.model_validate(
            {
                "access_id": "ACCESS-002",
                "request_id": "HISYS-REQ-LIVE-001",
                "connector_id": "open_access_pdf_fetch",
                "source_url": "https://publisher.example/closed.pdf",
                "accessed_at": "2026-05-09T16:30:00Z",
                "http_status": 200,
                "content_type": "application/pdf",
                "license_signal": "unknown",
                "sha256": "b" * 64,
                "pdf_downloaded": True,
                "external_call_made": True,
            }
        )
