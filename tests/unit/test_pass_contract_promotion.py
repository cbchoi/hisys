"""Human-approved pass-contract promotion tests.

Traceability: HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001, HISYS-T-024.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.cli.main import main


def _candidate(tmp_path: Path) -> str:
    ref = "runtime-boundary/pass-contract-candidates/20260513/product_architecture_architecture_choice_v0_1_candidate.json"
    path = tmp_path / ref
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({
        "contract_id": "product_architecture_architecture_choice_v0_1_candidate",
        "domain": "product_architecture",
        "question_type": "architecture_choice",
        "status": "candidate",
        "active": False,
        "version": "0.1.0",
        "minimum_evidence": {"artifact_refs_required": True},
        "blocked_if": ["no_traceable_artifact_refs"],
        "promotion_gate": "human_reviewed_traceable_change",
        "automatic_promotion_allowed": False,
        "external_call_made": False,
        "mutation_performed": False,
        "publication_or_live_action_approved": False,
    }), encoding="utf-8")
    return ref


def _review_and_validation(tmp_path: Path) -> tuple[str, str]:
    review_ref = "runtime-boundary/pass-contract-reviews/20260513/review.json"
    validation_ref = "reports/run-summaries/20260513/pass-contract-evaluation-report.json"
    (tmp_path / review_ref).parent.mkdir(parents=True)
    (tmp_path / validation_ref).parent.mkdir(parents=True)
    (tmp_path / review_ref).write_text(json.dumps({"promotion_allowed": False}), encoding="utf-8")
    (tmp_path / validation_ref).write_text(json.dumps({"quality_gate": "passed"}), encoding="utf-8")
    return review_ref, validation_ref


def test_promotion_requires_human_approval_ref(tmp_path: Path):
    candidate_ref = _candidate(tmp_path)
    review_ref, validation_ref = _review_and_validation(tmp_path)

    result = main(["promote-pass-contract", "--instance", str(tmp_path), "--date", "20260513", "--candidate-ref", candidate_ref, "--review-ref", review_ref, "--validation-ref", validation_ref, "--format", "json"])

    assert result == 2


def test_promotion_writes_active_registry_with_human_approval(tmp_path: Path, capsys):
    candidate_ref = _candidate(tmp_path)
    review_ref, validation_ref = _review_and_validation(tmp_path)

    result = main(["promote-pass-contract", "--instance", str(tmp_path), "--date", "20260513", "--candidate-ref", candidate_ref, "--review-ref", review_ref, "--validation-ref", validation_ref, "--human-approval-ref", "APPROVAL-001", "--format", "json"])

    assert result == 0
    output = json.loads(capsys.readouterr().out)
    active_path = tmp_path / output["active_registry_ref"]
    active = json.loads(active_path.read_text(encoding="utf-8"))
    assert active["status"] == "active"
    assert active["human_approval_ref"] == "APPROVAL-001"
    assert active["external_call_made"] is False
