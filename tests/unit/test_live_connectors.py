"""Live connector adapter control tests.

Traceability: HISYS-FR-AGT-004, HISYS-T-020, HISYS-T-022,
HISYS-CON-010, HISYS-CON-012, HISYS-CON-022..023.
"""

from __future__ import annotations

from pathlib import Path

from hisys.integrations.live_connectors import LiveConnectorRequest, evaluate_live_connector_request


def test_disabled_live_connector_request_is_blocked_and_persisted_as_boundary_record(tmp_path: Path) -> None:
    request = LiveConnectorRequest(
        connector_id="discord-live-alert",
        connector_type="discord",
        target="discord:#ops",
        requested_action="send_message",
        payload_summary="Notify operators about high-severity memo conflict.",
        approval_ref="APPROVAL-OPS-001",
        policy_refs=["HISYS-CE-POLICY-001"],
    )

    decision = evaluate_live_connector_request(
        request=request,
        runtime_root=tmp_path,
        yyyymmdd="20260509",
        enabled_connectors={},
    )

    assert decision.connector_id == "discord-live-alert"
    assert decision.execution_status == "blocked"
    assert decision.blocked_reason == "connector_disabled"
    assert decision.live_execution_permitted is False
    assert decision.action_taken == "none"
    assert decision.external_call_made is False
    assert decision.policy_refs == ["HISYS-CE-POLICY-001"]
    report_path = Path(decision.report_path)
    assert report_path == tmp_path / "runtime-boundary" / "live-connectors" / "20260509" / "live-connector-decision-discord-live-alert.md"
    assert report_path.exists()
    report = report_path.read_text(encoding="utf-8")
    assert "# Live Connector Execution Decision" in report
    assert "execution_status: `blocked`" in report
    assert "external_call_made: `False`" in report
    assert "HISYS-T-020" in report


def test_enabled_connector_still_requires_explicit_allowed_action_and_approval(tmp_path: Path) -> None:
    request = LiveConnectorRequest(
        connector_id="software-trigger",
        connector_type="software_trigger",
        target="deployment:prod",
        requested_action="restart_service",
        payload_summary="Restart production service.",
        approval_ref=None,
        policy_refs=["HISYS-CE-POLICY-001"],
    )

    decision = evaluate_live_connector_request(
        request=request,
        runtime_root=tmp_path,
        yyyymmdd="20260509",
        enabled_connectors={"software-trigger": {"allowed_actions": ["create_ticket"]}},
    )

    assert decision.execution_status == "blocked"
    assert decision.blocked_reason == "action_not_allowed"
    assert decision.live_execution_permitted is False
    assert decision.action_taken == "none"
    assert decision.external_call_made is False
