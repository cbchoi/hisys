"""CLI tests for controlled recommendation claim registry construction.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.cli.main import main


def test_build_recommendation_claim_registry_cli_writes_refs_and_required_claim_ids(tmp_path: Path, capsys) -> None:
    result = main(
        [
            "build-recommendation-claim-registry",
            "--instance",
            str(tmp_path),
            "--date",
            "20260509",
            "--request-id",
            "REQ-REG-CLI-001",
            "--recommendation-text",
            "Recommend a conditional research direction and evaluation scenario.",
            "--claim-text",
            "Self-organizing Dynamic Structure DEVS is the recommended research direction.",
            "--claim-text",
            "Evaluation scenarios should demonstrate topology/behavior co-evolution.",
        ]
    )

    out = capsys.readouterr().out
    assert result == 0
    assert "recommendation claim registry" in out
    assert "external_call_made: false" in out
    report = json.loads(
        (tmp_path / "reports" / "run-summaries" / "20260509" / "recommendation-claim-registry-report.json").read_text(
            encoding="utf-8"
        )
    )
    assert report["recommendation_claim_registry_refs"]
    assert report["required_claim_ids"] == [
        "CLAIM-REQ-REG-CLI-001-001",
        "CLAIM-REQ-REG-CLI-001-002",
    ]
    assert report["feeds_live_k_coverage_gates"] is True
    assert report["external_call_made"] is False
    registry = json.loads((tmp_path / report["recommendation_claim_registry_refs"][0]).read_text(encoding="utf-8"))
    assert registry["required_claim_ids"] == report["required_claim_ids"]
    assert registry["conditional_manuscript_language_only"] is True
