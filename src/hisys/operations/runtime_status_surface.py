"""Local runtime status surface for operator-visible Hisys state.

Traceability: docs/plans/2026-05-19-runtime-status-surface-cli.md.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

SCHEMA_ID = "hisys.runtime_status_surface"
SCHEMA_VERSION = "0.1.0"
_SECRET_PATTERNS = (
    re.compile(r"(?i)(sk|api[_-]?key|token|secret|password|passwd|credential)[A-Za-z0-9_:=\-\.]{4,}"),
    re.compile(r"(?i)[A-Za-z0-9_\-]{12,}\.[A-Za-z0-9_\-]{12,}\.[A-Za-z0-9_\-]{12,}"),
)
_HOME_PATH_PATTERN = re.compile(r"/home/([^/\s]+)")


def redact_sensitive_value(value: Any) -> Any:
    """Redact credential-like values and private home usernames."""

    if value is None or isinstance(value, bool | int | float):
        return value
    if isinstance(value, list):
        return [redact_sensitive_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): redact_sensitive_value(item) for key, item in value.items()}

    text = str(value)
    redacted = text
    for pattern in _SECRET_PATTERNS:
        if pattern.search(redacted):
            return "[REDACTED]"
    return _HOME_PATH_PATTERN.sub("/home/[REDACTED]", redacted)


def collect_git_context(workdir: Path) -> dict[str, Any]:
    """Collect bounded local Git context; no network calls are made."""

    workdir = workdir.resolve()
    if not workdir.exists():
        return {"workdir": redact_sensitive_value(str(workdir)), "available": False, "reason": "workdir_missing"}

    def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=workdir,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )

    root_result = run_git(["rev-parse", "--show-toplevel"])
    if root_result.returncode != 0:
        return {"workdir": redact_sensitive_value(str(workdir)), "available": False, "reason": "not_git_repo"}

    branch_result = run_git(["branch", "--show-current"])
    status_result = run_git(["status", "--short", "--branch"])
    branch = branch_result.stdout.strip() or "detached"
    status_lines = [line for line in status_result.stdout.splitlines() if line]
    header = status_lines[0] if status_lines else ""
    ahead, behind = _parse_ahead_behind(header)
    dirty = any(not line.startswith("## ") for line in status_lines)
    return {
        "workdir": redact_sensitive_value(str(workdir)),
        "repo_root": redact_sensitive_value(root_result.stdout.strip()),
        "available": True,
        "branch": branch,
        "dirty": dirty,
        "ahead": ahead,
        "behind": behind,
        "status_header": header,
    }


def _parse_ahead_behind(status_header: str) -> tuple[int, int]:
    ahead_match = re.search(r"ahead (\d+)", status_header)
    behind_match = re.search(r"behind (\d+)", status_header)
    return int(ahead_match.group(1)) if ahead_match else 0, int(behind_match.group(1)) if behind_match else 0


def build_runtime_status_packet(
    *,
    instance_root: Path,
    yyyymmdd: str,
    workdir: Path | None = None,
    model: str | None = None,
    session: str | None = None,
    approval_state: str = "unknown",
    context_budget: str = "unknown",
    git_branch: str | None = None,
    git_dirty: bool | None = None,
    git_ahead: int | None = None,
    git_behind: int | None = None,
) -> dict[str, Any]:
    """Build a deterministic redacted local runtime status packet."""

    instance_root = instance_root.resolve()
    resolved_workdir = (workdir or Path.cwd()).resolve()
    if git_branch is None or git_dirty is None or git_ahead is None or git_behind is None:
        git = collect_git_context(resolved_workdir)
    else:
        git = {
            "workdir": redact_sensitive_value(str(resolved_workdir)),
            "available": True,
            "branch": git_branch,
            "dirty": git_dirty,
            "ahead": git_ahead,
            "behind": git_behind,
        }

    runtime = {
        "model": redact_sensitive_value(model or "unknown"),
        "session": redact_sensitive_value(session or "unknown"),
        "context_budget": redact_sensitive_value(context_budget),
        "approval_state": redact_sensitive_value(approval_state),
    }
    return {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "date": yyyymmdd,
        "instance_root": redact_sensitive_value(str(instance_root)),
        "runtime": runtime,
        "git": git,
        "boundary_flags": {
            "external_call_made": False,
            "mutation_performed": False,
            "publication_or_live_action_approved": False,
            "execution_authorized": False,
            "action_taken": "none",
        },
        "artifacts_policy": {
            "local_only": True,
            "network_calls_allowed": False,
            "live_runtime_mutation_allowed": False,
        },
        "privacy": {
            "redaction_applied": _contains_redaction({"runtime": runtime, "git": git, "instance_root": str(instance_root)}),
            "redaction_rules": ["credential_like_values", "home_usernames"],
        },
    }


def _contains_redaction(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_contains_redaction(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_redaction(item) for item in value)
    return value == "[REDACTED]" or (isinstance(value, str) and "/home/[REDACTED]" in value)


def render_runtime_status_text(packet: dict[str, Any], *, json_ref: str) -> str:
    git = packet["git"]
    runtime = packet["runtime"]
    flags = packet["boundary_flags"]
    return (
        "runtime status: "
        f"branch={git.get('branch', 'unknown')} "
        f"dirty={str(git.get('dirty', False)).lower()} "
        f"ahead={git.get('ahead', 0)} behind={git.get('behind', 0)} "
        f"approval={runtime.get('approval_state', 'unknown')} "
        f"external_call_made={str(flags['external_call_made']).lower()} "
        f"mutation_performed={str(flags['mutation_performed']).lower()} "
        f"report={json_ref}"
    )


def render_runtime_status_markdown(packet: dict[str, Any]) -> str:
    git = packet["git"]
    runtime = packet["runtime"]
    flags = packet["boundary_flags"]
    return "\n".join(
        [
            "# Hisys Runtime Status Surface",
            "",
            f"- schema: `{packet['schema_id']}@{packet['schema_version']}`",
            f"- date: `{packet['date']}`",
            f"- workdir: `{git.get('workdir', 'unknown')}`",
            f"- branch: `{git.get('branch', 'unknown')}`",
            f"- dirty: `{str(git.get('dirty', False)).lower()}`",
            f"- ahead: `{git.get('ahead', 0)}`",
            f"- behind: `{git.get('behind', 0)}`",
            f"- model: `{runtime.get('model', 'unknown')}`",
            f"- session: `{runtime.get('session', 'unknown')}`",
            f"- context_budget: `{runtime.get('context_budget', 'unknown')}`",
            f"- approval_state: `{runtime.get('approval_state', 'unknown')}`",
            f"- external_call_made: `{str(flags['external_call_made']).lower()}`",
            f"- mutation_performed: `{str(flags['mutation_performed']).lower()}`",
            f"- action_taken: `{flags['action_taken']}`",
            "",
            "This packet is local/read-only evidence. It does not approve live runtime actions, publication, push, or external connectors.",
            "",
        ]
    )


def write_runtime_status_surface(*, instance_root: Path, yyyymmdd: str, packet: dict[str, Any]) -> dict[str, str]:
    """Write JSON and Markdown runtime status artifacts under the instance root."""

    report_dir = instance_root / "reports" / "run-summaries" / yyyymmdd
    report_dir.mkdir(parents=True, exist_ok=True)
    json_ref = f"reports/run-summaries/{yyyymmdd}/hisys-runtime-status-surface.json"
    markdown_ref = f"reports/run-summaries/{yyyymmdd}/hisys-runtime-status-surface.md"
    (instance_root / json_ref).write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (instance_root / markdown_ref).write_text(render_runtime_status_markdown(packet), encoding="utf-8")
    return {"json_ref": json_ref, "markdown_ref": markdown_ref}
