"""Domain investigation pass-contract integration tests.

Traceability: HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001, HISYS-T-024.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.cli.main import main


def _request(tmp_path: Path) -> Path:
    path = tmp_path / "request.json"
    path.write_text(json.dumps({
        "request_id": "HISYS-REQ-PC-001",
        "producer_id": "hermes",
        "status": "submitted",
        "domain": "general",
        "objective": "Choose architecture with traceable alternatives.",
        "sources": [{"source_id": "SRC-ARCH-001", "source_type": "current_artifact", "ref": "fixture://arch", "access_mode": "read_only"}]
    }), encoding="utf-8")
    return path


def _active_registry(tmp_path: Path) -> Path:
    path = tmp_path / "active-registry.json"
    path.write_text(json.dumps({"contracts": [{
        "contract_id": "product_architecture_architecture_choice_v0_1",
        "domain": "general",
        "question_type": "architecture_choice",
        "status": "active",
        "active": True,
        "version": "0.1.0",
        "human_approval_ref": "APPROVAL-001",
        "minimum_evidence": {"artifact_refs_required": True, "alternative_set_required": True},
        "blocked_if": ["no_traceable_artifact_refs"],
        "promotion_gate": "human_reviewed_traceable_change"
    }]}), encoding="utf-8")
    return path


def _evidence(tmp_path: Path) -> Path:
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps({"artifact_refs": ["evidence/1"], "alternative_count": 2, "claims_covered": True}), encoding="utf-8")
    return path


def test_domain_investigation_uses_active_pass_contract(tmp_path: Path, capsys):
    result = main(["investigate-domain", "--instance", str(tmp_path), "--request", str(_request(tmp_path)), "--date", "20260513", "--pass-contract-registry", str(_active_registry(tmp_path)), "--question-type", "architecture_choice", "--evidence-summary", str(_evidence(tmp_path))])

    assert result == 0
    assert "status: completed" in capsys.readouterr().out
    tool_result = tmp_path / "runtime-boundary/domain-investigation/general/20260513/hisys-tool-result-HISYS-REQ-PC-001.json"
    data = json.loads(tool_result.read_text(encoding="utf-8"))
    assert data["status"] == "completed"
    assert data["quality_gate"] == "passed"
