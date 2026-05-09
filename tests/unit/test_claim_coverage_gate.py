"""Tests for conditional manuscript claim coverage gates.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.connectors.claim_coverage_gate import ClaimCoverageGateBuilder
from hisys.connectors.claim_evidence_ledger import ClaimEvidenceLedgerBuilder
from hisys.connectors.claim_evidence_summary import ClaimEvidenceSummaryBuilder


def _write_quote(root: Path, *, request_id: str, quote_id: str) -> str:
    quote_dir = root / "runtime-boundary" / "source-connectors" / "20260509"
    quote_dir.mkdir(parents=True, exist_ok=True)
    quote_ref = f"runtime-boundary/source-connectors/20260509/source-quote-{quote_id}.json"
    (root / quote_ref).write_text(
        json.dumps(
            {
                "schema_id": "hisys.source_connector.source_quote",
                "schema_version": "0.1.0",
                "quote_id": quote_id,
                "request_id": request_id,
                "connector_id": "open_access_pdf_fetch",
                "source_access_ref": "runtime-boundary/source-connectors/20260509/source-access-ACCESS-open_access_pdf_fetch.json",
                "source_evidence_ref": "runtime-boundary/source-connectors/20260509/source-evidence-EVID-open_access_pdf_fetch.json",
                "source_url": "https://example.org/open.pdf",
                "quote_text": "The source discusses topology and behavior co-evolution.",
                "quote_sha256": "sha256test",
                "interpretation": None,
                "claim_type": "source_quote",
                "provenance": {},
                "external_call_made": False,
                "mutation_performed": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return quote_ref


def _build_summary(root: Path, *, claim_id: str, request_id: str = "REQ-K") -> str:
    quote_ref = _write_quote(root, request_id=request_id, quote_id=f"QUOTE-{claim_id}")
    ledger = ClaimEvidenceLedgerBuilder(root=root).build(
        request_id=request_id,
        claim_id=claim_id,
        claim_text=f"Major recommendation claim {claim_id}",
        relation="support",
        rationale="Explicit source quote supports this claim conditionally.",
        source_quote_refs=[quote_ref],
        yyyymmdd="20260509",
    )
    summary = ClaimEvidenceSummaryBuilder(root=root).build(
        request_id=request_id,
        claim_id=claim_id,
        claim_evidence_ledger_refs=ledger.claim_evidence_ledger_refs,
        yyyymmdd="20260509",
    )
    return summary.claim_evidence_summary_refs[0]


def test_claim_coverage_gate_records_uncovered_claims_and_conditional_language(tmp_path):
    summary_ref = _build_summary(tmp_path, claim_id="CLAIM-1")

    result = ClaimCoverageGateBuilder(root=tmp_path).build(
        request_id="REQ-K",
        required_claim_ids=["CLAIM-1", "CLAIM-2"],
        claim_evidence_summary_refs=[summary_ref],
        yyyymmdd="20260509",
    )

    assert result.claim_coverage_gate_refs
    gate = json.loads((tmp_path / result.claim_coverage_gate_refs[0]).read_text(encoding="utf-8"))
    assert gate["coverage_status"] == "needs_more_claim_evidence"
    assert gate["covered_claim_ids"] == ["CLAIM-1"]
    assert gate["uncovered_claim_ids"] == ["CLAIM-2"]
    assert gate["conditional_manuscript_language_only"] is True
    assert gate["does_not_approve_publication_ready_claims"] is True
    assert gate["external_call_made"] is False
    assert gate["mutation_performed"] is False


def test_claim_coverage_gate_rejects_summary_for_wrong_request(tmp_path):
    summary_ref = _build_summary(tmp_path, claim_id="CLAIM-1", request_id="OTHER")

    with pytest.raises(ValueError, match="request_id"):
        ClaimCoverageGateBuilder(root=tmp_path).build(
            request_id="REQ-K",
            required_claim_ids=["CLAIM-1"],
            claim_evidence_summary_refs=[summary_ref],
            yyyymmdd="20260509",
        )
