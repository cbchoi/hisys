"""RED tests for the Hisys MCP live LLM/provider adapter contract.

Traceability:
- docs/plans/hisys-mcp-full-live-dars-altas-judge-drloo-plan.md (Increment 2)

These tests define the live adapter contract without making any real network or
provider calls. They use a fake injected transport and a fake approval ledger so
that the production path remains fully testable in CI.

Requirements covered:
1. No approval -> blocked before provider invocation; external_call_made=false.
2. Missing provider_url_ref or credential_ref -> blocked / needs_more_evidence;
   external_call_made=false; transport must not be invoked.
3. Approval verification consults a decision packet / approval-ledger record
   that names approver role, approved tool/subsystem, allowed provider refs,
   time window, cost/quota boundary, and approval artifact ref; invalid or
   missing approval_ref returns blocked.
4. A fake live adapter success returns execution_mode=live_llm,
   result_basis='Live LLM/provider', llm_service_used=true,
   external_call_made=true, provider_ref/provider_url_ref/credential_ref/
   approval_ref, redacted telemetry, and requires_human_review=true.
5. Secrets are not persisted in payloads/artifacts.
"""

from __future__ import annotations

import importlib
from typing import Any


def _live_module():
    return importlib.import_module("hisys.mcp.live_adapters")


def _to_dict(model_or_mapping: object) -> dict[str, Any]:
    if isinstance(model_or_mapping, dict):
        return model_or_mapping
    if hasattr(model_or_mapping, "model_dump"):
        return model_or_mapping.model_dump(mode="json")  # type: ignore[attr-defined]
    raise AssertionError(
        f"live adapter result is not a dict/model envelope: {type(model_or_mapping)!r}"
    )


def _valid_approval_record() -> dict[str, Any]:
    return {
        "approval_ref": "APPROVAL-MCP-LIVE-ALTAS-001",
        "approver_role": "release_steward",
        "approved_tool": "altas_search_live",
        "approved_subsystem": "altas",
        "allowed_provider_refs": ["provider://fake-live-search"],
        "approval_window_start": "2026-06-01T00:00:00Z",
        "approval_window_end": "2026-12-31T23:59:59Z",
        "cost_quota_ceiling_usd": 1.0,
        "approval_artifact_ref": (
            "data/approvals/2026/APPROVAL-MCP-LIVE-ALTAS-001.json"
        ),
        "human_approved": True,
    }


def _valid_request(**overrides: Any) -> dict[str, Any]:
    request: dict[str, Any] = {
        "subsystem": "altas",
        "tool_name": "altas_search_live",
        "request_id": "REQ-LIVE-ALTAS-001",
        "approval_ref": "APPROVAL-MCP-LIVE-ALTAS-001",
        "provider_url_ref": "provider://fake-live-search",
        "credential_ref": "credstore://altas/live-search/v1",
        "prompt_summary": "advisory live altas_search rehearsal",
    }
    request.update(overrides)
    return request


def _approval_ledger(*records: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {record["approval_ref"]: record for record in records}


class _SpyFakeTransport:
    """Fake transport that records every invocation; never makes a network call."""

    def __init__(
        self,
        *,
        response: dict[str, Any] | None = None,
        raise_error: Exception | None = None,
    ) -> None:
        self.invocations: list[dict[str, Any]] = []
        self._response = response or {
            "provider_request_id": "fake-provider-req-001",
            "provider_ref": "fake-live-llm/v1",
            "latency_ms": 42,
            "cost_usd": 0.0001,
            "tokens_in": 10,
            "tokens_out": 7,
            "redacted_output_excerpt": "advisory output (fake live transport)",
        }
        self._raise_error = raise_error

    def invoke(self, *, request: Any) -> dict[str, Any]:
        self.invocations.append({"request": request})
        if self._raise_error is not None:
            raise self._raise_error
        return dict(self._response)

    @property
    def invocation_count(self) -> int:
        return len(self.invocations)


# ---------------------------------------------------------------------------
# Requirement 1: no approval -> blocked before provider invocation
# ---------------------------------------------------------------------------


def test_live_adapter_without_approval_ref_is_blocked_before_provider_invocation() -> None:
    live = _live_module()
    transport = _SpyFakeTransport()
    request = _valid_request(approval_ref=None)

    envelope = _to_dict(
        live.invoke_live_adapter(
            request=request,
            transport=transport,
            approval_ledger=_approval_ledger(_valid_approval_record()),
        )
    )

    assert envelope["status"] == "blocked"
    assert envelope["tool_name"] == "altas_search_live"
    assert envelope["external_call_made"] is False
    assert envelope["mutation_performed"] is False
    assert envelope["publication_or_live_action_approved"] is False
    assert envelope["human_approval_required"] is True
    assert transport.invocation_count == 0
    payload = envelope["payload"]
    assert payload["external_call_made"] is False
    assert payload["llm_service_used"] is False
    assert payload["execution_mode"] != "live_llm"
    assert "approval" in (envelope.get("error") or "").lower()


def test_live_adapter_with_unknown_approval_ref_is_blocked_before_provider_invocation() -> None:
    live = _live_module()
    transport = _SpyFakeTransport()
    request = _valid_request(approval_ref="APPROVAL-UNKNOWN")

    envelope = _to_dict(
        live.invoke_live_adapter(
            request=request,
            transport=transport,
            approval_ledger=_approval_ledger(_valid_approval_record()),
        )
    )

    assert envelope["status"] == "blocked"
    assert envelope["external_call_made"] is False
    assert transport.invocation_count == 0
    assert "approval" in (envelope.get("error") or "").lower()


# ---------------------------------------------------------------------------
# Requirement 2: missing provider/credential refs -> blocked or needs_more_evidence
# ---------------------------------------------------------------------------


def test_live_adapter_without_provider_url_ref_blocks_without_invocation() -> None:
    live = _live_module()
    transport = _SpyFakeTransport()
    request = _valid_request(provider_url_ref=None)

    envelope = _to_dict(
        live.invoke_live_adapter(
            request=request,
            transport=transport,
            approval_ledger=_approval_ledger(_valid_approval_record()),
        )
    )

    assert envelope["status"] in {"blocked", "needs_more_evidence"}
    assert envelope["external_call_made"] is False
    assert envelope["payload"]["external_call_made"] is False
    assert envelope["payload"]["llm_service_used"] is False
    assert transport.invocation_count == 0
    assert "provider_url_ref" in (envelope.get("error") or "")


def test_live_adapter_without_credential_ref_blocks_without_invocation() -> None:
    live = _live_module()
    transport = _SpyFakeTransport()
    request = _valid_request(credential_ref=None)

    envelope = _to_dict(
        live.invoke_live_adapter(
            request=request,
            transport=transport,
            approval_ledger=_approval_ledger(_valid_approval_record()),
        )
    )

    assert envelope["status"] in {"blocked", "needs_more_evidence"}
    assert envelope["external_call_made"] is False
    assert envelope["payload"]["external_call_made"] is False
    assert transport.invocation_count == 0
    assert "credential_ref" in (envelope.get("error") or "")


# ---------------------------------------------------------------------------
# Requirement 3: approval verification reads structured decision packet
# ---------------------------------------------------------------------------


def test_live_adapter_rejects_approval_packet_missing_required_fields() -> None:
    live = _live_module()
    transport = _SpyFakeTransport()
    incomplete_record = {
        "approval_ref": "APPROVAL-MCP-LIVE-ALTAS-001",
        # missing approver_role, approved_tool, approved_subsystem,
        # allowed_provider_refs, time window, cost ceiling, artifact ref
    }
    request = _valid_request()

    envelope = _to_dict(
        live.invoke_live_adapter(
            request=request,
            transport=transport,
            approval_ledger=_approval_ledger(incomplete_record),
        )
    )

    assert envelope["status"] == "blocked"
    assert envelope["external_call_made"] is False
    assert transport.invocation_count == 0
    error_text = (envelope.get("error") or "").lower()
    assert "approval" in error_text


def test_live_adapter_rejects_approval_record_whose_tool_does_not_match_request() -> None:
    live = _live_module()
    transport = _SpyFakeTransport()
    record = _valid_approval_record()
    record["approved_tool"] = "judge_advisory_live"  # mismatch vs altas_search_live
    record["approved_subsystem"] = "judge"

    envelope = _to_dict(
        live.invoke_live_adapter(
            request=_valid_request(),
            transport=transport,
            approval_ledger=_approval_ledger(record),
        )
    )

    assert envelope["status"] == "blocked"
    assert envelope["external_call_made"] is False
    assert transport.invocation_count == 0


def test_live_adapter_rejects_approval_record_whose_provider_ref_is_not_allowed() -> None:
    live = _live_module()
    transport = _SpyFakeTransport()
    record = _valid_approval_record()
    record["allowed_provider_refs"] = ["provider://something-else"]

    envelope = _to_dict(
        live.invoke_live_adapter(
            request=_valid_request(),
            transport=transport,
            approval_ledger=_approval_ledger(record),
        )
    )

    assert envelope["status"] == "blocked"
    assert envelope["external_call_made"] is False
    assert transport.invocation_count == 0


def test_live_adapter_rejects_approval_record_with_human_approved_false() -> None:
    live = _live_module()
    transport = _SpyFakeTransport()
    record = _valid_approval_record()
    record["human_approved"] = False

    envelope = _to_dict(
        live.invoke_live_adapter(
            request=_valid_request(),
            transport=transport,
            approval_ledger=_approval_ledger(record),
        )
    )

    assert envelope["status"] == "blocked"
    assert envelope["external_call_made"] is False
    assert transport.invocation_count == 0


# ---------------------------------------------------------------------------
# Requirement 4: fake live adapter success returns live envelope fields
# ---------------------------------------------------------------------------


def test_fake_live_adapter_success_returns_live_envelope_fields() -> None:
    live = _live_module()
    transport = _SpyFakeTransport()

    envelope = _to_dict(
        live.invoke_live_adapter(
            request=_valid_request(),
            transport=transport,
            approval_ledger=_approval_ledger(_valid_approval_record()),
        )
    )

    assert envelope["status"] == "ok"
    assert envelope["tool_name"] == "altas_search_live"
    assert envelope["external_call_made"] is True
    assert envelope["human_approval_required"] is True
    assert envelope["mutation_performed"] is False
    assert envelope["publication_or_live_action_approved"] is False

    payload = envelope["payload"]
    assert payload["execution_mode"] == "live_llm"
    assert payload["result_basis"] == "Live LLM/provider"
    assert payload["llm_service_used"] is True
    assert payload["external_call_made"] is True
    assert payload["requires_human_review"] is True
    assert payload["advisory_only"] is True
    assert payload["mutation_performed"] is False
    assert payload["publication_or_live_action_approved"] is False

    assert payload["approval_ref"] == "APPROVAL-MCP-LIVE-ALTAS-001"
    assert payload["provider_url_ref"] == "provider://fake-live-search"
    assert payload["credential_ref"] == "credstore://altas/live-search/v1"
    assert payload["provider_ref"] == "fake-live-llm/v1"

    telemetry = payload["telemetry"]
    assert telemetry["provider_request_id"] == "fake-provider-req-001"
    assert telemetry["latency_ms"] == 42
    assert telemetry["cost_usd"] == 0.0001
    assert telemetry["tokens_in"] == 10
    assert telemetry["tokens_out"] == 7
    assert "redacted_output_excerpt" in telemetry

    assert transport.invocation_count == 1


def test_fake_live_adapter_failure_does_not_fabricate_success() -> None:
    live = _live_module()
    transport = _SpyFakeTransport(raise_error=RuntimeError("fake provider rate-limited"))

    envelope = _to_dict(
        live.invoke_live_adapter(
            request=_valid_request(),
            transport=transport,
            approval_ledger=_approval_ledger(_valid_approval_record()),
        )
    )

    assert envelope["status"] in {"needs_more_evidence", "blocked", "error"}
    payload = envelope["payload"]
    assert payload["llm_service_used"] is False or payload["llm_service_used"] is True
    assert payload["execution_mode"] != "live_llm" or envelope["status"] != "ok"
    assert payload["mutation_performed"] is False
    assert payload["publication_or_live_action_approved"] is False
    assert transport.invocation_count == 1


# ---------------------------------------------------------------------------
# Requirement 5: secrets are not persisted in payloads
# ---------------------------------------------------------------------------


def test_live_adapter_does_not_persist_raw_secret_values_in_payload() -> None:
    live = _live_module()
    raw_secret = "sk-LIVE-RAW-SECRET-VALUE-FAKE-001"
    transport = _SpyFakeTransport(
        response={
            "provider_request_id": "fake-provider-req-002",
            "provider_ref": "fake-live-llm/v1",
            "latency_ms": 33,
            "cost_usd": 0.0002,
            "tokens_in": 11,
            "tokens_out": 5,
            # The transport tries to leak a raw secret in the output excerpt.
            "redacted_output_excerpt": (
                f"output containing token={raw_secret} and password={raw_secret}"
            ),
        }
    )
    request = _valid_request(
        prompt_summary=f"advisory prompt referencing token={raw_secret}",
        # An adapter caller may accidentally pass a raw secret in extras; the
        # adapter must not persist it verbatim.
        extras={"trace_log": f"Authorization: Bearer {raw_secret}"},
    )

    envelope = _to_dict(
        live.invoke_live_adapter(
            request=request,
            transport=transport,
            approval_ledger=_approval_ledger(_valid_approval_record()),
        )
    )

    serialized = repr(envelope)
    assert raw_secret not in serialized, "raw secret leaked into adapter envelope"

    payload = envelope["payload"]
    # credential_ref is a non-secret pointer and must be retained.
    assert payload.get("credential_ref") == "credstore://altas/live-search/v1"
    # The raw secret value must never appear in payload telemetry/prompt fields.
    assert raw_secret not in repr(payload)


def test_live_adapter_blocked_outputs_do_not_persist_credentials_or_secrets() -> None:
    live = _live_module()
    transport = _SpyFakeTransport()
    raw_secret = "sk-BLOCKED-PATH-SECRET-FAKE-002"
    request = _valid_request(
        approval_ref=None,
        prompt_summary=f"prompt with token={raw_secret}",
        extras={"note": f"password={raw_secret}"},
    )

    envelope = _to_dict(
        live.invoke_live_adapter(
            request=request,
            transport=transport,
            approval_ledger=_approval_ledger(_valid_approval_record()),
        )
    )

    assert envelope["status"] == "blocked"
    assert raw_secret not in repr(envelope)
