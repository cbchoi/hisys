"""End-to-end governed pass-contract self-improvement flow.

Traceability: HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001, HISYS-T-024.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.cli.main import main


def test_governed_pass_contract_self_improvement_flow(tmp_path: Path):
    assert main([
        "propose-pass-contract",
        "--instance", str(tmp_path),
        "--date", "20260513",
        "--domain", "general",
        "--question-type", "architecture_choice",
        "--failure-mode", "adapter_missing",
        "--example-request-id", "REQ-ARCH-001",
        "--format", "json",
    ]) == 0
    proposal_report = json.loads((tmp_path / "reports/run-summaries/20260513/pass-contract-proposal-report.json").read_text(encoding="utf-8"))

    assert main([
        "convert-pass-contract-proposal",
        "--instance", str(tmp_path),
        "--date", "20260513",
        "--proposal-ref", proposal_report["proposal_ref"],
        "--format", "json",
    ]) == 0
    candidate_report = json.loads((tmp_path / "reports/run-summaries/20260513/pass-contract-candidate-report.json").read_text(encoding="utf-8"))

    evidence = tmp_path / "evidence-summary.json"
    evidence.write_text(json.dumps({
        "artifact_refs": ["evidence/architecture.md"],
        "alternative_count": 2,
        "claims_covered": True,
        "contradiction_checked": True,
        "dars_critique_refs": ["runtime-boundary/review.md"],
    }), encoding="utf-8")

    assert main([
        "evaluate-pass-contract",
        "--instance", str(tmp_path),
        "--date", "20260513",
        "--contract-ref", candidate_report["candidate_ref"],
        "--evidence-summary", str(evidence),
        "--format", "json",
    ]) == 0
    evaluation_report = json.loads((tmp_path / "reports/run-summaries/20260513/pass-contract-evaluation-report.json").read_text(encoding="utf-8"))
    assert evaluation_report["quality_gate"] == "passed"

    assert main([
        "request-pass-contract-review",
        "--instance", str(tmp_path),
        "--date", "20260513",
        "--candidate-ref", candidate_report["candidate_ref"],
        "--reviewer", "chief_editor",
        "--reviewer", "dars_devil",
        "--format", "json",
    ]) == 0
    review_report = json.loads((tmp_path / "reports/run-summaries/20260513/pass-contract-review-report.json").read_text(encoding="utf-8"))
    assert review_report["approval_authority_transferred"] is False

    assert main([
        "promote-pass-contract",
        "--instance", str(tmp_path),
        "--date", "20260513",
        "--candidate-ref", candidate_report["candidate_ref"],
        "--review-ref", review_report["review_ref"],
        "--validation-ref", "reports/run-summaries/20260513/pass-contract-evaluation-report.json",
        "--human-approval-ref", "APPROVAL-PASS-CONTRACT-20260513-001",
        "--format", "json",
    ]) == 0
    promotion_report = json.loads((tmp_path / "reports/run-summaries/20260513/pass-contract-promotion-report.json").read_text(encoding="utf-8"))
    active_registry = tmp_path / promotion_report["active_registry_ref"]
    assert active_registry.exists()

    request = tmp_path / "request.json"
    request.write_text(json.dumps({
        "request_id": "HISYS-REQ-PC-E2E-001",
        "producer_id": "hermes",
        "status": "submitted",
        "domain": "general",
        "objective": "Choose architecture with traceable alternatives.",
        "sources": [{"source_id": "SRC-ARCH-001", "source_type": "current_artifact", "ref": "fixture://arch", "access_mode": "read_only"}],
    }), encoding="utf-8")
    registry = tmp_path / "active-registry.json"
    registry.write_text(json.dumps({"contracts": [json.loads(active_registry.read_text(encoding="utf-8"))]}), encoding="utf-8")

    assert main([
        "investigate-domain",
        "--instance", str(tmp_path),
        "--request", str(request),
        "--date", "20260513",
        "--pass-contract-registry", str(registry),
        "--question-type", "architecture_choice",
        "--evidence-summary", str(evidence),
    ]) == 0
    tool_result = json.loads((tmp_path / "runtime-boundary/domain-investigation/general/20260513/hisys-tool-result-HISYS-REQ-PC-E2E-001.json").read_text(encoding="utf-8"))
    assert tool_result["status"] == "completed"
    assert tool_result["quality_gate"] == "passed"
    assert tool_result["external_call_made"] is False
    assert tool_result["mutation_performed"] is False
