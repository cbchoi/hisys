"""Tests for Hisys host environment config and vault target registry.

Traceability: HISYS-CON-010..012, HISYS-CON-022..023, Evidence-Store-A.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from hisys.environment_config import environment_config_status, init_environment_config


def test_environment_config_init_records_vault_locations_without_enabling_raw_writes(tmp_path: Path) -> None:
    config_path = tmp_path / "environment.yaml"
    report = init_environment_config(
        config_path=config_path,
        host_id="test-host",
        hisys_tool_root=tmp_path / "tool" / "hisys",
        hisys_source_repo=tmp_path / "repo" / "hisys",
        evidence_store_root=tmp_path / "research" / "hisys-evidence-store",
        evidence_store_config=tmp_path / "store.yaml",
        personal_vault_root=tmp_path / "me",
        lab_vault_root=tmp_path / "obsidian",
    )

    assert report["schema_id"] == "hisys.environment_config.init_report"
    assert report["config_path"] == str(config_path)
    assert report["mutation_performed"] is True
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert data["schema_id"] == "hisys.environment_config"
    assert data["host_id"] == "test-host"
    assert data["paths"]["hisys_tool_root"] == str(tmp_path / "tool" / "hisys")
    assert data["paths"]["hisys_source_repo"] == str(tmp_path / "repo" / "hisys")
    assert data["stores"]["evidence"]["root"] == str(tmp_path / "research" / "hisys-evidence-store")
    assert data["stores"]["evidence"]["config"] == str(tmp_path / "store.yaml")
    assert data["vaults"]["personal"]["root"] == str(tmp_path / "me")
    assert data["vaults"]["lab"]["root"] == str(tmp_path / "obsidian")
    assert data["vaults"]["personal"]["write_policy"]["raw_evidence"] == "forbidden"
    assert data["vaults"]["personal"]["write_policy"]["curated_projection"] == "approval_required"
    assert data["vaults"]["personal"]["write_policy"]["default_enabled"] is False
    assert data["projection_targets"]["approved_stones"]["personal_vault_enabled"] is False
    assert data["projection_targets"]["approved_stones"]["require_human_approval"] is True


def test_environment_config_status_blocks_me_vault_as_evidence_store(tmp_path: Path) -> None:
    config_path = tmp_path / "environment.yaml"
    bad = {
        "schema_id": "hisys.environment_config",
        "schema_version": "0.1.0",
        "host_id": "test-host",
        "paths": {
            "hisys_tool_root": str(tmp_path / "tool" / "hisys"),
            "hisys_source_repo": str(tmp_path / "repo" / "hisys"),
        },
        "stores": {
            "evidence": {
                "id": "hisys-evidence-store",
                "root": str(tmp_path / "me"),
                "config": str(tmp_path / "store.yaml"),
            }
        },
        "vaults": {
            "personal": {"id": "cbchoi-me", "kind": "obsidian", "root": str(tmp_path / "me"), "write_policy": {"raw_evidence": "forbidden", "curated_projection": "approval_required", "default_enabled": False}},
            "lab": {"id": "sysailab-obsidian", "kind": "obsidian", "root": str(tmp_path / "obsidian"), "write_policy": {"raw_evidence": "forbidden", "curated_projection": "approval_required", "default_enabled": False}},
        },
        "projection_targets": {"approved_stones": {"personal_vault_enabled": False, "require_human_approval": True}},
    }
    config_path.write_text(yaml.safe_dump(bad, sort_keys=False), encoding="utf-8")

    report = environment_config_status(config_path)

    assert report["schema_id"] == "hisys.environment_config.status_report"
    assert report["safe_to_use"] is False
    assert "evidence_store_points_to_personal_vault" in report["issues"]
    assert report["external_call_made"] is False
    assert report["vault_write_attempted"] is False


def test_environment_config_status_requires_projection_gate_for_personal_vault(tmp_path: Path) -> None:
    config_path = tmp_path / "environment.yaml"
    init_environment_config(
        config_path=config_path,
        host_id="test-host",
        hisys_tool_root=tmp_path / "tool" / "hisys",
        hisys_source_repo=tmp_path / "repo" / "hisys",
        evidence_store_root=tmp_path / "research" / "hisys-evidence-store",
        evidence_store_config=tmp_path / "store.yaml",
        personal_vault_root=tmp_path / "me",
        lab_vault_root=tmp_path / "obsidian",
    )
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    data["projection_targets"]["approved_stones"]["personal_vault_enabled"] = True
    data["projection_targets"]["approved_stones"]["require_human_approval"] = False
    config_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    report = environment_config_status(config_path)

    assert report["safe_to_use"] is False
    assert "personal_vault_projection_enabled_without_human_approval" in report["issues"]


def test_environment_config_cli_init_and_status_emit_json(tmp_path: Path, capsys) -> None:
    from hisys.cli.main import main

    config_path = tmp_path / "environment.yaml"
    result = main([
        "environment-init",
        "--config", str(config_path),
        "--host-id", "test-host",
        "--hisys-tool-root", str(tmp_path / "tool" / "hisys"),
        "--hisys-source-repo", str(tmp_path / "repo" / "hisys"),
        "--evidence-store-root", str(tmp_path / "research" / "hisys-evidence-store"),
        "--evidence-store-config", str(tmp_path / "store.yaml"),
        "--personal-vault-root", str(tmp_path / "me"),
        "--lab-vault-root", str(tmp_path / "obsidian"),
        "--format", "json",
    ])
    assert result == 0
    init_report = json.loads(capsys.readouterr().out)
    assert init_report["config_path"] == str(config_path)

    result = main(["environment-status", "--config", str(config_path), "--format", "json"])
    assert result == 0
    status = json.loads(capsys.readouterr().out)
    assert status["safe_to_use"] is True
    assert status["vaults"]["personal"]["root"] == str(tmp_path / "me")
    assert status["stores"]["evidence"]["root"] == str(tmp_path / "research" / "hisys-evidence-store")
