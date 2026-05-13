"""CLI tests for self-improving pass-contract proposal artifacts.

Traceability: HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001, HISYS-T-024.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.cli.main import main


def test_propose_pass_contract_writes_governed_self_improvement_artifacts(tmp_path: Path, capsys):
    result = main(
        [
            "propose-pass-contract",
            "--instance",
            str(tmp_path),
            "--date",
            "20260513",
            "--domain",
            "product_architecture",
            "--question-type",
            "architecture_choice",
            "--failure-mode",
            "adapter_missing",
            "--example-request-id",
            "REQ-ARCH-001",
            "--example-request-id",
            "REQ-ARCH-002",
            "--format",
            "json",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "pass contract proposal" in captured.out
    report_path = tmp_path / "reports" / "run-summaries" / "20260513" / "pass-contract-proposal-report.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    proposal_ref = report["proposal_ref"]
    assert proposal_ref.startswith("runtime-boundary/pass-contract-proposals/20260513/")

    proposal_path = tmp_path / proposal_ref
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    assert proposal["schema_id"] == "hisys.pass_contract.proposal"
    assert proposal["status"] == "proposed_for_human_review"
    assert proposal["domain"] == "product_architecture"
    assert proposal["question_type"] == "architecture_choice"
    assert proposal["dominant_failure_mode"] == "adapter_missing"
    assert proposal["example_request_ids"] == ["REQ-ARCH-001", "REQ-ARCH-002"]
    assert proposal["automatic_promotion_allowed"] is False
    assert proposal["external_call_made"] is False
    assert proposal["mutation_performed"] is False
    assert proposal["publication_or_live_action_approved"] is False
    assert "adapter_missing" in proposal["needs_more_evidence_reason_taxonomy"]
    assert "domain_contract_missing" in proposal["needs_more_evidence_reason_taxonomy"]
    assert proposal["candidate_contract"]["promotion_gate"] == "human_reviewed_traceable_change"
    assert "tests/fixtures/pass-contracts/product_architecture_architecture_choice.yaml" in proposal["suggested_artifacts"]

    markdown_path = proposal_path.with_suffix(".md")
    assert markdown_path.exists()
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "Self-improvement boundary" in markdown
    assert "does not self-authorize lower standards" in markdown
