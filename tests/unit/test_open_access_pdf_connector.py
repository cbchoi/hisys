"""Tests for fixture-first open-access PDF collector.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.connectors.open_access_pdf import OpenAccessPdfConnector


def test_open_access_pdf_connector_collects_local_fixture_with_open_access_license(tmp_path: Path):
    fixture = tmp_path / "formalism-open-access.pdf"
    fixture.write_bytes(b"%PDF-1.4\nFixture OA PDF text about dynamic-structure DEVS.\n%%EOF\n")

    package = OpenAccessPdfConnector().collect_fixture(
        request_id="HISYS-REQ-LIVE-D-001",
        fixture_path=fixture,
        source_url="https://www.mdpi.com/fixture/open-access.pdf",
        license_signal="open_access",
        output_root=tmp_path,
        yyyymmdd="20260509",
    )

    assert package.access_record.connector_id == "open_access_pdf_fetch"
    assert package.access_record.license_signal == "open_access"
    assert package.access_record.pdf_downloaded is True
    assert package.access_record.external_call_made is False
    assert package.access_record.mutation_performed is False
    assert package.access_record.content_type == "application/pdf"
    assert package.evidence_items[0].quoted_text.startswith("PDF bytes collected from legal open-access fixture")
    assert package.evidence_ref.endswith("source-evidence-EVID-HISYS-REQ-LIVE-D-001-open_access_pdf_fetch.json")

    access_artifact = tmp_path / package.access_ref
    evidence_artifact = tmp_path / package.evidence_ref
    assert access_artifact.exists()
    assert evidence_artifact.exists()
    access = json.loads(access_artifact.read_text(encoding="utf-8"))
    assert access["license_signal"] == "open_access"
    assert access["pdf_downloaded"] is True
    assert access["external_call_made"] is False


def test_open_access_pdf_connector_rejects_non_open_access_license_before_writing(tmp_path: Path):
    fixture = tmp_path / "closed.pdf"
    fixture.write_bytes(b"%PDF-1.4\nClosed fixture.\n%%EOF\n")

    with pytest.raises(ValueError, match="license_signal=open_access"):
        OpenAccessPdfConnector().collect_fixture(
            request_id="HISYS-REQ-LIVE-D-002",
            fixture_path=fixture,
            source_url="https://www.mdpi.com/fixture/closed.pdf",
            license_signal="closed",
            output_root=tmp_path,
            yyyymmdd="20260509",
        )

    assert not list((tmp_path / "runtime-boundary").glob("**/*.json"))
