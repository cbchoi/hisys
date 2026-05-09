"""Tests for manual-smoke DOI metadata connector.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.connectors.doi_metadata import DoiMetadataConnector


def test_doi_metadata_connector_uses_injected_transport_and_records_provenance(tmp_path: Path):
    calls: list[str] = []

    def fake_fetch(url: str) -> tuple[int, str, str]:
        calls.append(url)
        return (
            200,
            "application/json",
            json.dumps(
                {
                    "message": {
                        "DOI": "10.0000/hisys.fixture.formalism",
                        "title": ["Fixture Dynamic Structure DEVS Metadata"],
                        "publisher": "Hisys Fixture Press",
                        "URL": "https://doi.org/10.0000/hisys.fixture.formalism",
                    }
                }
            ),
        )

    connector = DoiMetadataConnector(fetch=fake_fetch)
    package = connector.collect(
        request_id="HISYS-REQ-LIVE-C-001",
        doi="10.0000/hisys.fixture.formalism",
        output_root=tmp_path,
        yyyymmdd="20260509",
    )

    assert calls == ["https://api.crossref.org/works/10.0000%2Fhisys.fixture.formalism"]
    assert package.access_record.connector_id == "doi_metadata_search"
    assert package.access_record.source_url == calls[0]
    assert package.access_record.external_call_made is True
    assert package.access_record.mutation_performed is False
    assert package.access_record.http_status == 200
    assert package.evidence_items[0].quoted_text.startswith("Fixture Dynamic Structure DEVS Metadata")
    assert package.evidence_items[0].claim_type == "source_evidence"
    assert (tmp_path / package.access_ref).exists()
    assert (tmp_path / package.evidence_ref).exists()
