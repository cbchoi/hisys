"""Tests for fixture-only Obsidian Git lifecycle execution.

Traceability: Live-Obsidian-Git-C, HISYS-CON-010..012, HISYS-CON-022..023.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from hisys.config.obsidian_live import (
    build_obsidian_git_initialization_plan,
    build_obsidian_git_sync_plan,
    execute_obsidian_git_initialization_in_fixture,
    execute_obsidian_git_sync_in_fixture,
)


def _git(*args: str, cwd: Path | None = None, git_dir: Path | None = None) -> str:
    command = ["git", *args]
    if git_dir is not None:
        command = ["git", f"--git-dir={git_dir}", *args]
    return subprocess.run(command, cwd=cwd, check=True, text=True, capture_output=True).stdout.strip()


def _init_plan(vault_root: Path, remote_root: Path) -> dict:
    return build_obsidian_git_initialization_plan(
        request_id="REQ-GIT-FIXTURE-INIT",
        vault_root=vault_root,
        remote_url=str(remote_root),
        default_branch="main",
        credential_ref="op:sysailab/obsidian-git/deploy-key",
        operator_id="professor",
        approval_ref="APPROVAL-GIT-FIXTURE-INIT",
    )


def test_fixture_git_initialization_executes_only_against_fixture_remote(tmp_path: Path) -> None:
    vault_root = tmp_path / "fixture-vault"
    remote_root = tmp_path / "fixture-remote.git"
    plan = _init_plan(vault_root, remote_root)

    report = execute_obsidian_git_initialization_in_fixture(
        plan=plan,
        fixture_vault_root=vault_root,
        fixture_remote_root=remote_root,
        fixture_git_only=True,
    )

    assert report["schema_id"] == "hisys.obsidian.git_fixture_execution_report"
    assert report["status"] == "applied"
    assert report["operation"] == "initialization"
    assert report["fixture_git_only"] is True
    assert report["target_vault_git_mutation_performed"] is True
    assert report["fixture_remote_push_performed"] is True
    assert report["real_obsidian_vault_write_performed"] is False
    assert report["external_call_made"] is False
    assert report["credential_ref_resolved"] is False
    assert (vault_root / ".git").exists()
    assert (vault_root / ".gitignore").read_text(encoding="utf-8").startswith("# Hisys lightweight Obsidian vault policy")
    assert _git("rev-parse", "--verify", "refs/heads/main", git_dir=remote_root)


def test_fixture_git_sync_commits_approved_runtime_boundary_only_refs(tmp_path: Path) -> None:
    vault_root = tmp_path / "fixture-vault"
    remote_root = tmp_path / "fixture-remote.git"
    init_report = execute_obsidian_git_initialization_in_fixture(
        plan=_init_plan(vault_root, remote_root),
        fixture_vault_root=vault_root,
        fixture_remote_root=remote_root,
        fixture_git_only=True,
    )
    assert init_report["status"] == "applied"

    approved_ref = "runtime-boundary/topic-gatekeeper/decision.json"
    approved_path = vault_root / approved_ref
    approved_path.parent.mkdir(parents=True, exist_ok=True)
    approved_path.write_text('{"decision":"same_as_existing_topic"}\n', encoding="utf-8")
    plan = build_obsidian_git_sync_plan(
        request_id="REQ-GIT-FIXTURE-SYNC",
        vault_root=vault_root,
        memo_refs=[],
        runtime_boundary_refs=[approved_ref],
        commit_message="chore(obsidian): record gatekeeper decision",
        remote_name="origin",
        branch="main",
        credential_ref="op:sysailab/obsidian-git/deploy-key",
        approval_ref="APPROVAL-GIT-FIXTURE-SYNC",
    )

    report = execute_obsidian_git_sync_in_fixture(
        plan=plan,
        fixture_vault_root=vault_root,
        fixture_remote_root=remote_root,
        fixture_git_only=True,
    )

    assert report["status"] == "applied"
    assert report["operation"] == "sync"
    assert report["approved_refs"] == [approved_ref]
    assert report["fixture_remote_push_performed"] is True
    assert report["real_obsidian_vault_write_performed"] is False
    assert report["external_call_made"] is False
    assert report["pushed_commit"] == _git("rev-parse", "refs/heads/main", git_dir=remote_root)


def test_fixture_git_executor_blocks_without_fixture_flag(tmp_path: Path) -> None:
    vault_root = tmp_path / "fixture-vault"
    remote_root = tmp_path / "fixture-remote.git"
    plan = _init_plan(vault_root, remote_root)

    report = execute_obsidian_git_initialization_in_fixture(
        plan=plan,
        fixture_vault_root=vault_root,
        fixture_remote_root=remote_root,
        fixture_git_only=False,
    )

    assert report["status"] == "blocked"
    assert report["reason_code"] == "fixture_git_only_required"
    assert report["target_vault_git_mutation_performed"] is False
    assert report["fixture_remote_push_performed"] is False
    assert not (vault_root / ".git").exists()


def test_fixture_git_sync_blocks_refs_missing_from_fixture_vault(tmp_path: Path) -> None:
    vault_root = tmp_path / "fixture-vault"
    remote_root = tmp_path / "fixture-remote.git"
    init_report = execute_obsidian_git_initialization_in_fixture(
        plan=_init_plan(vault_root, remote_root),
        fixture_vault_root=vault_root,
        fixture_remote_root=remote_root,
        fixture_git_only=True,
    )
    assert init_report["status"] == "applied"
    plan = build_obsidian_git_sync_plan(
        request_id="REQ-GIT-FIXTURE-MISSING",
        vault_root=vault_root,
        memo_refs=["missing.md"],
        runtime_boundary_refs=[],
        commit_message="docs(obsidian): missing",
        remote_name="origin",
        branch="main",
        credential_ref="op:sysailab/obsidian-git/deploy-key",
        approval_ref="APPROVAL-GIT-FIXTURE-SYNC",
    )

    report = execute_obsidian_git_sync_in_fixture(
        plan=plan,
        fixture_vault_root=vault_root,
        fixture_remote_root=remote_root,
        fixture_git_only=True,
    )

    assert report["status"] == "blocked"
    assert report["reason_code"] == "approved_ref_missing_from_fixture_vault"
    assert report["missing_refs"] == ["missing.md"]
    assert report["fixture_remote_push_performed"] is False
