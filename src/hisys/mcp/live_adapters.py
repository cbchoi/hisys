"""Live LLM/provider adapter contract for the Hisys MCP wrappers.

This module defines the transport-neutral request/result shape for live
LLM/provider use behind the MCP gateway. It does *not* perform any real network
or provider call; production callers must inject an explicit transport, and the
fake transport defined here is for tests and dry-runs only.

Safety invariants enforced by ``invoke_live_adapter``:

* Live provider invocation is gated on a structured approval/decision-packet
  record (an "approval ledger" entry). Missing, mismatched, or human-unapproved
  records return ``blocked`` and the transport is not invoked.
* Missing ``provider_url_ref`` or ``credential_ref`` returns ``blocked`` and the
  transport is not invoked.
* Successful invocation surfaces only non-secret references
  (``provider_url_ref``, ``credential_ref``, ``approval_ref``, ``provider_ref``)
  and redacted telemetry; raw secret values are stripped from every persisted
  payload.

Traceability:
    docs/plans/hisys-mcp-full-live-dars-altas-judge-drloo-plan.md (Increment 2)
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Protocol

from .cli_adapter import redact_text
from .contracts import McpToolResultEnvelope


_LIVE_RESULT_BASIS = "Live LLM/provider"
_LIVE_EXECUTION_MODE = "live_llm"

_REQUIRED_APPROVAL_FIELDS = (
    "approval_ref",
    "approver_role",
    "approved_tool",
    "approved_subsystem",
    "allowed_provider_refs",
    "approval_window_start",
    "approval_window_end",
    "cost_quota_ceiling_usd",
    "approval_artifact_ref",
    "human_approved",
)

_SECRET_VALUE_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_\-]{4,}"),
    re.compile(r"sk_[A-Za-z0-9_\-]{4,}"),
    re.compile(r"ghp_[A-Za-z0-9_\-]{4,}"),
    re.compile(r"xox[bp]-[A-Za-z0-9_\-]{4,}"),
    re.compile(r"hf_[A-Za-z0-9_\-]{4,}"),
)

_REDACTED = "<redacted>"


class LiveProviderTransport(Protocol):
    """Transport contract for live provider invocation.

    Implementations MUST perform their own boundary/credentials handling. The
    adapter only passes references; it never resolves credentials itself.
    """

    def invoke(self, *, request: "LiveAdapterRequest") -> Mapping[str, Any]:
        ...


class LiveAdapterRequest(dict):
    """Lightweight typed-ish request wrapper.

    A plain ``dict`` subclass is used to keep the contract transport-neutral
    and trivially serializable for boundary records. Required string fields:
    ``subsystem``, ``tool_name``, ``request_id``. Optional refs:
    ``approval_ref``, ``provider_url_ref``, ``credential_ref``. Free-form
    metadata fields (``prompt_summary``, ``extras``) are accepted but always
    redacted before persistence.
    """


def _scrub_secrets(value: Any) -> Any:
    if isinstance(value, str):
        scrubbed = redact_text(value)
        for pattern in _SECRET_VALUE_PATTERNS:
            scrubbed = pattern.sub(_REDACTED, scrubbed)
        return scrubbed
    if isinstance(value, Mapping):
        return {key: _scrub_secrets(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_scrub_secrets(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_scrub_secrets(item) for item in value)
    return value


def _blocked_envelope(
    *,
    tool_name: str,
    request_id: str | None,
    error: str,
    extra_payload: Mapping[str, Any] | None = None,
) -> McpToolResultEnvelope:
    payload: dict[str, Any] = {
        "execution_mode": "blocked",
        "result_basis": "blocked_before_provider_invocation",
        "llm_service_used": False,
        "external_call_made": False,
        "mutation_performed": False,
        "publication_or_live_action_approved": False,
        "advisory_only": True,
        "requires_human_review": True,
    }
    if extra_payload:
        payload.update(_scrub_secrets(dict(extra_payload)))
    return McpToolResultEnvelope(
        status="blocked",
        tool_name=tool_name,
        request_id=request_id,
        external_call_made=False,
        mutation_performed=False,
        publication_or_live_action_approved=False,
        human_approval_required=True,
        payload=payload,
        error=error,
    )


def _normalize_request(request: Any) -> dict[str, Any]:
    if isinstance(request, Mapping):
        return dict(request)
    if hasattr(request, "model_dump"):
        return request.model_dump(mode="json")  # type: ignore[no-any-return]
    raise TypeError(
        f"live adapter request must be a mapping or pydantic model, got {type(request)!r}"
    )


def _verify_approval(
    *,
    approval_ref: str,
    request: Mapping[str, Any],
    approval_ledger: Mapping[str, Mapping[str, Any]],
) -> tuple[Mapping[str, Any] | None, str | None]:
    record = approval_ledger.get(approval_ref)
    if record is None:
        return None, f"approval_ref not found in approval ledger: {approval_ref}"
    missing = [field for field in _REQUIRED_APPROVAL_FIELDS if field not in record]
    if missing:
        return None, (
            "approval record missing required fields: "
            + ", ".join(sorted(missing))
        )
    if record.get("human_approved") is not True:
        return None, "approval record is not human_approved"
    if record.get("approved_tool") != request.get("tool_name"):
        return None, (
            "approval record approved_tool does not match request tool_name: "
            f"{record.get('approved_tool')!r} vs {request.get('tool_name')!r}"
        )
    if record.get("approved_subsystem") != request.get("subsystem"):
        return None, (
            "approval record approved_subsystem does not match request subsystem"
        )
    allowed = record.get("allowed_provider_refs") or []
    if request.get("provider_url_ref") not in allowed:
        return None, "request provider_url_ref is not in approval allowed_provider_refs"
    return record, None


def invoke_live_adapter(
    *,
    request: Mapping[str, Any] | LiveAdapterRequest,
    transport: LiveProviderTransport,
    approval_ledger: Mapping[str, Mapping[str, Any]],
) -> McpToolResultEnvelope:
    """Run the live adapter contract; only the injected transport may be called.

    The function fail-closes on missing approval, missing provider refs, or any
    transport exception. Every persisted payload is scrubbed for raw secrets.
    """

    req = _normalize_request(request)
    tool_name = str(req.get("tool_name") or "live_adapter")
    request_id = req.get("request_id")
    approval_ref = req.get("approval_ref")
    provider_url_ref = req.get("provider_url_ref")
    credential_ref = req.get("credential_ref")

    if not approval_ref:
        return _blocked_envelope(
            tool_name=tool_name,
            request_id=request_id,
            error="live adapter requires an approval_ref before provider invocation",
        )
    if not provider_url_ref:
        return _blocked_envelope(
            tool_name=tool_name,
            request_id=request_id,
            error="live adapter requires a provider_url_ref before provider invocation",
        )
    if not credential_ref:
        return _blocked_envelope(
            tool_name=tool_name,
            request_id=request_id,
            error="live adapter requires a credential_ref before provider invocation",
        )

    record, approval_error = _verify_approval(
        approval_ref=str(approval_ref),
        request=req,
        approval_ledger=approval_ledger,
    )
    if record is None:
        return _blocked_envelope(
            tool_name=tool_name,
            request_id=request_id,
            error=approval_error or "approval verification failed",
        )

    try:
        response = transport.invoke(request=req)
    except Exception as exc:  # noqa: BLE001 - we fail closed on any transport error
        return McpToolResultEnvelope(
            status="needs_more_evidence",
            tool_name=tool_name,
            request_id=request_id if isinstance(request_id, str) else None,
            external_call_made=True,
            mutation_performed=False,
            publication_or_live_action_approved=False,
            human_approval_required=True,
            payload={
                "execution_mode": "live_llm_failed",
                "result_basis": "live_provider_invocation_failed",
                "llm_service_used": False,
                "external_call_made": True,
                "mutation_performed": False,
                "publication_or_live_action_approved": False,
                "advisory_only": True,
                "requires_human_review": True,
                "approval_ref": str(approval_ref),
                "provider_url_ref": str(provider_url_ref),
                "credential_ref": str(credential_ref),
                "error_summary": _scrub_secrets(str(exc))[:240],
            },
            error="live provider invocation failed; no fabricated result returned",
        )

    response_map = dict(response)
    provider_ref = response_map.get("provider_ref")
    telemetry = {
        "provider_request_id": response_map.get("provider_request_id"),
        "latency_ms": response_map.get("latency_ms"),
        "cost_usd": response_map.get("cost_usd"),
        "tokens_in": response_map.get("tokens_in"),
        "tokens_out": response_map.get("tokens_out"),
        "redacted_output_excerpt": _scrub_secrets(
            str(response_map.get("redacted_output_excerpt", ""))
        )[:240],
    }
    payload: dict[str, Any] = {
        "execution_mode": _LIVE_EXECUTION_MODE,
        "result_basis": _LIVE_RESULT_BASIS,
        "llm_service_used": True,
        "external_call_made": True,
        "mutation_performed": False,
        "publication_or_live_action_approved": False,
        "advisory_only": True,
        "requires_human_review": True,
        "approval_ref": str(approval_ref),
        "approval_artifact_ref": record.get("approval_artifact_ref"),
        "approver_role": record.get("approver_role"),
        "provider_url_ref": str(provider_url_ref),
        "credential_ref": str(credential_ref),
        "provider_ref": provider_ref,
        "telemetry": _scrub_secrets(telemetry),
        "operator_notice": (
            "Live LLM/provider result: human review required before any "
            "downstream publication or live action."
        ),
    }
    return McpToolResultEnvelope(
        status="ok",
        tool_name=tool_name,
        request_id=request_id if isinstance(request_id, str) else None,
        external_call_made=True,
        mutation_performed=False,
        publication_or_live_action_approved=False,
        human_approval_required=True,
        payload=payload,
    )


class FakeLiveProviderTransport:
    """In-process fake transport for tests and dry-run harnesses.

    Records each invocation. NEVER opens a socket, resolves a credential, or
    contacts a real provider.
    """

    def __init__(self, *, response: Mapping[str, Any] | None = None) -> None:
        self.invocations: list[dict[str, Any]] = []
        self._response: dict[str, Any] = dict(response) if response else {
            "provider_request_id": "fake-provider-req",
            "provider_ref": "fake-live-llm/v1",
            "latency_ms": 1,
            "cost_usd": 0.0,
            "tokens_in": 0,
            "tokens_out": 0,
            "redacted_output_excerpt": "fake live transport output",
        }

    def invoke(self, *, request: Any) -> Mapping[str, Any]:
        self.invocations.append({"request": dict(request) if isinstance(request, Mapping) else request})
        return dict(self._response)


__all__ = [
    "FakeLiveProviderTransport",
    "LiveAdapterRequest",
    "LiveProviderTransport",
    "invoke_live_adapter",
]
