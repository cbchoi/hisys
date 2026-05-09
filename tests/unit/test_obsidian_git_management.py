"""Tests for Git-managed Obsidian vault lifecycle planning.

Traceability: Live-Obsidian-Git-A/B, HISYS-CON-010..012, HISYS-CON-022..023.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hisys.config.obsidian_live import (
    build_obsidian_git_initialization_plan,
    build_obsidian_git_sync_plan,
)


def test_obsidian_git_initialization_plan_requires_credential_ref_and_remote() -> None:
    plan = build_obsidian_git_initialization_plan(
        request_id="REQ-GIT-INIT-001",
        vault_root=Path("/tmp/example-vault"),
        remote_url="git@github.com-sysailab-obsidian:sysailab/obsidian.git",
        default_branch="main",
        credential_ref="keyring:hisys/obsidian-github-deploy-key",
        operator_id="professor",
    )

    assert plan["schema_id"] == "hisys.obsidian.git_initialization_plan"
    assert plan["status"] == "planned_requires_operator_credentials"
    assert plan["credential_ref"] == "keyring:hisys/obsidian-github-deploy-key"
    assert plan["raw_credential_stored"] is False
    assert plan["planned_operation_count"] == 6
    assert [op["operation"] for op in plan["planned_operations"]] == [
        "verify_or_create_vault_root",
        "git_init_if_missing",
        "configure_remote_origin",
        "install_lightweight_gitignore_policy",
        "credential_ref_binding",
        "initial_commit_and_push",
    ]
    assert "attachments_ignored_by_default" in plan["gitignore_policy"]
    assert plan["mutation_performed"] is False
    assert plan["external_call_made"] is False


@pytest.mark.parametrize(
    ("credential_ref", "remote_url", "expected"),
    [
        ("", "git@github.com:owner/repo.git", "credential_ref_required"),
        ("ghp_thisIsARawTokenLikeCredential", "git@github.com:owner/repo.git", "raw_credential_value_not_allowed"),
        ("env:HISYS_OBSIDIAN_GIT_SSH_KEY", "", "remote_url_required"),
    ],
)
def test_obsidian_git_initialization_plan_blocks_missing_or_raw_credentials(
    credential_ref: str, remote_url: str, expected: str
) -> None:
    plan = build_obsidian_git_initialization_plan(
        request_id="REQ-GIT-INIT-BLOCKED",
        vault_root=Path("/tmp/example-vault"),
        remote_url=remote_url,
        default_branch="main",
        credential_ref=credential_ref,
        operator_id="professor",
    )

    assert plan["status"] == "blocked"
    assert plan["reason_code"] == expected
    assert plan["raw_credential_stored"] is False
    assert plan["mutation_performed"] is False
    assert plan["external_call_made"] is False


def test_obsidian_git_sync_plan_commits_memo_and_pushes_after_write() -> None:
    plan = build_obsidian_git_sync_plan(
        request_id="REQ-GIT-SYNC-001",
        vault_root=Path("/tmp/example-vault"),
        memo_refs=["91 Hisys/Live Research/topics/TOPIC-20260509-7F3A92__devs/index.md"],
        runtime_boundary_refs=["91 Hisys/Live Research/topics/TOPIC-20260509-7F3A92__devs/investigations/2026-05-09/INV-20260509-2130-VAULT/runtime-boundary/runtime-index.json"],
        commit_message="docs(obsidian): add Hisys investigation memo",
        remote_name="origin",
        branch="main",
        credential_ref="env:HISYS_OBSIDIAN_GIT_SSH_KEY",
        approval_ref="APPROVAL-20260510-001",
    )

    assert plan["schema_id"] == "hisys.obsidian.git_sync_plan"
    assert plan["status"] == "planned_after_vault_write"
    assert plan["credential_ref"] == "env:HISYS_OBSIDIAN_GIT_SSH_KEY"
    assert [op["operation"] for op in plan["planned_operations"]] == [
        "pre_sync_git_status",
        "stage_approved_memo_and_runtime_boundary_refs",
        "commit_memo_projection",
        "push_commit_to_remote",
        "record_post_push_status",
    ]
    assert plan["planned_operations"][1]["refs"] == plan["memo_refs"] + plan["runtime_boundary_refs"]
    assert plan["planned_operations"][3]["remote_name"] == "origin"
    assert plan["planned_operations"][3]["branch"] == "main"
    assert plan["raw_credential_stored"] is False
    assert plan["mutation_performed"] is False
    assert plan["external_call_made"] is False


def test_obsidian_git_sync_plan_blocks_unsafe_refs() -> None:
    plan = build_obsidian_git_sync_plan(
        request_id="REQ-GIT-SYNC-UNSAFE",
        vault_root=Path("/tmp/example-vault"),
        memo_refs=["../escape.md"],
        runtime_boundary_refs=[],
        commit_message="docs(obsidian): unsafe",
        remote_name="origin",
        branch="main",
        credential_ref="env:HISYS_OBSIDIAN_GIT_SSH_KEY",
        approval_ref="APPROVAL-20260510-001",
    )

    assert plan["status"] == "blocked"
    assert plan["reason_code"] == "unsafe_vault_ref"
    assert plan["planned_operation_count"] == 0
