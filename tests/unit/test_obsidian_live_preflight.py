"""Tests for Live-Obsidian-Config-I live vault preflight without writes.

Traceability: Live-Obsidian-Config-I, HISYS-FR-INV-001..006,
HISYS-T-024, HISYS-CON-010..012, HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.config.obsidian_live import build_live_vault_preflight_report


def test_live_vault_preflight_detects_vault_without_writing(tmp_path: Path) -> None:
    vault = tmp_path / "obsidian"
    vault.mkdir()
    (vault / ".obsidian").mkdir()
    (vault / ".git").mkdir()
    (vault / ".gitignore").write_text("91 Hisys/Live Research/**/attachments/pdf/\n", encoding="utf-8")
    before = sorted(path.relative_to(vault) for path in vault.rglob("*"))

    report = build_live_vault_preflight_report(vault_root=vault, request_id="REQ-PREFLIGHT-1")

    after = sorted(path.relative_to(vault) for path in vault.rglob("*"))
    assert after == before
    assert report["status"] == "ready_for_approval_package"
    assert report["vault_exists"] is True
    assert report["obsidian_config_detected"] is True
    assert report["git_repo_detected"] is True
    assert report["ignored_attachment_policy_detected"] is True
    assert report["write_probe_performed"] is False
    assert report["live_write_enabled"] is False
    assert report["mutation_performed"] is False


def test_live_vault_preflight_reports_missing_controls(tmp_path: Path) -> None:
    vault = tmp_path / "not-yet-vault"

    report = build_live_vault_preflight_report(vault_root=vault, request_id="REQ-PREFLIGHT-MISSING")

    assert report["status"] == "blocked"
    codes = {issue["code"] for issue in report["issues"]}
    assert "vault_root_missing" in codes
    assert "obsidian_config_missing" in codes
    assert report["live_write_enabled"] is False
    assert report["real_obsidian_vault_write_performed"] is False


def test_live_vault_preflight_cli_writes_runtime_report(tmp_path: Path, capsys) -> None:
    from hisys.cli.main import main

    instance = tmp_path / "instance"
    vault = tmp_path / "obsidian"
    vault.mkdir()
    (vault / ".obsidian").mkdir()
    (vault / ".git").mkdir()
    (vault / ".gitignore").write_text("91 Hisys/Live Research/**/attachments/pdf/\n", encoding="utf-8")

    exit_code = main(
        [
            "vault-live-preflight",
            "--instance",
            str(instance),
            "--date",
            "20260509",
            "--request-id",
            "REQ-PREFLIGHT-CLI",
            "--vault-root",
            str(vault),
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr().out
    assert "vault live preflight: ready_for_approval_package" in captured
    report_path = instance / "runtime-boundary" / "obsidian-live" / "20260509" / "vault-live-preflight-REQ-PREFLIGHT-CLI.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["live_write_enabled"] is False
    assert report["write_probe_performed"] is False
