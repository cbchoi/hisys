"""DARS live/unattended operations status and rollback readiness tests.

Traceability:
- HISYS-FR-DARS-CP-014
- HISYS-T-DARS-CP-016
- DARS-LIVE-RELEASE-R6-STATUS-ROLLBACK
"""

from __future__ import annotations

import json
from pathlib import Path


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def test_dars_live_status_reports_kill_switch_and_latest_boundary_refs_without_secrets(tmp_path: Path) -> None:
    from hisys.operations.dars_live_status import build_dars_live_status

    instance = tmp_path / "instance"
    instance.mkdir()
    kill_switch_ref = "ops/dars-live-kill-switch.json"
    budget_state_ref = "ops/dars-live-budget-state.json"
    _write_json(instance / kill_switch_ref, {"kill_switch_engaged": True, "reason": "operator pause"})
    _write_json(instance / budget_state_ref, {"budget_cap_ref": "budget://dars-r6-dry-run", "used_usd": 0.42})

    secret_like = "sk-" + "x" * 24
    _write_json(
        instance
        / "runtime-boundary"
        / "dars-unattended-advisory"
        / "20260523"
        / "APPROVAL-DARS-LP-PANEL-SMOKE-20260523-001"
        / "REQ-001.json",
        {
            "request_id": "REQ-001",
            "status": "completed",
            "completed_at": "2026-05-23T10:00:00Z",
            "provider_debug_output": secret_like,
        },
    )
    _write_json(
        instance
        / "runtime-boundary"
        / "dars-unattended-advisory"
        / "20260523"
        / "APPROVAL-DARS-LP-PANEL-SMOKE-20260523-001"
        / "REQ-002.json",
        {
            "request_id": "REQ-002",
            "status": "failed",
            "completed_at": "2026-05-23T10:10:00Z",
            "failure_code": "provider_output_redaction_failed",
            "raw_output": secret_like,
        },
    )

    status = build_dars_live_status(
        instance_root=instance,
        yyyymmdd="20260523",
        policy_refs=["docs/examples/dars/live-provider-panel-smoke.policy.example.json"],
        standing_approval_ref="docs/examples/dars/unattended-standing-approval.example.json",
        kill_switch_ref=kill_switch_ref,
        budget_state_ref=budget_state_ref,
        rollback_runbook_ref="docs/runbooks/dars-live-rollback.md",
        release_ref="unreleased/dars-r6-local-safe",
    )

    assert status["schema_id"] == "hisys.dars_live.status"
    assert status["schema_version"] == "0.1.0"
    assert status["traceability"] == ["HISYS-FR-DARS-CP-014", "HISYS-T-DARS-CP-016"]
    assert status["kill_switch"]["ref"] == kill_switch_ref
    assert status["kill_switch"]["engaged"] is True
    assert status["budget"]["state_ref"] == budget_state_ref
    assert status["latest_boundary_refs"] == [
        "runtime-boundary/dars-unattended-advisory/20260523/APPROVAL-DARS-LP-PANEL-SMOKE-20260523-001/REQ-002.json",
        "runtime-boundary/dars-unattended-advisory/20260523/APPROVAL-DARS-LP-PANEL-SMOKE-20260523-001/REQ-001.json",
    ]
    assert status["failed_run_count"] == 1
    assert status["rollback"]["runbook_ref"] == "docs/runbooks/dars-live-rollback.md"
    assert status["boundary_flags"] == {
        "external_call_made": False,
        "credential_lookup_performed": False,
        "mutation_performed": False,
        "publication_performed": False,
        "live_action_authorized": False,
        "standing_approval_activated": False,
    }
    serialized = json.dumps(status, ensure_ascii=False)
    assert secret_like not in serialized
    assert "provider_debug_output" not in serialized
    assert "raw_output" not in serialized


def test_dars_live_status_writes_json_and_markdown_report(tmp_path: Path) -> None:
    from hisys.operations.dars_live_status import (
        build_dars_live_status,
        render_dars_live_status_text,
        write_dars_live_status_report,
    )

    instance = tmp_path / "instance"
    instance.mkdir()
    _write_json(instance / "ops/kill-switch.json", {"kill_switch_engaged": False})
    status = build_dars_live_status(
        instance_root=instance,
        yyyymmdd="20260523",
        policy_refs=["policy://dars-r6-local"],
        standing_approval_ref="approval://not-activated",
        kill_switch_ref="ops/kill-switch.json",
        budget_state_ref="ops/budget-state.json",
        rollback_runbook_ref="docs/runbooks/dars-live-rollback.md",
        release_ref="unreleased",
    )

    refs = write_dars_live_status_report(instance_root=instance, yyyymmdd="20260523", status=status)

    assert refs == {
        "json_ref": "reports/run-summaries/20260523/dars-live-status.json",
        "markdown_ref": "reports/run-summaries/20260523/dars-live-status.md",
    }
    persisted = json.loads((instance / refs["json_ref"]).read_text(encoding="utf-8"))
    assert persisted["schema_id"] == "hisys.dars_live.status"
    markdown = (instance / refs["markdown_ref"]).read_text(encoding="utf-8")
    assert "# DARS Live Operations Status" in markdown
    assert "standing_approval_activated: `false`" in markdown
    text = render_dars_live_status_text(status, json_ref=refs["json_ref"])
    assert "dars live status:" in text
    assert "live_action_authorized=false" in text


def test_dars_live_status_cli_writes_report_and_prints_json(tmp_path: Path, capsys) -> None:
    from hisys.cli.main import main

    instance = tmp_path / "instance"
    instance.mkdir()
    _write_json(instance / "ops/kill-switch.json", {"kill_switch_engaged": False})

    exit_code = main(
        [
            "dars-live-status",
            "--instance",
            str(instance),
            "--date",
            "20260523",
            "--policy-ref",
            "policy://dars-r6-local",
            "--standing-approval-ref",
            "approval://not-activated",
            "--kill-switch-ref",
            "ops/kill-switch.json",
            "--budget-state-ref",
            "ops/budget-state.json",
            "--rollback-runbook-ref",
            "docs/runbooks/dars-live-rollback.md",
            "--release-ref",
            "unreleased",
            "--format",
            "json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"]["schema_id"] == "hisys.dars_live.status"
    assert payload["status"]["kill_switch"]["engaged"] is False
    assert payload["artifacts"]["json_ref"] == "reports/run-summaries/20260523/dars-live-status.json"
    assert (instance / payload["artifacts"]["json_ref"]).exists()


def test_dars_live_operations_and_rollback_runbooks_define_disable_recovery_and_privacy() -> None:
    operations = Path("docs/runbooks/dars-live-operations.md").read_text(encoding="utf-8")
    rollback = Path("docs/runbooks/dars-live-rollback.md").read_text(encoding="utf-8")

    for phrase in [
        "HISYS-FR-DARS-CP-014",
        "kill-switch state",
        "latest boundary refs",
        "budget/circuit-breaker state",
        "does not authorize live provider calls",
        "evidence-retention",
        "privacy",
        "troubleshooting",
    ]:
        assert phrase in operations

    for phrase in [
        "revoke standing approval",
        "disable provider policy",
        "rotate credential outside Hisys",
        "stop scheduler outside Hisys",
        "verify no further runs",
        "rollback readiness",
        "human review",
    ]:
        assert phrase in rollback
