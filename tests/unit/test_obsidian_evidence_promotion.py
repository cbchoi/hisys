"""Tests for Obsidian evidence promotion planning and fixture rehearsal.

Traceability: Obsidian-Evidence-Promotion-A, HISYS-FR-INV-001..006,
HISYS-T-024, HISYS-CON-010..012, HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.config.obsidian_live import (
    build_obsidian_evidence_promotion_plan,
    rehearse_obsidian_evidence_promotion_in_fixture,
)


def _promotion_request() -> dict:
    return {
        "request_id": "REQ-EP-A",
        "topic_uid": "TOPIC-20260509-AAAAAA",
        "topic_slug": "devs-structural-change-formalism",
        "investigation_id": "INV-20260510-0122-ABCD",
        "source_refs": ["runtime-boundary/source-connectors/20260510/source-access-SRC-001.json"],
        "evidence_refs": ["runtime-boundary/source-connectors/20260510/source-evidence-EVID-001.json"],
        "claim_refs": ["runtime-boundary/source-connectors/20260510/claim-evidence-ledger-LEDGER-001.json"],
        "decision_refs": ["runtime-boundary/topic-gatekeeper/topic-gatekeeper-decision-REQ-TG-A.json"],
        "approval_ref": "APPROVAL-EP-A",
    }


def test_build_obsidian_evidence_promotion_plan_is_canonical_and_no_write() -> None:
    plan = build_obsidian_evidence_promotion_plan(request=_promotion_request())

    assert plan["status"] == "planned_not_executed"
    assert plan["topic_uid"] == "TOPIC-20260509-AAAAAA"
    assert plan["approval_ref"] == "APPROVAL-EP-A"
    assert plan["promotion_plan_only"] is True
    assert plan["real_obsidian_vault_write_performed"] is False
    assert plan["external_call_made"] is False
    assert plan["mutation_performed"] is False
    assert plan["planned_operation_count"] == 5
    refs = [op["vault_relative_ref"] for op in plan["planned_operations"]]
    assert "91 Hisys/Live Research/topics/TOPIC-20260509-AAAAAA__devs-structural-change-formalism/canonical/sources/source-index.json" in refs
    assert "91 Hisys/Live Research/topics/TOPIC-20260509-AAAAAA__devs-structural-change-formalism/canonical/evidence/evidence-index.json" in refs
    assert "91 Hisys/Live Research/topics/TOPIC-20260509-AAAAAA__devs-structural-change-formalism/canonical/claims/claim-index.json" in refs
    assert "91 Hisys/Live Research/topics/TOPIC-20260509-AAAAAA__devs-structural-change-formalism/canonical/decisions/decision-index.json" in refs
    assert any(op["operation"] == "write_promotion_manifest" for op in plan["planned_operations"])


def test_rehearse_obsidian_evidence_promotion_writes_only_fixture(tmp_path: Path) -> None:
    plan = build_obsidian_evidence_promotion_plan(request=_promotion_request())
    report = rehearse_obsidian_evidence_promotion_in_fixture(
        promotion_plan=plan,
        fixture_vault_root=tmp_path,
        approval_ref="APPROVAL-EP-A",
        fixture_vault_only=True,
    )

    assert report["status"] == "rehearsed_fixture_only"
    assert report["operation_count"] == plan["planned_operation_count"]
    assert report["real_obsidian_vault_write_performed"] is False
    first = tmp_path / report["written_fixture_refs"][0]["vault_relative_ref"]
    assert first.exists()
    payload = json.loads(first.read_text(encoding="utf-8"))
    assert payload["obsidian_evidence_promotion_projection_only"] is True
    assert payload["source_promotion_request_id"] == "REQ-EP-A"


def test_obsidian_evidence_promotion_cli_writes_plan(tmp_path: Path, capsys) -> None:
    from hisys.cli.main import main

    instance = tmp_path / "instance"
    request_path = tmp_path / "promotion-request.json"
    request_path.write_text(json.dumps(_promotion_request()), encoding="utf-8")

    exit_code = main([
        "vault-evidence-promotion-plan",
        "--instance", str(instance),
        "--date", "20260510",
        "--request", str(request_path),
    ])

    assert exit_code == 0
    assert "obsidian evidence promotion plan: planned_not_executed" in capsys.readouterr().out
    report_path = instance / "runtime-boundary" / "obsidian-live" / "20260510" / "evidence-promotion-plan-REQ-EP-A.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["promotion_plan_only"] is True
    assert report["real_obsidian_vault_write_performed"] is False
