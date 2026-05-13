"""Pass-contract evaluation CLI tests.

Traceability: HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001, HISYS-T-024.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.cli.main import main


def test_evaluate_pass_contract_writes_local_report(tmp_path: Path, capsys):
    contract = tmp_path / "contract.json"
    contract.write_text(json.dumps({"contracts": [{
        "contract_id": "product_architecture_architecture_choice_v0_1_candidate",
        "domain": "product_architecture",
        "question_type": "architecture_choice",
        "status": "candidate",
        "version": "0.1.0",
        "minimum_evidence": {"artifact_refs_required": True, "alternative_set_required": True},
        "blocked_if": ["no_traceable_artifact_refs"],
        "promotion_gate": "human_reviewed_traceable_change"
    }]}), encoding="utf-8")
    evidence = tmp_path / "evidence.json"
    evidence.write_text(json.dumps({"artifact_refs": ["evidence/1"], "alternative_count": 2, "claims_covered": True}), encoding="utf-8")

    result = main(["evaluate-pass-contract", "--instance", str(tmp_path), "--date", "20260513", "--contract-ref", str(contract), "--evidence-summary", str(evidence), "--format", "json"])

    assert result == 0
    output = json.loads(capsys.readouterr().out)
    assert output["quality_gate"] == "passed"
    assert output["external_call_made"] is False
    assert (tmp_path / "reports/run-summaries/20260513/pass-contract-evaluation-report.json").exists()
