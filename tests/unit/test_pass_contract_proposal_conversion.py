"""Pass-contract proposal conversion tests.

Traceability: HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001, HISYS-T-024.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.cli.main import main
from hisys.contracts.pass_registry import candidate_from_proposal


def _proposal() -> dict:
    return {
        "proposal_id": "CONTRACT-PROP-PRODUCT-ARCHITECTURE-ARCHITECTURE-CHOICE-ADAPTER-MISSING",
        "domain": "product_architecture",
        "question_type": "architecture_choice",
        "candidate_contract": {
            "contract_id": "product_architecture_architecture_choice_v0_1_candidate",
            "minimum_evidence": {"artifact_refs_required": True},
            "blocked_if": ["no_traceable_artifact_refs"],
            "promotion_gate": "human_reviewed_traceable_change",
        },
    }


def test_candidate_from_proposal_is_inactive_and_not_auto_promoted():
    candidate = candidate_from_proposal(_proposal())
    assert candidate.status == "candidate"
    assert candidate.active is False
    assert candidate.automatic_promotion_allowed is False


def test_convert_pass_contract_proposal_writes_candidate(tmp_path: Path, capsys):
    proposal_path = tmp_path / "runtime-boundary/pass-contract-proposals/20260513/proposal.json"
    proposal_path.parent.mkdir(parents=True)
    proposal_path.write_text(json.dumps(_proposal()), encoding="utf-8")

    result = main(["convert-pass-contract-proposal", "--instance", str(tmp_path), "--date", "20260513", "--proposal-ref", "runtime-boundary/pass-contract-proposals/20260513/proposal.json", "--format", "json"])

    assert result == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "candidate"
    assert output["automatic_promotion_allowed"] is False
    assert (tmp_path / output["candidate_ref"]).exists()
