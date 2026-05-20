"""Local governance-document current-state consistency reporting.

This operation is a bounded repository-read checker. It reads committed project
control documents and the local Git checkout, then reports whether the current
bootstrap/Ralph state is unambiguous for the next Ralph loop. It performs no
network, model, credential, publication, deployment, or remote Git action.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel


class GovernanceCurrentStateReport(BaseModel):
    """Bounded advisory report for local governance-resume state."""

    schema_id: str = "hisys.governance.current_state.v1"
    repository: str
    branch: str
    profile_version: str
    next_safe_task: str
    planning_baseline_head: str
    current_head_short: str
    current_head_subject: str
    current_head_at_plan_creation: str
    ralph_checkpoint_head: str
    v0012_validation_status: str
    remote_push_authorized: bool
    live_model_call_authorized: bool
    live_external_action_authorized: bool
    advisory_only: bool = True
    requires_human_review: bool = True
    external_call_made: bool = False
    mutation_performed: bool = False
    raw_source_content_persisted: bool = False
    issues: tuple[str, ...] = ()


def _run_git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    return data


def _task_status(tasks_doc: dict[str, Any], task_id: str) -> str:
    tasks = tasks_doc.get("tasks")
    if not isinstance(tasks, list):
        return "missing"
    for task in tasks:
        if isinstance(task, dict) and task.get("id") == task_id:
            status = task.get("status")
            return status if isinstance(status, str) else "missing"
    return "missing"


def _latest_ralph_checkpoint_head(ralph_text: str) -> str:
    marker = "### 2026-05-20 — Current code/document weakness analysis improvement plan"
    section_start = ralph_text.rfind(marker)
    if section_start == -1:
        return "missing"
    section = ralph_text[section_start:]
    for line in section.splitlines():
        if line.startswith("- Current HEAD:"):
            return line.split(":", 1)[1].strip()
    return "missing"


def _is_ancestor(repo_root: Path, candidate: str) -> bool:
    candidate_short = candidate.split(maxsplit=1)[0] if candidate else ""
    if not candidate_short or candidate_short == "missing":
        return False
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", candidate_short, "HEAD"],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.returncode == 0


def build_governance_current_state_report(repo_root: Path) -> GovernanceCurrentStateReport:
    """Build a deterministic local advisory governance-state report."""

    root = repo_root.resolve()
    profile = _load_yaml(root / "docs" / "milestone-bootstrap" / "profile.yaml")
    tasks_v0012 = _load_yaml(
        root / "docs" / "milestone-bootstrap" / "tasks" / "milestone_tasks_v0.0.12.yaml"
    )
    ralph_text = (root / "ralph.md").read_text(encoding="utf-8")

    branch = _run_git(root, "branch", "--show-current")
    head_short = _run_git(root, "rev-parse", "--short", "HEAD")
    head_subject = _run_git(root, "log", "-1", "--pretty=%s")
    head_label = f"{head_short} {head_subject}"

    profile_version = str(profile.get("version", ""))
    next_safe_task = str(profile.get("next_safe_task", ""))
    planning_baseline_head = str(profile.get("planning_baseline_head", ""))
    current_head_at_plan_creation = str(profile.get("current_head_at_plan_creation", ""))
    ralph_checkpoint_head = _latest_ralph_checkpoint_head(ralph_text)
    v0012_status = _task_status(tasks_v0012, "MB-DARS-LIVE-PREP-3")

    issues: list[str] = []
    if str(profile.get("target_workspace", "")) != root.as_posix():
        issues.append("profile.target_workspace does not match repo root")
    if str(profile.get("selected_profile", "")) != "develop":
        issues.append("profile.selected_profile is not develop")
    if current_head_at_plan_creation != ralph_checkpoint_head:
        issues.append("profile and Ralph documented current heads differ")
    if not _is_ancestor(root, current_head_at_plan_creation):
        issues.append("profile.current_head_at_plan_creation is not an ancestor of current HEAD")
    if v0012_status != "completed":
        issues.append("v0.0.12 validation task is not completed")
    if profile.get("remote_push_authorized") is not False:
        issues.append("remote_push_authorized must be false")
    if profile.get("live_model_call_authorized") is not False:
        issues.append("live_model_call_authorized must be false")
    if profile.get("live_external_action_authorized") is not False:
        issues.append("live_external_action_authorized must be false")

    return GovernanceCurrentStateReport(
        repository=root.as_posix(),
        branch=branch,
        profile_version=profile_version,
        next_safe_task=next_safe_task,
        planning_baseline_head=planning_baseline_head,
        current_head_short=head_short,
        current_head_subject=head_subject,
        current_head_at_plan_creation=current_head_at_plan_creation,
        ralph_checkpoint_head=ralph_checkpoint_head,
        v0012_validation_status=v0012_status,
        remote_push_authorized=profile.get("remote_push_authorized") is True,
        live_model_call_authorized=profile.get("live_model_call_authorized") is True,
        live_external_action_authorized=profile.get("live_external_action_authorized") is True,
        issues=tuple(issues),
    )


__all__ = [
    "GovernanceCurrentStateReport",
    "build_governance_current_state_report",
]
