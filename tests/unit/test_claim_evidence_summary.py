"""Tests for advisory claim evidence balance summaries.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.connectors.claim_evidence_ledger import ClaimEvidenceLedgerRecord
from hisys.connectors.claim_evidence_summary import ClaimEvidenceSummaryBuilder


def _write_ledger(root: Path, *, relation: str, index: int = 1, claim_id: str = "CLAIM-001") -> str:
    ledger_dir = root / "runtime-boundary" / "source-connectors" / "20260509"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    ledger = ClaimEvidenceLedgerRecord(
        ledger_id=f"LEDGER-HISYS-REQ-LIVE-J-001-{claim_id}-{index:03d}",
        request_id="HISYS-REQ-LIVE-J-001",
        claim_id=claim_id,
        claim_text="Dynamic Structure DEVS is relevant to topology-changing simulation.",
        relation=relation,  # type: ignore[arg-type]
        rationale=f"Fixture rationale {relation}",
        source_quote_ref=f"runtime-boundary/source-connectors/20260509/source-quote-QUOTE-HISYS-REQ-LIVE-J-001-{index:03d}.json",
        quote_id=f"QUOTE-HISYS-REQ-LIVE-J-001-{index:03d}",
        quote_text="Dynamic structure models include structural change evidence.",
        quote_sha256="c" * 64,
        policy_refs=["HISYS-T-024", "HISYS-CON-010"],
    )
    path = ledger_dir / f"claim-evidence-ledger-{ledger.ledger_id}.json"
    path.write_text(ledger.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return str(path.relative_to(root))


def test_claim_evidence_summary_aggregates_balance_conservatively(tmp_path: Path) -> None:
    support_ref = _write_ledger(tmp_path, relation="support", index=1)
    needs_ref = _write_ledger(tmp_path, relation="needs_evidence", index=2)

    result = ClaimEvidenceSummaryBuilder(root=tmp_path).build(
        request_id="HISYS-REQ-LIVE-J-001",
        claim_id="CLAIM-001",
        claim_evidence_ledger_refs=[support_ref, needs_ref],
        yyyymmdd="20260509",
    )

    assert result.external_call_made is False
    assert result.mutation_performed is False
    assert len(result.claim_evidence_summary_refs) == 1
    summary_ref = result.claim_evidence_summary_refs[0]
    summary = json.loads((tmp_path / summary_ref).read_text(encoding="utf-8"))
    assert summary["claim_id"] == "CLAIM-001"
    assert summary["support_count"] == 1
    assert summary["contradict_count"] == 0
    assert summary["needs_evidence_count"] == 1
    assert summary["evidence_balance"] == "mixed_needs_more_evidence"
    assert summary["advisory_confidence"] == "low"
    assert summary["advisory_confidence_only"] is True
    assert summary["does_not_prove_novelty"] is True
    assert summary["claim_evidence_ledger_refs"] == [support_ref, needs_ref]
    assert summary["external_call_made"] is False
    assert summary["mutation_performed"] is False


def test_claim_evidence_summary_rejects_mismatched_claim_refs(tmp_path: Path) -> None:
    first_ref = _write_ledger(tmp_path, relation="support", index=1, claim_id="CLAIM-001")
    other_ref = _write_ledger(tmp_path, relation="support", index=2, claim_id="CLAIM-OTHER")

    with pytest.raises(ValueError, match="same claim_id"):
        ClaimEvidenceSummaryBuilder(root=tmp_path).build(
            request_id="HISYS-REQ-LIVE-J-001",
            claim_id="CLAIM-001",
            claim_evidence_ledger_refs=[first_ref, other_ref],
            yyyymmdd="20260509",
        )
