"""Live source connector dispatch gate.

The gate records allow/block decisions before any source connector adapter can
make a network, browser, API, or external LLM call. It performs no connector call.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict

from ..config import InstanceRoot
from .live_source_config import SourceConnectorConfig, SourceConnectorRegistry


class SourceConnectorDispatchDecision(BaseModel):
    """Runtime-boundary decision made before source connector execution."""

    model_config = ConfigDict(extra="forbid")

    schema_id: Literal["hisys.source_connector.dispatch_decision"] = "hisys.source_connector.dispatch_decision"
    schema_version: Literal["0.1.0"] = "0.1.0"
    request_id: str
    connector_id: str
    connector_type: str | None = None
    decision: Literal["allowed", "blocked"]
    reason_code: str
    reason: str
    approval_ref: str | None = None
    requested_domain: str | None = None
    requested_actions: list[str]
    external_call_requested: bool
    external_call_permitted: bool
    external_call_made: Literal[False] = False
    mutation_requested: bool = False
    mutation_performed: Literal[False] = False
    output_schema: str | None = None
    policy_refs: list[str]


class SourceConnectorDispatchGate:
    """Evaluate source connector dispatch eligibility and persist evidence."""

    def __init__(self, *, instance: InstanceRoot) -> None:
        self.instance = instance

    def evaluate(
        self,
        *,
        yyyymmdd: str,
        request_id: str,
        registry: SourceConnectorRegistry,
        connector_id: str,
        approval_ref: str | None,
        requested_domain: str | None,
        requested_actions: list[str],
    ) -> SourceConnectorDispatchDecision:
        connector = registry.connectors.get(connector_id)
        mutation_requested = bool({"write", "post", "upload", "form_submit", "purchase", "mutation"} & set(requested_actions))
        external_call_requested = bool(connector and connector.connector_type != "local_file")
        if connector is None:
            decision = _decision(
                request_id=request_id,
                connector_id=connector_id,
                connector=None,
                decision="blocked",
                reason_code="unknown_connector",
                reason="Source connector is not declared in the validated registry.",
                approval_ref=approval_ref,
                requested_domain=requested_domain,
                requested_actions=requested_actions,
                external_call_requested=False,
                external_call_permitted=False,
                mutation_requested=mutation_requested,
            )
        elif set(requested_actions) & set(connector.forbidden_actions):
            decision = _decision(
                request_id=request_id,
                connector_id=connector_id,
                connector=connector,
                decision="blocked",
                reason_code="forbidden_action_requested",
                reason="Request included an action forbidden by the source connector policy.",
                approval_ref=approval_ref,
                requested_domain=requested_domain,
                requested_actions=requested_actions,
                external_call_requested=external_call_requested,
                external_call_permitted=False,
                mutation_requested=mutation_requested,
            )
        elif not connector.enabled:
            decision = _decision(
                request_id=request_id,
                connector_id=connector_id,
                connector=connector,
                decision="blocked",
                reason_code="connector_disabled",
                reason="Source connector is disabled in the resolved registry snapshot.",
                approval_ref=approval_ref,
                requested_domain=requested_domain,
                requested_actions=requested_actions,
                external_call_requested=external_call_requested,
                external_call_permitted=False,
                mutation_requested=mutation_requested,
            )
        elif connector.external_call_allowed and connector.requires_human_approval and not approval_ref:
            decision = _decision(
                request_id=request_id,
                connector_id=connector_id,
                connector=connector,
                decision="blocked",
                reason_code="external_call_requires_approval",
                reason="Source connector requests an external call and requires approval_ref before dispatch.",
                approval_ref=approval_ref,
                requested_domain=requested_domain,
                requested_actions=requested_actions,
                external_call_requested=external_call_requested,
                external_call_permitted=False,
                mutation_requested=mutation_requested,
            )
        elif requested_domain and connector.allowed_domains and requested_domain not in connector.allowed_domains:
            decision = _decision(
                request_id=request_id,
                connector_id=connector_id,
                connector=connector,
                decision="blocked",
                reason_code="domain_not_allowlisted",
                reason="Requested domain is not allowlisted for this source connector.",
                approval_ref=approval_ref,
                requested_domain=requested_domain,
                requested_actions=requested_actions,
                external_call_requested=external_call_requested,
                external_call_permitted=False,
                mutation_requested=mutation_requested,
            )
        else:
            decision = _decision(
                request_id=request_id,
                connector_id=connector_id,
                connector=connector,
                decision="allowed",
                reason_code="connector_policy_allowed",
                reason="Source connector satisfied registry and dispatch policy. Adapter execution is still separate.",
                approval_ref=approval_ref,
                requested_domain=requested_domain,
                requested_actions=requested_actions,
                external_call_requested=external_call_requested,
                external_call_permitted=bool(connector.external_call_allowed),
                mutation_requested=mutation_requested,
            )
        _write_decision(self.instance, yyyymmdd, decision)
        return decision


def _decision(
    *,
    request_id: str,
    connector_id: str,
    connector: SourceConnectorConfig | None,
    decision: Literal["allowed", "blocked"],
    reason_code: str,
    reason: str,
    approval_ref: str | None,
    requested_domain: str | None,
    requested_actions: list[str],
    external_call_requested: bool,
    external_call_permitted: bool,
    mutation_requested: bool,
) -> SourceConnectorDispatchDecision:
    return SourceConnectorDispatchDecision(
        request_id=request_id,
        connector_id=connector_id,
        connector_type=connector.connector_type if connector else None,
        decision=decision,
        reason_code=reason_code,
        reason=reason,
        approval_ref=approval_ref,
        requested_domain=requested_domain,
        requested_actions=list(requested_actions),
        external_call_requested=external_call_requested,
        external_call_permitted=external_call_permitted,
        mutation_requested=mutation_requested,
        output_schema=connector.output_schema if connector else None,
        policy_refs=["docs/use-cases/live-research-connectors.md", "examples/instance/config/source-connectors.yaml"],
    )


def _write_decision(instance: InstanceRoot, yyyymmdd: str, decision: SourceConnectorDispatchDecision) -> None:
    output_dir = instance.runtime_boundary_dir / "source-connectors" / yyyymmdd
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"connector-dispatch-{decision.request_id}-{decision.connector_id}"
    json_path = output_dir / f"{stem}.json"
    md_path = output_dir / f"{stem}.md"
    payload = decision.model_dump(mode="json")
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(_decision_markdown(decision), encoding="utf-8")


def _decision_markdown(decision: SourceConnectorDispatchDecision) -> str:
    return "\n".join(
        [
            f"# Source connector dispatch decision {decision.request_id}",
            "",
            f"- connector_id: {decision.connector_id}",
            f"- decision: {decision.decision}",
            f"- reason_code: {decision.reason_code}",
            f"- external_call_requested: {decision.external_call_requested}",
            f"- external_call_permitted: {decision.external_call_permitted}",
            f"- external_call_made: {decision.external_call_made}",
            f"- mutation_performed: {decision.mutation_performed}",
            "",
            decision.reason,
            "",
        ]
    )


__all__ = ["SourceConnectorDispatchDecision", "SourceConnectorDispatchGate"]
