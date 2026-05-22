"""DARS remote subscription dispatch harness tests.

Traceability: M-DARS-BE-6, docs/plans/dars-live-backend-implementation-plan.md.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.config.instance import InstanceRoot

ROOT = Path(__file__).resolve().parents[2]


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


def _build_valid_request(tmp_path: Path, **request_overrides):
    """Build a request whose activation+policy pair are mutually valid.

    Helper for defense-in-depth tests so each case only varies the field that
    drives the failure mode it exercises.
    """

    from hisys.agents.dars_remote_subscription_dispatch import (
        RemoteSubscriptionDispatchRequest,
    )

    policy_ref = _write_json(tmp_path / "remote-policy.json", _valid_policy_data())
    activation_ref = _write_json(
        tmp_path / "activation.json",
        _valid_activation_data(remote_policy_packet_ref=str(policy_ref)),
    )
    defaults = {
        "yyyymmdd": "20260521",
        "request_id": "REQ-DARS-REMOTE-DID-001",
        "backend_id": "claude_subscription_dars",
        "backend_kind": "remote_subscription",
        "source_execution_id": "EXEC-DARS-REMOTE-DID-001",
        "approval_ref": "APPROVAL-DARS-RS-20260521-001",
        "activation_packet_ref": str(activation_ref),
        "policy_packet_ref": str(policy_ref),
        "prompt": "Critique EXEC-DARS-REMOTE-DID-001 with provenance.",
    }
    defaults.update(request_overrides)
    return RemoteSubscriptionDispatchRequest(**defaults), policy_ref, activation_ref


def test_remote_subscription_dispatch_requires_executor_even_when_activation_and_policy_valid(tmp_path: Path):
    """Valid activation + valid policy must still fail closed if no executor is supplied."""

    from hisys.agents.dars_remote_subscription_dispatch import (
        run_dars_remote_subscription_dispatch,
    )

    request, _policy_ref, _activation_ref = _build_valid_request(tmp_path)

    with pytest.raises(ValueError, match="remote_subscription_executor_required"):
        run_dars_remote_subscription_dispatch(
            InstanceRoot(tmp_path),
            request,
            executor=None,
        )

    # No boundary record should have been written because the executor was never called.
    boundary_dir = tmp_path / "runtime-boundary" / "dars-remote-subscriptions"
    assert not boundary_dir.exists()


def test_remote_subscription_dispatch_rejects_empty_executor_output(tmp_path: Path):
    """An executor that returns blank/whitespace output must fail closed without a boundary record."""

    from hisys.agents.dars_remote_subscription_dispatch import (
        run_dars_remote_subscription_dispatch,
    )

    request, _policy_ref, _activation_ref = _build_valid_request(
        tmp_path, request_id="REQ-DARS-REMOTE-DID-002", source_execution_id="EXEC-DARS-REMOTE-DID-002"
    )

    def whitespace_only_executor(_payload):
        return "   "

    with pytest.raises(ValueError, match="remote_subscription_executor_empty_output"):
        run_dars_remote_subscription_dispatch(
            InstanceRoot(tmp_path),
            request,
            executor=whitespace_only_executor,
        )

    boundary_dir = tmp_path / "runtime-boundary" / "dars-remote-subscriptions"
    assert not boundary_dir.exists()


def test_remote_subscription_dispatch_rejects_non_string_executor_output(tmp_path: Path):
    """An executor that returns a non-string must fail closed before writing any boundary record."""

    from hisys.agents.dars_remote_subscription_dispatch import (
        run_dars_remote_subscription_dispatch,
    )

    request, _policy_ref, _activation_ref = _build_valid_request(
        tmp_path, request_id="REQ-DARS-REMOTE-DID-003", source_execution_id="EXEC-DARS-REMOTE-DID-003"
    )

    def non_string_executor(_payload):
        return None

    with pytest.raises(ValueError, match="remote_subscription_executor_empty_output"):
        run_dars_remote_subscription_dispatch(
            InstanceRoot(tmp_path),
            request,
            executor=non_string_executor,
        )

    boundary_dir = tmp_path / "runtime-boundary" / "dars-remote-subscriptions"
    assert not boundary_dir.exists()


def test_remote_subscription_dispatch_rejects_missing_activation_packet_file(tmp_path: Path):
    """Activation packet pointed to a non-existent file must fail closed with the missing code."""

    from hisys.agents.dars_remote_subscription_dispatch import (
        RemoteSubscriptionDispatchRequest,
        run_dars_remote_subscription_dispatch,
    )

    policy_ref = _write_json(tmp_path / "remote-policy.json", _valid_policy_data())
    activation_ref = tmp_path / "does-not-exist-activation.json"

    request = RemoteSubscriptionDispatchRequest(
        yyyymmdd="20260521",
        request_id="REQ-DARS-REMOTE-DID-004",
        backend_id="claude_subscription_dars",
        backend_kind="remote_subscription",
        source_execution_id="EXEC-DARS-REMOTE-DID-004",
        approval_ref="APPROVAL-DARS-RS-20260521-001",
        activation_packet_ref=str(activation_ref),
        policy_packet_ref=str(policy_ref),
        prompt="Critique EXEC-DARS-REMOTE-DID-004 with provenance.",
    )

    def fail_if_called(_payload):
        raise AssertionError("executor must not be reached when activation file is missing")

    with pytest.raises(ValueError, match="backend_activation_packet_required"):
        run_dars_remote_subscription_dispatch(
            InstanceRoot(tmp_path),
            request,
            executor=fail_if_called,
        )


def test_remote_subscription_dispatch_rejects_missing_policy_packet_file(tmp_path: Path):
    """Policy packet pointed to a non-existent file must fail closed with the missing code."""

    from hisys.agents.dars_remote_subscription_dispatch import (
        RemoteSubscriptionDispatchRequest,
        run_dars_remote_subscription_dispatch,
    )

    policy_ref = tmp_path / "does-not-exist-policy.json"
    activation_ref = _write_json(
        tmp_path / "activation.json",
        _valid_activation_data(remote_policy_packet_ref=str(policy_ref)),
    )

    request = RemoteSubscriptionDispatchRequest(
        yyyymmdd="20260521",
        request_id="REQ-DARS-REMOTE-DID-005",
        backend_id="claude_subscription_dars",
        backend_kind="remote_subscription",
        source_execution_id="EXEC-DARS-REMOTE-DID-005",
        approval_ref="APPROVAL-DARS-RS-20260521-001",
        activation_packet_ref=str(activation_ref),
        policy_packet_ref=str(policy_ref),
        prompt="Critique EXEC-DARS-REMOTE-DID-005 with provenance.",
    )

    def fail_if_called(_payload):
        raise AssertionError("executor must not be reached when policy file is missing")

    with pytest.raises(ValueError, match="remote_policy_packet_required"):
        run_dars_remote_subscription_dispatch(
            InstanceRoot(tmp_path),
            request,
            executor=fail_if_called,
        )


def test_remote_subscription_dispatch_rejects_invalid_request_id_shape(tmp_path: Path):
    """request_id containing disallowed characters must fail closed before any packet is loaded."""

    from hisys.agents.dars_remote_subscription_dispatch import (
        RemoteSubscriptionDispatchRequest,
        run_dars_remote_subscription_dispatch,
    )

    policy_ref = _write_json(tmp_path / "remote-policy.json", _valid_policy_data())
    activation_ref = _write_json(
        tmp_path / "activation.json",
        _valid_activation_data(remote_policy_packet_ref=str(policy_ref)),
    )

    request = RemoteSubscriptionDispatchRequest(
        yyyymmdd="20260521",
        request_id="bad request id with spaces",
        backend_id="claude_subscription_dars",
        backend_kind="remote_subscription",
        source_execution_id="EXEC-DARS-REMOTE-DID-006",
        approval_ref="APPROVAL-DARS-RS-20260521-001",
        activation_packet_ref=str(activation_ref),
        policy_packet_ref=str(policy_ref),
        prompt="Critique EXEC-DARS-REMOTE-DID-006 with provenance.",
    )

    def fail_if_called(_payload):
        raise AssertionError("executor must not be reached when request shape is invalid")

    with pytest.raises(ValueError, match="invalid_request_id"):
        run_dars_remote_subscription_dispatch(
            InstanceRoot(tmp_path),
            request,
            executor=fail_if_called,
        )


def test_remote_subscription_dispatch_rejects_invalid_yyyymmdd_partition(tmp_path: Path):
    """yyyymmdd not matching the 8-digit format must fail closed before any packet is loaded."""

    from hisys.agents.dars_remote_subscription_dispatch import (
        RemoteSubscriptionDispatchRequest,
        run_dars_remote_subscription_dispatch,
    )

    policy_ref = _write_json(tmp_path / "remote-policy.json", _valid_policy_data())
    activation_ref = _write_json(
        tmp_path / "activation.json",
        _valid_activation_data(remote_policy_packet_ref=str(policy_ref)),
    )

    request = RemoteSubscriptionDispatchRequest(
        yyyymmdd="2026-05-21",
        request_id="REQ-DARS-REMOTE-DID-007",
        backend_id="claude_subscription_dars",
        backend_kind="remote_subscription",
        source_execution_id="EXEC-DARS-REMOTE-DID-007",
        approval_ref="APPROVAL-DARS-RS-20260521-001",
        activation_packet_ref=str(activation_ref),
        policy_packet_ref=str(policy_ref),
        prompt="Critique EXEC-DARS-REMOTE-DID-007 with provenance.",
    )

    def fail_if_called(_payload):
        raise AssertionError("executor must not be reached when yyyymmdd is malformed")

    with pytest.raises(ValueError, match="invalid_date_partition"):
        run_dars_remote_subscription_dispatch(
            InstanceRoot(tmp_path),
            request,
            executor=fail_if_called,
        )


def test_remote_subscription_dispatch_rejects_activation_endpoint_scope_mismatch(tmp_path: Path):
    """Activation packet with non-external_api endpoint_scope must fail closed before executor contact."""

    from hisys.agents.dars_remote_subscription_dispatch import (
        run_dars_remote_subscription_dispatch,
    )

    policy_ref = _write_json(tmp_path / "remote-policy.json", _valid_policy_data())
    activation_ref = _write_json(
        tmp_path / "activation.json",
        _valid_activation_data(
            remote_policy_packet_ref=str(policy_ref),
            endpoint_scope="localhost_only",
        ),
    )

    from hisys.agents.dars_remote_subscription_dispatch import (
        RemoteSubscriptionDispatchRequest,
    )

    request = RemoteSubscriptionDispatchRequest(
        yyyymmdd="20260521",
        request_id="REQ-DARS-REMOTE-DID-008",
        backend_id="claude_subscription_dars",
        backend_kind="remote_subscription",
        source_execution_id="EXEC-DARS-REMOTE-DID-008",
        approval_ref="APPROVAL-DARS-RS-20260521-001",
        activation_packet_ref=str(activation_ref),
        policy_packet_ref=str(policy_ref),
        prompt="Critique EXEC-DARS-REMOTE-DID-008 with provenance.",
    )

    def fail_if_called(_payload):
        raise AssertionError("executor must not be reached when endpoint_scope mismatches")

    with pytest.raises(ValueError, match="activation_endpoint_scope_mismatch"):
        run_dars_remote_subscription_dispatch(
            InstanceRoot(tmp_path),
            request,
            executor=fail_if_called,
        )


# M-DARS-BE-6.2 — parametrized activation/policy mismatch coverage matrix.
# Each row pins one (mutation, expected ValueError code) pair so removing or
# weakening any single guard in `_enforce_activation_packet` or
# `_enforce_policy_packet` produces a deterministic test failure with a code
# that maps 1:1 to the harness invariant. No production code is modified.


_ACTIVATION_MISMATCH_CASES = [
    pytest.param(
        {"approval_ref": "APPROVAL-DARS-RS-OTHER"},
        {},
        "activation_approval_ref_mismatch",
        id="activation_approval_ref_mismatch",
    ),
    pytest.param(
        {"backend_id": "some_other_backend_id"},
        {},
        "activation_backend_id_mismatch",
        id="activation_backend_id_mismatch",
    ),
    pytest.param(
        {"backend_kind": "other_remote_kind"},
        {},
        "activation_backend_kind_mismatch",
        id="activation_backend_kind_mismatch",
    ),
    pytest.param(
        {"allowed_actions": "execute"},
        {},
        # The activation validator rejects allowed_actions=execute first with
        # `invalid_allowed_actions`; the dispatch harness re-raises that code
        # through `_raise_first_error` so the deterministic invariant is the
        # same code regardless of where the rejection happens.
        "invalid_allowed_actions",
        id="invalid_allowed_actions_in_activation",
    ),
]

_POLICY_MISMATCH_CASES = [
    pytest.param(
        {},
        {"access_mode": "api_key"},
        "invalid_access_mode",
        id="invalid_access_mode_in_policy",
    ),
    pytest.param(
        {},
        {"audit_required": False},
        "audit_required_must_be_true",
        id="audit_required_must_be_true_in_policy",
    ),
]


@pytest.mark.parametrize(
    "activation_overrides,policy_overrides,expected_code",
    _ACTIVATION_MISMATCH_CASES + _POLICY_MISMATCH_CASES,
)
def test_remote_subscription_dispatch_rejects_activation_policy_mismatches(
    tmp_path: Path,
    activation_overrides: dict,
    policy_overrides: dict,
    expected_code: str,
):
    """Each activation/policy mismatch must fail closed with the deterministic code."""

    from hisys.agents.dars_remote_subscription_dispatch import (
        RemoteSubscriptionDispatchRequest,
        run_dars_remote_subscription_dispatch,
    )

    policy_data = _valid_policy_data(**policy_overrides)
    policy_ref = _write_json(tmp_path / "remote-policy.json", policy_data)
    activation_overrides_with_policy = {
        "remote_policy_packet_ref": str(policy_ref),
        **activation_overrides,
    }
    activation_data = _valid_activation_data(**activation_overrides_with_policy)
    activation_ref = _write_json(tmp_path / "activation.json", activation_data)

    request = RemoteSubscriptionDispatchRequest(
        yyyymmdd="20260521",
        request_id="REQ-DARS-REMOTE-MATRIX-001",
        backend_id="claude_subscription_dars",
        backend_kind="remote_subscription",
        source_execution_id="EXEC-DARS-REMOTE-MATRIX-001",
        approval_ref="APPROVAL-DARS-RS-20260521-001",
        activation_packet_ref=str(activation_ref),
        policy_packet_ref=str(policy_ref),
        prompt="Critique EXEC-DARS-REMOTE-MATRIX-001 with provenance.",
    )

    def fail_if_called(_payload):
        raise AssertionError(
            f"executor must not be reached for mismatch case {expected_code}"
        )

    with pytest.raises(ValueError, match=expected_code):
        run_dars_remote_subscription_dispatch(
            InstanceRoot(tmp_path),
            request,
            executor=fail_if_called,
        )

    boundary_dir = tmp_path / "runtime-boundary" / "dars-remote-subscriptions"
    assert not boundary_dir.exists()


def test_remote_subscription_dispatch_rejects_activation_remote_policy_ref_mismatch(tmp_path: Path):
    """Activation packet whose remote_policy_packet_ref does not match the request's policy_packet_ref must fail closed."""

    from hisys.agents.dars_remote_subscription_dispatch import (
        RemoteSubscriptionDispatchRequest,
        run_dars_remote_subscription_dispatch,
    )

    policy_ref = _write_json(tmp_path / "remote-policy.json", _valid_policy_data())
    # Activation references a *different* policy path than the request supplies.
    activation_data = _valid_activation_data(
        remote_policy_packet_ref=str(tmp_path / "other-policy.json"),
    )
    activation_ref = _write_json(tmp_path / "activation.json", activation_data)

    request = RemoteSubscriptionDispatchRequest(
        yyyymmdd="20260521",
        request_id="REQ-DARS-REMOTE-MATRIX-002",
        backend_id="claude_subscription_dars",
        backend_kind="remote_subscription",
        source_execution_id="EXEC-DARS-REMOTE-MATRIX-002",
        approval_ref="APPROVAL-DARS-RS-20260521-001",
        activation_packet_ref=str(activation_ref),
        policy_packet_ref=str(policy_ref),
        prompt="Critique EXEC-DARS-REMOTE-MATRIX-002 with provenance.",
    )

    def fail_if_called(_payload):
        raise AssertionError("executor must not be reached when activation_remote_policy_ref mismatches")

    with pytest.raises(ValueError, match="activation_remote_policy_ref_mismatch"):
        run_dars_remote_subscription_dispatch(
            InstanceRoot(tmp_path),
            request,
            executor=fail_if_called,
        )

    boundary_dir = tmp_path / "runtime-boundary" / "dars-remote-subscriptions"
    assert not boundary_dir.exists()



def test_remote_subscription_multi_critic_panel_dispatch_writes_aggregate_boundary(tmp_path: Path):
    """M24: a governed remote-subscription DARS panel can run multiple critics via injected executors."""

    from hisys.agents.dars_remote_subscription_dispatch import (
        RemoteSubscriptionDispatchRequest,
        run_dars_remote_subscription_panel_dispatch,
    )

    policy_ref = _write_json(
        tmp_path / "codex-policy.json",
        _valid_policy_data(
            provider_id="codex",
            adapter_class="codex_subscription",
            subscription_account_ref="vault://dars/codex/subscription-001",
        ),
    )
    activation_ref = _write_json(
        tmp_path / "codex-activation.json",
        _valid_activation_data(
            backend_id="codex_subscription_dars",
            remote_policy_packet_ref=str(policy_ref),
        ),
    )
    requests = [
        RemoteSubscriptionDispatchRequest(
            yyyymmdd="20260521",
            request_id="REQ-DARS-MULTI-001",
            backend_id="codex_subscription_dars",
            backend_kind="remote_subscription",
            source_execution_id="EXEC-DARS-MULTI-LOGICAL",
            approval_ref="APPROVAL-DARS-RS-20260521-001",
            activation_packet_ref=str(activation_ref),
            policy_packet_ref=str(policy_ref),
            prompt="Critique candidate as logical_devil with provenance.",
        ),
        RemoteSubscriptionDispatchRequest(
            yyyymmdd="20260521",
            request_id="REQ-DARS-MULTI-001",
            backend_id="codex_subscription_dars",
            backend_kind="remote_subscription",
            source_execution_id="EXEC-DARS-MULTI-EVIDENCE",
            approval_ref="APPROVAL-DARS-RS-20260521-001",
            activation_packet_ref=str(activation_ref),
            policy_packet_ref=str(policy_ref),
            prompt="Critique candidate as evidence_governance_devil with provenance.",
        ),
    ]
    calls: list[dict] = []

    def fake_codex_executor(payload):
        calls.append(payload)
        return f"{payload['source_execution_id']} critique from injected Codex subscription executor"

    result = run_dars_remote_subscription_panel_dispatch(
        InstanceRoot(tmp_path),
        yyyymmdd="20260521",
        request_id="REQ-DARS-MULTI-001",
        panel_id="PANEL-DARS-REMOTE-MULTI-001",
        requests=requests,
        executor=fake_codex_executor,
    )

    assert result.status == "completed"
    assert result.panel_id == "PANEL-DARS-REMOTE-MULTI-001"
    assert result.request_id == "REQ-DARS-MULTI-001"
    assert len(result.critic_results) == 2
    assert len(result.boundary_refs) == 2
    assert result.external_call_made is True
    assert [call["source_execution_id"] for call in calls] == [
        "EXEC-DARS-MULTI-LOGICAL",
        "EXEC-DARS-MULTI-EVIDENCE",
    ]

    aggregate = json.loads((tmp_path / result.panel_boundary_ref).read_text(encoding="utf-8"))
    assert aggregate["schema_id"] == "hisys.dars.remote_subscription_panel_dispatch"
    assert aggregate["panel_id"] == "PANEL-DARS-REMOTE-MULTI-001"
    assert aggregate["request_id"] == "REQ-DARS-MULTI-001"
    assert aggregate["critic_count"] == 2
    assert aggregate["completed_critic_count"] == 2
    assert aggregate["provider_ids"] == ["codex"]
    assert aggregate["adapter_classes"] == ["codex_subscription"]
    assert aggregate["boundary_refs"] == result.boundary_refs
    assert aggregate["external_call_made"] is True
    assert aggregate["model_boundary_crossed"] is True
    assert aggregate["local_model_call_made"] is False
    assert aggregate["mutation_performed"] is False
    assert aggregate["publication_performed"] is False
    assert aggregate["allowed_actions"] == "advisory_only"
    assert aggregate["requires_human_review"] is True


def test_remote_subscription_multi_critic_panel_rejects_mixed_request_ids_before_executor(tmp_path: Path):
    """Panel-level dispatch must fail closed before executor contact if critic requests do not share request_id."""

    from hisys.agents.dars_remote_subscription_dispatch import (
        RemoteSubscriptionDispatchRequest,
        run_dars_remote_subscription_panel_dispatch,
    )

    policy_ref = _write_json(tmp_path / "remote-policy.json", _valid_policy_data())
    activation_ref = _write_json(
        tmp_path / "activation.json",
        _valid_activation_data(remote_policy_packet_ref=str(policy_ref)),
    )
    base = dict(
        yyyymmdd="20260521",
        backend_id="claude_subscription_dars",
        backend_kind="remote_subscription",
        approval_ref="APPROVAL-DARS-RS-20260521-001",
        activation_packet_ref=str(activation_ref),
        policy_packet_ref=str(policy_ref),
        prompt="Critique with provenance.",
    )
    requests = [
        RemoteSubscriptionDispatchRequest(
            **base,
            request_id="REQ-DARS-MULTI-001",
            source_execution_id="EXEC-DARS-MULTI-001",
        ),
        RemoteSubscriptionDispatchRequest(
            **base,
            request_id="REQ-DARS-MULTI-OTHER",
            source_execution_id="EXEC-DARS-MULTI-002",
        ),
    ]

    def fail_if_called(_payload):
        raise AssertionError("executor must not be reached for mismatched panel request ids")

    with pytest.raises(ValueError, match="panel_request_id_mismatch"):
        run_dars_remote_subscription_panel_dispatch(
            InstanceRoot(tmp_path),
            yyyymmdd="20260521",
            request_id="REQ-DARS-MULTI-001",
            panel_id="PANEL-DARS-REMOTE-MULTI-001",
            requests=requests,
            executor=fail_if_called,
        )

    boundary_dir = tmp_path / "runtime-boundary" / "dars-remote-subscription-panels"
    assert not boundary_dir.exists()


def test_codex_cli_subprocess_multi_critic_panel_prep_packet_matches_dispatch_contract(tmp_path: Path):
    """DARS-CODEX-CLI-SUBPROCESS-MULTI-CRITIC-PANEL-PREP defines a runnable bounded panel packet."""

    from hisys.agents.dars_remote_subscription_dispatch import (
        RemoteSubscriptionDispatchRequest,
        run_dars_remote_subscription_panel_dispatch,
    )

    packet_path = ROOT / "docs/examples/dars/codex-cli-subprocess-multi-critic-panel.prepared.json"
    packet = json.loads(packet_path.read_text(encoding="utf-8"))

    assert packet["schema_id"] == "hisys.dars.codex_cli_subprocess_multi_critic_panel_prep"
    assert packet["prepared_for_row"] == "DARS-CODEX-CLI-SUBPROCESS-MULTI-CRITIC-PANEL-PREP"
    assert packet["future_smoke_row"] == "DARS-CODEX-CLI-SUBPROCESS-MULTI-CRITIC-PANEL-SMOKE-GATE"
    assert packet["live_execution_performed"] is False
    assert packet["provider_id"] == "codex"
    assert packet["adapter_class"] == "codex_subscription"
    assert packet["critic_count"] >= 2

    policy_ref = _write_json(tmp_path / "codex-policy.json", _valid_policy_data(
        provider_id="codex",
        adapter_class="codex_subscription",
        subscription_account_ref="vault://existing-auth/codex-subscription",
        approval_ref=packet["approval_ref"],
    ))
    activation_ref = _write_json(tmp_path / "codex-activation.json", _valid_activation_data(
        backend_id=packet["backend_id"],
        backend_kind=packet["backend_kind"],
        approval_ref=packet["approval_ref"],
        remote_policy_packet_ref=str(policy_ref),
    ))

    requests = []
    for critic in packet["critics"]:
        assert critic["transport_kind"] == "codex_cli_subprocess_prompt_mode"
        assert critic["allowed_actions"] == "advisory_only"
        assert critic["mutation_performed"] is False
        assert critic["publication_performed"] is False
        assert critic["requires_human_review"] is True
        requests.append(RemoteSubscriptionDispatchRequest(
            yyyymmdd=packet["yyyymmdd"],
            request_id=packet["request_id"],
            backend_id=packet["backend_id"],
            backend_kind=packet["backend_kind"],
            source_execution_id=critic["source_execution_id"],
            approval_ref=packet["approval_ref"],
            activation_packet_ref=str(activation_ref),
            policy_packet_ref=str(policy_ref),
            prompt=critic["prompt"],
            transport_kind=critic["transport_kind"],
        ))

    calls: list[dict] = []

    def fake_codex_cli_executor(payload: dict):
        calls.append(payload)
        assert payload["provider_id"] == "codex"
        assert payload["adapter_class"] == "codex_subscription"
        assert payload["transport_kind"] == "codex_cli_subprocess_prompt_mode"
        assert payload["allowed_actions"] == "advisory_only"
        return f"{payload['source_execution_id']} advisory critique; requires_human_review=true"

    result = run_dars_remote_subscription_panel_dispatch(
        InstanceRoot(tmp_path),
        yyyymmdd=packet["yyyymmdd"],
        request_id=packet["request_id"],
        panel_id=packet["panel_id"],
        requests=requests,
        executor=fake_codex_cli_executor,
    )

    aggregate = json.loads((tmp_path / result.panel_boundary_ref).read_text(encoding="utf-8"))
    assert len(calls) == packet["critic_count"]
    assert aggregate["critic_count"] == packet["critic_count"]
    assert aggregate["completed_critic_count"] == packet["critic_count"]
    assert aggregate["transport_kind"] == "injected_subscription_executor_panel"
    assert aggregate["external_call_made"] is True
    assert aggregate["model_boundary_crossed"] is True
    assert aggregate["mutation_performed"] is False
    assert aggregate["publication_performed"] is False
    assert aggregate["requires_human_review"] is True


def test_codex_cli_subprocess_multi_critic_evidence_packet_prep_includes_claim_and_evidence(tmp_path: Path):
    """DARS-CODEX-CLI-SUBPROCESS-MULTI-CRITIC-EVIDENCE-PACKET-PREP fixes the evidence gap locally."""

    from hisys.agents.dars_remote_subscription_dispatch import (
        RemoteSubscriptionDispatchRequest,
        run_dars_remote_subscription_panel_dispatch,
    )

    packet_path = ROOT / "docs/examples/dars/codex-cli-subprocess-multi-critic-panel.evidence-prep.json"
    packet = json.loads(packet_path.read_text(encoding="utf-8"))

    assert packet["schema_id"] == "hisys.dars.codex_cli_subprocess_multi_critic_evidence_packet_prep"
    assert packet["prepared_for_row"] == "DARS-CODEX-CLI-SUBPROCESS-MULTI-CRITIC-EVIDENCE-PACKET-PREP"
    assert packet["future_smoke_row"] == "DARS-CODEX-CLI-SUBPROCESS-MULTI-CRITIC-EVIDENCE-PACKET-SMOKE-GATE"
    assert packet["live_execution_performed"] is False
    assert packet["completion_claim_upgrade_authorized"] is False
    assert packet["provider_id"] == "codex"
    assert packet["adapter_class"] == "codex_subscription"
    assert packet["critic_count"] >= 2

    bounded_claim = packet["bounded_claim"]
    assert bounded_claim["claim_id"] == "CLAIM-DARS-CODEX-PANEL-SMOKE-20260522-001"
    assert bounded_claim["claim_text"] == "codex_cli_subprocess_multi_critic_panel_smoke_completed_with_findings"
    assert bounded_claim["requires_human_review"] is True
    assert bounded_claim["completion_claim_upgrade_requested"] is False

    evidence_summary = packet["evidence_summary"]
    assert evidence_summary["panel_boundary_ref"].endswith("PANEL-DARS-CODEX-SUBPROCESS-20260522-001.json")
    assert evidence_summary["critic_count"] == 2
    assert evidence_summary["completed_critic_count"] == 2
    assert evidence_summary["external_call_made"] is True
    assert evidence_summary["model_boundary_crossed"] is True
    assert evidence_summary["mutation_performed"] is False
    assert evidence_summary["publication_performed"] is False
    assert evidence_summary["requires_human_review"] is True
    assert evidence_summary["known_findings"]

    policy_ref = _write_json(tmp_path / "codex-policy.json", _valid_policy_data(
        provider_id="codex",
        adapter_class="codex_subscription",
        subscription_account_ref="vault://existing-auth/codex-subscription",
        approval_ref=packet["approval_ref"],
    ))
    activation_ref = _write_json(tmp_path / "codex-activation.json", _valid_activation_data(
        backend_id=packet["backend_id"],
        backend_kind=packet["backend_kind"],
        approval_ref=packet["approval_ref"],
        remote_policy_packet_ref=str(policy_ref),
    ))

    requests = []
    calls: list[dict] = []
    for critic in packet["critics"]:
        assert critic["transport_kind"] == "codex_cli_subprocess_prompt_mode"
        assert critic["allowed_actions"] == "advisory_only"
        assert critic["mutation_performed"] is False
        assert critic["publication_performed"] is False
        assert critic["requires_human_review"] is True
        assert "Bounded claim:" in critic["prompt"]
        assert bounded_claim["claim_id"] in critic["prompt"]
        assert "Evidence summary:" in critic["prompt"]
        assert evidence_summary["panel_boundary_ref"] in critic["prompt"]
        assert "Do not upgrade the DARS completion claim" in critic["prompt"]
        requests.append(RemoteSubscriptionDispatchRequest(
            yyyymmdd=packet["yyyymmdd"],
            request_id=packet["request_id"],
            backend_id=packet["backend_id"],
            backend_kind=packet["backend_kind"],
            source_execution_id=critic["source_execution_id"],
            approval_ref=packet["approval_ref"],
            activation_packet_ref=str(activation_ref),
            policy_packet_ref=str(policy_ref),
            prompt=critic["prompt"],
            transport_kind=critic["transport_kind"],
        ))

    def fake_codex_cli_executor(payload: dict):
        calls.append(payload)
        assert payload["transport_kind"] == "codex_cli_subprocess_prompt_mode"
        assert packet["bounded_claim"]["claim_id"] in payload["prompt"]
        assert packet["evidence_summary"]["panel_boundary_ref"] in payload["prompt"]
        return f"{payload['source_execution_id']} advisory evidence-bearing critique; requires_human_review=true"

    result = run_dars_remote_subscription_panel_dispatch(
        InstanceRoot(tmp_path),
        yyyymmdd=packet["yyyymmdd"],
        request_id=packet["request_id"],
        panel_id=packet["panel_id"],
        requests=requests,
        executor=fake_codex_cli_executor,
    )

    aggregate = json.loads((tmp_path / result.panel_boundary_ref).read_text(encoding="utf-8"))
    assert len(calls) == packet["critic_count"]
    assert aggregate["critic_count"] == packet["critic_count"]
    assert aggregate["completed_critic_count"] == packet["critic_count"]
    assert aggregate["requires_human_review"] is True
