"""DARS backend dispatch decision gate.

This module decides whether a validated DARS backend may be dispatched for a
request and records the decision as a runtime-boundary artifact. It performs no
backend call by itself.

Traceability: HISYS-DARS-CONTRACT-001, HISYS-FR-AGT-001..005,
HISYS-T-019, HISYS-T-020, HISYS-T-024, HISYS-CON-010, HISYS-CON-011,
HISYS-CON-012.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from ..config.instance import InstanceRoot
from ..schemas.lapidary_governance import AppraiserSeparationPolicy
from .appraiser_separation import (
    ADVISORY_INTENTS,
    AUTHORITY_INTENTS,
    DEFAULT_APPRAISER_POLICY_REF,
    classify_intent,
    resolve_policy_ref,
)
from .dars_config import DarsBackendConfig, DarsConfig


class DarsDispatchDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_id: Literal["hisys.dars.dispatch_decision"] = "hisys.dars.dispatch_decision"
    schema_version: Literal["0.1.0"] = "0.1.0"
    request_id: str
    backend_id: str
    backend_kind: str | None = None
    decision: Literal["allowed", "blocked"]
    reason_code: str
    reason: str
    approval_ref: str | None = None
    intent: str = "advisory_critique"
    allowed_actions: Literal["advisory_only"] = "advisory_only"
    action_taken: Literal["none"] = "none"
    external_call_requested: bool = False
    external_call_made: Literal[False] = False
    mutation_requested: bool = False
    mutation_performed: Literal[False] = False
    output_contract: str | None = None
    config_ref: str
    policy_refs: list[str]


class DarsDispatchGate:
    """Evaluate DARS backend dispatch safety and persist boundary records."""

    def __init__(self, *, instance: InstanceRoot) -> None:
        self.instance = instance

    def evaluate(
        self,
        *,
        yyyymmdd: str,
        request_id: str,
        config: DarsConfig,
        backend_id: str,
        approval_ref: str | None,
        intent: str = "advisory_critique",
        appraiser_policy: AppraiserSeparationPolicy | None = None,
    ) -> DarsDispatchDecision:
        backend = config.spec.backends.get(backend_id)
        policy_ref = resolve_policy_ref(appraiser_policy)
        verdict = classify_intent(intent, appraiser_policy=appraiser_policy)
        if verdict.decision == "blocked":
            decision = self._blocked(
                request_id=request_id,
                backend_id=backend_id,
                backend=backend,
                config=config,
                approval_ref=approval_ref,
                reason_code=verdict.reason_code,
                reason=verdict.reason,
                intent=intent,
                policy_ref=policy_ref,
            )
        elif backend is None:
            decision = self._blocked(
                request_id=request_id,
                backend_id=backend_id,
                backend=None,
                config=config,
                approval_ref=approval_ref,
                reason_code="unknown_backend",
                reason="DARS backend is not declared in the validated config.",
                intent=intent,
                policy_ref=policy_ref,
            )
        elif not backend.enabled:
            decision = self._blocked(
                request_id=request_id,
                backend_id=backend_id,
                backend=backend,
                config=config,
                approval_ref=approval_ref,
                reason_code="backend_disabled",
                reason="DARS backend is disabled in the resolved config snapshot.",
                intent=intent,
                policy_ref=policy_ref,
            )
        elif backend.external_call_allowed and not approval_ref:
            decision = self._blocked(
                request_id=request_id,
                backend_id=backend_id,
                backend=backend,
                config=config,
                approval_ref=approval_ref,
                reason_code="external_call_requires_approval",
                reason="DARS backend requests an external call and requires explicit approval before dispatch.",
                intent=intent,
                policy_ref=policy_ref,
            )
        elif backend.external_call_allowed and approval_ref:
            decision = self._allowed(
                request_id=request_id,
                backend_id=backend_id,
                backend=backend,
                config=config,
                approval_ref=approval_ref,
                reason_code="approved_external_backend_allowed",
                reason="DARS backend requests an external advisory call and has an explicit approval reference.",
                intent=intent,
                policy_ref=policy_ref,
            )
        elif backend.kind == "loopback":
            decision = self._allowed(
                request_id=request_id,
                backend_id=backend_id,
                backend=backend,
                config=config,
                approval_ref=approval_ref,
                reason_code="loopback_backend_allowed",
                reason="Loopback DARS backend is local-only and advisory-only.",
                intent=intent,
                policy_ref=policy_ref,
            )
        elif not backend.external_call_allowed and backend.mode in {"local_only", "read_only", "local_network_only"}:
            decision = self._allowed(
                request_id=request_id,
                backend_id=backend_id,
                backend=backend,
                config=config,
                approval_ref=approval_ref,
                reason_code="local_backend_allowed",
                reason="Enabled local/read-only DARS backend does not request external calls.",
                intent=intent,
                policy_ref=policy_ref,
            )
        else:
            decision = self._blocked(
                request_id=request_id,
                backend_id=backend_id,
                backend=backend,
                config=config,
                approval_ref=approval_ref,
                reason_code="backend_policy_blocked",
                reason="DARS backend did not satisfy the current dispatch policy.",
                intent=intent,
                policy_ref=policy_ref,
            )

        _write_decision(self.instance, yyyymmdd, decision)
        return decision

    def _allowed(
        self,
        *,
        request_id: str,
        backend_id: str,
        backend: DarsBackendConfig,
        config: DarsConfig,
        approval_ref: str | None,
        reason_code: str,
        reason: str,
        intent: str,
        policy_ref: str,
    ) -> DarsDispatchDecision:
        return _decision(
            request_id=request_id,
            backend_id=backend_id,
            backend=backend,
            config=config,
            approval_ref=approval_ref,
            decision="allowed",
            reason_code=reason_code,
            reason=reason,
            intent=intent,
            policy_ref=policy_ref,
        )

    def _blocked(
        self,
        *,
        request_id: str,
        backend_id: str,
        backend: DarsBackendConfig | None,
        config: DarsConfig,
        approval_ref: str | None,
        reason_code: str,
        reason: str,
        intent: str,
        policy_ref: str,
    ) -> DarsDispatchDecision:
        return _decision(
            request_id=request_id,
            backend_id=backend_id,
            backend=backend,
            config=config,
            approval_ref=approval_ref,
            decision="blocked",
            reason_code=reason_code,
            reason=reason,
            intent=intent,
            policy_ref=policy_ref,
        )


def _decision(
    *,
    request_id: str,
    backend_id: str,
    backend: DarsBackendConfig | None,
    config: DarsConfig,
    approval_ref: str | None,
    decision: Literal["allowed", "blocked"],
    reason_code: str,
    reason: str,
    intent: str,
    policy_ref: str,
) -> DarsDispatchDecision:
    traceability = config.traceability
    policy_refs = list(traceability.get("constraints", []))
    if policy_ref not in policy_refs:
        policy_refs.append(policy_ref)
    return DarsDispatchDecision(
        request_id=request_id,
        backend_id=backend_id,
        backend_kind=backend.kind if backend else None,
        decision=decision,
        reason_code=reason_code,
        reason=reason,
        approval_ref=approval_ref,
        intent=intent,
        external_call_requested=bool(backend.external_call_allowed) if backend else False,
        mutation_requested=False,
        output_contract=backend.output_contract if backend else None,
        config_ref=f"{config.config_id}@{config.config_version}",
        policy_refs=policy_refs,
    )


def _write_decision(instance: InstanceRoot, yyyymmdd: str, decision: DarsDispatchDecision) -> None:
    output_dir = instance.runtime_boundary_dir / "dars" / yyyymmdd
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"dars-dispatch-decision-{decision.request_id}.json"
    md_path = output_dir / f"dars-dispatch-decision-{decision.request_id}.md"
    payload = decision.model_dump(mode="json")
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(_decision_markdown(decision), encoding="utf-8")


def _decision_markdown(decision: DarsDispatchDecision) -> str:
    return "\n".join(
        [
            f"# DARS dispatch decision {decision.request_id}",
            "",
            f"- decision: {decision.decision}",
            f"- reason_code: {decision.reason_code}",
            f"- backend_id: {decision.backend_id}",
            f"- backend_kind: {decision.backend_kind}",
            f"- intent: {decision.intent}",
            f"- allowed_actions: {decision.allowed_actions}",
            f"- policy_refs: {', '.join(decision.policy_refs)}",
            f"- external_call_requested: {decision.external_call_requested}",
            f"- external_call_made: {decision.external_call_made}",
            f"- mutation_performed: {decision.mutation_performed}",
            f"- action_taken: {decision.action_taken}",
            "",
            decision.reason,
            "",
        ]
    )


__all__ = ["DarsDispatchDecision", "DarsDispatchGate"]
