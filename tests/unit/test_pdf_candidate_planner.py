"""Tests for DOI metadata to OA PDF candidate planning.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.connectors.pdf_candidate_planner import PdfCandidatePlanner


def test_pdf_candidate_planner_accepts_open_access_pdf_hint_without_fetching_pdf(tmp_path: Path):
    metadata = {
        "message": {
            "DOI": "10.0000/hisys.fixture.formalism",
            "title": ["Fixture formalism article"],
            "license": [{"URL": "https://creativecommons.org/licenses/by/4.0/"}],
            "link": [
                {
                    "URL": "https://www.mdpi.com/fixture/formalism.pdf",
                    "content-type": "application/pdf",
                    "intended-application": "text-mining",
                }
            ],
        }
    }

    plan = PdfCandidatePlanner().plan(
        request_id="HISYS-REQ-LIVE-E-001",
        metadata=metadata,
        metadata_access_ref="runtime-boundary/source-connectors/20260509/source-access-ACCESS-HISYS-REQ-LIVE-E-001-doi_metadata_search.json",
        metadata_evidence_refs=["runtime-boundary/source-connectors/20260509/source-evidence-EVID-HISYS-REQ-LIVE-E-001-doi_metadata_search.json"],
        output_root=tmp_path,
        yyyymmdd="20260509",
    )

    assert plan.candidate_plan_only is True
    assert plan.pdf_downloaded is False
    assert plan.external_call_made is False
    assert plan.mutation_performed is False
    assert plan.candidates[0]["license_signal"] == "open_access"
    assert plan.candidates[0]["candidate_url"] == "https://www.mdpi.com/fixture/formalism.pdf"
    assert plan.candidates[0]["connector_id"] == "open_access_pdf_fetch"
    artifact = tmp_path / plan.plan_ref
    assert artifact.exists()
    data = json.loads(artifact.read_text(encoding="utf-8"))
    assert data["candidate_plan_only"] is True
    assert data["pdf_downloaded"] is False
    assert data["metadata_evidence_refs"] == ["runtime-boundary/source-connectors/20260509/source-evidence-EVID-HISYS-REQ-LIVE-E-001-doi_metadata_search.json"]


def test_pdf_candidate_planner_rejects_closed_license_pdf_hint_without_artifact(tmp_path: Path):
    metadata = {
        "message": {
            "DOI": "10.0000/hisys.closed.fixture",
            "license": [{"URL": "https://publisher.example/license/closed"}],
            "link": [{"URL": "https://publisher.example/closed.pdf", "content-type": "application/pdf"}],
        }
    }

    plan = PdfCandidatePlanner().plan(
        request_id="HISYS-REQ-LIVE-E-002",
        metadata=metadata,
        metadata_access_ref="runtime-boundary/source-connectors/20260509/source-access-ACCESS-HISYS-REQ-LIVE-E-002-doi_metadata_search.json",
        metadata_evidence_refs=[],
        output_root=tmp_path,
        yyyymmdd="20260509",
    )

    assert plan.candidates == []
    assert plan.reason_codes == ["license_not_open_access"]
    assert plan.pdf_downloaded is False
    assert (tmp_path / plan.plan_ref).exists()
