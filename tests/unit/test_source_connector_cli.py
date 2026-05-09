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


def test_smoke_source_connector_dry_run_blocks_without_external_call(tmp_path: Path, capsys) -> None:
    result = main(
        [
            "smoke-source-connector",
            "--instance",
            str(tmp_path),
            "--config",
            "examples/instance/config/source-connectors.yaml",
            "--date",
            "20260509",
            "--request-id",
            "HISYS-REQ-LIVE-C-001",
            "--connector-id",
            "doi_metadata_search",
            "--doi",
            "10.0000/hisys.fixture.formalism",
            "--dry-run",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "source connector smoke" in captured.out
    smoke_dir = tmp_path / "runtime-boundary" / "source-connectors" / "20260509"
    report_artifact = tmp_path / "reports" / "run-summaries" / "20260509" / "source-connector-smoke-report.json"
    dispatch_artifact = smoke_dir / "connector-dispatch-HISYS-REQ-LIVE-C-001-doi_metadata_search.json"
    assert dispatch_artifact.exists()
    assert report_artifact.exists()
    dispatch = json.loads(dispatch_artifact.read_text(encoding="utf-8"))
    report = json.loads(report_artifact.read_text(encoding="utf-8"))
    assert dispatch["decision"] == "blocked"
    assert dispatch["external_call_made"] is False
    assert dispatch["mutation_performed"] is False
    assert report["mode"] == "dry_run"
    assert report["external_call_made"] is False
    assert report["source_evidence_refs"] == []


def test_smoke_source_connector_requires_env_for_manual_live(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("HISYS_ALLOW_LIVE_SMOKE", raising=False)

    result = main(
        [
            "smoke-source-connector",
            "--instance",
            str(tmp_path),
            "--config",
            "examples/instance/config/source-connectors.yaml",
            "--date",
            "20260509",
            "--request-id",
            "HISYS-REQ-LIVE-C-002",
            "--connector-id",
            "doi_metadata_search",
            "--doi",
            "10.0000/hisys.fixture.formalism",
            "--approval-ref",
            "APPROVAL-LIVE-SMOKE-001",
        ]
    )

    assert result == 2
    report_artifact = tmp_path / "reports" / "run-summaries" / "20260509" / "source-connector-smoke-report.json"
    report = json.loads(report_artifact.read_text(encoding="utf-8"))
    assert report["status"] == "blocked"
    assert report["reason_code"] == "manual_smoke_env_missing"
    assert report["external_call_made"] is False
