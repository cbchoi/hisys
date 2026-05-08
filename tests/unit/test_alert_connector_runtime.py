"""Chief Editor disabled connector runtime tests.

Traceability: HISYS-FR-CE-006, HISYS-FR-AGT-004, HISYS-D-015,
HISYS-T-022.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.chief_editor.connector import AlertConnectorRuntime
from hisys.config.instance import InstanceRoot


def test_disabled_alert_connector_records_blocked_execution_without_live_send(tmp_path: Path):
    plan_dir = tmp_path / "data" / "alert-action-plans" / "20260508"
    plan_dir.mkdir(parents=True)
    plan_path = plan_dir / "PLAN-APPROVED-001.json"
    plan_path.write_text(
        json.dumps(
            {
                "plan_id": "PLAN-APPROVED-001",
                "alert_decision_ref": "ALERT-APPROVED-001",
                "target_channel": "discord:#ops",
                "approval_required": False,
                "would_send": True,
                "blocked_reason": "live_delivery_disabled",
                "live_delivery_permitted": False,
                "action_taken": "none",
                "producer_id": "action-plan-test",
                "policy_refs": ["HISYS-FR-CE-006", "HISYS-T-021"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    report = AlertConnectorRuntime(
        instance=InstanceRoot(tmp_path),
        connector_id="disabled-discord-fixture",
    ).execute_run(yyyymmdd="20260508")

    assert report.action_plan_refs == ["PLAN-APPROVED-001"]
    assert report.execution_refs == ["EXEC-APPROVED-001"]
    assert report.blocked_refs == ["EXEC-APPROVED-001"]
    assert report.sent_refs == []
    execution_path = tmp_path / "data" / "alert-connector-executions" / "20260508" / "EXEC-APPROVED-001.json"
    execution = json.loads(execution_path.read_text(encoding="utf-8"))
    assert execution["connector_id"] == "disabled-discord-fixture"
    assert execution["action_plan_ref"] == "PLAN-APPROVED-001"
    assert execution["would_send"] is True
    assert execution["live_delivery_permitted"] is False
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "live_delivery_disabled"
    assert execution["action_taken"] == "none"
    assert (tmp_path / "reports" / "run-summaries" / "20260508" / "alert-connector-execution-report.md").exists()
