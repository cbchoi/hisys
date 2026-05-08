"""DARS handoff loop runtime tests.

Traceability: HISYS-FR-AGT-001..005, HISYS-DARS-CONTRACT-001,
HISYS-D-015, HISYS-T-023, HISYS-T-024.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.agents.dars import DarsRuntime
from hisys.config.instance import InstanceRoot


def test_dars_runtime_loopback_placeholder_returns_without_implemented_dars(tmp_path: Path):
    execution_dir = tmp_path / "data" / "alert-connector-executions" / "20260508"
    execution_dir.mkdir(parents=True)
    (execution_dir / "EXEC-LOOPBACK-001.json").write_text(
        json.dumps(
            {
                "execution_id": "EXEC-LOOPBACK-001",
                "action_plan_ref": "PLAN-LOOPBACK-001",
                "alert_decision_ref": "ALERT-LOOPBACK-001",
                "connector_id": "disabled-fixture-connector",
                "target_channel": "discord:#ops",
                "would_send": True,
                "live_delivery_permitted": False,
                "execution_status": "blocked",
                "blocked_reason": "live_delivery_disabled",
                "action_taken": "none",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    report = DarsRuntime(instance=InstanceRoot(tmp_path)).run_loopback_placeholder(
        yyyymmdd="20260508",
        source_execution_id="EXEC-LOOPBACK-001",
        producer_id="dars-loopback-test",
    )

    assert report.handoff_refs == ["HANDOFF-DARS-LOOPBACK-001"]
    assert report.critique_refs == ["CRITIQUE-DARS-LOOPBACK-001"]
    handoff = json.loads((tmp_path / "data" / "agent-handoffs" / "20260508" / "HANDOFF-DARS-LOOPBACK-001.json").read_text(encoding="utf-8"))
    critique = json.loads((tmp_path / "data" / "agent-critiques" / "20260508" / "CRITIQUE-DARS-LOOPBACK-001.json").read_text(encoding="utf-8"))
    assert handoff["allowed_actions"] == "advisory_only"
    assert handoff["status"] == "linked"
    assert "dars_backend=loopback_placeholder" in handoff["constraints"]
    assert critique["critique_text"].startswith("DARS is not implemented yet")
    assert critique["dars_backend"] == "loopback_placeholder"
    assert critique["external_call_made"] is False
    assert critique["action_taken"] == "none"



def test_dars_runtime_prepares_advisory_handoff_and_ingests_fixture_critique(tmp_path: Path):
    execution_dir = tmp_path / "data" / "alert-connector-executions" / "20260508"
    execution_dir.mkdir(parents=True)
    execution_path = execution_dir / "EXEC-DARS-001.json"
    execution_path.write_text(
        json.dumps(
            {
                "execution_id": "EXEC-DARS-001",
                "action_plan_ref": "PLAN-DARS-001",
                "alert_decision_ref": "ALERT-DARS-001",
                "connector_id": "disabled-fixture-connector",
                "target_channel": "discord:#ops",
                "would_send": True,
                "live_delivery_permitted": False,
                "execution_status": "blocked",
                "blocked_reason": "live_delivery_disabled",
                "action_taken": "none",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    report = DarsRuntime(instance=InstanceRoot(tmp_path)).run_fixture_critique(
        yyyymmdd="20260508",
        source_execution_id="EXEC-DARS-001",
        critique_text="Confidence overstated; cite raw payload.",
        producer_id="dars-fixture-test",
    )

    assert report.handoff_refs == ["HANDOFF-DARS-001"]
    assert report.critique_refs == ["CRITIQUE-DARS-001"]
    assert report.linked_execution_refs == ["EXEC-DARS-001"]

    handoff_path = tmp_path / "data" / "agent-handoffs" / "20260508" / "HANDOFF-DARS-001.json"
    critique_path = tmp_path / "data" / "agent-critiques" / "20260508" / "CRITIQUE-DARS-001.json"
    handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
    critique = json.loads(critique_path.read_text(encoding="utf-8"))

    assert handoff["target_agent_system"] == "DARS"
    assert handoff["allowed_actions"] == "advisory_only"
    assert handoff["approval_state"] == "not_required"
    assert handoff["status"] == "linked"
    assert handoff["evidence_bundle"] == ["EXEC-DARS-001"]
    assert "no live external action" in handoff["constraints"]

    assert critique["critique_id"] == "CRITIQUE-DARS-001"
    assert critique["handoff_ref"] == "HANDOFF-DARS-001"
    assert critique["source_execution_ref"] == "EXEC-DARS-001"
    assert critique["allowed_actions"] == "advisory_only"
    assert critique["action_taken"] == "none"
    assert critique["status"] == "received"
    assert "Confidence overstated" in critique["critique_text"]
    assert (tmp_path / "reports" / "run-summaries" / "20260508" / "dars-critique-report.md").exists()
