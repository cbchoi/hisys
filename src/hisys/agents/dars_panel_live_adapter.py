"""Local fake-server bridge for controlled live DARS panel rehearsals.

M-CP-LIVE-2 intentionally supports only localhost OpenAI-compatible fake/local
model endpoints after a valid M-CP-LIVE-1 activation packet. It performs no
credential lookup, sends no Authorization header, rejects remote endpoints before
opening a socket, and persists a model-boundary record for each critic task.
"""

from __future__ import annotations

import json
import re
import socket
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

from hisys.config.instance import InstanceRoot

from .dars_config import _classify_local_endpoint
from .dars_panel_live_config import (
    LiveDarsPanelActivationPacket,
    validate_live_dars_panel_activation_packet,
)

_DATE_PATTERN = re.compile(r"^[0-9]{8}$")
_SLUG_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
LIVE_PANEL_BOUNDARY_SCHEMA_ID = "hisys.dars.panel.live.local_model_boundary"
LIVE_PANEL_BOUNDARY_SCHEMA_VERSION = "0.1.0"


@dataclass(frozen=True)
class LocalModelCriticRequest:
    """One critic request routed to a localhost-only model endpoint."""

    yyyymmdd: str
    request_id: str
    task_id: str
    critic_id: str
    critic_role: str
    backend_id: str
    model: str
    endpoint: str
    candidate_ref: str
    evidence_refs: list[str]
    rubric_ref: str
    critique_dimensions: list[str] = field(default_factory=list)
    timeout_seconds: float = 5.0


@dataclass(frozen=True)
class LocalModelCriticResult:
    """Result of one controlled local-model critic task."""

    task_id: str
    critic_id: str
    critic_role: str
    status: Literal["completed", "failed"]
    boundary_ref: str
    critique_text: str | None = None
    error_message: str | None = None
    external_call_made: bool = False
    local_model_call_made: bool = False
    model_boundary_crossed: bool = False
    endpoint_scope: Literal["localhost_only"] = "localhost_only"
    mutation_performed: bool = False


class LocalModelPanelAdapter:
    """Run one DARS critic task through a localhost OpenAI-compatible endpoint."""

    def __init__(self, *, instance: InstanceRoot) -> None:
        self.instance = instance

    def run_critic(
        self,
        *,
        activation_packet: LiveDarsPanelActivationPacket,
        critic_request: LocalModelCriticRequest,
    ) -> LocalModelCriticResult:
        _validate_request_slugs(critic_request)
        _validate_activation_packet(activation_packet)
        endpoint_issue = _classify_local_endpoint(critic_request.endpoint)
        if endpoint_issue is not None:
            raise ValueError(f"localhost_only endpoint required for live DARS panel adapter: {endpoint_issue}")
        if critic_request.backend_id != activation_packet.requested_backend_id:
            raise ValueError("critic request backend_id must match the activation packet requested_backend_id")

        started = time.time()
        status: Literal["completed", "failed"] = "completed"
        critique_text: str | None = None
        error_message: str | None = None
        local_model_call_made = False
        model_boundary_crossed = False
        try:
            critique_text = _post_openai_chat_completion(
                critic_request=critic_request,
                timeout_seconds=critic_request.timeout_seconds,
            )
            local_model_call_made = True
            model_boundary_crossed = True
        except ValueError as exc:
            status = "failed"
            error_message = str(exc)
            # A local model boundary was attempted if endpoint validation passed
            # and the HTTP client reached the request stage. It is still not an
            # external call and has no mutation authority.
            local_model_call_made = True
            model_boundary_crossed = True
        duration_ms = max(0, int((time.time() - started) * 1000))
        boundary_ref = _write_boundary_record(
            instance_root=Path(self.instance.root),
            activation_packet=activation_packet,
            critic_request=critic_request,
            status=status,
            critique_text=critique_text,
            error_message=error_message,
            duration_ms=duration_ms,
            local_model_call_made=local_model_call_made,
            model_boundary_crossed=model_boundary_crossed,
        )
        return LocalModelCriticResult(
            task_id=critic_request.task_id,
            critic_id=critic_request.critic_id,
            critic_role=critic_request.critic_role,
            status=status,
            critique_text=critique_text,
            error_message=error_message,
            boundary_ref=boundary_ref,
            local_model_call_made=local_model_call_made,
            model_boundary_crossed=model_boundary_crossed,
        )


def _validate_activation_packet(packet: LiveDarsPanelActivationPacket) -> None:
    report = validate_live_dars_panel_activation_packet(
        packet.model_dump(mode="json"),
        config_ref=f"activation-packet:{packet.activation_id}",
    )
    if not report.valid:
        issues = ", ".join(f"{issue.path}:{issue.code}" for issue in report.issues)
        raise ValueError(f"invalid activation packet for live DARS panel adapter: {issues}")


def _validate_request_slugs(request: LocalModelCriticRequest) -> None:
    if not _DATE_PATTERN.fullmatch(request.yyyymmdd):
        raise ValueError(f"invalid yyyymmdd for live DARS panel boundary: {request.yyyymmdd!r}")
    for name, value in {
        "request_id": request.request_id,
        "task_id": request.task_id,
        "critic_id": request.critic_id,
        "backend_id": request.backend_id,
    }.items():
        if not _SLUG_PATTERN.fullmatch(value):
            raise ValueError(f"invalid {name} for live DARS panel boundary: {value!r}")


def _post_openai_chat_completion(
    *,
    critic_request: LocalModelCriticRequest,
    timeout_seconds: float,
) -> str:
    payload = _build_openai_payload(critic_request)
    request = urllib.request.Request(
        critic_request.endpoint,
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "accept": "application/json",
            "user-agent": "hisys-dars-panel-local-model/0.1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read()
    except urllib.error.HTTPError:
        raise ValueError("local DARS panel model returned non-2xx response") from None
    except (socket.timeout, TimeoutError):
        raise ValueError("local DARS panel model request timed out") from None
    except (urllib.error.URLError, ConnectionError, OSError):
        raise ValueError("local DARS panel model request failed") from None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError("local DARS panel model response is malformed JSON") from None
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise ValueError("local DARS panel model response is missing message content") from None
    if not isinstance(content, str) or not content.strip():
        raise ValueError("local DARS panel model response is missing message content")
    return content


def _build_openai_payload(critic_request: LocalModelCriticRequest) -> dict[str, object]:
    system = (
        "You are a DARS critic role in a controlled Hisys local-model rehearsal. "
        "Allowed actions: advisory_only. You have no browser, no search, and no tool authorization. "
        "Do not mutate state, publish, approve, deploy, or call external services."
    )
    user = "\n".join(
        [
            f"critic_id={critic_request.critic_id}",
            f"critic_role={critic_request.critic_role}",
            f"backend_id={critic_request.backend_id}",
            f"candidate_ref={critic_request.candidate_ref}",
            f"evidence_refs={json.dumps(critic_request.evidence_refs, ensure_ascii=False)}",
            f"rubric_ref={critic_request.rubric_ref}",
            f"critique_dimensions={json.dumps(critic_request.critique_dimensions, ensure_ascii=False)}",
            "Return concise advisory critique text only.",
        ]
    )
    return {
        "model": critic_request.model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
    }


def _write_boundary_record(
    *,
    instance_root: Path,
    activation_packet: LiveDarsPanelActivationPacket,
    critic_request: LocalModelCriticRequest,
    status: Literal["completed", "failed"],
    critique_text: str | None,
    error_message: str | None,
    duration_ms: int,
    local_model_call_made: bool,
    model_boundary_crossed: bool,
) -> str:
    relative = (
        Path("runtime-boundary")
        / "dars-panel-live"
        / critic_request.yyyymmdd
        / critic_request.request_id
        / f"{critic_request.task_id}.json"
    )
    target = instance_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_id": LIVE_PANEL_BOUNDARY_SCHEMA_ID,
        "schema_version": LIVE_PANEL_BOUNDARY_SCHEMA_VERSION,
        "activation_id": activation_packet.activation_id,
        "approval_ref": activation_packet.approval_ref,
        "operator_id": activation_packet.operator_id,
        "request_id": critic_request.request_id,
        "task_id": critic_request.task_id,
        "critic_id": critic_request.critic_id,
        "critic_role": critic_request.critic_role,
        "backend_id": critic_request.backend_id,
        "adapter_class": "local_model",
        "endpoint_scope": "localhost_only",
        "allowed_actions": "advisory_only",
        "dispatch_decision": "allowed",
        "task_status": status,
        "duration_ms": duration_ms,
        "model_boundary_crossed": model_boundary_crossed,
        "local_model_call_made": local_model_call_made,
        "external_call_made": False,
        "mutation_performed": False,
        "publication_performed": False,
        "action_authorized": False,
        "advisory_only": True,
        "requires_human_review": True,
        "critique_text_excerpt": (critique_text or "")[:240],
        "error_message": error_message,
        "policy_refs": [
            "M-CP-LIVE-1",
            "M-CP-LIVE-2",
            "HISYS-FR-DARS-CP-007",
            "HISYS-NFR-DARS-CP-002",
        ],
    }
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return relative.as_posix()


__all__ = [
    "LIVE_PANEL_BOUNDARY_SCHEMA_ID",
    "LIVE_PANEL_BOUNDARY_SCHEMA_VERSION",
    "LocalModelCriticRequest",
    "LocalModelCriticResult",
    "LocalModelPanelAdapter",
]
