import json
from pathlib import Path

from hisys.cli.main import main


def _public_browser_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "source-connectors-enabled.yaml"
    config_path.write_text(
        """
default_mode: read_only
policy:
  live_network_enabled: true
  require_human_approval_for_external_call: true
  allow_credentials: false
  allow_mutation: false
  require_allowlist: true
  require_provenance_record: true
connectors:
  playwright_read_only:
    connector_id: playwright_read_only
    connector_type: playwright_read_only
    enabled: true
    mode: read_only
    external_call_allowed: true
    domain_decision_policy: orchestrator_decided
    requires_human_approval: true
    approval_policy_ref: POLICY-LIVE-RESEARCH-001
    allowed_domains:
      - example.org
    forbidden_actions:
      - login
      - credential_use
      - form_submit
      - upload
      - purchase
      - post
      - mutation
      - access_control_bypass
      - captcha_bypass
      - anti_bot_bypass
      - proxy_rotation
    output_schema: EvidencePackage
    manual_smoke_only: true
    manual_smoke_env_var: HISYS_ALLOW_BROWSER_SMOKE
    smoke_test_in_ci: false
""".lstrip(),
        encoding="utf-8",
    )
    return config_path


def test_public_browser_readiness_reports_ready_without_live_network_call(tmp_path: Path) -> None:
    result = main(
        [
            "public-browser-readiness",
            "--instance",
            str(tmp_path),
            "--config",
            str(_public_browser_config(tmp_path)),
            "--profile",
            "examples/instance/config/profiles/public-browser.yaml",
            "--date",
            "20260511",
        ]
    )

    assert result == 0
    report_path = tmp_path / "reports" / "run-summaries" / "20260511" / "public-browser-readiness-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["schema_id"] == "hisys.public_browser_readiness.report"
    assert report["status"] == "ready"
    assert report["profile_valid"] is True
    assert report["connector_ready"] is True
    assert report["playwright_importable"] in {True, False}
    assert report["external_call_made"] is False
    assert report["mutation_performed"] is False


def test_public_browser_readiness_blocks_fixture_only_config(tmp_path: Path) -> None:
    config_path = tmp_path / "source-connectors.yaml"
    config_path.write_text(Path("examples/instance/config/source-connectors.yaml").read_text(encoding="utf-8"), encoding="utf-8")

    result = main(
        [
            "public-browser-readiness",
            "--instance",
            str(tmp_path),
            "--config",
            str(config_path),
            "--profile",
            "examples/instance/config/profiles/public-browser.yaml",
            "--date",
            "20260511",
        ]
    )

    assert result == 2
    report = json.loads((tmp_path / "reports" / "run-summaries" / "20260511" / "public-browser-readiness-report.json").read_text(encoding="utf-8"))
    assert report["status"] == "blocked"
    assert "connector_not_enabled" in report["blockers"]
    assert "connector_external_call_not_allowed" in report["blockers"]
