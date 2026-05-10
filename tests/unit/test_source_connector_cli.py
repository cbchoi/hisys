"""CLI tests for source connector planning and fixture evidence.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import json
import subprocess
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
    assert report["pdf_downloaded"] is True
    assert report["transport_kind"] == "fixture_injected"
    assert report["source_access_refs"]
    assert report["source_evidence_refs"]
    access_ref = tmp_path / report["source_access_refs"][0]
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


def test_live_ideation_run_gates_doi_metadata_into_dars_and_chief_editor(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HISYS_ALLOW_LIVE_IDEATION", "1")
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)
    metadata_fixture = tmp_path / "crossref.json"
    metadata_fixture.write_text(
        json.dumps(
            {
                "message": {
                    "DOI": "10.0000/hisys.fixture.formalism",
                    "title": ["Dynamic Structure Formalism Fixture"],
                    "publisher": "Fixture Publisher",
                    "URL": "https://doi.org/10.0000/hisys.fixture.formalism",
                }
            }
        ),
        encoding="utf-8",
    )
    config_path = tmp_path / "source-connectors-enabled.yaml"
    config_path.write_text(
        Path("examples/instance/config/source-connectors.yaml")
        .read_text(encoding="utf-8")
        .replace("live_network_enabled: false", "live_network_enabled: true", 1)
        .replace(
            "  doi_metadata_search:\n    connector_id: doi_metadata_search\n    connector_type: metadata_search\n    enabled: false\n    mode: read_only\n    external_call_allowed: false",
            "  doi_metadata_search:\n    connector_id: doi_metadata_search\n    connector_type: metadata_search\n    enabled: true\n    mode: read_only\n    external_call_allowed: true",
            1,
        ),
        encoding="utf-8",
    )

    result = main(
        [
            "live-ideation-run",
            "--instance",
            str(tmp_path),
            "--request",
            str(request_path),
            "--config",
            str(config_path),
            "--date",
            "20260510",
            "--doi",
            "10.0000/hisys.fixture.formalism",
            "--approval-ref",
            "APPROVAL-LIVE-IDEATION-001",
            "--explicit-live-source-enable",
            "--metadata-fixture",
            str(metadata_fixture),
        ]
    )

    assert result == 0
    report = json.loads((tmp_path / "reports" / "run-summaries" / "20260510" / "live-ideation-run-report.json").read_text(encoding="utf-8"))
    assert report["status"] == "completed"
    assert report["external_call_made"] is True
    assert report["transport_kind"] == "fixture_injected"
    assert report["dars_chief_editor_pipeline_invoked"] is True
    decision = json.loads(
        (tmp_path / "runtime-boundary" / "chief-editor" / "research" / "20260510" / "research-recommendation-review-CEDEC-HISYS-REQ-LIVE-B-001.json").read_text(encoding="utf-8")
    )
    assert decision["source_validation_status"] == "fixture_source_evidence_present"
    assert any("doi_metadata_search" in ref for ref in decision["source_evidence_refs"])
    assert decision["dars_acceptance_decision"] == "accepted_as_conditions"


def test_live_ideation_run_blocks_without_explicit_live_enable(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HISYS_ALLOW_LIVE_IDEATION", "1")
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)

    result = main(
        [
            "live-ideation-run",
            "--instance",
            str(tmp_path),
            "--request",
            str(request_path),
            "--config",
            "examples/instance/config/source-connectors.yaml",
            "--date",
            "20260510",
            "--doi",
            "10.0000/hisys.fixture.formalism",
            "--approval-ref",
            "APPROVAL-LIVE-IDEATION-001",
        ]
    )

    assert result == 2
    report = json.loads((tmp_path / "reports" / "run-summaries" / "20260510" / "live-ideation-run-report.json").read_text(encoding="utf-8"))
    assert report["status"] == "blocked"
    assert report["reason_code"] == "explicit_live_source_enable_required"
    assert report["external_call_made"] is False


def test_live_ideation_persist_runs_ideation_vault_write_and_git_sync(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HISYS_ALLOW_LIVE_IDEATION", "1")
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)
    metadata_fixture = tmp_path / "crossref.json"
    metadata_fixture.write_text(
        json.dumps({"message": {"DOI": "10.0000/hisys.fixture.formalism", "title": ["Dynamic Structure Formalism Fixture"]}}),
        encoding="utf-8",
    )
    config_path = tmp_path / "source-connectors-enabled.yaml"
    config_path.write_text(
        Path("examples/instance/config/source-connectors.yaml")
        .read_text(encoding="utf-8")
        .replace("live_network_enabled: false", "live_network_enabled: true", 1)
        .replace(
            "  doi_metadata_search:\n    connector_id: doi_metadata_search\n    connector_type: metadata_search\n    enabled: false\n    mode: read_only\n    external_call_allowed: false",
            "  doi_metadata_search:\n    connector_id: doi_metadata_search\n    connector_type: metadata_search\n    enabled: true\n    mode: read_only\n    external_call_allowed: true",
            1,
        ),
        encoding="utf-8",
    )
    vault_root = tmp_path / "vault"
    remote_root = tmp_path / "remote.git"
    vault_root.mkdir()
    subprocess.run(["git", "init", "--bare", str(remote_root)], check=True, capture_output=True, text=True)
    subprocess.run(["git", "init", "-b", "main"], cwd=vault_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "hisys-test@example.invalid"], cwd=vault_root, check=True)
    subprocess.run(["git", "config", "user.name", "Hisys Test"], cwd=vault_root, check=True)
    subprocess.run(["git", "remote", "add", "origin", str(remote_root)], cwd=vault_root, check=True)

    result = main(
        [
            "live-ideation-persist",
            "--instance",
            str(tmp_path / "instance"),
            "--request",
            str(request_path),
            "--config",
            str(config_path),
            "--date",
            "20260510",
            "--doi",
            "10.0000/hisys.fixture.formalism",
            "--approval-ref",
            "APPROVAL-LIVE-PIPELINE-001",
            "--vault-root",
            str(vault_root),
            "--credential-ref",
            "env:HISYS_OBSIDIAN_GIT_SSH_KEY",
            "--explicit-live-source-enable",
            "--explicit-live-write-enable",
            "--explicit-live-git-enable",
            "--clean-git-status",
            "--metadata-fixture",
            str(metadata_fixture),
        ]
    )

    assert result == 0
    report = json.loads((tmp_path / "instance" / "reports" / "run-summaries" / "20260510" / "live-ideation-persist-report.json").read_text(encoding="utf-8"))
    assert report["status"] == "completed"
    assert report["external_call_made"] is True
    assert report["mutation_performed"] is True
    assert report["network_push_performed"] is False
    assert report["real_obsidian_vault_write_performed"] is False
    assert report["vault_refs"] == ["91 Hisys/Live Research/approved-ideation/live-ideation-HISYS-REQ-LIVE-B-001.json"]
    assert (vault_root / report["vault_refs"][0]).exists()
    assert subprocess.run(["git", "rev-parse", "--verify", "main"], cwd=remote_root, capture_output=True, text=True).returncode == 0


def test_live_ideation_persist_blocks_before_vault_write_without_write_enable(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HISYS_ALLOW_LIVE_IDEATION", "1")
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)
    metadata_fixture = tmp_path / "crossref.json"
    metadata_fixture.write_text(json.dumps({"message": {"DOI": "10.0000/hisys.fixture.formalism"}}), encoding="utf-8")
    config_path = tmp_path / "source-connectors-enabled.yaml"
    config_path.write_text(
        Path("examples/instance/config/source-connectors.yaml")
        .read_text(encoding="utf-8")
        .replace("live_network_enabled: false", "live_network_enabled: true", 1)
        .replace(
            "  doi_metadata_search:\n    connector_id: doi_metadata_search\n    connector_type: metadata_search\n    enabled: false\n    mode: read_only\n    external_call_allowed: false",
            "  doi_metadata_search:\n    connector_id: doi_metadata_search\n    connector_type: metadata_search\n    enabled: true\n    mode: read_only\n    external_call_allowed: true",
            1,
        ),
        encoding="utf-8",
    )

    result = main(
        [
            "live-ideation-persist",
            "--instance",
            str(tmp_path / "instance"),
            "--request",
            str(request_path),
            "--config",
            str(config_path),
            "--date",
            "20260510",
            "--doi",
            "10.0000/hisys.fixture.formalism",
            "--approval-ref",
            "APPROVAL-LIVE-PIPELINE-001",
            "--vault-root",
            str(tmp_path / "vault"),
            "--credential-ref",
            "env:HISYS_OBSIDIAN_GIT_SSH_KEY",
            "--explicit-live-source-enable",
            "--explicit-live-git-enable",
            "--clean-git-status",
            "--metadata-fixture",
            str(metadata_fixture),
        ]
    )

    assert result == 2
    report = json.loads((tmp_path / "instance" / "reports" / "run-summaries" / "20260510" / "live-ideation-persist-report.json").read_text(encoding="utf-8"))
    assert report["status"] == "blocked"
    assert report["reason_code"] == "live_apply_gate_not_satisfied"
    assert report["mutation_performed"] is False


def test_live_ideation_persist_accepts_standing_approval_policy(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HISYS_ALLOW_LIVE_IDEATION", "1")
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)
    metadata_fixture = tmp_path / "crossref.json"
    metadata_fixture.write_text(json.dumps({"message": {"DOI": "10.0000/hisys.fixture.formalism"}}), encoding="utf-8")
    config_path = tmp_path / "source-connectors-enabled.yaml"
    config_path.write_text(
        Path("examples/instance/config/source-connectors.yaml")
        .read_text(encoding="utf-8")
        .replace("live_network_enabled: false", "live_network_enabled: true", 1)
        .replace(
            "  doi_metadata_search:\n    connector_id: doi_metadata_search\n    connector_type: metadata_search\n    enabled: false\n    mode: read_only\n    external_call_allowed: false",
            "  doi_metadata_search:\n    connector_id: doi_metadata_search\n    connector_type: metadata_search\n    enabled: true\n    mode: read_only\n    external_call_allowed: true",
            1,
        ),
        encoding="utf-8",
    )
    vault_root = tmp_path / "vault"
    remote_root = tmp_path / "remote.git"
    vault_root.mkdir()
    subprocess.run(["git", "init", "--bare", str(remote_root)], check=True, capture_output=True, text=True)
    subprocess.run(["git", "init", "-b", "main"], cwd=vault_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "hisys-test@example.invalid"], cwd=vault_root, check=True)
    subprocess.run(["git", "config", "user.name", "Hisys Test"], cwd=vault_root, check=True)
    subprocess.run(["git", "remote", "add", "origin", str(remote_root)], cwd=vault_root, check=True)
    policy_path = tmp_path / "standing-approval.json"
    policy_path.write_text(
        json.dumps(
            {
                "schema_id": "hisys.live_ideation.standing_approval_policy",
                "status": "approved",
                "approval_ref": "STANDING-LIVE-IDEATION-001",
                "expires_on": "20261231",
                "capabilities": ["live_source_access", "live_vault_write", "obsidian_git_push"],
                "allowed_domains": ["research"],
                "allowed_vault_roots": [str(vault_root)],
                "allowed_remote_names": ["origin"],
                "allowed_branches": ["main"],
                "allowed_credential_refs": ["env:HISYS_OBSIDIAN_GIT_SSH_KEY"],
                "clean_git_status_required": True,
            }
        ),
        encoding="utf-8",
    )

    result = main(
        [
            "live-ideation-persist",
            "--instance",
            str(tmp_path / "instance"),
            "--request",
            str(request_path),
            "--config",
            str(config_path),
            "--date",
            "20260510",
            "--doi",
            "10.0000/hisys.fixture.formalism",
            "--vault-root",
            str(vault_root),
            "--credential-ref",
            "env:HISYS_OBSIDIAN_GIT_SSH_KEY",
            "--metadata-fixture",
            str(metadata_fixture),
            "--standing-approval-policy",
            str(policy_path),
        ]
    )

    assert result == 0
    report = json.loads((tmp_path / "instance" / "reports" / "run-summaries" / "20260510" / "live-ideation-persist-report.json").read_text(encoding="utf-8"))
    assert report["status"] == "completed"
    assert report["approval_ref"] == "STANDING-LIVE-IDEATION-001"
    assert report["standing_approval_applied"] is True
    assert report["mutation_performed"] is True
    assert (vault_root / report["vault_refs"][0]).exists()


def test_live_ideation_persist_blocks_standing_approval_outside_scope(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HISYS_ALLOW_LIVE_IDEATION", "1")
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)
    config_path = tmp_path / "source-connectors-enabled.yaml"
    config_path.write_text(Path("examples/instance/config/source-connectors.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    policy_path = tmp_path / "standing-approval.json"
    policy_path.write_text(
        json.dumps(
            {
                "status": "approved",
                "approval_ref": "STANDING-LIVE-IDEATION-001",
                "capabilities": ["live_source_access", "live_vault_write", "obsidian_git_push"],
                "allowed_domains": ["research"],
                "allowed_vault_roots": [str(tmp_path / "other-vault")],
            }
        ),
        encoding="utf-8",
    )

    result = main(
        [
            "live-ideation-persist",
            "--instance",
            str(tmp_path / "instance"),
            "--request",
            str(request_path),
            "--config",
            str(config_path),
            "--date",
            "20260510",
            "--doi",
            "10.0000/hisys.fixture.formalism",
            "--vault-root",
            str(tmp_path / "vault"),
            "--credential-ref",
            "env:HISYS_OBSIDIAN_GIT_SSH_KEY",
            "--standing-approval-policy",
            str(policy_path),
        ]
    )

    assert result == 2
    report = json.loads((tmp_path / "instance" / "reports" / "run-summaries" / "20260510" / "live-ideation-persist-report.json").read_text(encoding="utf-8"))
    assert report["status"] == "blocked"
    assert report["reason_code"] == "standing_approval_vault_root_not_allowed"
    assert report["standing_approval_applied"] is False


def test_live_ideation_persist_blocks_invalid_standing_approval_expiry(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HISYS_ALLOW_LIVE_IDEATION", "1")
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)
    config_path = tmp_path / "source-connectors-enabled.yaml"
    config_path.write_text(Path("examples/instance/config/source-connectors.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    policy_path = tmp_path / "standing-approval.json"
    policy_path.write_text(
        json.dumps(
            {
                "status": "approved",
                "approval_ref": "STANDING-LIVE-IDEATION-001",
                "expires_on": "2026-12-31",
                "capabilities": ["live_source_access", "live_vault_write", "obsidian_git_push"],
                "allowed_domains": ["research"],
                "allowed_vault_roots": [str(tmp_path / "vault")],
            }
        ),
        encoding="utf-8",
    )

    result = main(
        [
            "live-ideation-persist",
            "--instance",
            str(tmp_path / "instance"),
            "--request",
            str(request_path),
            "--config",
            str(config_path),
            "--date",
            "20260510",
            "--doi",
            "10.0000/hisys.fixture.formalism",
            "--vault-root",
            str(tmp_path / "vault"),
            "--credential-ref",
            "env:HISYS_OBSIDIAN_GIT_SSH_KEY",
            "--standing-approval-policy",
            str(policy_path),
        ]
    )

    assert result == 2
    report = json.loads((tmp_path / "instance" / "reports" / "run-summaries" / "20260510" / "live-ideation-persist-report.json").read_text(encoding="utf-8"))
    assert report["status"] == "blocked"
    assert report["reason_code"] == "standing_approval_expiry_invalid"
    assert report["external_call_made"] is False


def test_live_autonomy_run_executes_standing_approved_queue(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HISYS_ALLOW_LIVE_IDEATION", "1")
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)
    metadata_fixture = tmp_path / "crossref.json"
    metadata_fixture.write_text(json.dumps({"message": {"DOI": "10.0000/hisys.fixture.formalism"}}), encoding="utf-8")
    config_path = tmp_path / "source-connectors-enabled.yaml"
    config_path.write_text(
        Path("examples/instance/config/source-connectors.yaml")
        .read_text(encoding="utf-8")
        .replace("live_network_enabled: false", "live_network_enabled: true", 1)
        .replace(
            "  doi_metadata_search:\n    connector_id: doi_metadata_search\n    connector_type: metadata_search\n    enabled: false\n    mode: read_only\n    external_call_allowed: false",
            "  doi_metadata_search:\n    connector_id: doi_metadata_search\n    connector_type: metadata_search\n    enabled: true\n    mode: read_only\n    external_call_allowed: true",
            1,
        ),
        encoding="utf-8",
    )
    vault_root = tmp_path / "vault"
    remote_root = tmp_path / "remote.git"
    vault_root.mkdir()
    subprocess.run(["git", "init", "--bare", str(remote_root)], check=True, capture_output=True, text=True)
    subprocess.run(["git", "init", "-b", "main"], cwd=vault_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "hisys-test@example.invalid"], cwd=vault_root, check=True)
    subprocess.run(["git", "config", "user.name", "Hisys Test"], cwd=vault_root, check=True)
    subprocess.run(["git", "remote", "add", "origin", str(remote_root)], cwd=vault_root, check=True)
    policy_path = tmp_path / "standing-approval.json"
    policy_path.write_text(
        json.dumps(
            {
                "status": "approved",
                "approval_ref": "STANDING-LIVE-AUTONOMY-001",
                "expires_on": "20261231",
                "capabilities": ["live_source_access", "live_vault_write", "obsidian_git_push"],
                "allowed_domains": ["research"],
                "allowed_vault_roots": [str(vault_root)],
                "allowed_remote_names": ["origin"],
                "allowed_branches": ["main"],
                "allowed_credential_refs": ["env:HISYS_OBSIDIAN_GIT_SSH_KEY"],
                "clean_git_status_required": True,
            }
        ),
        encoding="utf-8",
    )
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(
        json.dumps(
            {
                "queue_id": "LIVE-AUTONOMY-Q-001",
                "entries": [
                    {
                        "entry_id": "formalism-gap-001",
                        "request_path": request_path.name,
                        "doi": "10.0000/hisys.fixture.formalism",
                        "metadata_fixture": metadata_fixture.name,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = main(
        [
            "live-autonomy-run",
            "--instance",
            str(tmp_path / "instance"),
            "--queue",
            str(queue_path),
            "--config",
            str(config_path),
            "--date",
            "20260510",
            "--vault-root",
            str(vault_root),
            "--credential-ref",
            "env:HISYS_OBSIDIAN_GIT_SSH_KEY",
            "--standing-approval-policy",
            str(policy_path),
            "--clean-git-status",
        ]
    )

    assert result == 0
    report = json.loads((tmp_path / "instance" / "reports" / "run-summaries" / "20260510" / "live-autonomy-run-report.json").read_text(encoding="utf-8"))
    assert report["status"] == "completed"
    assert report["entry_count"] == 1
    assert report["completed_count"] == 1
    assert report["blocked_count"] == 0
    assert report["mutation_performed"] is True
    assert report["results"][0]["status"] == "completed"
    assert report["results"][0]["pipeline_report_ref"].endswith("live-ideation-persist-report.json")
    assert subprocess.run(["git", "rev-parse", "--verify", "main"], cwd=remote_root, capture_output=True, text=True).returncode == 0

    second_result = main(
        [
            "live-autonomy-run",
            "--instance",
            str(tmp_path / "instance"),
            "--queue",
            str(queue_path),
            "--config",
            str(config_path),
            "--date",
            "20260510",
            "--vault-root",
            str(vault_root),
            "--credential-ref",
            "env:HISYS_OBSIDIAN_GIT_SSH_KEY",
            "--standing-approval-policy",
            str(policy_path),
            "--clean-git-status",
        ]
    )
    assert second_result == 0
    second_report = json.loads((tmp_path / "instance" / "reports" / "run-summaries" / "20260510" / "live-autonomy-run-report.json").read_text(encoding="utf-8"))
    assert second_report["completed_count"] == 0
    assert second_report["skipped_completed_count"] == 1
    assert second_report["results"][0]["status"] == "skipped_completed"
    ledger = json.loads((tmp_path / "instance" / second_report["ledger_ref"]).read_text(encoding="utf-8"))
    assert ledger["entries"]["formalism-gap-001"]["status"] == "completed"
    assert ledger["entries"]["formalism-gap-001"]["attempt_count"] == 1
    assert [state["state"] for state in ledger["entries"]["formalism-gap-001"]["state_history"]] == ["queued", "running", "completed", "queued", "skipped_completed"]
    watchdog = json.loads((tmp_path / "instance" / second_report["watchdog_report_ref"]).read_text(encoding="utf-8"))
    assert watchdog["scheduler_ready"] is True
    assert watchdog["health_status"] == "ok"
    assert watchdog["next_scheduler_action"] == "sleep"


def test_live_autonomy_run_skips_retry_exhausted_entries(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HISYS_ALLOW_LIVE_IDEATION", "1")
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(
        json.dumps(
            {
                "queue_id": "LIVE-AUTONOMY-Q-RETRY",
                "entries": [
                    {
                        "entry_id": "retry-exhausted-001",
                        "request_path": "missing-request.json",
                        "doi": "10.0000/hisys.fixture.formalism",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    config_path = tmp_path / "source-connectors.yaml"
    config_path.write_text(Path("examples/instance/config/source-connectors.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    policy_path = tmp_path / "standing-approval.json"
    policy_path.write_text(json.dumps({"status": "approved", "approval_ref": "STANDING-LIVE-AUTONOMY-RETRY"}), encoding="utf-8")
    ledger_path = tmp_path / "ledger.json"
    ledger_path.write_text(
        json.dumps(
            {
                "schema_id": "hisys.live_autonomy.queue_retry_ledger",
                "schema_version": "0.1.0",
                "queue_id": "LIVE-AUTONOMY-Q-RETRY",
                "date": "20260510",
                "entries": {
                    "retry-exhausted-001": {
                        "entry_id": "retry-exhausted-001",
                        "status": "blocked",
                        "reason_code": "live_ideation_stage_failed",
                        "attempt_count": 1,
                        "retry_eligible": True,
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    result = main(
        [
            "live-autonomy-run",
            "--instance",
            str(tmp_path / "instance"),
            "--queue",
            str(queue_path),
            "--config",
            str(config_path),
            "--date",
            "20260510",
            "--vault-root",
            str(tmp_path / "vault"),
            "--credential-ref",
            "env:HISYS_OBSIDIAN_GIT_SSH_KEY",
            "--standing-approval-policy",
            str(policy_path),
            "--ledger",
            str(ledger_path),
            "--max-retries",
            "1",
        ]
    )

    assert result == 0
    report = json.loads((tmp_path / "instance" / "reports" / "run-summaries" / "20260510" / "live-autonomy-run-report.json").read_text(encoding="utf-8"))
    assert report["completed_count"] == 0
    assert report["skipped_retry_exhausted_count"] == 1
    assert report["results"][0]["status"] == "skipped_retry_exhausted"
    assert report["results"][0]["attempt_count"] == 1
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert ledger["entries"]["retry-exhausted-001"]["current_state"] == "skipped_retry_exhausted"
    assert [state["state"] for state in ledger["entries"]["retry-exhausted-001"]["state_history"]][-2:] == ["queued", "skipped_retry_exhausted"]
    watchdog = json.loads((tmp_path / "instance" / report["watchdog_report_ref"]).read_text(encoding="utf-8"))
    assert watchdog["scheduler_ready"] is True
    assert watchdog["health_status"] == "ok"


def test_live_autonomy_tick_reports_idle_when_no_queues(tmp_path: Path) -> None:
    queue_dir = tmp_path / "queues"
    queue_dir.mkdir()
    config_path = tmp_path / "source-connectors.yaml"
    config_path.write_text(Path("examples/instance/config/source-connectors.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    policy_path = tmp_path / "standing-approval.json"
    policy_path.write_text(json.dumps({"status": "approved", "approval_ref": "STANDING-LIVE-SCHEDULER"}), encoding="utf-8")

    result = main(
        [
            "live-autonomy-tick",
            "--instance",
            str(tmp_path / "instance"),
            "--queue-dir",
            str(queue_dir),
            "--config",
            str(config_path),
            "--date",
            "20260510",
            "--vault-root",
            str(tmp_path / "vault"),
            "--credential-ref",
            "env:HISYS_OBSIDIAN_GIT_SSH_KEY",
            "--standing-approval-policy",
            str(policy_path),
        ]
    )

    assert result == 0
    report = json.loads((tmp_path / "instance" / "reports" / "run-summaries" / "20260510" / "live-autonomy-scheduler-tick-report.json").read_text(encoding="utf-8"))
    assert report["status"] == "idle"
    assert report["scheduler_ready"] is True
    assert report["discovered_queue_count"] == 0
    assert report["processed_queue_count"] == 0
    assert report["next_scheduler_action"] == "sleep"


def test_live_autonomy_tick_runs_queue_and_reports_attention(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HISYS_ALLOW_LIVE_IDEATION", "1")
    queue_dir = tmp_path / "queues"
    queue_dir.mkdir()
    queue_path = queue_dir / "queue.json"
    queue_path.write_text(
        json.dumps(
            {
                "queue_id": "LIVE-SCHEDULER-Q-001",
                "entries": [{"entry_id": "missing-input", "doi": "10.0000/hisys.fixture.formalism"}],
            }
        ),
        encoding="utf-8",
    )
    config_path = tmp_path / "source-connectors.yaml"
    config_path.write_text(Path("examples/instance/config/source-connectors.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    policy_path = tmp_path / "standing-approval.json"
    policy_path.write_text(json.dumps({"status": "approved", "approval_ref": "STANDING-LIVE-SCHEDULER"}), encoding="utf-8")

    result = main(
        [
            "live-autonomy-tick",
            "--instance",
            str(tmp_path / "instance"),
            "--queue-dir",
            str(queue_dir),
            "--config",
            str(config_path),
            "--date",
            "20260510",
            "--vault-root",
            str(tmp_path / "vault"),
            "--credential-ref",
            "env:HISYS_OBSIDIAN_GIT_SSH_KEY",
            "--standing-approval-policy",
            str(policy_path),
        ]
    )

    assert result == 2
    report = json.loads((tmp_path / "instance" / "reports" / "run-summaries" / "20260510" / "live-autonomy-scheduler-tick-report.json").read_text(encoding="utf-8"))
    assert report["status"] == "attention_required"
    assert report["processed_queue_count"] == 1
    assert report["attention_count"] == 1
    assert report["queue_results"][0]["status"] == "attention_required"
    assert report["queue_results"][0]["watchdog_report_ref"].endswith("live-autonomy-watchdog-report.json")
    watchdog = json.loads((tmp_path / "instance" / report["queue_results"][0]["watchdog_report_ref"]).read_text(encoding="utf-8"))
    assert watchdog["scheduler_ready"] is True
    assert watchdog["health_status"] == "attention_required"

    second_result = main(
        [
            "live-autonomy-tick",
            "--instance",
            str(tmp_path / "instance"),
            "--queue-dir",
            str(queue_dir),
            "--config",
            str(config_path),
            "--date",
            "20260510",
            "--vault-root",
            str(tmp_path / "vault"),
            "--credential-ref",
            "env:HISYS_OBSIDIAN_GIT_SSH_KEY",
            "--standing-approval-policy",
            str(policy_path),
        ]
    )
    assert second_result == 0
    second_report = json.loads((tmp_path / "instance" / "reports" / "run-summaries" / "20260510" / "live-autonomy-scheduler-tick-report.json").read_text(encoding="utf-8"))
    assert second_report["status"] == "completed"
    assert second_report["queue_results"][0]["blocked_count"] == 0
    second_run_report = json.loads((tmp_path / "instance" / second_report["queue_results"][0]["queue_run_report_ref"]).read_text(encoding="utf-8"))
    assert second_run_report["skipped_non_retryable_count"] == 1
    assert second_run_report["results"][0]["status"] == "skipped_non_retryable"


def test_live_autonomy_tick_namespaces_multiple_queue_reports(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HISYS_ALLOW_LIVE_IDEATION", "1")
    queue_dir = tmp_path / "queues"
    queue_dir.mkdir()
    for queue_id in ["LIVE-SCHEDULER-Q-A", "LIVE-SCHEDULER-Q-B"]:
        (queue_dir / f"{queue_id}.json").write_text(
            json.dumps({"queue_id": queue_id, "entries": [{"entry_id": f"{queue_id}-missing", "doi": "10.0000/hisys.fixture.formalism"}]}),
            encoding="utf-8",
        )
    config_path = tmp_path / "source-connectors.yaml"
    config_path.write_text(Path("examples/instance/config/source-connectors.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    policy_path = tmp_path / "standing-approval.json"
    policy_path.write_text(json.dumps({"status": "approved", "approval_ref": "STANDING-LIVE-SCHEDULER"}), encoding="utf-8")

    result = main(
        [
            "live-autonomy-tick",
            "--instance",
            str(tmp_path / "instance"),
            "--queue-dir",
            str(queue_dir),
            "--config",
            str(config_path),
            "--date",
            "20260510",
            "--vault-root",
            str(tmp_path / "vault"),
            "--credential-ref",
            "env:HISYS_OBSIDIAN_GIT_SSH_KEY",
            "--standing-approval-policy",
            str(policy_path),
            "--max-queues",
            "2",
        ]
    )

    assert result == 2
    report = json.loads((tmp_path / "instance" / "reports" / "run-summaries" / "20260510" / "live-autonomy-scheduler-tick-report.json").read_text(encoding="utf-8"))
    refs = [item["queue_run_report_ref"] for item in report["queue_results"]]
    assert len(refs) == 2
    assert len(set(refs)) == 2
    for ref in refs:
        assert (tmp_path / "instance" / ref).exists()
        run_report = json.loads((tmp_path / "instance" / ref).read_text(encoding="utf-8"))
        assert run_report["blocked_count"] == 1
        assert run_report["results"][0]["reason_code"] == "queue_entry_missing_request_or_doi"
