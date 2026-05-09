"""Tests for Live-Obsidian-Config-D memo ontology template planning.

Traceability: Live-Obsidian-Config-D, HISYS-FR-INV-001..006,
HISYS-T-024, HISYS-CON-010..012, HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.config.obsidian_live import build_vault_template_plan


def test_build_vault_template_plan_defines_structured_memo_ontology_without_wikilink_governance() -> None:
    plan = build_vault_template_plan(request_id="REQ-TEMPLATE-001")

    assert plan["schema_id"] == "hisys.obsidian.vault_template_plan"
    assert plan["request_id"] == "REQ-TEMPLATE-001"
    assert plan["vault_write_attempted"] is False
    assert plan["external_call_made"] is False
    assert plan["mutation_performed"] is False
    template_types = {template["type"] for template in plan["templates"]}
    assert "hisys/topic" in template_types
    assert "hisys/investigation" in template_types
    assert "hisys/gatekeeper-decision" in template_types
    assert "hisys/claim-coverage-gate" in template_types
    claim_template = next(template for template in plan["templates"] if template["type"] == "hisys/claim")
    assert "phase" in claim_template["frontmatter_fields"]
    assert "tags" in claim_template["frontmatter_fields"]
    assert "links" in claim_template["frontmatter_fields"]
    assert claim_template["link_policy"] == "structured_links_primary_wikilinks_projection_only"
    assert "supports_claim" in plan["allowed_relations"]
    assert "gates_claims" in plan["allowed_relations"]
    assert all("hisys/live-k" not in template.get("default_tags", []) for template in plan["templates"])


def test_vault_template_plan_cli_writes_runtime_boundary_template_plan_only(tmp_path: Path, capsys) -> None:
    from hisys.cli.main import main

    result = main(
        [
            "vault-template-plan",
            "--instance",
            str(tmp_path),
            "--date",
            "20260509",
            "--request-id",
            "REQ-TEMPLATE-CLI",
        ]
    )

    out = capsys.readouterr().out
    assert result == 0
    assert "vault template plan" in out
    assert "vault_write_attempted: false" in out
    assert not (tmp_path / "91 Hisys").exists()
    plan_path = tmp_path / "runtime-boundary" / "obsidian-live" / "20260509" / "vault-template-plan-REQ-TEMPLATE-CLI.json"
    report_path = tmp_path / "reports" / "run-summaries" / "20260509" / "vault-template-plan-report.json"
    assert plan_path.exists()
    assert report_path.exists()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["template_count"] == len(plan["templates"])
    assert report["vault_write_attempted"] is False
