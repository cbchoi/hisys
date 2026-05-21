"""DARS remote subscription dispatch harness tests.

Traceability: M-DARS-BE-6, docs/plans/dars-live-backend-implementation-plan.md.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.config.instance import InstanceRoot


def _valid_policy_data(**overrides):
    data = {
        "policy_id": "DARS-RS-POLICY-20260521-001",
        "approval_ref": "APPROVAL-DARS-RS-20260521-001",
        "operator_id": "operator:cbchoi",
        "provider_id": "claude",
        "access_mode": "subscription",
        "subscription_account_ref": "vault://dars/claude/subscription-001",
        "adapter_class": "claude_subscription",
        "redaction_policy_ref": "redaction://dars/no-raw-source",
        "egress_scope": "subscription_only",
        "max_session_or_token_budget": 100000,
        "expires_at": "2026-06-21T00:00:00Z",
        "revocation_ref": "revocation://dars/claude/subscription-001",
        "audit_required": True,
    }
    data.update(overrides)
    return data


def _valid_activation_data(**overrides):
    data = {
        "activation_id": "DARS-BE-ACT-REMOTE-20260521-001",
        "backend_id": "claude_subscription_dars",
        "backend_kind": "remote_subscription",
        "endpoint_scope": "external_api",
        "allowed_actions": "advisory_only",
        "human_approved": True,
        "approval_ref": "APPROVAL-DARS-RS-20260521-001",
        "expires_at": "2026-06-21T00:00:00Z",
        "remote_policy_packet_ref": "remote-policy.json",
    }
    data.update(overrides)
    return data


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_remote_subscription_dispatch_uses_injected_executor_and_writes_boundary(tmp_path: Path):
    from hisys.agents.dars_remote_subscription_dispatch import (
        RemoteSubscriptionDispatchRequest,
        run_dars_remote_subscription_dispatch,
    )

    policy_ref = _write_json(tmp_path / "remote-policy.json", _valid_policy_data())
    activation_ref = _write_json(
        tmp_path / "activation.json",
        _valid_activation_data(remote_policy_packet_ref=str(policy_ref)),
    )
    calls = []

    def fake_subscription_executor(payload):
        calls.append(payload)
        assert payload["provider_id"] == "claude"
        assert payload["adapter_class"] == "claude_subscription"
        assert payload["allowed_actions"] == "advisory_only"
        assert payload["prompt"].startswith("Critique")
        return "Remote subscription DARS critique: cite missing evidence."

    result = run_dars_remote_subscription_dispatch(
        InstanceRoot(tmp_path),
        RemoteSubscriptionDispatchRequest(
            yyyymmdd="20260521",
            request_id="REQ-DARS-REMOTE-001",
            backend_id="claude_subscription_dars",
            backend_kind="remote_subscription",
            source_execution_id="EXEC-DARS-REMOTE-001",
            approval_ref="APPROVAL-DARS-RS-20260521-001",
            activation_packet_ref=str(activation_ref),
            policy_packet_ref=str(policy_ref),
            prompt="Critique EXEC-DARS-REMOTE-001 with provenance.",
        ),
        executor=fake_subscription_executor,
    )

    assert result.status == "completed"
    assert result.provider_id == "claude"
    assert result.adapter_class == "claude_subscription"
    assert result.critique_text.startswith("Remote subscription DARS critique")
    assert result.external_call_made is True
    assert len(calls) == 1

    boundary = json.loads((tmp_path / result.boundary_ref).read_text(encoding="utf-8"))
    assert boundary["schema_id"] == "hisys.dars.remote_subscription_dispatch"
    assert boundary["request_id"] == "REQ-DARS-REMOTE-001"
    assert boundary["backend_id"] == "claude_subscription_dars"
    assert boundary["provider_id"] == "claude"
    assert boundary["adapter_class"] == "claude_subscription"
    assert boundary["endpoint_scope"] == "external_api"
    assert boundary["approval_ref"] == "APPROVAL-DARS-RS-20260521-001"
    assert boundary["activation_ref"] == str(activation_ref)
    assert boundary["policy_ref"] == str(policy_ref)
    assert boundary["external_call_made"] is True
    assert boundary["model_boundary_crossed"] is True
    assert boundary["local_model_call_made"] is False
    assert boundary["mutation_performed"] is False
    assert boundary["publication_performed"] is False
    assert boundary["allowed_actions"] == "advisory_only"
    assert boundary["transport_kind"] == "injected_subscription_executor"


def test_remote_subscription_dispatch_blocks_before_executor_on_activation_policy_mismatch(tmp_path: Path):
    from hisys.agents.dars_remote_subscription_dispatch import (
        RemoteSubscriptionDispatchRequest,
        run_dars_remote_subscription_dispatch,
    )

    policy_ref = _write_json(
        tmp_path / "remote-policy.json",
        _valid_policy_data(approval_ref="APPROVAL-DARS-RS-OTHER"),
    )
    activation_ref = _write_json(
        tmp_path / "activation.json",
        _valid_activation_data(remote_policy_packet_ref=str(policy_ref)),
    )
    contacted_executor = False

    def fail_if_called(payload):
        nonlocal contacted_executor
        contacted_executor = True
        return "should not be called"

    with pytest.raises(ValueError, match="remote_policy_approval_ref_mismatch"):
        run_dars_remote_subscription_dispatch(
            InstanceRoot(tmp_path),
            RemoteSubscriptionDispatchRequest(
                yyyymmdd="20260521",
                request_id="REQ-DARS-REMOTE-002",
                backend_id="claude_subscription_dars",
                backend_kind="remote_subscription",
                source_execution_id="EXEC-DARS-REMOTE-002",
                approval_ref="APPROVAL-DARS-RS-20260521-001",
                activation_packet_ref=str(activation_ref),
                policy_packet_ref=str(policy_ref),
                prompt="Critique EXEC-DARS-REMOTE-002 with provenance.",
            ),
            executor=fail_if_called,
        )

    assert contacted_executor is False
