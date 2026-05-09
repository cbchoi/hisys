"""CLI tests for advisory claim evidence summary construction.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.cli.main import main
from hisys.connectors.claim_evidence_ledger import ClaimEvidenceLedgerRecord


def _write_ledger(root: Path) -> str:
    ledger_dir = root / "runtime-boundary" / "source-connectors" / "20260509"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    ledger = ClaimEvidenceLedgerRecord(
        ledger_id="LEDGER-HISYS-REQ-LIVE-J-CLI-001-CLAIM-CLI-001-001",
        request_id="HISYS-REQ-LIVE-J-CLI-001",
        claim_id="CLAIM-CLI-001",
        claim_text="Dynamic Structure DEVS supports topology-changing simulation.",
        relation="support",
        rationale="The source quote supports topology-change relevance.",
        source_quote_ref="runtime-boundary/source-connectors/20260509/source-quote-QUOTE-HISYS-REQ-LIVE-J-CLI-001-001.json",
        quote_id="QUOTE-HISYS-REQ-LIVE-J-CLI-001-001",
        quote_text="Dynamic structure models can alter structure during execution.",
        quote_sha256="d" * 64,
        policy_refs=["HISYS-T-024", "HISYS-CON-010"],
    )
    path = ledger_dir / f"claim-evidence-ledger-{ledger.ledger_id}.json"
    path.write_text(ledger.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return str(path.relative_to(root))


def test_build_claim_evidence_summary_cli_writes_report_without_external_call(tmp_path: Path, capsys) -> None:
    ledger_ref = _write_ledger(tmp_path)

    result = main(
        [
            "build-claim-evidence-summary",
            "--instance",
            str(tmp_path),
            "--date",
            "20260509",
            "--request-id",
            "HISYS-REQ-LIVE-J-CLI-001",
            "--claim-id",
            "CLAIM-CLI-001",
            "--claim-evidence-ledger-ref",
            ledger_ref,
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "claim evidence summary" in captured.out
    report_path = tmp_path / "reports" / "run-summaries" / "20260509" / "claim-evidence-summary-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "completed"
    assert report["claim_id"] == "CLAIM-CLI-001"
    assert report["summary_count"] == 1
    assert report["external_call_made"] is False
    assert report["mutation_performed"] is False
    summary_ref = report["claim_evidence_summary_refs"][0]
    summary = json.loads((tmp_path / summary_ref).read_text(encoding="utf-8"))
    assert summary["claim_evidence_ledger_refs"] == [ledger_ref]
    assert summary["evidence_balance"] == "supported"
    assert summary["advisory_confidence"] == "medium"
    assert summary["advisory_confidence_only"] is True
    assert summary["does_not_prove_novelty"] is True
