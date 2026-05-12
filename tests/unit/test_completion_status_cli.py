"""Hisys completion status CLI tests.

Traceability: HISYS-T-024, HISYS-CON-010..012, HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path


def test_completion_status_reports_gaps_gates_and_validation_state(tmp_path: Path, capsys) -> None:
    from hisys.cli.main import main

    date = "20260512"
    evidence_report_dir = tmp_path / "reports" / "run-summaries" / date
    evidence_report_dir.mkdir(parents=True)
    evidence_report_dir.joinpath("investment-evidence-package-report.json").write_text(
        json.dumps(
            {
                "schema_id": "hisys.investment_evidence_package_report",
                "package_ref": "data/evidence-packages/20260512/PKG-INV-SOURCE-SP500-001.json",
                "external_call_made": False,
                "mutation_performed": False,
            }
        ),
        encoding="utf-8",
    )
    investment_dir = tmp_path / "runtime-boundary" / "investment-decisions" / date
    investment_dir.mkdir(parents=True)
    investment_dir.joinpath("investment-decision-packet-report.json").write_text(
        json.dumps(
            {
                "schema_id": "hisys.investment_decision_packet_report",
                "workflow": "investment_decision_dry_run",
                "fixture_backend_used": False,
                "external_call_made": False,
                "mutation_performed": False,
                "execution_authorized": False,
                "publication_or_live_action_approved": False,
            }
        ),
        encoding="utf-8",
    )

    result = main(
        [
            "completion-status",
            "--instance",
            str(tmp_path),
            "--date",
            date,
            "--validation",
            "focused=passed",
            "--validation",
            "full=passed",
            "--format",
            "json",
        ]
    )

    assert result == 0
    report = json.loads(capsys.readouterr().out)
    assert report["schema_id"] == "hisys.completion_status_report"
    assert report["overall_status"] == "gated_release_candidate"
    assert report["validation"]["focused"] == "passed"
    assert report["validation"]["full"] == "passed"
    components = {component["component_id"]: component for component in report["components"]}
    assert components["investment_source_e2e"]["status"] == "complete"
    assert components["investment_dry_run_boundary"]["status"] == "complete"
    assert components["live_external_action"]["status"] == "gated"
    assert any(gate["gate_id"] == "high_impact_confirm_gate" for gate in report["gates"])
    persisted = evidence_report_dir / "hisys-completion-status.json"
    assert persisted.exists()
    assert json.loads(persisted.read_text(encoding="utf-8"))["overall_status"] == "gated_release_candidate"
