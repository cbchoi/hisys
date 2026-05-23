"""DARS live-provider transport contract and fake/injected executor seam.

DARS-LIVE-RELEASE-R1-POLICY introduces a transport request/result contract
that the future R2 fail-closed adapter and R3 single-critic live smoke will
consume. This module only specifies the contract and provides a
``FakeLiveProviderTransport`` that calls an injected executor. No real
provider call, credential lookup, socket, or HTTP request is ever performed
by this module.

Every result preserves the safety envelope:

- ``advisory_only=True``
- ``requires_human_review=True``
- ``mutation_performed=False``
- ``publication_performed=False``
- ``external_call_made=False`` (the fake transport never crosses an external
  boundary; the field exists so a future real adapter can flip it to ``True``)

Traceability:

- HISYS-FR-DARS-CP-010, HISYS-T-DARS-CP-012
- docs/plans/dars-panel-live-provider-unattended-release-final-plan.md (R1)
- docs/design/dars-critic-panel-runtime-sdd.md (LiveProvider transport seam)
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal


LIVE_PROVIDER_TRANSPORT_SCHEMA_ID = "hisys.dars.live_provider_transport"
LIVE_PROVIDER_TRANSPORT_SCHEMA_VERSION = "0.1.0"

_ALLOWED_TRANSPORT_KINDS = (
    "fake_injected_provider_transport",
    "codex_cli_subprocess_prompt_mode",
    "real_provider_subscription_transport",
)
_FAKE_TRANSPORT_KIND = "fake_injected_provider_transport"
_ALLOWED_ACTIONS = "advisory_only"

_ALLOWED_PROMPT_PACKET_SCHEMES = (
    "redacted://",
    "prompt-ref://",
    "policy-redacted://",
)

_SECRET_VALUE_RE = re.compile(
    r"\b(?:sk|ghp|xox[baprs]|hf)_[A-Za-z0-9][A-Za-z0-9_-]{8,}\b"
    r"|\bsk-[A-Za-z0-9][A-Za-z0-9_-]{8,}\b"
)
_UNAUTHORIZED_AUTHORITY_MARKERS = (
    "mutation_performed=true",
    "publication_performed=true",
    "requires_human_review=false",
    "release published",
    "workspace_write",
    "web_search",
    "sandbox bypass",
    "danger-full-access",
)


class LiveProviderTransportFailure(Exception):
    """Raised by a fake/injected executor to signal a deterministic failure code."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class LiveProviderTransportRequest:
    request_id: str
    source_execution_id: str
    backend_id: str
    policy_ref: str
    approval_ref: str
    activation_ref: str
    provider_id: str
    provider_kind: str
    model_id: str
    endpoint_ref: str
    prompt_packet_ref: str
    prompt_byte_count: int
    max_prompt_bytes: int
    max_output_bytes: int
    allowed_actions: str
    external_call_allowed: bool
    mutation_allowed: bool
    publication_allowed: bool
    requires_human_review: bool
    redaction_policy_ref: str
    transport_kind: str = _FAKE_TRANSPORT_KIND

    def __post_init__(self) -> None:
        for field_name in (
            "request_id",
            "source_execution_id",
            "backend_id",
            "policy_ref",
            "approval_ref",
            "activation_ref",
            "provider_id",
            "provider_kind",
            "model_id",
            "endpoint_ref",
            "prompt_packet_ref",
            "redaction_policy_ref",
            "transport_kind",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"missing_{field_name}")
        if self.allowed_actions != _ALLOWED_ACTIONS:
            raise ValueError("invalid_allowed_actions")
        if self.transport_kind not in _ALLOWED_TRANSPORT_KINDS:
            raise ValueError("invalid_transport_kind")
        if self.mutation_allowed is True:
            raise ValueError("mutation_authority_not_allowed")
        if self.publication_allowed is True:
            raise ValueError("publication_authority_not_allowed")
        if self.external_call_allowed is False:
            raise ValueError("external_call_must_be_allowed")
        if self.requires_human_review is False:
            raise ValueError("requires_human_review_must_be_true")
        for field_name in ("max_prompt_bytes", "max_output_bytes"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{field_name}_must_be_positive")
        if (
            isinstance(self.prompt_byte_count, bool)
            or not isinstance(self.prompt_byte_count, int)
            or self.prompt_byte_count < 0
        ):
            raise ValueError("prompt_byte_count_must_be_non_negative")
        if self.prompt_byte_count > self.max_prompt_bytes:
            raise ValueError("prompt_byte_count_exceeds_max_prompt_bytes")
        if not self.prompt_packet_ref.startswith(_ALLOWED_PROMPT_PACKET_SCHEMES):
            raise ValueError(
                "prompt_packet_ref must use a controlled redacted scheme: "
                + ", ".join(_ALLOWED_PROMPT_PACKET_SCHEMES)
            )


@dataclass(frozen=True)
class LiveProviderTransportResult:
    status: Literal["completed", "failed"]
    request_id: str
    backend_id: str
    provider_id: str
    model_id: str
    transport_kind: str
    critique_text: str
    output_byte_count: int
    input_tokens: int
    output_tokens: int
    latency_ms: int
    external_call_made: bool
    model_boundary_crossed: bool
    mutation_performed: bool
    publication_performed: bool
    advisory_only: bool
    requires_human_review: bool
    failure_code: str | None = None
    failure_detail: str = ""
    diagnostic_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FakeLiveProviderTransport:
    """Injected fake transport: never opens a socket or calls a provider."""

    executor: Callable[[dict[str, Any]], dict[str, Any]]

    def __post_init__(self) -> None:
        if not callable(self.executor):
            raise ValueError("fake_transport_executor_must_be_callable")


def run_live_provider_transport(
    request: LiveProviderTransportRequest,
    *,
    transport: FakeLiveProviderTransport | None,
) -> LiveProviderTransportResult:
    """Run a single live-provider transport request through an injected transport.

    The function fails closed when no transport is supplied. The supplied
    transport is constrained to the fake/injected seam in R1; a real provider
    transport requires R2's fail-closed adapter and a human-approved decision
    packet.
    """

    if transport is None:
        raise ValueError("live_provider_transport_required")
    if not isinstance(transport, FakeLiveProviderTransport):
        raise ValueError("live_provider_transport_must_be_fake_in_r1")
    if request.transport_kind != _FAKE_TRANSPORT_KIND:
        raise ValueError("fake_transport_requires_fake_transport_kind")

    payload = _build_executor_payload(request)

    try:
        raw = transport.executor(payload)
    except LiveProviderTransportFailure as exc:
        return _failed_result(request, failure_code=exc.code)
    except Exception as exc:  # noqa: BLE001 — every executor exception is bounded
        return _failed_result(
            request,
            failure_code="live_provider_transport_unhandled_error",
            failure_detail=type(exc).__name__,
        )

    if not isinstance(raw, dict):
        return _failed_result(request, failure_code="live_provider_invalid_executor_payload")

    critique_text = raw.get("critique_text", "")
    if not isinstance(critique_text, str) or not critique_text.strip():
        return _failed_result(request, failure_code="live_provider_empty_output")

    output_byte_count = raw.get("output_byte_count", len(critique_text.encode("utf-8")))
    if (
        isinstance(output_byte_count, bool)
        or not isinstance(output_byte_count, int)
        or output_byte_count < 0
    ):
        return _failed_result(
            request, failure_code="live_provider_invalid_output_byte_count"
        )
    if output_byte_count > request.max_output_bytes:
        return _failed_result(request, failure_code="live_provider_output_too_long")
    if _SECRET_VALUE_RE.search(critique_text):
        return _failed_result(request, failure_code="live_provider_output_not_redacted")
    lowered = critique_text.lower()
    if any(marker in lowered for marker in _UNAUTHORIZED_AUTHORITY_MARKERS):
        return _failed_result(
            request,
            failure_code="live_provider_output_claims_unauthorized_authority",
        )

    input_tokens = _coerce_metric(raw.get("input_tokens"))
    output_tokens = _coerce_metric(raw.get("output_tokens"))
    latency_ms = _coerce_metric(raw.get("latency_ms"))

    diagnostic = {
        key: value
        for key, value in raw.items()
        if key
        not in {
            "critique_text",
            "output_byte_count",
            "input_tokens",
            "output_tokens",
            "latency_ms",
        }
    }

    return LiveProviderTransportResult(
        status="completed",
        request_id=request.request_id,
        backend_id=request.backend_id,
        provider_id=request.provider_id,
        model_id=request.model_id,
        transport_kind=request.transport_kind,
        critique_text=critique_text,
        output_byte_count=output_byte_count,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        external_call_made=False,
        model_boundary_crossed=False,
        mutation_performed=False,
        publication_performed=False,
        advisory_only=True,
        requires_human_review=True,
        failure_code=None,
        diagnostic_metadata=diagnostic,
    )


def _build_executor_payload(request: LiveProviderTransportRequest) -> dict[str, Any]:
    """Build the redacted payload handed to the injected executor.

    The payload deliberately contains *no* credential, token, authorization
    header, or raw secret. The injected executor receives provider/model refs,
    redaction-policy refs, the redacted prompt packet ref, and the safety
    envelope.
    """

    return {
        "schema_id": LIVE_PROVIDER_TRANSPORT_SCHEMA_ID,
        "schema_version": LIVE_PROVIDER_TRANSPORT_SCHEMA_VERSION,
        "request_id": request.request_id,
        "source_execution_id": request.source_execution_id,
        "backend_id": request.backend_id,
        "policy_ref": request.policy_ref,
        "approval_ref": request.approval_ref,
        "activation_ref": request.activation_ref,
        "provider_id": request.provider_id,
        "provider_kind": request.provider_kind,
        "model_id": request.model_id,
        "endpoint_ref": request.endpoint_ref,
        "prompt_packet_ref": request.prompt_packet_ref,
        "prompt_byte_count": request.prompt_byte_count,
        "max_prompt_bytes": request.max_prompt_bytes,
        "max_output_bytes": request.max_output_bytes,
        "allowed_actions": request.allowed_actions,
        "redaction_policy_ref": request.redaction_policy_ref,
        "transport_kind": request.transport_kind,
        "external_call_made": False,
        "model_boundary_crossed": False,
        "mutation_performed": False,
        "publication_performed": False,
        "advisory_only": True,
        "requires_human_review": True,
    }


def _failed_result(
    request: LiveProviderTransportRequest,
    *,
    failure_code: str,
    failure_detail: str = "",
) -> LiveProviderTransportResult:
    return LiveProviderTransportResult(
        status="failed",
        request_id=request.request_id,
        backend_id=request.backend_id,
        provider_id=request.provider_id,
        model_id=request.model_id,
        transport_kind=request.transport_kind,
        critique_text="",
        output_byte_count=0,
        input_tokens=0,
        output_tokens=0,
        latency_ms=0,
        external_call_made=False,
        model_boundary_crossed=False,
        mutation_performed=False,
        publication_performed=False,
        advisory_only=True,
        requires_human_review=True,
        failure_code=failure_code,
        failure_detail=failure_detail,
    )


def _coerce_metric(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int) and value >= 0:
        return value
    return 0


__all__ = [
    "LIVE_PROVIDER_TRANSPORT_SCHEMA_ID",
    "LIVE_PROVIDER_TRANSPORT_SCHEMA_VERSION",
    "FakeLiveProviderTransport",
    "LiveProviderTransportFailure",
    "LiveProviderTransportRequest",
    "LiveProviderTransportResult",
    "run_live_provider_transport",
]
