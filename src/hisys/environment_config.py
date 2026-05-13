"""Host-local Hisys environment config helpers.

The environment config records where Hisys-related stores and vaults live on a
specific host. It is separate from the deployed-wrapper runtime config and from
the evidence store write-policy config.

Traceability: HISYS-CON-010..012, HISYS-CON-022..023, Evidence-Store-A.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


SCHEMA_ID = "hisys.environment_config"
SCHEMA_VERSION = "0.1.0"
DEFAULT_ENVIRONMENT_CONFIG = Path("/home/cbchoi/.config/hisys/environment.yaml")


def _p(path: str | Path) -> str:
    return str(Path(path).expanduser())


def _write_policy() -> dict[str, Any]:
    return {
        "raw_evidence": "forbidden",
        "curated_projection": "approval_required",
        "default_enabled": False,
    }


def build_environment_config(
    *,
    host_id: str,
    hisys_tool_root: str | Path,
    hisys_source_repo: str | Path,
    evidence_store_root: str | Path,
    evidence_store_config: str | Path,
    personal_vault_root: str | Path,
    lab_vault_root: str | Path,
) -> dict[str, Any]:
    """Build the host-local Hisys environment registry document."""

    return {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "host_id": host_id,
        "paths": {
            "hisys_tool_root": _p(hisys_tool_root),
            "hisys_source_repo": _p(hisys_source_repo),
        },
        "stores": {
            "evidence": {
                "id": "hisys-evidence-store",
                "root": _p(evidence_store_root),
                "config": _p(evidence_store_config),
            }
        },
        "vaults": {
            "personal": {
                "id": "cbchoi-me",
                "kind": "obsidian",
                "root": _p(personal_vault_root),
                "write_policy": _write_policy(),
            },
            "lab": {
                "id": "sysailab-obsidian",
                "kind": "obsidian",
                "root": _p(lab_vault_root),
                "write_policy": _write_policy(),
            },
        },
        "projection_targets": {
            "stone_candidates": {
                "default_store": "evidence",
                "personal_vault_enabled": False,
            },
            "approved_stones": {
                "default_store": "evidence",
                "personal_vault_enabled": False,
                "require_human_approval": True,
            },
        },
        "safety": {
            "code_repo_is_not_evidence_store": True,
            "evidence_repo_is_not_personal_vault": True,
            "raw_evidence_vault_write_allowed": False,
            "external_call_made": False,
            "vault_write_attempted": False,
        },
    }


def init_environment_config(
    *,
    config_path: str | Path,
    host_id: str,
    hisys_tool_root: str | Path,
    hisys_source_repo: str | Path,
    evidence_store_root: str | Path,
    evidence_store_config: str | Path,
    personal_vault_root: str | Path,
    lab_vault_root: str | Path,
) -> dict[str, Any]:
    config_file = Path(config_path).expanduser()
    config_file.parent.mkdir(parents=True, exist_ok=True)
    document = build_environment_config(
        host_id=host_id,
        hisys_tool_root=hisys_tool_root,
        hisys_source_repo=hisys_source_repo,
        evidence_store_root=evidence_store_root,
        evidence_store_config=evidence_store_config,
        personal_vault_root=personal_vault_root,
        lab_vault_root=lab_vault_root,
    )
    config_file.write_text(yaml.safe_dump(document, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return {
        "schema_id": "hisys.environment_config.init_report",
        "schema_version": SCHEMA_VERSION,
        "config_path": str(config_file),
        "host_id": host_id,
        "mutation_performed": True,
        "external_call_made": False,
        "vault_write_attempted": False,
        "safe_to_use": True,
    }


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("environment config must be a YAML mapping")
    return data


def _path_equal_or_nested(path: str | Path | None, other: str | Path | None) -> bool:
    if not path or not other:
        return False
    left = Path(path).expanduser().resolve(strict=False)
    right = Path(other).expanduser().resolve(strict=False)
    return left == right or right in left.parents or left in right.parents


def environment_config_status(config_path: str | Path) -> dict[str, Any]:
    config_file = Path(config_path).expanduser()
    issues: list[str] = []
    if not config_file.exists():
        return {
            "schema_id": "hisys.environment_config.status_report",
            "schema_version": SCHEMA_VERSION,
            "config_path": str(config_file),
            "exists": False,
            "safe_to_use": False,
            "issues": ["environment_config_missing"],
            "external_call_made": False,
            "vault_write_attempted": False,
            "mutation_performed": False,
        }

    data = _load_yaml(config_file)
    if data.get("schema_id") != SCHEMA_ID:
        issues.append("schema_id_invalid")

    paths = data.get("paths") if isinstance(data.get("paths"), dict) else {}
    stores = data.get("stores") if isinstance(data.get("stores"), dict) else {}
    evidence = stores.get("evidence") if isinstance(stores.get("evidence"), dict) else {}
    vaults = data.get("vaults") if isinstance(data.get("vaults"), dict) else {}
    personal = vaults.get("personal") if isinstance(vaults.get("personal"), dict) else {}
    lab = vaults.get("lab") if isinstance(vaults.get("lab"), dict) else {}
    projections = data.get("projection_targets") if isinstance(data.get("projection_targets"), dict) else {}
    approved_stones = projections.get("approved_stones") if isinstance(projections.get("approved_stones"), dict) else {}

    required_paths = [
        ("paths.hisys_tool_root", paths.get("hisys_tool_root")),
        ("paths.hisys_source_repo", paths.get("hisys_source_repo")),
        ("stores.evidence.root", evidence.get("root")),
        ("stores.evidence.config", evidence.get("config")),
        ("vaults.personal.root", personal.get("root")),
        ("vaults.lab.root", lab.get("root")),
    ]
    for code, value in required_paths:
        if not value:
            issues.append(f"missing_{code}")

    evidence_root = evidence.get("root")
    personal_root = personal.get("root")
    lab_root = lab.get("root")
    source_repo = paths.get("hisys_source_repo")
    tool_root = paths.get("hisys_tool_root")
    if _path_equal_or_nested(evidence_root, personal_root):
        issues.append("evidence_store_points_to_personal_vault")
    if _path_equal_or_nested(evidence_root, lab_root):
        issues.append("evidence_store_points_to_lab_vault")
    if _path_equal_or_nested(evidence_root, source_repo):
        issues.append("evidence_store_points_to_source_repo")
    if _path_equal_or_nested(evidence_root, tool_root):
        issues.append("evidence_store_points_to_tool_root")

    for vault_name, vault in (("personal", personal), ("lab", lab)):
        policy = vault.get("write_policy") if isinstance(vault.get("write_policy"), dict) else {}
        if policy.get("raw_evidence") != "forbidden":
            issues.append(f"{vault_name}_vault_raw_evidence_not_forbidden")
        if policy.get("curated_projection") != "approval_required":
            issues.append(f"{vault_name}_vault_projection_not_approval_required")
        if policy.get("default_enabled") is not False:
            issues.append(f"{vault_name}_vault_default_write_enabled")

    if approved_stones.get("personal_vault_enabled") is True and approved_stones.get("require_human_approval") is not True:
        issues.append("personal_vault_projection_enabled_without_human_approval")

    return {
        "schema_id": "hisys.environment_config.status_report",
        "schema_version": SCHEMA_VERSION,
        "config_path": str(config_file),
        "exists": True,
        "safe_to_use": not issues,
        "issues": issues,
        "host_id": data.get("host_id"),
        "paths": paths,
        "stores": stores,
        "vaults": vaults,
        "projection_targets": projections,
        "external_call_made": False,
        "vault_write_attempted": False,
        "mutation_performed": False,
    }
