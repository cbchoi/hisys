"""CLI tests for conditional claim coverage gate construction.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.cli.main import main
from hisys.connectors.claim_evidence_summary import ClaimEvidenceSummaryRecord


def _write_summary(root: Path, *, claim_id: str) -> str:
    summary_dir = root / "runtime-boundary" / "source-connectors" / "20260509"
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary = ClaimEvidenceSummaryRecord(
        summary_id=f"SUMMARY-HISYS-REQ-LIVE-K-CLI-001-{claim_id}",
        request_id="HISYS-REQ-LIVE-K-CLI-001",
        claim_id=claim_id,
        claim_text=f"Major recommendation claim {claim_id}",
        claim_evidence_ledger_refs=[
            f"runtime-boundary/source-connectors/20260509/claim-evidence-ledger-LEDGER-{claim_id}.json"
        ],
        support_count=1,
        contradict_count=0,
        needs_evidence_count=0,
        evidence_balance="supported",
        advisory_confidence="medium",
        interpretation_summary="Advisory summary only; does not prove novelty.",
        policy_refs=["HISYS-T-024", "HISYS-CON-010"],
    )
    path = summary_dir / f"claim-evidence-summary-{summary.summary_id}.json"
    path.write_text(summary.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return str(path.relative_to(root))


def test_build_claim_coverage_gate_cli_writes_report_without_external_call(tmp_path: Path, capsys) -> None:
    summary_ref = _write_summary(tmp_path, claim_id="CLAIM-CLI-001")

    result = main(
        [
            "build-claim-coverage-gate",
            "--instance",
            str(tmp_path),
            "--date",
            "20260509",
            "--request-id",
            "HISYS-REQ-LIVE-K-CLI-001",
            "--required-claim-id",
            "CLAIM-CLI-001",
            "--required-claim-id",
            "CLAIM-CLI-002",
            "--claim-evidence-summary-ref",
            summary_ref,
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "claim coverage gate" in captured.out
    report_path = tmp_path / "reports" / "run-summaries" / "20260509" / "claim-coverage-gate-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "completed"
    assert report["coverage_status"] == "needs_more_claim_evidence"
    assert report["gate_count"] == 1
    assert report["external_call_made"] is False
    assert report["mutation_performed"] is False
    gate_ref = report["claim_coverage_gate_refs"][0]
    gate = json.loads((tmp_path / gate_ref).read_text(encoding="utf-8"))
    assert gate["covered_claim_ids"] == ["CLAIM-CLI-001"]
    assert gate["uncovered_claim_ids"] == ["CLAIM-CLI-002"]
    assert gate["conditional_manuscript_language_only"] is True
    assert gate["does_not_approve_publication_ready_claims"] is True
