"""Hermes tool/user-input/delegated subagent mock adapter.

Traceability:
- HISYS-FR-DS-006, HISYS-FR-INV-006, HISYS-FR-AGT-005, HISYS-DATA-005.
- HISYS-IDD-001 Section 4 (HermesToolSource subtype) and Section 6
  (Markdown boundary path convention).
- HISYS-FIXTURE-001 (hermes-tool-hierarchy), HISYS-T-005A.

The adapter produces both a ``RawCollectionResult`` (suitable for
``DataSource.to_observation``) and a ``HermesCollectionTrace`` linking
campaign / parent run / delegated task / tool invocation IDs and the
working-directory Markdown boundary record reference.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ..core.ids import IdNamespace, make_id
from ..core.time import utc_now
from ..schemas.hermes_trace import ApprovalState, HermesCollectionTrace
from ..schemas.observation import DataQuality, ProvenanceBundle
from .base import DataSource, RawCollectionResult, _hash_payload


@dataclass(frozen=True)
class HermesCollectionInputs:
    campaign_id: str
    hermes_parent_run_id: str
    user_input_ref: str
    prompt_or_query_ref: str
    tool_output_ref: str
    boundary_record_ref: str
    working_directory: str
    scope_policy_ref: str
    approval_state: ApprovalState = "preapproved"
    tool_invocation_id: str | None = None
    tool_name: str | None = None
    enabled_toolsets: tuple[str, ...] = ()
    delegated_task_id: str | None = None
    delegated_subagent_preapproval_ref: str | None = None
    source_scope: str = "default"


class HermesToolMockSource(DataSource):
    def __init__(
        self,
        source,
        *,
        payload: dict[str, Any],
        inputs: HermesCollectionInputs,
    ) -> None:
        super().__init__(source)
        self._payload = payload
        self._inputs = inputs

    def collect(self, collection_context: Mapping[str, Any] | None = None) -> RawCollectionResult:
        run_id = make_id(IdNamespace.COLLECTION_RUN)
        provenance = ProvenanceBundle(
            collector_kind="hermes_tool",
            method="hermes_tool_mock",
            campaign_id=self._inputs.campaign_id,
            hermes_parent_run_id=self._inputs.hermes_parent_run_id,
            user_input_ref=self._inputs.user_input_ref,
            delegated_task_id=self._inputs.delegated_task_id,
            delegated_subagent_preapproval_ref=self._inputs.delegated_subagent_preapproval_ref,
            tool_invocation_id=self._inputs.tool_invocation_id,
            tool_name=self._inputs.tool_name,
            enabled_toolsets=list(self._inputs.enabled_toolsets),
            prompt_or_query_ref=self._inputs.prompt_or_query_ref,
            tool_output_ref=self._inputs.tool_output_ref,
            boundary_record_ref=self._inputs.boundary_record_ref,
            working_directory=self._inputs.working_directory,
            scope_policy_ref=self._inputs.scope_policy_ref,
            approval_state=self._inputs.approval_state,
        )
        quality = DataQuality(
            completeness="full",
            freshness="current",
            anomaly_flags=[],
            source_confidence=0.65,
        )
        payload_ref = f"fixture://hermes-tool/{run_id}.json"
        return RawCollectionResult(
            source_id=self.source.source_id,
            collection_run_id=run_id,
            collected_at=utc_now(),
            payload=self._payload,
            payload_ref=payload_ref,
            payload_hash=_hash_payload(self._payload),
            provenance_bundle=provenance,
            data_quality=quality,
        )

    def build_trace(
        self,
        *,
        producer_id: str,
        observation_refs: list[str],
        audit_event_refs: list[str] | None = None,
        status: str = "completed",
    ) -> HermesCollectionTrace:
        return HermesCollectionTrace(
            campaign_id=self._inputs.campaign_id,
            hermes_parent_run_id=self._inputs.hermes_parent_run_id,
            delegated_task_id=self._inputs.delegated_task_id,
            delegated_subagent_preapproval_ref=self._inputs.delegated_subagent_preapproval_ref,
            tool_invocation_id=self._inputs.tool_invocation_id,
            tool_name=self._inputs.tool_name,
            enabled_toolsets=list(self._inputs.enabled_toolsets),
            source_scope=self._inputs.source_scope,
            user_input_ref=self._inputs.user_input_ref,
            prompt_or_query_ref=self._inputs.prompt_or_query_ref,
            tool_output_ref=self._inputs.tool_output_ref,
            boundary_record_ref=self._inputs.boundary_record_ref,
            working_directory=self._inputs.working_directory,
            scope_policy_ref=self._inputs.scope_policy_ref,
            approval_state=self._inputs.approval_state,
            raw_observation_refs=observation_refs,
            audit_event_refs=list(audit_event_refs or []),
            producer_id=producer_id,
            status=status,
        )
