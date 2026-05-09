"""Tests for Live-Obsidian-Config-F controlled fixture vault apply.

Traceability: Live-Obsidian-Config-F, HISYS-FR-INV-001..006,
HISYS-T-024, HISYS-CON-010..012, HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.config.obsidian_live import apply_vault_plan_to_fixture


EXAMPLES = Path(__file__).resolve().parents[2] / "examples" / "obsidian-live"


def _plan() -> dict:
    return {
        "schema_id": "hisys.obsidian.vault_plan",
        "schema_version": "0.1.0",
        "request_id": "REQ-VAULT-APPLY",
        "topic_uid": "TOPIC-20260509-7F3A92",
        "topic_slug": "devs-structural-change-formalism",
        "topic_path": "topics/TOPIC-20260509-7F3A92__devs-structural-change-formalism",
        "investigation_id": "INV-20260509-2101-A8C4",
        "investigation_path": "topics/TOPIC-20260509-7F3A92__devs-structural-change-formalism/investigations/2026-05-09/INV-20260509-2101-A8C4",
        "planned_files": [
            "registry.json",
            "topics/INDEX.json",
            "topics/TOPIC-20260509-7F3A92__devs-structural-change-formalism/index.md",
            "topics/TOPIC-20260509-7F3A92__devs-structural-change-formalism/topic-manifest.json",
            "topics/TOPIC-20260509-7F3A92__devs-structural-change-formalism/investigations/2026-05-09/INV-20260509-2101-A8C4/index.md",
            "topics/TOPIC-20260509-7F3A92__devs-structural-change-formalism/investigations/2026-05-09/INV-20260509-2101-A8C4/investigation-manifest.json",
        ],
        "decision": {
            "action": "same_as_existing_topic",
            "scores": {"semantic_similarity": {"value": 1.0, "evidence_refs": ["registry.json#/topics/0"]}},
        },
        "dry_run": True,
        "vault_write_attempted": False,
        "external_call_made": False,
        "mutation_performed": False,
    }


def test_apply_vault_plan_blocks_without_human_approval(tmp_path: Path) -> None:
    report = apply_vault_plan_to_fixture(
        plan=_plan(),
        target_vault_root=tmp_path / "fixture-vault",
        approval_ref=None,
        fixture_vault_only=True,
    )

    assert report["status"] == "blocked"
    assert report["reason_code"] == "approval_ref_required"
    assert report["vault_write_attempted"] is False
    assert report["target_vault_write_performed"] is False
    assert not (tmp_path / "fixture-vault" / "registry.json").exists()


def test_apply_vault_plan_writes_only_fixture_vault_with_approval(tmp_path: Path) -> None:
    target = tmp_path / "fixture-vault"

    report = apply_vault_plan_to_fixture(
        plan=_plan(),
        target_vault_root=target,
        approval_ref="APPROVAL-local-fixture-vault-001",
        fixture_vault_only=True,
    )

    assert report["status"] == "applied"
    assert report["approval_ref"] == "APPROVAL-local-fixture-vault-001"
    assert report["target_vault_write_performed"] is True
    assert report["real_obsidian_vault_write_performed"] is False
    assert report["external_call_made"] is False
    assert (target / "registry.json").exists()
    assert (target / "topics" / "INDEX.json").exists()
    assert (target / "topics" / "TOPIC-20260509-7F3A92__devs-structural-change-formalism" / "index.md").exists()
    registry = json.loads((target / "registry.json").read_text(encoding="utf-8"))
    assert registry["schema_id"] == "hisys.obsidian.fixture_registry_projection"
    assert registry["source_plan_request_id"] == "REQ-VAULT-APPLY"


def test_apply_vault_plan_rejects_real_obsidian_vault_even_with_approval() -> None:
    report = apply_vault_plan_to_fixture(
        plan=_plan(),
        target_vault_root=Path("/home/cbchoi/obsidian"),
        approval_ref="APPROVAL-real-vault-not-accepted-by-fixture-writer",
        fixture_vault_only=True,
    )

    assert report["status"] == "blocked"
    assert report["reason_code"] == "real_obsidian_vault_blocked"
    assert report["vault_write_attempted"] is False
    assert report["target_vault_write_performed"] is False


def test_vault_apply_cli_requires_fixture_flag_and_writes_runtime_report(tmp_path: Path, capsys) -> None:
    from hisys.cli.main import main

    instance = tmp_path / "instance"
    target = tmp_path / "fixture-vault"
    plan_path = tmp_path / "vault-plan.json"
    plan_path.write_text(json.dumps(_plan()), encoding="utf-8")

    exit_code = main(
        [
            "vault-apply",
            "--instance",
            str(instance),
            "--date",
            "20260509",
            "--plan",
            str(plan_path),
            "--target-vault-root",
            str(target),
            "--approval-ref",
            "APPROVAL-local-fixture-vault-001",
            "--fixture-vault-only",
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr().out
    assert "vault apply: applied" in captured
    report_path = instance / "runtime-boundary" / "obsidian-live" / "20260509" / "vault-apply-report-REQ-VAULT-APPLY.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["target_vault_write_performed"] is True
    assert report["real_obsidian_vault_write_performed"] is False
