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
    assert plan["planned_handoffs"] == [
        {
            "from_connector_id": "doi_metadata_search",
            "to_connector_id": "open_access_pdf_fetch",
            "handoff_type": "pdf_candidate_plan_only",
            "artifact_kind": "pdf-candidate-plan",
            "pdf_downloaded": False,
            "external_call_made": False,
        }
    ]
    assert report["planned_handoff_count"] == 1


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


def test_smoke_source_connector_pdf_dry_run_requires_open_access_license_without_network(tmp_path: Path) -> None:
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
            "HISYS-REQ-LIVE-D-001",
            "--connector-id",
            "open_access_pdf_fetch",
            "--source-url",
            "https://www.mdpi.com/fixture/open-access.pdf",
            "--license-signal",
            "unknown",
            "--dry-run",
        ]
    )

    assert result == 0
    report_artifact = tmp_path / "reports" / "run-summaries" / "20260509" / "source-connector-smoke-report.json"
    report = json.loads(report_artifact.read_text(encoding="utf-8"))
    assert report["connector_id"] == "open_access_pdf_fetch"
    assert report["status"] == "blocked"
    assert report["reason_code"] == "pdf_license_not_open_access"
    assert report["external_call_made"] is False
    assert report["source_evidence_refs"] == []


def test_smoke_source_connector_pdf_manual_live_requires_env_without_network(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("HISYS_ALLOW_LIVE_PDF_SMOKE", raising=False)

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
            "HISYS-REQ-LIVE-D-002",
            "--connector-id",
            "open_access_pdf_fetch",
            "--source-url",
            "https://www.mdpi.com/fixture/open-access.pdf",
            "--license-signal",
            "open_access",
            "--approval-ref",
            "APPROVAL-PDF-SMOKE-001",
        ]
    )

    assert result == 2
    report_artifact = tmp_path / "reports" / "run-summaries" / "20260509" / "source-connector-smoke-report.json"
    report = json.loads(report_artifact.read_text(encoding="utf-8"))
    assert report["connector_id"] == "open_access_pdf_fetch"
    assert report["reason_code"] == "manual_smoke_env_missing"
    assert report["external_call_made"] is False


def test_smoke_source_connector_pdf_manual_live_uses_fixture_transport_after_gates(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HISYS_ALLOW_LIVE_PDF_SMOKE", "1")
    config_path = tmp_path / "source-connectors-enabled.yaml"
    config_path.write_text(
        Path("examples/instance/config/source-connectors.yaml")
        .read_text(encoding="utf-8")
        .replace("live_network_enabled: false", "live_network_enabled: true", 1)
        .replace("enabled: false\n    mode: read_only\n    external_call_allowed: false", "enabled: true\n    mode: read_only\n    external_call_allowed: true", 1)
        .replace("enabled: false\n    mode: read_only\n    external_call_allowed: false", "enabled: true\n    mode: read_only\n    external_call_allowed: true", 1)
        .replace("enabled: false\n    mode: read_only\n    external_call_allowed: false", "enabled: true\n    mode: read_only\n    external_call_allowed: true", 1),
        encoding="utf-8",
    )
    fixture = tmp_path / "manual-smoke.pdf"
    fixture.write_bytes(b"%PDF-1.7\nApproved manual smoke bytes.\n%%EOF\n")

    result = main(
        [
            "smoke-source-connector",
            "--instance",
            str(tmp_path),
            "--config",
            str(config_path),
            "--date",
            "20260509",
            "--request-id",
            "HISYS-REQ-LIVE-F-CLI-001",
            "--connector-id",
            "open_access_pdf_fetch",
            "--source-url",
            "https://mdpi.com/fixture/open-access.pdf",
            "--license-signal",
            "open_access",
            "--approval-ref",
            "APPROVAL-PDF-SMOKE-F-001",
            "--transport-fixture-pdf",
            str(fixture),
        ]
    )

    assert result == 0
    report_artifact = tmp_path / "reports" / "run-summaries" / "20260509" / "source-connector-smoke-report.json"
    report = json.loads(report_artifact.read_text(encoding="utf-8"))
    assert report["status"] == "completed"
    assert report["reason_code"] == "manual_pdf_smoke_completed"
    assert report["external_call_made"] is True
    assert report["source_evidence_refs"]
    access_ref = tmp_path / report["source_evidence_refs"][0]
    assert json.loads(access_ref.read_text(encoding="utf-8"))["pdf_downloaded"] is True


def test_plan_pdf_candidates_writes_candidate_plan_without_fetching_pdf(tmp_path: Path, capsys) -> None:
    metadata_path = tmp_path / "doi-metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "message": {
                    "DOI": "10.0000/hisys.fixture.formalism",
                    "license": [{"URL": "https://creativecommons.org/licenses/by/4.0/"}],
                    "link": [{"URL": "https://www.mdpi.com/fixture/formalism.pdf", "content-type": "application/pdf"}],
                }
            }
        ),
        encoding="utf-8",
    )

    result = main(
        [
            "plan-pdf-candidates",
            "--instance",
            str(tmp_path),
            "--metadata",
            str(metadata_path),
            "--date",
            "20260509",
            "--request-id",
            "HISYS-REQ-LIVE-E-CLI-001",
            "--metadata-access-ref",
            "runtime-boundary/source-connectors/20260509/source-access-ACCESS-HISYS-REQ-LIVE-E-CLI-001-doi_metadata_search.json",
            "--metadata-evidence-ref",
            "runtime-boundary/source-connectors/20260509/source-evidence-EVID-HISYS-REQ-LIVE-E-CLI-001-doi_metadata_search.json",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "pdf candidate plan" in captured.out
    plan_artifact = tmp_path / "runtime-boundary" / "source-connectors" / "20260509" / "pdf-candidate-plan-HISYS-REQ-LIVE-E-CLI-001.json"
    report_artifact = tmp_path / "reports" / "run-summaries" / "20260509" / "pdf-candidate-plan-report.json"
    assert plan_artifact.exists()
    assert report_artifact.exists()
    plan = json.loads(plan_artifact.read_text(encoding="utf-8"))
    report = json.loads(report_artifact.read_text(encoding="utf-8"))
    assert plan["candidate_plan_only"] is True
    assert plan["pdf_downloaded"] is False
    assert plan["external_call_made"] is False
    assert plan["candidates"][0]["connector_id"] == "open_access_pdf_fetch"
    assert report["plan_ref"] == str(plan_artifact.relative_to(tmp_path))
    assert report["candidate_count"] == 1
    assert report["pdf_downloaded"] is False
