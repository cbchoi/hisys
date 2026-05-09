"""Tests for Live-Obsidian-Config-B fixture-only vault planning.

Traceability: Live-Obsidian-Config-A/B, HISYS-FR-INV-001..006,
HISYS-T-024, HISYS-CON-010..012, HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.config.obsidian_live import build_vault_plan


ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples" / "obsidian-live"


def test_build_vault_plan_routes_existing_topic_without_vault_write(tmp_path: Path) -> None:
    plan = build_vault_plan(
        registry_path=EXAMPLES / "registry.json",
        request_id="REQ-VAULT-PLAN-001",
        submitted_title="DEVS Structural Change Formalism",
        domain="research",
        objective="Investigate DEVS structural-change formalisms.",
        yyyymmdd="20260509",
        hhmm="2130",
        dry_run=True,
    )

    assert plan["schema_id"] == "hisys.obsidian.vault_plan"
    assert plan["request_id"] == "REQ-VAULT-PLAN-001"
    assert plan["decision"]["action"] == "same_as_existing_topic"
    assert plan["decision"]["target_topic_uid"] == "TOPIC-20260509-7F3A92"
    assert plan["topic_path"] == "topics/TOPIC-20260509-7F3A92__devs-structural-change-formalism"
    assert plan["investigation_path"].endswith("investigations/2026-05-09/INV-20260509-2130-VAULT")
    assert plan["vault_write_attempted"] is False
    assert plan["external_call_made"] is False
    assert plan["mutation_performed"] is False
    assert plan["dry_run"] is True
    assert plan["planned_files"]
    assert plan["vault_relative_root"] == "91 Hisys/Live Research"
    assert all(ref.startswith("91 Hisys/Live Research/") for ref in plan["planned_files"])
    assert all(not Path(ref).is_absolute() for ref in plan["planned_files"])
    assert all(".." not in Path(ref).parts for ref in plan["planned_files"])
    assert plan["decision"]["scores"]["semantic_similarity"]["evidence_refs"]


def test_build_vault_plan_rejects_path_traversal_topic_title() -> None:
    with pytest.raises(ValueError, match="unsafe topic title"):
        build_vault_plan(
            registry_path=EXAMPLES / "registry.json",
            request_id="REQ-VAULT-PLAN-002",
            submitted_title="../escape",
            domain="research",
            objective="Attempt path traversal.",
            yyyymmdd="20260509",
            hhmm="2130",
            dry_run=True,
        )


def test_vault_plan_cli_writes_runtime_boundary_report_only(tmp_path: Path, capsys) -> None:
    from hisys.cli.main import main

    result = main(
        [
            "vault-plan",
            "--instance",
            str(tmp_path),
            "--registry",
            str(EXAMPLES / "registry.json"),
            "--date",
            "20260509",
            "--time",
            "2130",
            "--request-id",
            "REQ-VAULT-PLAN-CLI",
            "--topic-title",
            "DEVS Structural Change Formalism",
            "--domain",
            "research",
            "--objective",
            "Investigate DEVS structural-change formalisms.",
            "--dry-run",
        ]
    )

    out = capsys.readouterr().out
    assert result == 0
    assert "vault plan" in out
    assert "vault_write_attempted: false" in out
    assert not (tmp_path / "91 Hisys").exists()

    plan_path = tmp_path / "runtime-boundary" / "obsidian-live" / "20260509" / "vault-plan-REQ-VAULT-PLAN-CLI.json"
    report_path = tmp_path / "reports" / "run-summaries" / "20260509" / "vault-plan-report.json"
    assert plan_path.exists()
    assert report_path.exists()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["vault_plan_ref"] == "runtime-boundary/obsidian-live/20260509/vault-plan-REQ-VAULT-PLAN-CLI.json"
    assert plan["vault_write_attempted"] is False
    assert plan["decision"]["action"] == "same_as_existing_topic"
