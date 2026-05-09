"""Tests for Live-Obsidian-Config-G topic identity transition planning.

Traceability: Live-Obsidian-Config-G, HISYS-FR-INV-001..006,
HISYS-T-024, HISYS-CON-010..012, HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.config.obsidian_live import build_topic_identity_transition_plan


def test_merge_transition_requires_approval_and_is_non_destructive() -> None:
    plan = build_topic_identity_transition_plan(
        request_id="REQ-MERGE-1",
        action="merge_with_existing_topic",
        source_topic_uid="TOPIC-20260509-AAAAAA",
        target_topic_uid="TOPIC-20260509-BBBBBB",
        approval_ref="APPROVAL-topic-merge-001",
        rationale="duplicate canonical topics",
    )

    assert plan["action"] == "merge_with_existing_topic"
    assert plan["approval_required"] is True
    assert plan["approval_ref"] == "APPROVAL-topic-merge-001"
    assert plan["non_destructive"] is True
    assert plan["delete_old_topic_folder"] is False
    assert plan["planned_tombstone_ref"] == "topics/TOPIC-20260509-AAAAAA/MERGED_INTO.md"
    assert plan["planned_manifest_updates"][0]["status"] == "merged"
    assert plan["real_obsidian_vault_write_performed"] is False


def test_merge_transition_blocks_without_approval() -> None:
    plan = build_topic_identity_transition_plan(
        request_id="REQ-MERGE-BLOCKED",
        action="merge_with_existing_topic",
        source_topic_uid="TOPIC-20260509-AAAAAA",
        target_topic_uid="TOPIC-20260509-BBBBBB",
        approval_ref=None,
        rationale="duplicate canonical topics",
    )

    assert plan["status"] == "blocked"
    assert plan["reason_code"] == "approval_ref_required"
    assert plan["planned_file_writes"] == []
    assert plan["vault_write_attempted"] is False


def test_split_transition_requires_approval_and_preserves_source_topic() -> None:
    plan = build_topic_identity_transition_plan(
        request_id="REQ-SPLIT-1",
        action="split_topic_recommended",
        source_topic_uid="TOPIC-20260509-AAAAAA",
        target_topic_uid="TOPIC-20260509-CCCCCC",
        approval_ref="APPROVAL-topic-split-001",
        rationale="mixed topic scope",
    )

    assert plan["action"] == "split_topic_recommended"
    assert plan["approval_required"] is True
    assert plan["non_destructive"] is True
    assert plan["delete_old_topic_folder"] is False
    assert plan["planned_tombstone_ref"] == "topics/TOPIC-20260509-AAAAAA/SPLIT_INTO.md"
    assert plan["planned_manifest_updates"][0]["status"] == "active"
    assert plan["planned_manifest_updates"][0]["split_into"] == ["TOPIC-20260509-CCCCCC"]


def test_topic_transition_cli_writes_runtime_plan(tmp_path: Path, capsys) -> None:
    from hisys.cli.main import main

    instance = tmp_path / "instance"
    exit_code = main(
        [
            "vault-topic-transition-plan",
            "--instance",
            str(instance),
            "--date",
            "20260509",
            "--request-id",
            "REQ-MERGE-CLI",
            "--action",
            "merge_with_existing_topic",
            "--source-topic-uid",
            "TOPIC-20260509-AAAAAA",
            "--target-topic-uid",
            "TOPIC-20260509-BBBBBB",
            "--approval-ref",
            "APPROVAL-topic-merge-cli",
            "--rationale",
            "duplicate canonical topics",
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr().out
    assert "topic transition plan" in captured
    plan_path = instance / "runtime-boundary" / "obsidian-live" / "20260509" / "topic-transition-plan-REQ-MERGE-CLI.json"
    assert plan_path.exists()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    assert plan["planned_tombstone_ref"] == "topics/TOPIC-20260509-AAAAAA/MERGED_INTO.md"
    assert plan["real_obsidian_vault_write_performed"] is False
