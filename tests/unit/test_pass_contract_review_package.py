"""Pass-contract advisory review package tests.

Traceability: HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001, HISYS-T-024.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.cli.main import main
from hisys.contracts.review_package import build_review_package


def test_review_package_never_transfers_approval_authority():
    package = build_review_package(candidate_ref="runtime-boundary/candidate.json", reviewers=["chief_editor", "dars_devil"])
    assert package["approval_authority_transferred"] is False
    assert package["promotion_allowed"] is False
    assert package["reviewers"] == ["chief_editor", "dars_devil"]


def test_request_pass_contract_review_writes_local_artifact(tmp_path: Path, capsys):
    candidate = tmp_path / "runtime-boundary/pass-contract-candidates/20260513/candidate.json"
    candidate.parent.mkdir(parents=True)
    candidate.write_text(json.dumps({"contract_id": "candidate", "status": "candidate"}), encoding="utf-8")

    result = main(["request-pass-contract-review", "--instance", str(tmp_path), "--date", "20260513", "--candidate-ref", "runtime-boundary/pass-contract-candidates/20260513/candidate.json", "--reviewer", "chief_editor", "--reviewer", "dars_devil", "--format", "json"])

    assert result == 0
    output = json.loads(capsys.readouterr().out)
    assert output["approval_authority_transferred"] is False
    assert (tmp_path / output["review_ref"]).exists()
