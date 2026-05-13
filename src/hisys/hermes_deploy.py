from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_HERMES_TOOL_ROOT = Path.home() / ".hermes" / "tools" / "hisys"


def deploy_hisys_to_hermes(
    *,
    source_root: Path,
    target_root: Path = DEFAULT_HERMES_TOOL_ROOT,
    channel_id: str | None = None,
    channel_name: str | None = None,
    force: bool = False,
) -> dict[str, object]:
    """Deploy a controlled Hisys tool wrapper under a Hermes tool directory.

    The deployment is intentionally CLI-first: it does not mutate Hermes config.
    Instead it writes an executable wrapper, manifest, and channel config snippet
    that an operator can review and paste into ``~/.hermes/config.yaml``.
    """

    source_root = source_root.expanduser().resolve()
    target_root = target_root.expanduser().resolve()
    manifest_path = target_root / "manifest.json"
    if target_root.exists() and not force:
        return {
            "status": "blocked",
            "reason": "target_exists_use_force",
            "target_root": str(target_root),
            "manifest": str(manifest_path),
        }

    staging_root = target_root.parent / f".{target_root.name}.staging-{uuid.uuid4().hex}"
    backup_root = target_root.parent / f".{target_root.name}.backup-{uuid.uuid4().hex}"
    try:
        _write_deployment_tree(
            staging_root=staging_root,
            target_root=target_root,
            source_root=source_root,
            channel_id=channel_id,
            channel_name=channel_name,
        )
        _install_staged_tree(staging_root=staging_root, target_root=target_root, backup_root=backup_root)
    except Exception:
        if staging_root.exists():
            shutil.rmtree(staging_root, ignore_errors=True)
        if backup_root.exists() and not target_root.exists():
            os.replace(backup_root, target_root)
        raise
    finally:
        if backup_root.exists():
            shutil.rmtree(backup_root, ignore_errors=True)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {"status": "deployed", **manifest}


def _write_deployment_tree(
    *,
    staging_root: Path,
    target_root: Path,
    source_root: Path,
    channel_id: str | None,
    channel_name: str | None,
) -> None:
    bin_dir = staging_root / "bin"
    config_dir = staging_root / "config"
    staged_runtime_dir = staging_root / "runtime"
    docs_dir = staging_root / "docs"
    releases_dir = staging_root / "releases"
    release_id = _release_id(source_root)
    staged_release_dir = releases_dir / release_id
    staged_snapshot_root = staged_release_dir / "source"
    deployed_source_root = target_root / "releases" / "current" / "source"
    for directory in (bin_dir, config_dir, staged_runtime_dir, docs_dir, releases_dir):
        directory.mkdir(parents=True, exist_ok=True)
    _preserve_existing_releases(target_root=target_root, releases_dir=releases_dir)
    _copy_source_snapshot(source_root=source_root, snapshot_root=staged_snapshot_root)
    current_link = releases_dir / "current"
    os.symlink(release_id, current_link)

    wrapper_path = target_root / "bin" / "hisys"
    staged_wrapper_path = bin_dir / "hisys"
    staged_wrapper_path.write_text(_render_wrapper(deployed_source_root), encoding="utf-8")
    staged_wrapper_path.chmod(staged_wrapper_path.stat().st_mode | 0o755)

    profile_source = source_root / "examples" / "instance" / "config" / "profiles" / "public-browser.yaml"
    profile_target = target_root / "config" / "public-browser.yaml"
    staged_profile_target = config_dir / "public-browser.yaml"
    if profile_source.exists():
        shutil.copy2(profile_source, staged_profile_target)
    else:
        staged_profile_target.write_text(_default_public_profile(), encoding="utf-8")

    channel_prompt_path = target_root / "channel-prompt.md"
    (staging_root / "channel-prompt.md").write_text(
        _render_channel_prompt(source_root=deployed_source_root, target_root=target_root, channel_name=channel_name),
        encoding="utf-8",
    )
    snippet_path = target_root / "hermes-channel-snippet.yaml"
    (staging_root / "hermes-channel-snippet.yaml").write_text(
        _render_channel_snippet(
            source_root=deployed_source_root,
            target_root=target_root,
            channel_id=channel_id,
            channel_name=channel_name,
        ),
        encoding="utf-8",
    )
    (staging_root / "README.md").write_text(_render_readme(target_root=target_root, source_root=deployed_source_root), encoding="utf-8")

    manifest = {
        "schema_id": "hisys.hermes_tool_deployment",
        "schema_version": "0.1.0",
        "tool_name": "hisys",
        "deployed_at": datetime.now(timezone.utc).isoformat(),
        "deployment_mode": "immutable_snapshot",
        "release_id": release_id,
        "source_commit": _git_commit(source_root),
        "upstream_source_root": str(source_root),
        "source_root": str(deployed_source_root),
        "target_root": str(target_root),
        "wrapper": str(wrapper_path),
        "public_browser_profile": str(profile_target),
        "runtime_root": str(target_root / "runtime"),
        "channel_id": channel_id,
        "channel_name": channel_name,
        "config_snippet": str(snippet_path),
        "channel_prompt": str(channel_prompt_path),
        "safety_boundary": {
            "cli_first": True,
            "read_only_browser_default": True,
            "mutation_performed": False,
            "publication_or_live_action_approved": False,
            "human_approval_required_for_consequential_use": True,
            "forbidden_actions": [
                "login",
                "credential_use",
                "form_submit",
                "upload",
                "purchase",
                "post",
                "mutation",
                "access_control_bypass",
                "captcha_bypass",
                "proxy_rotation",
            ],
        },
    }
    (staging_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (staged_release_dir / "deployment-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _preserve_existing_releases(*, target_root: Path, releases_dir: Path) -> None:
    existing_releases = target_root / "releases"
    if not existing_releases.exists():
        return
    for child in existing_releases.iterdir():
        if child.name == "current":
            continue
        destination = releases_dir / child.name
        if child.is_dir() and not destination.exists():
            shutil.copytree(child, destination, symlinks=True)
    manifest_path = target_root / "manifest.json"
    current_link = existing_releases / "current"
    if manifest_path.exists() and current_link.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            current_release_id = current_link.readlink().name if current_link.is_symlink() else manifest.get("release_id")
        except Exception:
            return
        if isinstance(current_release_id, str) and current_release_id:
            release_manifest = releases_dir / current_release_id / "deployment-manifest.json"
            if release_manifest.parent.exists() and not release_manifest.exists():
                release_manifest.write_text(
                    json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )


def _install_staged_tree(*, staging_root: Path, target_root: Path, backup_root: Path) -> None:
    target_root.parent.mkdir(parents=True, exist_ok=True)
    if target_root.exists():
        os.replace(target_root, backup_root)
    os.replace(staging_root, target_root)


def _release_id(source_root: Path) -> str:
    commit = _git_commit(source_root)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if commit:
        return f"{timestamp}-{commit[:12]}-{uuid.uuid4().hex[:8]}"
    return f"{timestamp}-{uuid.uuid4().hex[:12]}"


def _git_commit(source_root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=source_root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except Exception:
        return None
    return completed.stdout.strip() or None


def _copy_source_snapshot(*, source_root: Path, snapshot_root: Path) -> None:
    def ignore(directory: str, names: list[str]) -> set[str]:
        ignored = {
            ".git",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            ".tox",
            ".venv",
            "__pycache__",
            "dist",
            "build",
            "uv.lock",
        }
        return {name for name in names if name in ignored or name.endswith(".pyc")}

    shutil.copytree(source_root, snapshot_root, ignore=ignore)


def _render_wrapper(source_root: Path) -> str:
    return f"""#!/usr/bin/env bash
set -euo pipefail
HISYS_SOURCE_ROOT={sh_quote(str(source_root))}
cd "$HISYS_SOURCE_ROOT"
if command -v uv >/dev/null 2>&1; then
  unset VIRTUAL_ENV
  exec uv run --project "$HISYS_SOURCE_ROOT" --extra browser python -m hisys.cli.main "$@"
fi
export PYTHONPATH="$HISYS_SOURCE_ROOT/src${{PYTHONPATH:+:$PYTHONPATH}}"
exec python3 -m hisys.cli.main "$@"
"""


def _render_channel_prompt(*, source_root: Path, target_root: Path, channel_name: str | None) -> str:
    label = channel_name or "Hisys governed investigation channel"
    return f"""# {label}

This Discord channel/thread is for Hisys governed investigation and Hisys-as-Hermes-tool development.

Working directory: {source_root}
Hisys source repo: {source_root}
Hermes tool deployment root: {target_root}
Hisys wrapper: {target_root / 'bin' / 'hisys'}
Default runtime root: {target_root / 'runtime'}
Public browser profile: {target_root / 'config' / 'public-browser.yaml'}

Use Hisys as a CLI-first governed evidence tool for Hermes:

- Hermes plans and synthesizes.
- Hisys investigates, records artifacts, checks evidence sufficiency, and runs Chief Editor/DARS/final gates.
- Humans approve consequential action.

Required boundaries:

- use read-only browser mode by default;
- run readiness before live browser runs;
- no login, credential use, form submit, upload, purchase, post, mutation, proxy rotation, CAPTCHA bypass, or access-control bypass;
- report request_id, artifact paths, pages_collected, final_decision, blockers, and no-publication/no-mutation status;
- classify access-denied/empty pages as source-access/evidence-quality limitations unless actual cyber-abuse behavior occurred.

Load the `hisys-cli-tool` skill for Hisys tasks.
"""


def _render_channel_snippet(*, source_root: Path, target_root: Path, channel_id: str | None, channel_name: str | None) -> str:
    channel = channel_id or "<DISCORD_CHANNEL_OR_THREAD_ID>"
    label = channel_name or "Hisys governed investigation channel"
    return f"""# Paste/reconcile this under `discord:` in ~/.hermes/config.yaml, then run:
#   hermes config check
#   hermes gateway restart

free_response_channels:
  - '{channel}'

channel_prompts:
  '{channel}': |
    {label}.
    Working directory: {source_root}
    Hisys source repo: {source_root}
    Hermes Hisys tool root: {target_root}
    Hisys wrapper: {target_root / 'bin' / 'hisys'}
    Default Hisys runtime root: {target_root / 'runtime'}
    Public browser profile: {target_root / 'config' / 'public-browser.yaml'}
    Use Hisys as a CLI-first governed evidence tool. Load the hisys-cli-tool skill.
    Preserve read-only/no-login/no-credential/no-mutation/no-bypass boundaries.
    Report request_id, artifact refs, final_decision, blockers, and human-reviewed-use limits.

channel_skill_bindings:
  - id: '{channel}'
    skills:
      - hisys-cli-tool
      - systematic-debugging
      - test-driven-development
"""


def get_hermes_deployment_status(*, target_root: Path) -> dict[str, Any]:
    target_root = target_root.expanduser().resolve()
    manifest_path = target_root / "manifest.json"
    wrapper_path = target_root / "bin" / "hisys"
    releases_root = target_root / "releases"
    current_link = releases_root / "current"
    if not manifest_path.exists():
        return {
            "schema_id": "hisys.hermes_tool_deployment_status",
            "schema_version": "0.1.0",
            "status": "missing",
            "target_root": str(target_root),
            "safe_to_use": False,
            "rollback_available": False,
            "available_release_ids": [],
        }
    manifest = _read_json(manifest_path)
    current_release_id = _current_release_id(current_link) or manifest.get("release_id")
    available_release_ids = _available_release_ids(releases_root)
    wrapper_text = wrapper_path.read_text(encoding="utf-8") if wrapper_path.exists() else ""
    upstream_source_root = str(manifest.get("upstream_source_root") or "")
    expected_source = str(target_root / "releases" / "current" / "source")
    wrapper_points_to_snapshot = expected_source in wrapper_text
    wrapper_references_live_source = bool(upstream_source_root and upstream_source_root in wrapper_text)
    safety = manifest.get("safety_boundary") if isinstance(manifest.get("safety_boundary"), dict) else {}
    safety_ok = (
        manifest.get("deployment_mode") == "immutable_snapshot"
        and safety.get("cli_first") is True
        and safety.get("read_only_browser_default") is True
        and safety.get("human_approval_required_for_consequential_use") is True
        and safety.get("mutation_performed") is False
        and safety.get("publication_or_live_action_approved") is False
    )
    safe_to_use = bool(
        wrapper_path.exists()
        and current_release_id
        and (target_root / "releases" / str(current_release_id) / "source").exists()
        and wrapper_points_to_snapshot
        and not wrapper_references_live_source
        and safety_ok
    )
    return {
        "schema_id": "hisys.hermes_tool_deployment_status",
        "schema_version": "0.1.0",
        "status": "deployed" if safe_to_use else "unsafe",
        "deployment_mode": manifest.get("deployment_mode"),
        "target_root": str(target_root),
        "current_release_id": current_release_id,
        "available_release_ids": available_release_ids,
        "source_commit": manifest.get("source_commit"),
        "source_root": manifest.get("source_root"),
        "upstream_source_root": manifest.get("upstream_source_root"),
        "wrapper": str(wrapper_path),
        "wrapper_exists": wrapper_path.exists(),
        "wrapper_points_to_snapshot": wrapper_points_to_snapshot,
        "wrapper_references_live_source": wrapper_references_live_source,
        "rollback_available": len([r for r in available_release_ids if r != current_release_id]) > 0,
        "safe_to_use": safe_to_use,
        "manifest": str(manifest_path),
    }


def rollback_hisys_hermes_tool(
    *,
    target_root: Path,
    to_release: str | None = None,
    previous: bool = False,
) -> dict[str, Any]:
    target_root = target_root.expanduser().resolve()
    releases_root = target_root / "releases"
    current_link = releases_root / "current"
    current_release_id = _current_release_id(current_link)
    available = _available_release_ids(releases_root)
    if not available or not current_release_id:
        return {"status": "blocked", "reason": "no_release_available", "target_root": str(target_root)}
    target_release = to_release
    if previous:
        candidates = [release_id for release_id in available if release_id != current_release_id]
        target_release = candidates[-1] if candidates else None
    if not target_release:
        return {"status": "blocked", "reason": "target_release_required", "target_root": str(target_root)}
    if target_release not in available:
        return {
            "status": "blocked",
            "reason": "release_not_found",
            "target_root": str(target_root),
            "requested_release_id": target_release,
            "available_release_ids": available,
        }
    tmp_link = releases_root / f".current.rollback-{uuid.uuid4().hex}"
    os.symlink(target_release, tmp_link)
    os.replace(tmp_link, current_link)
    manifest = _manifest_for_release(target_root=target_root, release_id=target_release)
    manifest["release_id"] = target_release
    manifest["source_root"] = str(target_root / "releases" / "current" / "source")
    manifest["target_root"] = str(target_root)
    manifest["wrapper"] = str(target_root / "bin" / "hisys")
    manifest["runtime_root"] = str(target_root / "runtime")
    manifest["rollback"] = {
        "rolled_back_at": datetime.now(timezone.utc).isoformat(),
        "from_release_id": current_release_id,
        "to_release_id": target_release,
        "action_taken": "current_release_pointer_updated",
        "external_call_made": False,
        "mutation_scope": "local_hermes_tool_release_pointer",
    }
    (target_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    status = get_hermes_deployment_status(target_root=target_root)
    return {
        "status": "rolled_back",
        "previous_release_id": current_release_id,
        "current_release_id": target_release,
        "target_root": str(target_root),
        "deployment_status": status,
    }


def build_hermes_deploy_report(
    *,
    target_root: Path,
    validations: dict[str, str] | None = None,
    output: Path | None = None,
) -> dict[str, Any]:
    status = get_hermes_deployment_status(target_root=target_root)
    report = {
        "schema_id": "hisys.hermes_tool_deploy_report",
        "schema_version": "0.1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "deployment_status": status,
        "source_commit": status.get("source_commit"),
        "release_id": status.get("current_release_id"),
        "verification": validations or {},
        "promotion_allowed": False,
        "human_approval_required_for_host_install": True,
        "external_call_made": False,
        "mutation_performed": False,
        "publication_or_live_action_approved": False,
    }
    if output is not None:
        output = output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _current_release_id(current_link: Path) -> str | None:
    if not current_link.exists():
        return None
    if current_link.is_symlink():
        return current_link.readlink().name
    return None


def _available_release_ids(releases_root: Path) -> list[str]:
    if not releases_root.exists():
        return []
    return sorted(child.name for child in releases_root.iterdir() if child.is_dir() and child.name != "current")


def _manifest_for_release(*, target_root: Path, release_id: str) -> dict[str, Any]:
    release_manifest = target_root / "releases" / release_id / "deployment-manifest.json"
    if release_manifest.exists():
        return _read_json(release_manifest)
    manifest_path = target_root / "manifest.json"
    manifest = _read_json(manifest_path) if manifest_path.exists() else {}
    manifest.setdefault("schema_id", "hisys.hermes_tool_deployment")
    manifest.setdefault("schema_version", "0.1.0")
    manifest.setdefault("tool_name", "hisys")
    manifest.setdefault("deployment_mode", "immutable_snapshot")
    return manifest


def _render_readme(*, target_root: Path, source_root: Path) -> str:
    return f"""# Hisys Hermes Tool Deployment

This directory is the controlled Hermes-side deployment for Hisys.

- Source repo: `{source_root}`
- Wrapper: `{target_root / 'bin' / 'hisys'}`
- Runtime root: `{target_root / 'runtime'}`
- Public browser profile: `{target_root / 'config' / 'public-browser.yaml'}`
- Hermes config snippet: `{target_root / 'hermes-channel-snippet.yaml'}`

Example:

```bash
{target_root / 'bin' / 'hisys'} validate-public-browser-profile \\
  --profile {target_root / 'config' / 'public-browser.yaml'}
```

For live browser runs, use readiness first and keep Hisys boundaries: no login,
credentials, mutation, publication, or access-control bypass.
"""


def _default_public_profile() -> str:
    return """profile_id: public-browser-beta
live_network_enabled: true
connector_id: playwright_read_only
mode: read_only
external_call_allowed: true
domain_decision_policy: orchestrator_decided
allow_credentials: false
allow_mutation: false
fixture_mode_publicly_exposed: false
experimental_transports_enabled: false
transport_kind: playwright_live
manual_smoke_env_var: HISYS_ALLOW_BROWSER_SMOKE
max_source_urls: 10
max_follow_links_per_source: 3
navigation_timeout_ms: 20000
allowed_url_schemes:
  - https
  - http
forbidden_actions:
  - login
  - credential_use
  - form_submit
  - upload
  - purchase
  - post
  - mutation
  - access_control_bypass
"""


def sh_quote(value: str) -> str:
    return "'" + value.replace("'", "'\\''") + "'"
