"""DARS fail-closed live-provider adapter.

DARS-LIVE-RELEASE-R2-ADAPTER composes the R1 policy validator
(:mod:`hisys.agents.dars_live_provider_policy`), the existing backend
activation validator (:mod:`hisys.agents.dars_backend_activation`), and the
R1 fake/injected transport seam
(:mod:`hisys.agents.dars_live_provider_transport`) into a single fail-closed
adapter entry point.

The adapter never resolves credentials, opens sockets, or calls a real
provider. Both supported modes (``dry_run`` and ``live``) route through the
injected ``FakeLiveProviderTransport`` and write a per-request boundary
record under the instance root. The ``live`` mode additionally requires the
``HISYS_DARS_LIVE_PROVIDER_LIVE_TRANSPORT_ENABLED`` environment gate to be
set to ``true`` so a configuration mistake cannot accidentally promote a
dry-run call into a live call.

A future increment (R3+) may add a real-provider transport behind the same
gates. Until that increment lands, every boundary record persisted by this
adapter carries ``external_call_made=False`` and
``model_boundary_crossed=False``.

Traceability:

- HISYS-FR-DARS-CP-010, HISYS-FR-DARS-CP-011
- HISYS-T-DARS-CP-012
- docs/plans/dars-panel-live-provider-unattended-release-final-plan.md (R2)
- docs/design/dars-critic-panel-runtime-sdd.md (LiveProvider transport seam)
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from hisys.agents.dars_backend_activation import (
    validate_dars_backend_activation_packet,
)
from hisys.agents.dars_live_provider_policy import (
    validate_live_provider_policy_packet,
)
from hisys.agents.dars_live_provider_transport import (
    FakeLiveProviderTransport,
    LiveProviderTransportRequest,
    LiveProviderTransportResult,
    run_live_provider_transport,
)
from hisys.config.instance import InstanceRoot


DARS_LIVE_PROVIDER_ADAPTER_SCHEMA_ID = "hisys.dars.live_provider_adapter"
DARS_LIVE_PROVIDER_ADAPTER_SCHEMA_VERSION = "0.1.0"
DARS_LIVE_PROVIDER_LIVE_TRANSPORT_ENV_VAR = (
    "HISYS_DARS_LIVE_PROVIDER_LIVE_TRANSPORT_ENABLED"
)

_DATE_RE = re.compile(r"^\d{8}$")
_SLUG_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_ALLOWED_MODES = ("dry_run", "live")
_ALLOWED_ACTIONS = "advisory_only"
_ALLOWED_ACTIVATION_ENDPOINT_SCOPE = "external_api"
_FAKE_TRANSPORT_KIND = "fake_injected_provider_transport"


@dataclass(frozen=True)
class DarsLiveProviderAdapterRequest:
    request_id: str
    source_execution_id: str
    backend_id: str
    policy_packet_ref: str
    activation_packet_ref: str
    approval_ref: str
    prompt_packet_ref: str
    prompt_byte_count: int
    yyyymmdd: str
    mode: Literal["dry_run", "live"] = "dry_run"
    now: str | datetime | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "request_id",
            "source_execution_id",
            "backend_id",
            "policy_packet_ref",
            "activation_packet_ref",
            "approval_ref",
            "prompt_packet_ref",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"missing_{field_name}")
        if not _SLUG_RE.fullmatch(self.request_id):
            raise ValueError("invalid_request_id")
        if not _SLUG_RE.fullmatch(self.source_execution_id):
            raise ValueError("invalid_source_execution_id")
        if not _SLUG_RE.fullmatch(self.backend_id):
            raise ValueError("invalid_backend_id")
        if not _DATE_RE.fullmatch(self.yyyymmdd):
            raise ValueError("invalid_yyyymmdd")
        if self.mode not in _ALLOWED_MODES:
            raise ValueError("invalid_adapter_mode")
        if (
            isinstance(self.prompt_byte_count, bool)
            or not isinstance(self.prompt_byte_count, int)
            or self.prompt_byte_count < 0
        ):
            raise ValueError("invalid_prompt_byte_count")


@dataclass(frozen=True)
class DarsLiveProviderAdapterResult:
    status: Literal["completed", "failed"]
    mode: Literal["dry_run", "live"]
    request_id: str
    backend_id: str
    provider_id: str
    model_id: str
    transport_kind: str
    critique_text: str
    failure_code: str | None
    failure_detail: str
    boundary_ref: str | None
    external_call_made: bool
    model_boundary_crossed: bool
    mutation_performed: bool
    publication_performed: bool
    advisory_only: bool
    requires_human_review: bool
    policy_issue_codes: set[str] | None = None
    activation_issue_codes: set[str] | None = None


def run_dars_live_provider_adapter(
    request: DarsLiveProviderAdapterRequest,
    *,
    transport: FakeLiveProviderTransport | None,
    instance: InstanceRoot,
    env: Mapping[str, str] | None = None,
) -> DarsLiveProviderAdapterResult:
    """Run the fail-closed DARS live-provider adapter.

    The adapter validates the policy packet, activation packet, approval ref
    coherence, backend ref coherence, and (for live mode) the env gate. If
    any gate fails, the result is failed and no transport call is attempted.
    On success, the injected ``transport`` is invoked through the R1 fake
    transport seam and a boundary record is persisted under the instance
    root regardless of success or failure.
    """

    if transport is None:
        raise ValueError("live_provider_transport_required")
    if env is None:
        import os

        env = os.environ

    # Stage 1: load packets
    try:
        policy_data = _load_packet(request.policy_packet_ref)
    except _PacketLoadError:
        return _write_and_return_failed(
            request,
            instance=instance,
            provider_id="",
            model_id="",
            failure_code="live_provider_policy_packet_unreadable",
            failure_detail=request.policy_packet_ref,
        )
    try:
        activation_data = _load_packet(request.activation_packet_ref)
    except _PacketLoadError:
        return _write_and_return_failed(
            request,
            instance=instance,
            provider_id="",
            model_id="",
            failure_code="live_provider_activation_packet_unreadable",
            failure_detail=request.activation_packet_ref,
        )

    # Stage 2: policy validation
    policy_report = validate_live_provider_policy_packet(
        policy_data, config_ref=request.policy_packet_ref, now=request.now
    )
    if not policy_report.valid:
        codes = {
            issue.code
            for issue in policy_report.issues
            if issue.severity == "error"
        }
        return _write_and_return_failed(
            request,
            instance=instance,
            provider_id=str(policy_data.get("provider_id", "")),
            model_id=str(policy_data.get("model_id", "")),
            failure_code="live_provider_policy_invalid",
            failure_detail="; ".join(sorted(codes)),
            policy_issue_codes=codes,
        )

    # Stage 3: activation validation
    activation_report = validate_dars_backend_activation_packet(
        activation_data,
        config_ref=request.activation_packet_ref,
        now=request.now,
    )
    if not activation_report.valid:
        codes = {
            issue.code
            for issue in activation_report.issues
            if issue.severity == "error"
        }
        return _write_and_return_failed(
            request,
            instance=instance,
            provider_id=str(policy_data.get("provider_id", "")),
            model_id=str(policy_data.get("model_id", "")),
            failure_code="live_provider_activation_invalid",
            failure_detail="; ".join(sorted(codes)),
            activation_issue_codes=codes,
        )

    # Stage 4: cross-checks
    if (
        request.approval_ref != policy_data.get("approval_ref")
        or request.approval_ref != activation_data.get("approval_ref")
    ):
        return _write_and_return_failed(
            request,
            instance=instance,
            provider_id=str(policy_data.get("provider_id", "")),
            model_id=str(policy_data.get("model_id", "")),
            failure_code="live_provider_approval_ref_mismatch",
            failure_detail="request/policy/activation approval_ref mismatch",
        )
    if request.backend_id != activation_data.get("backend_id"):
        return _write_and_return_failed(
            request,
            instance=instance,
            provider_id=str(policy_data.get("provider_id", "")),
            model_id=str(policy_data.get("model_id", "")),
            failure_code="live_provider_backend_id_mismatch",
            failure_detail="request/activation backend_id mismatch",
        )
    if activation_data.get("endpoint_scope") != _ALLOWED_ACTIVATION_ENDPOINT_SCOPE:
        return _write_and_return_failed(
            request,
            instance=instance,
            provider_id=str(policy_data.get("provider_id", "")),
            model_id=str(policy_data.get("model_id", "")),
            failure_code="live_provider_activation_scope_mismatch",
            failure_detail=(
                f"activation endpoint_scope must be {_ALLOWED_ACTIVATION_ENDPOINT_SCOPE}"
            ),
        )
    if activation_data.get("remote_policy_packet_ref") != request.policy_packet_ref:
        return _write_and_return_failed(
            request,
            instance=instance,
            provider_id=str(policy_data.get("provider_id", "")),
            model_id=str(policy_data.get("model_id", "")),
            failure_code="live_provider_activation_policy_ref_mismatch",
            failure_detail=(
                "activation remote_policy_packet_ref must match request"
                " policy_packet_ref"
            ),
        )

    # Stage 5: env gate (live mode only)
    if request.mode == "live":
        gate_value = env.get(DARS_LIVE_PROVIDER_LIVE_TRANSPORT_ENV_VAR, "")
        if gate_value.strip().lower() != "true":
            return _write_and_return_failed(
                request,
                instance=instance,
                provider_id=str(policy_data["provider_id"]),
                model_id=str(policy_data["model_id"]),
                failure_code="live_provider_env_gate_missing",
                failure_detail=(
                    f"{DARS_LIVE_PROVIDER_LIVE_TRANSPORT_ENV_VAR} must be set"
                    " to 'true' before live mode can be reached"
                ),
            )

    # Stage 6: build transport request and run through fake transport
    transport_request = LiveProviderTransportRequest(
        request_id=request.request_id,
        source_execution_id=request.source_execution_id,
        backend_id=request.backend_id,
        policy_ref=request.policy_packet_ref,
        approval_ref=request.approval_ref,
        activation_ref=request.activation_packet_ref,
        provider_id=str(policy_data["provider_id"]),
        provider_kind=str(policy_data["provider_kind"]),
        model_id=str(policy_data["model_id"]),
        endpoint_ref=str(policy_data["endpoint_ref"]),
        prompt_packet_ref=request.prompt_packet_ref,
        prompt_byte_count=request.prompt_byte_count,
        max_prompt_bytes=int(policy_data["max_prompt_bytes"]),
        max_output_bytes=int(policy_data["max_output_bytes"]),
        allowed_actions=_ALLOWED_ACTIONS,
        external_call_allowed=True,
        mutation_allowed=False,
        publication_allowed=False,
        requires_human_review=True,
        redaction_policy_ref=str(policy_data["redaction_policy_ref"]),
        transport_kind=_FAKE_TRANSPORT_KIND,
    )
    transport_result = run_live_provider_transport(
        transport_request, transport=transport
    )

    boundary_ref = _write_boundary_record(
        instance,
        request=request,
        transport_result=transport_result,
        provider_id=transport_request.provider_id,
        model_id=transport_request.model_id,
    )

    if transport_result.status == "completed":
        return DarsLiveProviderAdapterResult(
            status="completed",
            mode=request.mode,
            request_id=request.request_id,
            backend_id=request.backend_id,
            provider_id=transport_request.provider_id,
            model_id=transport_request.model_id,
            transport_kind=transport_result.transport_kind,
            critique_text=transport_result.critique_text,
            failure_code=None,
            failure_detail="",
            boundary_ref=boundary_ref,
            external_call_made=False,
            model_boundary_crossed=False,
            mutation_performed=False,
            publication_performed=False,
            advisory_only=True,
            requires_human_review=True,
        )
    return DarsLiveProviderAdapterResult(
        status="failed",
        mode=request.mode,
        request_id=request.request_id,
        backend_id=request.backend_id,
        provider_id=transport_request.provider_id,
        model_id=transport_request.model_id,
        transport_kind=transport_result.transport_kind,
        critique_text="",
        failure_code=transport_result.failure_code,
        failure_detail=transport_result.failure_detail,
        boundary_ref=boundary_ref,
        external_call_made=False,
        model_boundary_crossed=False,
        mutation_performed=False,
        publication_performed=False,
        advisory_only=True,
        requires_human_review=True,
    )


class _PacketLoadError(Exception):
    """Raised when a packet file cannot be read or parsed as JSON object."""


def _load_packet(path_ref: str) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path_ref).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:  # noqa: BLE001
        raise _PacketLoadError(str(exc)) from None
    if not isinstance(payload, dict):
        raise _PacketLoadError("packet must be a JSON object")
    return payload


def _write_and_return_failed(
    request: DarsLiveProviderAdapterRequest,
    *,
    instance: InstanceRoot,
    provider_id: str,
    model_id: str,
    failure_code: str,
    failure_detail: str,
    policy_issue_codes: set[str] | None = None,
    activation_issue_codes: set[str] | None = None,
) -> DarsLiveProviderAdapterResult:
    boundary_ref: str | None = None
    try:
        boundary_ref = _write_boundary_record(
            instance,
            request=request,
            transport_result=None,
            provider_id=provider_id,
            model_id=model_id,
            failure_code=failure_code,
            failure_detail=failure_detail,
            policy_issue_codes=policy_issue_codes,
            activation_issue_codes=activation_issue_codes,
        )
    except OSError:
        boundary_ref = None
    return DarsLiveProviderAdapterResult(
        status="failed",
        mode=request.mode,
        request_id=request.request_id,
        backend_id=request.backend_id,
        provider_id=provider_id,
        model_id=model_id,
        transport_kind=_FAKE_TRANSPORT_KIND,
        critique_text="",
        failure_code=failure_code,
        failure_detail=failure_detail,
        boundary_ref=boundary_ref,
        external_call_made=False,
        model_boundary_crossed=False,
        mutation_performed=False,
        publication_performed=False,
        advisory_only=True,
        requires_human_review=True,
        policy_issue_codes=policy_issue_codes,
        activation_issue_codes=activation_issue_codes,
    )


def _write_boundary_record(
    instance: InstanceRoot,
    *,
    request: DarsLiveProviderAdapterRequest,
    transport_result: LiveProviderTransportResult | None,
    provider_id: str,
    model_id: str,
    failure_code: str | None = None,
    failure_detail: str = "",
    policy_issue_codes: set[str] | None = None,
    activation_issue_codes: set[str] | None = None,
) -> str:
    output_dir = (
        instance.runtime_boundary_dir
        / "dars-live-provider-adapter"
        / request.yyyymmdd
        / request.request_id
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    if transport_result is not None:
        status = transport_result.status
        failure_code = failure_code or transport_result.failure_code
        failure_detail = failure_detail or transport_result.failure_detail
        transport_kind = transport_result.transport_kind
        critique_preview = transport_result.critique_text[:500]
        output_byte_count = transport_result.output_byte_count
        input_tokens = transport_result.input_tokens
        output_tokens = transport_result.output_tokens
        latency_ms = transport_result.latency_ms
    else:
        status = "failed"
        transport_kind = _FAKE_TRANSPORT_KIND
        critique_preview = ""
        output_byte_count = 0
        input_tokens = 0
        output_tokens = 0
        latency_ms = 0
    payload: dict[str, Any] = {
        "schema_id": DARS_LIVE_PROVIDER_ADAPTER_SCHEMA_ID,
        "schema_version": DARS_LIVE_PROVIDER_ADAPTER_SCHEMA_VERSION,
        "request_id": request.request_id,
        "source_execution_id": request.source_execution_id,
        "backend_id": request.backend_id,
        "provider_id": provider_id,
        "model_id": model_id,
        "mode": request.mode,
        "transport_kind": transport_kind,
        "status": status,
        "failure_code": failure_code,
        "failure_detail": failure_detail,
        "policy_ref": request.policy_packet_ref,
        "activation_ref": request.activation_packet_ref,
        "approval_ref": request.approval_ref,
        "prompt_packet_ref": request.prompt_packet_ref,
        "prompt_byte_count": request.prompt_byte_count,
        "critique_text_preview": critique_preview,
        "output_byte_count": output_byte_count,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_ms": latency_ms,
        "external_call_made": False,
        "model_boundary_crossed": False,
        "mutation_performed": False,
        "publication_performed": False,
        "advisory_only": True,
        "requires_human_review": True,
        "allowed_actions": _ALLOWED_ACTIONS,
        "policy_refs": [
            "HISYS-FR-DARS-CP-009",
            "HISYS-FR-DARS-CP-010",
            "HISYS-FR-DARS-CP-011",
            "HISYS-T-DARS-CP-012",
            "DARS-LIVE-RELEASE-R2-ADAPTER",
        ],
    }
    if policy_issue_codes:
        payload["policy_issue_codes"] = sorted(policy_issue_codes)
    if activation_issue_codes:
        payload["activation_issue_codes"] = sorted(activation_issue_codes)
    json_path = output_dir / f"{request.backend_id}-{request.source_execution_id}.json"
    md_path = output_dir / f"{request.backend_id}-{request.source_execution_id}.md"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(_render_markdown(payload), encoding="utf-8")
    return str(json_path.relative_to(instance.root))


def _render_markdown(payload: dict[str, Any]) -> str:
    failure_code = payload.get("failure_code") or "-"
    return "\n".join(
        [
            f"# DARS live-provider adapter — {payload['backend_id']}",
            "",
            f"- schema_id: {payload['schema_id']}",
            f"- schema_version: {payload['schema_version']}",
            f"- request_id: {payload['request_id']}",
            f"- source_execution_id: {payload['source_execution_id']}",
            f"- backend_id: {payload['backend_id']}",
            f"- provider_id: {payload['provider_id']}",
            f"- model_id: {payload['model_id']}",
            f"- mode: {payload['mode']}",
            f"- transport_kind: {payload['transport_kind']}",
            f"- status: {payload['status']}",
            f"- failure_code: {failure_code}",
            f"- policy_ref: {payload['policy_ref']}",
            f"- activation_ref: {payload['activation_ref']}",
            f"- approval_ref: {payload['approval_ref']}",
            f"- external_call_made: {str(payload['external_call_made']).lower()}",
            f"- model_boundary_crossed: {str(payload['model_boundary_crossed']).lower()}",
            f"- mutation_performed: {str(payload['mutation_performed']).lower()}",
            f"- publication_performed: {str(payload['publication_performed']).lower()}",
            f"- advisory_only: {str(payload['advisory_only']).lower()}",
            f"- requires_human_review: {str(payload['requires_human_review']).lower()}",
            f"- allowed_actions: {payload['allowed_actions']}",
            "",
        ]
    )


__all__ = [
    "DARS_LIVE_PROVIDER_ADAPTER_SCHEMA_ID",
    "DARS_LIVE_PROVIDER_ADAPTER_SCHEMA_VERSION",
    "DARS_LIVE_PROVIDER_LIVE_TRANSPORT_ENV_VAR",
    "DarsLiveProviderAdapterRequest",
    "DarsLiveProviderAdapterResult",
    "run_dars_live_provider_adapter",
]
