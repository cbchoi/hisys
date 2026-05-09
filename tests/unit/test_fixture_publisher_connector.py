"""Tests for local fixture publisher evidence connector.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

from pathlib import Path

from hisys.connectors.fixture_publisher import FixturePublisherConnector


def test_fixture_publisher_connector_extracts_evidence_without_network(tmp_path: Path):
    fixture = Path("examples/instance/harness/fixtures/web/publisher-formalism-page.html")
    connector = FixturePublisherConnector(connector_id="fixture_publisher_page_reader")

    package = connector.collect(
        request_id="HISYS-REQ-LIVE-B-001",
        fixture_path=fixture,
        output_root=tmp_path,
        yyyymmdd="20260509",
    )

    assert package.access_record.connector_id == "fixture_publisher_page_reader"
    assert package.access_record.source_url.startswith("file://")
    assert package.access_record.external_call_made is False
    assert package.access_record.mutation_performed is False
    assert package.access_record.sha256
    assert "Dynamic Structure DEVS" in package.access_record.title
    assert package.evidence_items
    assert package.evidence_items[0].quoted_text
    assert package.evidence_items[0].quoted_text != package.evidence_items[0].interpretation
    assert package.access_ref.endswith("source-access-ACCESS-HISYS-REQ-LIVE-B-001-fixture_publisher_page_reader.json")
    assert package.evidence_ref.endswith("source-evidence-EVID-HISYS-REQ-LIVE-B-001-fixture_publisher_page_reader.json")
    assert (tmp_path / package.access_ref).exists()
    assert (tmp_path / package.evidence_ref).exists()
