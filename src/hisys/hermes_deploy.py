from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path


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


def _install_staged_tree(*, staging_root: Path, target_root: Path, backup_root: Path) -> None:
    target_root.parent.mkdir(parents=True, exist_ok=True)
    if target_root.exists():
        os.replace(target_root, backup_root)
    os.replace(staging_root, target_root)


def _release_id(source_root: Path) -> str:
    commit = _git_commit(source_root)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if commit:
        return f"{timestamp}-{commit[:12]}"
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
