"""Runtime status surface packet tests.

Traceability: docs/plans/2026-05-19-runtime-status-surface-cli.md.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.operations.runtime_status_surface import (
    build_runtime_status_packet,
    redact_sensitive_value,
    render_runtime_status_markdown,
    render_runtime_status_text,
    write_runtime_status_surface,
)


def test_build_runtime_status_packet_is_local_read_only_and_redacted(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    instance = tmp_path / "instance"
    repo.mkdir()
    instance.mkdir()

    packet = build_runtime_status_packet(
        instance_root=instance,
        yyyymmdd="20260519",
        workdir=repo,
        model="claude-sonnet-token-abc123456789",
        session="session-secret-987654321",
        approval_state="approved_candidate_ids:CHERRY-20260519-005",
        context_budget="input=12000/output=2000",
        git_branch="feature/runtime-status",
        git_dirty=True,
        git_ahead=2,
        git_behind=0,
    )

    assert packet["schema_id"] == "hisys.runtime_status_surface"
    assert packet["schema_version"] == "0.1.0"
    assert packet["date"] == "20260519"
    assert packet["boundary_flags"] == {
        "external_call_made": False,
        "mutation_performed": False,
        "publication_or_live_action_approved": False,
        "execution_authorized": False,
        "action_taken": "none",
    }
    assert packet["runtime"]["model"] == "[REDACTED]"
    assert packet["runtime"]["session"] == "[REDACTED]"
    assert packet["git"]["branch"] == "feature/runtime-status"
    assert packet["git"]["dirty"] is True
    assert packet["git"]["ahead"] == 2
    assert packet["privacy"]["redaction_applied"] is True


def test_redact_sensitive_value_masks_secrets_and_private_home_paths() -> None:
    assert redact_sensitive_value("sk-live-secret-token") == "[REDACTED]"
    assert redact_sensitive_value("/home/cbchoi/workspaces/private") == "/home/[REDACTED]/workspaces/private"
    assert redact_sensitive_value("safe-model-name") == "safe-model-name"


def test_write_runtime_status_surface_writes_json_and_markdown(tmp_path: Path) -> None:
    instance = tmp_path / "instance"
    instance.mkdir()
    packet = build_runtime_status_packet(
        instance_root=instance,
        yyyymmdd="20260519",
        workdir=tmp_path / "repo",
        model="safe-model",
        session="session-id",
        approval_state="human_approved:CHERRY-20260519-005",
        context_budget="tokens=unknown",
        git_branch="main",
        git_dirty=False,
        git_ahead=0,
        git_behind=0,
    )

    refs = write_runtime_status_surface(instance_root=instance, yyyymmdd="20260519", packet=packet)

    json_path = instance / refs["json_ref"]
    md_path = instance / refs["markdown_ref"]
    assert json_path.exists()
    assert md_path.exists()
    persisted = json.loads(json_path.read_text(encoding="utf-8"))
    assert persisted["boundary_flags"]["action_taken"] == "none"
    assert "Hisys Runtime Status Surface" in md_path.read_text(encoding="utf-8")


def test_renderers_expose_compact_status_without_raw_secret(tmp_path: Path) -> None:
    packet = build_runtime_status_packet(
        instance_root=tmp_path,
        yyyymmdd="20260519",
        workdir=tmp_path,
        model="sk-secret-model",
        session="secret-session",
        approval_state="pending",
        context_budget="unknown",
        git_branch="main",
        git_dirty=False,
        git_ahead=0,
        git_behind=0,
    )

    text = render_runtime_status_text(packet, json_ref="reports/run-summaries/20260519/hisys-runtime-status-surface.json")
    markdown = render_runtime_status_markdown(packet)

    assert "runtime status:" in text
    assert "external_call_made=false" in text
    assert "[REDACTED]" in markdown
    assert "sk-secret" not in markdown
