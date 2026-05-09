"""CLI tests for source connector planning and fixture evidence.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.cli.main import main


def _write_domain_request(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "producer_id": "hermes",
                "status": "submitted",
                "request_id": "HISYS-REQ-LIVE-B-001",
                "domain": "research",
                "objective": "find research gap among formalisms for self-organizing structure",
                "sources": [
                    {
                        "source_id": "SRC-FORMALISM-FIXTURE-001",
                        "source_type": "fixture",
                        "ref": "fixture://formalism-gap",
                        "access_mode": "read_only",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def test_plan_source_connectors_writes_dry_run_plan_without_external_call(tmp_path: Path, capsys) -> None:
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)

    result = main(
        [
            "plan-source-connectors",
            "--instance",
            str(tmp_path),
            "--request",
            str(request_path),
            "--config",
            "examples/instance/config/source-connectors.yaml",
            "--date",
            "20260509",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "source connector plan" in captured.out
    plan_dir = tmp_path / "runtime-boundary" / "source-connectors" / "20260509"
    plan_artifact = plan_dir / "connector-plan-HISYS-REQ-LIVE-B-001.json"
    report_artifact = tmp_path / "reports" / "run-summaries" / "20260509" / "source-connector-plan-report.json"
    assert plan_artifact.exists()
    assert report_artifact.exists()

    plan = json.loads(plan_artifact.read_text(encoding="utf-8"))
    report = json.loads(report_artifact.read_text(encoding="utf-8"))
    assert plan["request_id"] == "HISYS-REQ-LIVE-B-001"
    assert "publisher_web_search" in plan["planned_connectors"]
    assert "doi_metadata_search" in plan["planned_connectors"]
    assert "open_access_pdf_fetch" in plan["planned_connectors"]
    assert "publisher_web_search" in plan["disabled_connectors"]
    assert plan["external_call_made"] is False
    assert plan["mutation_performed"] is False
    assert report["plan_ref"] == str(plan_artifact.relative_to(tmp_path))
    assert report["external_call_made"] is False
