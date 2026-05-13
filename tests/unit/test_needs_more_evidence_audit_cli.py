"""Needs-more-evidence audit CLI tests.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.cli.main import main


def test_audit_needs_more_evidence_counts_reason_patterns(tmp_path: Path, capsys):
    proposal_dir = tmp_path / "runtime-boundary/pass-contract-proposals/20260513"
    proposal_dir.mkdir(parents=True)
    for idx, reason in enumerate(["adapter_missing", "adapter_missing", "domain_contract_missing"]):
        (proposal_dir / f"proposal-{idx}.json").write_text(json.dumps({"dominant_failure_mode": reason, "domain": "product_architecture", "question_type": "architecture_choice"}), encoding="utf-8")

    result = main(["audit-needs-more-evidence", "--instance", str(tmp_path), "--date", "20260513", "--format", "json"])

    assert result == 0
    output = json.loads(capsys.readouterr().out)
    assert output["dominant_reasons"][0] == {"reason": "adapter_missing", "count": 2}
    assert "propose_pass_contract" in output["recommended_next_actions"]
