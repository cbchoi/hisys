"""DARS live-provider fail-closed adapter tests.

Traceability: HISYS-FR-DARS-CP-010, HISYS-FR-DARS-CP-011,
HISYS-T-DARS-CP-012, HISYS-T-DARS-CP-013, DARS-LIVE-RELEASE-R2-ADAPTER,
docs/plans/dars-panel-live-provider-unattended-release-final-plan.md.

These tests exercise only the local adapter, the R1 policy validator, the
existing backend-activation validator, and an injected fake transport. They
never read credentials, open sockets, call a provider, or activate live
dispatch. The R2 adapter is fail-closed for real provider calls; only the
fake/injected transport seam is reachable here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from hisys.agents.dars_live_provider_adapter import (
    DARS_LIVE_PROVIDER_ADAPTER_SCHEMA_ID,
    DARS_LIVE_PROVIDER_ADAPTER_SCHEMA_VERSION,
    DARS_LIVE_PROVIDER_LIVE_TRANSPORT_ENV_VAR,
    DarsLiveProviderAdapterRequest,
    DarsLiveProviderAdapterResult,
    run_dars_live_provider_adapter,
)
from hisys.agents.dars_live_provider_transport import (
    FakeLiveProviderTransport,
    LiveProviderTransportFailure,
)
from hisys.config.instance import InstanceRoot


def _valid_policy_data(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "policy_id": "DARS-LP-POL-20260523-001",
        "approval_ref": "APPROVAL-DARS-LP-20260523-001",
        "operator_id": "operator:cbchoi",
        "provider_id": "claude",
        "provider_kind": "subscription",
        "model_id": "claude-opus-4-7",
        "credential_ref": "env://HISYS_DARS_PROVIDER_TOKEN",
        "credential_ref_kind": "env",
        "endpoint_ref": "subscription://claude/default",
        "allowed_actions": "advisory_only",
        "external_call_allowed": True,
        "mutation_allowed": False,
        "publication_allowed": False,
        "requires_human_review": True,
        "max_prompt_bytes": 4096,
        "max_output_bytes": 4096,
        "rate_limit_per_minute": 30,
        "cost_budget_ref": "budget://dars/live-provider/2026-05",
        "expires_at": "2026-06-23T00:00:00Z",
        "redaction_policy_ref": "policy://hisys/dars/live-provider-redaction-v1",
        "audit_required": True,
    }
    data.update(overrides)
    return data


def _valid_activation_data(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "activation_id": "DARS-LP-ACT-20260523-001",
        "backend_id": "dars-live-claude-001",
        "backend_kind": "live_provider_subscription",
        "endpoint_scope": "external_api",
        "allowed_actions": "advisory_only",
        "approval_ref": "APPROVAL-DARS-LP-20260523-001",
        "human_approved": True,
        "expires_at": "2026-06-23T00:00:00Z",
        "remote_policy_packet_ref": "inline://policy-ref",
    }
    data.update(overrides)
    return data


def _write_packet(tmp_path: Path, name: str, data: dict[str, object]) -> str:
    path = tmp_path / name
    path.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")
    return str(path)


def _make_request(
    tmp_path: Path,
    *,
    mode: str = "dry_run",
    policy_overrides: dict[str, object] | None = None,
    activation_overrides: dict[str, object] | None = None,
    approval_ref: str = "APPROVAL-DARS-LP-20260523-001",
    backend_id: str = "dars-live-claude-001",
) -> DarsLiveProviderAdapterRequest:
    policy_data = _valid_policy_data(**(policy_overrides or {}))
    activation_data = _valid_activation_data(**(activation_overrides or {}))
    policy_ref = _write_packet(tmp_path, "policy.json", policy_data)
    activation_ref = _write_packet(tmp_path, "activation.json", activation_data)
    activation_data["remote_policy_packet_ref"] = policy_ref
    Path(activation_ref).write_text(
        json.dumps(activation_data, sort_keys=True), encoding="utf-8"
    )
    return DarsLiveProviderAdapterRequest(
        request_id="DARS-LP-REQ-20260523-001",
        source_execution_id="src-exec-001",
        backend_id=backend_id,
        policy_packet_ref=policy_ref,
        activation_packet_ref=activation_ref,
        approval_ref=approval_ref,
        prompt_packet_ref="redacted://dars/live-provider/prompt-001",
        prompt_byte_count=128,
        yyyymmdd="20260523",
        mode=mode,
        now="2026-05-23T00:00:00Z",
    )


def _success_executor(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "critique_text": "advisory-only fake critique",
        "output_byte_count": 31,
        "input_tokens": 12,
        "output_tokens": 5,
        "latency_ms": 42,
    }


def _instance(tmp_path: Path) -> InstanceRoot:
    return InstanceRoot(root=tmp_path / "instance")


def test_dars_live_provider_adapter_schema_constants_are_stable():
    assert DARS_LIVE_PROVIDER_ADAPTER_SCHEMA_ID == "hisys.dars.live_provider_adapter"
    assert DARS_LIVE_PROVIDER_ADAPTER_SCHEMA_VERSION == "0.1.0"
    assert DARS_LIVE_PROVIDER_LIVE_TRANSPORT_ENV_VAR == (
        "HISYS_DARS_LIVE_PROVIDER_LIVE_TRANSPORT_ENABLED"
    )


def test_live_provider_adapter_requires_policy_approval_and_credential_ref(tmp_path):
    request = _make_request(tmp_path)
    transport = FakeLiveProviderTransport(executor=_success_executor)
    instance = _instance(tmp_path)

    # baseline: should succeed in dry_run mode
    result = run_dars_live_provider_adapter(
        request, transport=transport, instance=instance, env={}
    )
    assert isinstance(result, DarsLiveProviderAdapterResult)
    assert result.status == "completed"
    assert result.external_call_made is False
    assert result.mode == "dry_run"


def test_live_provider_adapter_fails_closed_without_transport(tmp_path):
    request = _make_request(tmp_path)
    instance = _instance(tmp_path)
    with pytest.raises(ValueError) as excinfo:
        run_dars_live_provider_adapter(
            request, transport=None, instance=instance, env={}
        )
    assert "live_provider_transport_required" in str(excinfo.value)


def test_live_provider_adapter_fails_closed_on_policy_without_credential_ref(tmp_path):
    request = _make_request(
        tmp_path,
        policy_overrides={"credential_ref": "", "credential_ref_kind": ""},
    )
    transport = FakeLiveProviderTransport(executor=_success_executor)
    instance = _instance(tmp_path)
    result = run_dars_live_provider_adapter(
        request, transport=transport, instance=instance, env={}
    )
    assert result.status == "failed"
    assert result.failure_code == "live_provider_policy_invalid"
    assert result.policy_issue_codes is not None
    assert "missing_credential_ref" in result.policy_issue_codes
    assert result.external_call_made is False


def test_live_provider_adapter_fails_closed_on_policy_with_raw_secret(tmp_path):
    request = _make_request(
        tmp_path,
        policy_overrides={"api_key": "FAKE_not_a_real_secret_value"},
    )
    transport = FakeLiveProviderTransport(executor=_success_executor)
    instance = _instance(tmp_path)
    result = run_dars_live_provider_adapter(
        request, transport=transport, instance=instance, env={}
    )
    assert result.status == "failed"
    assert result.failure_code == "live_provider_policy_invalid"
    assert "raw_secret_value_not_allowed" in (result.policy_issue_codes or set())


def test_live_provider_adapter_fails_closed_on_activation_without_human_approval(tmp_path):
    request = _make_request(
        tmp_path, activation_overrides={"human_approved": False}
    )
    transport = FakeLiveProviderTransport(executor=_success_executor)
    instance = _instance(tmp_path)
    result = run_dars_live_provider_adapter(
        request, transport=transport, instance=instance, env={}
    )
    assert result.status == "failed"
    assert result.failure_code == "live_provider_activation_invalid"
    assert "human_approval_required" in (result.activation_issue_codes or set())


def test_live_provider_adapter_fails_closed_on_approval_ref_mismatch(tmp_path):
    request = _make_request(
        tmp_path,
        activation_overrides={"approval_ref": "APPROVAL-MISMATCH"},
    )
    transport = FakeLiveProviderTransport(executor=_success_executor)
    instance = _instance(tmp_path)
    result = run_dars_live_provider_adapter(
        request, transport=transport, instance=instance, env={}
    )
    assert result.status == "failed"
    assert result.failure_code == "live_provider_approval_ref_mismatch"


def test_live_provider_adapter_fails_closed_on_policy_approval_mismatch(tmp_path):
    request = _make_request(
        tmp_path,
        policy_overrides={"approval_ref": "APPROVAL-OTHER-001"},
        activation_overrides={"approval_ref": "APPROVAL-OTHER-001"},
        approval_ref="APPROVAL-DARS-LP-20260523-001",
    )
    transport = FakeLiveProviderTransport(executor=_success_executor)
    instance = _instance(tmp_path)
    result = run_dars_live_provider_adapter(
        request, transport=transport, instance=instance, env={}
    )
    assert result.status == "failed"
    assert result.failure_code == "live_provider_approval_ref_mismatch"


def test_live_provider_adapter_fails_closed_on_missing_env_gate_in_live_mode(tmp_path):
    request = _make_request(tmp_path, mode="live")
    transport = FakeLiveProviderTransport(executor=_success_executor)
    instance = _instance(tmp_path)
    result = run_dars_live_provider_adapter(
        request, transport=transport, instance=instance, env={}
    )
    assert result.status == "failed"
    assert result.failure_code == "live_provider_env_gate_missing"
    assert result.external_call_made is False


def test_live_provider_adapter_live_mode_allowed_when_env_gate_set(tmp_path):
    request = _make_request(tmp_path, mode="live")
    transport = FakeLiveProviderTransport(executor=_success_executor)
    instance = _instance(tmp_path)
    result = run_dars_live_provider_adapter(
        request,
        transport=transport,
        instance=instance,
        env={DARS_LIVE_PROVIDER_LIVE_TRANSPORT_ENV_VAR: "true"},
    )
    assert result.status == "completed"
    assert result.mode == "live"
    # R2 still uses a FakeLiveProviderTransport even in live mode; a real
    # provider transport requires a separately approved later increment.
    assert result.external_call_made is False
    assert result.transport_kind == "fake_injected_provider_transport"


def test_live_provider_adapter_fails_closed_on_mutation_authority_in_policy(tmp_path):
    request = _make_request(
        tmp_path, policy_overrides={"mutation_allowed": True}
    )
    transport = FakeLiveProviderTransport(executor=_success_executor)
    instance = _instance(tmp_path)
    result = run_dars_live_provider_adapter(
        request, transport=transport, instance=instance, env={}
    )
    assert result.status == "failed"
    assert result.failure_code == "live_provider_policy_invalid"
    assert "mutation_authority_not_allowed" in (result.policy_issue_codes or set())


def test_live_provider_adapter_writes_boundary_record(tmp_path):
    request = _make_request(tmp_path)
    transport = FakeLiveProviderTransport(executor=_success_executor)
    instance = _instance(tmp_path)
    result = run_dars_live_provider_adapter(
        request, transport=transport, instance=instance, env={}
    )
    assert result.status == "completed"
    assert result.boundary_ref is not None
    boundary_path = instance.root / result.boundary_ref
    assert boundary_path.exists()
    payload = json.loads(boundary_path.read_text(encoding="utf-8"))
    assert payload["schema_id"] == DARS_LIVE_PROVIDER_ADAPTER_SCHEMA_ID
    assert payload["mode"] == "dry_run"
    assert payload["external_call_made"] is False
    assert payload["model_boundary_crossed"] is False
    assert payload["mutation_performed"] is False
    assert payload["publication_performed"] is False
    assert payload["advisory_only"] is True
    assert payload["requires_human_review"] is True
    assert payload["allowed_actions"] == "advisory_only"
    assert payload["provider_id"] == "claude"
    assert payload["model_id"] == "claude-opus-4-7"
    assert payload["request_id"] == "DARS-LP-REQ-20260523-001"
    assert payload["transport_kind"] == "fake_injected_provider_transport"
    assert "credential_ref" not in payload
    assert "token" not in payload
    assert "api_key" not in payload


def test_live_provider_adapter_propagates_transport_failure_code(tmp_path):
    def _failing_executor(payload: dict[str, Any]) -> dict[str, Any]:
        raise LiveProviderTransportFailure("fake_executor_timeout")

    request = _make_request(tmp_path)
    transport = FakeLiveProviderTransport(executor=_failing_executor)
    instance = _instance(tmp_path)
    result = run_dars_live_provider_adapter(
        request, transport=transport, instance=instance, env={}
    )
    assert result.status == "failed"
    assert result.failure_code == "fake_executor_timeout"
    assert result.external_call_made is False
    # Boundary record is written even on transport failure for audit.
    assert result.boundary_ref is not None
    payload = json.loads((instance.root / result.boundary_ref).read_text(encoding="utf-8"))
    assert payload["failure_code"] == "fake_executor_timeout"
    assert payload["status"] == "failed"


def test_live_provider_adapter_fails_closed_when_packet_files_missing(tmp_path):
    request = DarsLiveProviderAdapterRequest(
        request_id="DARS-LP-REQ-20260523-001",
        source_execution_id="src-exec-001",
        backend_id="dars-live-claude-001",
        policy_packet_ref=str(tmp_path / "does-not-exist-policy.json"),
        activation_packet_ref=str(tmp_path / "does-not-exist-activation.json"),
        approval_ref="APPROVAL-DARS-LP-20260523-001",
        prompt_packet_ref="redacted://dars/live-provider/prompt-001",
        prompt_byte_count=128,
        yyyymmdd="20260523",
        mode="dry_run",
        now="2026-05-23T00:00:00Z",
    )
    transport = FakeLiveProviderTransport(executor=_success_executor)
    instance = _instance(tmp_path)
    result = run_dars_live_provider_adapter(
        request, transport=transport, instance=instance, env={}
    )
    assert result.status == "failed"
    assert result.failure_code == "live_provider_policy_packet_unreadable"


def test_live_provider_adapter_rejects_unknown_mode(tmp_path):
    with pytest.raises(ValueError):
        _make_request(tmp_path, mode="autonomous")


def test_live_provider_adapter_rejects_invalid_yyyymmdd(tmp_path):
    request = _make_request(tmp_path)
    with pytest.raises(ValueError):
        DarsLiveProviderAdapterRequest(
            request_id="DARS-LP-REQ-20260523-001",
            source_execution_id="src-exec-001",
            backend_id="dars-live-claude-001",
            policy_packet_ref=request.policy_packet_ref,
            activation_packet_ref=request.activation_packet_ref,
            approval_ref="APPROVAL-DARS-LP-20260523-001",
            prompt_packet_ref="redacted://dars/live-provider/prompt-001",
            prompt_byte_count=128,
            yyyymmdd="2026-05-23",  # hyphenated, not yyyymmdd
            mode="dry_run",
            now="2026-05-23T00:00:00Z",
        )


def test_live_provider_adapter_fails_closed_on_backend_id_mismatch(tmp_path):
    request = _make_request(
        tmp_path,
        activation_overrides={"backend_id": "dars-live-other-002"},
    )
    transport = FakeLiveProviderTransport(executor=_success_executor)
    instance = _instance(tmp_path)
    result = run_dars_live_provider_adapter(
        request, transport=transport, instance=instance, env={}
    )
    assert result.status == "failed"
    assert result.failure_code == "live_provider_backend_id_mismatch"
