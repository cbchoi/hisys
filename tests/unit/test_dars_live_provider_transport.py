"""DARS live-provider transport contract tests.

Traceability: HISYS-FR-DARS-CP-010, HISYS-T-DARS-CP-012,
DARS-LIVE-RELEASE-R1-POLICY,
docs/plans/dars-panel-live-provider-unattended-release-final-plan.md.

These tests exercise only the transport request/result contract and a fake
injected executor. They never read credentials, open sockets, call a
provider, or activate a real transport.
"""

from __future__ import annotations

from typing import Any

import pytest

from hisys.agents.dars_live_provider_transport import (
    LIVE_PROVIDER_TRANSPORT_SCHEMA_ID,
    LIVE_PROVIDER_TRANSPORT_SCHEMA_VERSION,
    FakeLiveProviderTransport,
    LiveProviderTransportFailure,
    LiveProviderTransportRequest,
    LiveProviderTransportResult,
    run_live_provider_transport,
)


def _valid_request(**overrides: object) -> LiveProviderTransportRequest:
    kwargs: dict[str, Any] = dict(
        request_id="DARS-LP-REQ-20260523-001",
        source_execution_id="src-exec-001",
        backend_id="dars-live-claude-001",
        policy_ref="inline://policy-ref",
        approval_ref="APPROVAL-DARS-LP-20260523-001",
        activation_ref="inline://activation-ref",
        provider_id="claude",
        provider_kind="subscription",
        model_id="claude-opus-4-7",
        endpoint_ref="subscription://claude/default",
        prompt_packet_ref="redacted://dars/live-provider/prompt-001",
        prompt_byte_count=128,
        max_prompt_bytes=4096,
        max_output_bytes=4096,
        allowed_actions="advisory_only",
        external_call_allowed=True,
        mutation_allowed=False,
        publication_allowed=False,
        requires_human_review=True,
        redaction_policy_ref="policy://hisys/dars/live-provider-redaction-v1",
        transport_kind="fake_injected_provider_transport",
    )
    kwargs.update(overrides)
    return LiveProviderTransportRequest(**kwargs)


def test_live_provider_transport_schema_constants_are_stable():
    assert LIVE_PROVIDER_TRANSPORT_SCHEMA_ID == "hisys.dars.live_provider_transport"
    assert LIVE_PROVIDER_TRANSPORT_SCHEMA_VERSION == "0.1.0"


def test_live_provider_transport_uses_fake_executor_without_external_call():
    captured_payloads: list[dict[str, Any]] = []

    def _fake_executor(payload: dict[str, Any]) -> dict[str, Any]:
        captured_payloads.append(payload)
        return {
            "critique_text": "advisory-only fake critique",
            "output_byte_count": 31,
            "input_tokens": 12,
            "output_tokens": 5,
            "latency_ms": 42,
        }

    request = _valid_request()
    transport = FakeLiveProviderTransport(executor=_fake_executor)
    result = run_live_provider_transport(request, transport=transport)

    assert isinstance(result, LiveProviderTransportResult)
    assert result.status == "completed"
    assert result.external_call_made is False
    assert result.model_boundary_crossed is False
    assert result.mutation_performed is False
    assert result.publication_performed is False
    assert result.advisory_only is True
    assert result.requires_human_review is True
    assert result.transport_kind == "fake_injected_provider_transport"
    assert result.provider_id == "claude"
    assert result.model_id == "claude-opus-4-7"
    assert result.critique_text == "advisory-only fake critique"
    assert result.output_byte_count == 31
    assert result.input_tokens == 12
    assert result.output_tokens == 5
    assert result.latency_ms == 42
    assert result.failure_code is None

    assert len(captured_payloads) == 1
    payload = captured_payloads[0]
    assert payload["request_id"] == "DARS-LP-REQ-20260523-001"
    assert payload["provider_id"] == "claude"
    assert payload["model_id"] == "claude-opus-4-7"
    assert payload["prompt_packet_ref"] == "redacted://dars/live-provider/prompt-001"
    assert payload["approval_ref"] == "APPROVAL-DARS-LP-20260523-001"
    assert payload["policy_ref"] == "inline://policy-ref"
    assert payload["activation_ref"] == "inline://activation-ref"
    assert payload["allowed_actions"] == "advisory_only"
    assert payload["external_call_made"] is False
    assert payload["mutation_performed"] is False
    assert payload["publication_performed"] is False
    assert "credential_ref" not in payload
    assert "credential" not in payload
    assert "token" not in payload
    assert "api_key" not in payload
    assert "authorization" not in payload


def test_live_provider_transport_rejects_missing_transport():
    request = _valid_request()
    with pytest.raises(ValueError) as excinfo:
        run_live_provider_transport(request, transport=None)
    assert "live_provider_transport_required" in str(excinfo.value)


def test_live_provider_transport_rejects_raw_prompt_text_field():
    with pytest.raises(ValueError) as excinfo:
        _valid_request(prompt_packet_ref="literal raw prompt body")
    assert "prompt_packet_ref" in str(excinfo.value).lower()


def test_live_provider_transport_request_rejects_invalid_allowed_actions():
    with pytest.raises(ValueError):
        _valid_request(allowed_actions="autonomous_decision")


def test_live_provider_transport_request_rejects_mutation_authority():
    for flag in ("mutation_allowed", "publication_allowed"):
        with pytest.raises(ValueError):
            _valid_request(**{flag: True})


def test_live_provider_transport_request_rejects_disabled_external_call_allowed():
    with pytest.raises(ValueError):
        _valid_request(external_call_allowed=False)


def test_live_provider_transport_request_rejects_disabled_human_review():
    with pytest.raises(ValueError):
        _valid_request(requires_human_review=False)


def test_live_provider_transport_request_rejects_unbounded_prompt_or_output():
    for field, value in (
        ("max_prompt_bytes", 0),
        ("max_output_bytes", 0),
        ("max_prompt_bytes", -1),
        ("max_output_bytes", -1),
        ("prompt_byte_count", -5),
    ):
        with pytest.raises(ValueError):
            _valid_request(**{field: value})


def test_live_provider_transport_request_rejects_oversized_prompt_byte_count():
    with pytest.raises(ValueError):
        _valid_request(prompt_byte_count=5000, max_prompt_bytes=4096)


def test_live_provider_transport_rejects_unknown_transport_kind():
    with pytest.raises(ValueError):
        _valid_request(transport_kind="real_provider_http_call")


def test_live_provider_transport_records_failure_code_when_executor_raises_failure():
    def _failing_executor(payload: dict[str, Any]) -> dict[str, Any]:
        raise LiveProviderTransportFailure("fake_executor_timeout")

    transport = FakeLiveProviderTransport(executor=_failing_executor)
    result = run_live_provider_transport(_valid_request(), transport=transport)

    assert result.status == "failed"
    assert result.failure_code == "fake_executor_timeout"
    assert result.critique_text == ""
    assert result.external_call_made is False
    assert result.advisory_only is True
    assert result.requires_human_review is True


def test_live_provider_transport_rejects_oversized_output():
    def _oversized_executor(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "critique_text": "x" * 10,
            "output_byte_count": 10_000,
            "latency_ms": 1,
        }

    request = _valid_request(max_output_bytes=64)
    transport = FakeLiveProviderTransport(executor=_oversized_executor)
    result = run_live_provider_transport(request, transport=transport)

    assert result.status == "failed"
    assert result.failure_code == "live_provider_output_too_long"


def test_live_provider_transport_rejects_empty_executor_output():
    def _empty_executor(payload: dict[str, Any]) -> dict[str, Any]:
        return {"critique_text": "   ", "output_byte_count": 0, "latency_ms": 1}

    transport = FakeLiveProviderTransport(executor=_empty_executor)
    result = run_live_provider_transport(_valid_request(), transport=transport)

    assert result.status == "failed"
    assert result.failure_code == "live_provider_empty_output"


def test_live_provider_transport_rejects_executor_output_with_raw_secret_marker():
    def _secret_executor(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "critique_text": "leaked sk-fake-1234567890abcdefghij",
            "output_byte_count": 35,
            "latency_ms": 1,
        }

    transport = FakeLiveProviderTransport(executor=_secret_executor)
    result = run_live_provider_transport(_valid_request(), transport=transport)

    assert result.status == "failed"
    assert result.failure_code == "live_provider_output_not_redacted"


def test_live_provider_transport_rejects_unauthorized_authority_claim_in_output():
    def _authority_executor(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "critique_text": "result: mutation_performed=true; release published",
            "output_byte_count": 47,
            "latency_ms": 1,
        }

    transport = FakeLiveProviderTransport(executor=_authority_executor)
    result = run_live_provider_transport(_valid_request(), transport=transport)

    assert result.status == "failed"
    assert result.failure_code == "live_provider_output_claims_unauthorized_authority"
