"""DARS remote subscription dispatch harness.

M-DARS-BE-6 starts remote subscription dispatch without embedding provider
credentials or direct provider SDK/API calls in Hisys. The runtime composes the
existing backend activation packet and remote subscription policy packet, then
calls an explicitly supplied executor. Tests use an injected executor; production
operators must supply a separately governed subscription executor after human
approval. This module never resolves credentials, stores raw secrets, publishes,
mutates external systems, or broadens the provider allowlist beyond the policy
validator.

Traceability: docs/plans/dars-live-backend-implementation-plan.md (M-DARS-BE-6).
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from ..config.instance import InstanceRoot
from .dars_backend_activation import validate_dars_backend_activation_packet
from .dars_remote_subscription_policy import (
    validate_dars_remote_subscription_policy_packet,
)

DARS_REMOTE_SUBSCRIPTION_DISPATCH_SCHEMA_ID = "hisys.dars.remote_subscription_dispatch"
DARS_REMOTE_SUBSCRIPTION_DISPATCH_SCHEMA_VERSION = "0.1.0"
DARS_REMOTE_SUBSCRIPTION_PANEL_DISPATCH_SCHEMA_ID = "hisys.dars.remote_subscription_panel_dispatch"
DARS_REMOTE_SUBSCRIPTION_PANEL_DISPATCH_SCHEMA_VERSION = "0.1.0"

_DATE_RE = re.compile(r"^\d{8}$")
_SLUG_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_ALLOWED_ENDPOINT_SCOPE = "external_api"
_ALLOWED_ACTIONS = "advisory_only"

RemoteSubscriptionExecutor = Callable[[dict[str, Any]], str]


@dataclass(frozen=True)
class RemoteSubscriptionDispatchRequest:
    yyyymmdd: str
    request_id: str
    backend_id: str
    backend_kind: str
    source_execution_id: str
    approval_ref: str
    activation_packet_ref: str
    policy_packet_ref: str
    prompt: str
    transport_kind: str = "injected_subscription_executor"


@dataclass(frozen=True)
class RemoteSubscriptionDispatchResult:
    status: Literal["completed"]
    boundary_ref: str
    critique_text: str
    provider_id: str
    adapter_class: str
    external_call_made: bool


@dataclass(frozen=True)
class RemoteSubscriptionPanelDispatchResult:
    status: Literal["completed"]
    panel_id: str
    request_id: str
    panel_boundary_ref: str
    boundary_refs: list[str]
    critic_results: list[RemoteSubscriptionDispatchResult]
    external_call_made: bool


def run_dars_remote_subscription_dispatch(
    instance: InstanceRoot,
    request: RemoteSubscriptionDispatchRequest,
    *,
    executor: RemoteSubscriptionExecutor | None = None,
) -> RemoteSubscriptionDispatchResult:
    """Run a governed remote subscription dispatch through an explicit executor.

    The activation and policy packet checks happen before the executor is
    touched. Without an executor the function fails closed, so merely importing
    or wiring this module cannot perform a live provider call.
    """

    _validate_request_shape(request)
    activation_data = _load_json_object(request.activation_packet_ref, "backend_activation_packet_required")
    policy_data = _load_json_object(request.policy_packet_ref, "remote_policy_packet_required")

    _enforce_activation_packet(request, activation_data)
    _enforce_policy_packet(request, activation_data, policy_data)
    if executor is None:
        raise ValueError("remote_subscription_executor_required")

    provider_id = str(policy_data["provider_id"])
    adapter_class = str(policy_data["adapter_class"])
    executor_payload = {
        "request_id": request.request_id,
        "source_execution_id": request.source_execution_id,
        "backend_id": request.backend_id,
        "backend_kind": request.backend_kind,
        "provider_id": provider_id,
        "adapter_class": adapter_class,
        "approval_ref": request.approval_ref,
        "policy_ref": request.policy_packet_ref,
        "activation_ref": request.activation_packet_ref,
        "allowed_actions": _ALLOWED_ACTIONS,
        "prompt": request.prompt,
        "external_call_made": True,
        "mutation_performed": False,
        "publication_performed": False,
        "transport_kind": request.transport_kind,
    }
    critique_text = executor(executor_payload)
    if not isinstance(critique_text, str) or not critique_text.strip():
        raise ValueError("remote_subscription_executor_empty_output")

    boundary_ref = _write_remote_subscription_boundary(
        instance,
        request=request,
        provider_id=provider_id,
        adapter_class=adapter_class,
        transport_kind=request.transport_kind,
        critique_text=critique_text.strip(),
    )
    return RemoteSubscriptionDispatchResult(
        status="completed",
        boundary_ref=boundary_ref,
        critique_text=critique_text.strip(),
        provider_id=provider_id,
        adapter_class=adapter_class,
        external_call_made=True,
    )


def run_dars_remote_subscription_panel_dispatch(
    instance: InstanceRoot,
    *,
    yyyymmdd: str,
    request_id: str,
    panel_id: str,
    requests: list[RemoteSubscriptionDispatchRequest],
    executor: RemoteSubscriptionExecutor | None = None,
) -> RemoteSubscriptionPanelDispatchResult:
    """Run a multi-critic remote-subscription DARS panel through an injected executor.

    This function is the panel-level composition seam for the existing governed
    dispatch harness. It does not resolve credentials or provider SDKs; every
    critic request still passes the activation/policy checks in
    ``run_dars_remote_subscription_dispatch`` before the injected executor can be
    contacted. Panel-shape mismatches are rejected before any executor contact.
    """

    _validate_panel_shape(
        yyyymmdd=yyyymmdd,
        request_id=request_id,
        panel_id=panel_id,
        requests=requests,
    )
    critic_results: list[RemoteSubscriptionDispatchResult] = []
    for request in requests:
        critic_results.append(
            run_dars_remote_subscription_dispatch(
                instance,
                request,
                executor=executor,
            )
        )
    panel_boundary_ref = _write_remote_subscription_panel_boundary(
        instance,
        yyyymmdd=yyyymmdd,
        request_id=request_id,
        panel_id=panel_id,
        critic_results=critic_results,
    )
    return RemoteSubscriptionPanelDispatchResult(
        status="completed",
        panel_id=panel_id,
        request_id=request_id,
        panel_boundary_ref=panel_boundary_ref,
        boundary_refs=[result.boundary_ref for result in critic_results],
        critic_results=critic_results,
        external_call_made=True,
    )


def _validate_panel_shape(
    *,
    yyyymmdd: str,
    request_id: str,
    panel_id: str,
    requests: list[RemoteSubscriptionDispatchRequest],
) -> None:
    if not _DATE_RE.fullmatch(yyyymmdd):
        raise ValueError("invalid_date_partition")
    for field_name, value in (("request_id", request_id), ("panel_id", panel_id)):
        if not isinstance(value, str) or not _SLUG_RE.fullmatch(value):
            raise ValueError(f"invalid_{field_name}")
    if len(requests) < 2:
        raise ValueError("multi_critic_panel_requires_at_least_two_requests")
    seen_source_execution_ids: set[str] = set()
    for request in requests:
        _validate_request_shape(request)
        if request.yyyymmdd != yyyymmdd:
            raise ValueError("panel_date_partition_mismatch")
        if request.request_id != request_id:
            raise ValueError("panel_request_id_mismatch")
        if request.source_execution_id in seen_source_execution_ids:
            raise ValueError("duplicate_panel_source_execution_id")
        seen_source_execution_ids.add(request.source_execution_id)


def _write_remote_subscription_panel_boundary(
    instance: InstanceRoot,
    *,
    yyyymmdd: str,
    request_id: str,
    panel_id: str,
    critic_results: list[RemoteSubscriptionDispatchResult],
) -> str:
    output_dir = (
        instance.runtime_boundary_dir
        / "dars-remote-subscription-panels"
        / yyyymmdd
        / request_id
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    provider_ids = sorted({result.provider_id for result in critic_results})
    adapter_classes = sorted({result.adapter_class for result in critic_results})
    boundary_refs = [result.boundary_ref for result in critic_results]
    payload = {
        "schema_id": DARS_REMOTE_SUBSCRIPTION_PANEL_DISPATCH_SCHEMA_ID,
        "schema_version": DARS_REMOTE_SUBSCRIPTION_PANEL_DISPATCH_SCHEMA_VERSION,
        "panel_id": panel_id,
        "request_id": request_id,
        "critic_count": len(critic_results),
        "completed_critic_count": len([result for result in critic_results if result.status == "completed"]),
        "provider_ids": provider_ids,
        "adapter_classes": adapter_classes,
        "boundary_refs": boundary_refs,
        "external_call_made": True,
        "model_boundary_crossed": True,
        "local_model_call_made": False,
        "mutation_performed": False,
        "publication_performed": False,
        "allowed_actions": _ALLOWED_ACTIONS,
        "requires_human_review": True,
        "transport_kind": "injected_subscription_executor_panel",
        "policy_refs": [
            "HISYS-FR-AGT-001",
            "HISYS-FR-AGT-003",
            "HISYS-CON-010",
            "HISYS-CON-012",
            "M-DARS-BE-6",
            "M24",
        ],
    }
    json_path = output_dir / f"{panel_id}.json"
    md_path = output_dir / f"{panel_id}.md"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(_render_panel_markdown(payload), encoding="utf-8")
    return str(json_path.relative_to(instance.root))


def _validate_request_shape(request: RemoteSubscriptionDispatchRequest) -> None:
    if not _DATE_RE.fullmatch(request.yyyymmdd):
        raise ValueError("invalid_date_partition")
    for field_name in ("request_id", "backend_id", "source_execution_id"):
        value = getattr(request, field_name)
        if not isinstance(value, str) or not _SLUG_RE.fullmatch(value):
            raise ValueError(f"invalid_{field_name}")
    for field_name in (
        "backend_kind",
        "approval_ref",
        "activation_packet_ref",
        "policy_packet_ref",
        "prompt",
    ):
        value = getattr(request, field_name)
        if not isinstance(value, str) or not value:
            raise ValueError(f"missing_{field_name}")
    if request.transport_kind not in {
        "injected_subscription_executor",
        "codex_cli_subprocess_prompt_mode",
    }:
        raise ValueError("invalid_transport_kind")


def _load_json_object(path_ref: str, missing_code: str) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path_ref).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise ValueError(missing_code) from None
    if not isinstance(payload, dict):
        raise ValueError(missing_code)
    return payload


def _enforce_activation_packet(
    request: RemoteSubscriptionDispatchRequest,
    activation_data: dict[str, Any],
) -> None:
    report = validate_dars_backend_activation_packet(
        activation_data,
        config_ref=request.activation_packet_ref,
    )
    if not report.valid:
        _raise_first_error(report.issues, "backend_activation_packet_required")
    if activation_data.get("approval_ref") != request.approval_ref:
        raise ValueError("activation_approval_ref_mismatch")
    if activation_data.get("backend_id") != request.backend_id:
        raise ValueError("activation_backend_id_mismatch")
    if activation_data.get("backend_kind") != request.backend_kind:
        raise ValueError("activation_backend_kind_mismatch")
    if activation_data.get("endpoint_scope") != _ALLOWED_ENDPOINT_SCOPE:
        raise ValueError("activation_endpoint_scope_mismatch")
    if activation_data.get("allowed_actions") != _ALLOWED_ACTIONS:
        raise ValueError("invalid_allowed_actions")
    if activation_data.get("remote_policy_packet_ref") != request.policy_packet_ref:
        raise ValueError("activation_remote_policy_ref_mismatch")


def _enforce_policy_packet(
    request: RemoteSubscriptionDispatchRequest,
    activation_data: dict[str, Any],
    policy_data: dict[str, Any],
) -> None:
    report = validate_dars_remote_subscription_policy_packet(
        policy_data,
        config_ref=request.policy_packet_ref,
    )
    if not report.valid:
        _raise_first_error(report.issues, "remote_policy_packet_invalid")
    if policy_data.get("approval_ref") != request.approval_ref:
        raise ValueError("remote_policy_approval_ref_mismatch")
    if policy_data.get("approval_ref") != activation_data.get("approval_ref"):
        raise ValueError("remote_policy_approval_ref_mismatch")
    if policy_data.get("access_mode") != "subscription":
        raise ValueError("invalid_access_mode")
    if policy_data.get("audit_required") is not True:
        raise ValueError("audit_required_must_be_true")


def _raise_first_error(issues: list[Any], fallback: str) -> None:
    for issue in issues:
        if getattr(issue, "severity", "error") == "error":
            raise ValueError(str(getattr(issue, "code", fallback)))
    raise ValueError(fallback)


def _write_remote_subscription_boundary(
    instance: InstanceRoot,
    *,
    request: RemoteSubscriptionDispatchRequest,
    provider_id: str,
    adapter_class: str,
    transport_kind: str,
    critique_text: str,
) -> str:
    output_dir = (
        instance.runtime_boundary_dir
        / "dars-remote-subscriptions"
        / request.yyyymmdd
        / request.request_id
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_id": DARS_REMOTE_SUBSCRIPTION_DISPATCH_SCHEMA_ID,
        "schema_version": DARS_REMOTE_SUBSCRIPTION_DISPATCH_SCHEMA_VERSION,
        "request_id": request.request_id,
        "source_execution_id": request.source_execution_id,
        "backend_id": request.backend_id,
        "backend_kind": request.backend_kind,
        "provider_id": provider_id,
        "adapter_class": adapter_class,
        "endpoint_scope": _ALLOWED_ENDPOINT_SCOPE,
        "approval_ref": request.approval_ref,
        "activation_ref": request.activation_packet_ref,
        "policy_ref": request.policy_packet_ref,
        "external_call_made": True,
        "model_boundary_crossed": True,
        "local_model_call_made": False,
        "mutation_performed": False,
        "publication_performed": False,
        "allowed_actions": _ALLOWED_ACTIONS,
        "requires_human_review": True,
        "transport_kind": transport_kind,
        "critique_text_preview": critique_text[:500],
        "policy_refs": [
            "HISYS-FR-AGT-001",
            "HISYS-FR-AGT-003",
            "HISYS-CON-010",
            "HISYS-CON-012",
            "M-DARS-BE-6",
        ],
    }
    json_path = output_dir / f"{request.backend_id}-{request.source_execution_id}.json"
    md_path = output_dir / f"{request.backend_id}-{request.source_execution_id}.md"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(_render_markdown(payload), encoding="utf-8")
    return str(json_path.relative_to(instance.root))


def _render_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# DARS remote subscription dispatch — {payload['backend_id']}",
            "",
            f"- schema_id: {payload['schema_id']}",
            f"- schema_version: {payload['schema_version']}",
            f"- request_id: {payload['request_id']}",
            f"- source_execution_id: {payload['source_execution_id']}",
            f"- backend_id: {payload['backend_id']}",
            f"- backend_kind: {payload['backend_kind']}",
            f"- provider_id: {payload['provider_id']}",
            f"- adapter_class: {payload['adapter_class']}",
            f"- endpoint_scope: {payload['endpoint_scope']}",
            f"- approval_ref: {payload['approval_ref']}",
            f"- activation_ref: {payload['activation_ref']}",
            f"- policy_ref: {payload['policy_ref']}",
            f"- external_call_made: {str(payload['external_call_made']).lower()}",
            f"- model_boundary_crossed: {str(payload['model_boundary_crossed']).lower()}",
            f"- local_model_call_made: {str(payload['local_model_call_made']).lower()}",
            f"- mutation_performed: {str(payload['mutation_performed']).lower()}",
            f"- publication_performed: {str(payload['publication_performed']).lower()}",
            f"- allowed_actions: {payload['allowed_actions']}",
            f"- requires_human_review: {str(payload['requires_human_review']).lower()}",
            f"- transport_kind: {payload['transport_kind']}",
            "",
        ]
    )


def _render_panel_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# DARS remote subscription panel dispatch — {payload['panel_id']}",
            "",
            f"- schema_id: {payload['schema_id']}",
            f"- schema_version: {payload['schema_version']}",
            f"- panel_id: {payload['panel_id']}",
            f"- request_id: {payload['request_id']}",
            f"- critic_count: {payload['critic_count']}",
            f"- completed_critic_count: {payload['completed_critic_count']}",
            f"- provider_ids: {', '.join(payload['provider_ids'])}",
            f"- adapter_classes: {', '.join(payload['adapter_classes'])}",
            f"- external_call_made: {str(payload['external_call_made']).lower()}",
            f"- model_boundary_crossed: {str(payload['model_boundary_crossed']).lower()}",
            f"- local_model_call_made: {str(payload['local_model_call_made']).lower()}",
            f"- mutation_performed: {str(payload['mutation_performed']).lower()}",
            f"- publication_performed: {str(payload['publication_performed']).lower()}",
            f"- allowed_actions: {payload['allowed_actions']}",
            f"- requires_human_review: {str(payload['requires_human_review']).lower()}",
            f"- transport_kind: {payload['transport_kind']}",
            "",
        ]
    )


__all__ = [
    "DARS_REMOTE_SUBSCRIPTION_DISPATCH_SCHEMA_ID",
    "DARS_REMOTE_SUBSCRIPTION_DISPATCH_SCHEMA_VERSION",
    "DARS_REMOTE_SUBSCRIPTION_PANEL_DISPATCH_SCHEMA_ID",
    "DARS_REMOTE_SUBSCRIPTION_PANEL_DISPATCH_SCHEMA_VERSION",
    "RemoteSubscriptionDispatchRequest",
    "RemoteSubscriptionDispatchResult",
    "RemoteSubscriptionPanelDispatchResult",
    "run_dars_remote_subscription_dispatch",
    "run_dars_remote_subscription_panel_dispatch",
]
