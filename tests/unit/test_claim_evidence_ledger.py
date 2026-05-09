"""Tests for quote-to-claim evidence ledger records.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.connectors.claim_evidence_ledger import ClaimEvidenceLedgerBuilder
from hisys.connectors.pdf_quote_extractor import SourceQuoteRecord


def _write_source_quote(root: Path, *, request_id: str = "HISYS-REQ-LIVE-I-001") -> str:
    quote_dir = root / "runtime-boundary" / "source-connectors" / "20260509"
    quote_dir.mkdir(parents=True, exist_ok=True)
    quote = SourceQuoteRecord(
        quote_id=f"QUOTE-{request_id}-open_access_pdf_fetch-001",
        request_id=request_id,
        connector_id="open_access_pdf_fetch",
        source_access_ref="runtime-boundary/source-connectors/20260509/source-access-ACCESS-HISYS-REQ-LIVE-I-001-open_access_pdf_fetch.json",
        source_evidence_ref="runtime-boundary/source-connectors/20260509/source-evidence-EVID-HISYS-REQ-LIVE-I-001-open_access_pdf_fetch.json",
        source_url="https://mdpi.com/fixture/open-access.pdf",
        quote_text="Dynamic structure models allow structural change during simulation.",
        quote_sha256="a" * 64,
        provenance={"origin": "promoted_pdf_evidence_ref"},
        policy_refs=["HISYS-T-024"],
    )
    quote_path = quote_dir / f"source-quote-{quote.quote_id}.json"
    quote_path.write_text(quote.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return str(quote_path.relative_to(root))


def test_claim_evidence_ledger_maps_quote_to_claim_without_mutating_quote(tmp_path: Path) -> None:
    quote_ref = _write_source_quote(tmp_path)
    before = (tmp_path / quote_ref).read_text(encoding="utf-8")

    result = ClaimEvidenceLedgerBuilder(root=tmp_path).build(
        request_id="HISYS-REQ-LIVE-I-001",
        claim_id="CLAIM-HISYS-REQ-LIVE-I-001-DSDEVS",
        claim_text="Dynamic Structure DEVS is relevant for topology-changing simulation.",
        relation="support",
        rationale="The quote directly states that dynamic-structure models allow structural change during simulation.",
        source_quote_refs=[quote_ref],
        yyyymmdd="20260509",
    )

    assert result.claim_evidence_ledger_refs == [
        "runtime-boundary/source-connectors/20260509/claim-evidence-ledger-LEDGER-HISYS-REQ-LIVE-I-001-CLAIM-HISYS-REQ-LIVE-I-001-DSDEVS-001.json"
    ]
    assert result.external_call_made is False
    assert result.mutation_performed is False
    assert (tmp_path / quote_ref).read_text(encoding="utf-8") == before
    ledger = json.loads((tmp_path / result.claim_evidence_ledger_refs[0]).read_text(encoding="utf-8"))
    assert ledger["claim_id"] == "CLAIM-HISYS-REQ-LIVE-I-001-DSDEVS"
    assert ledger["claim_text"] == "Dynamic Structure DEVS is relevant for topology-changing simulation."
    assert ledger["relation"] == "support"
    assert ledger["source_quote_ref"] == quote_ref
    assert ledger["quote_text"] == "Dynamic structure models allow structural change during simulation."
    assert ledger["quote_text_is_source_evidence"] is True
    assert ledger["claim_mapping_is_interpretation"] is True
    assert ledger["advisory_only"] is True
    assert ledger["external_call_made"] is False
    assert ledger["mutation_performed"] is False


def test_claim_evidence_ledger_rejects_invalid_relation(tmp_path: Path) -> None:
    quote_ref = _write_source_quote(tmp_path)

    with pytest.raises(ValueError, match="support/contradict/needs_evidence"):
        ClaimEvidenceLedgerBuilder(root=tmp_path).build(
            request_id="HISYS-REQ-LIVE-I-001",
            claim_id="CLAIM-HISYS-REQ-LIVE-I-001-DSDEVS",
            claim_text="Dynamic Structure DEVS is relevant.",
            relation="proves",
            rationale="Overstrong relation must be rejected.",
            source_quote_refs=[quote_ref],
            yyyymmdd="20260509",
        )
