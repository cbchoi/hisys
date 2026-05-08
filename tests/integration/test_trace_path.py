"""End-to-end trace path test.

Traceability: HISYS-IMP-001 Section 4 ("Definition of Done for Phase-3"
end-to-end traceability statement), HISYS-T-024 (end-to-end traceability),
HISYS-T-005A (Hermes hierarchical collection),
HISYS-FR-CE-004 (alert decisions both for escalation and non-escalation),
HISYS-FR-ADM-002 (audit events for all key operations).

Path:
    SourceRegistryEntry
      -> HermesCollectionTrace + RawObservation
      -> ExtractedSignal
      -> ZettelMemo
      -> AlertDecisionRecord
      -> AuditEvent

Each step MUST keep raw evidence and interpretation on separate linked
records (HISYS-DATA-002). Hermes hierarchical fields MUST be populated.
"""

from __future__ import annotations

from hisys.core.ids import IdNamespace, make_id
from hisys.schemas import (
    AlertDecisionRecord,
    AuditEvent,
    ExtractedSignal,
    HermesCollectionTrace,
    PerspectiveProfile,
    RawObservation,
    ZettelMemo,
)


def test_end_to_end_trace_path(hermes_adapter, hermes_inputs, hermes_source):
    # 1) Source -> collection -> RawObservation
    result = hermes_adapter.collect()
    obs: RawObservation = hermes_adapter.to_observation(
        result, producer_id="trace-test"
    )

    # 2) HermesCollectionTrace links observation back to campaign/parent run.
    trace: HermesCollectionTrace = hermes_adapter.build_trace(
        producer_id="trace-test",
        observation_refs=[obs.observation_id],
    )

    # 3) Extraction produces an interpretation that *references* evidence
    #    rather than copying it (HISYS-DATA-002).
    signal = ExtractedSignal(
        signal_id=make_id(IdNamespace.SIGNAL, "HERMES-001"),
        observation_refs=[obs.observation_id],
        signal_type="claim",
        claim_or_event="Two reliable sources contradict claim X",
        entities=["claim_X"],
        confidence=0.7,
        uncertainty="contradiction_present",
        contradictions=["claim_X_alt"],
        extraction_method="mock_extractor_v0",
        producer_id="trace-test",
        status="proposed",
    )

    # 4) Perspective + memo (interpretation, with refs back to evidence).
    persp = PerspectiveProfile(
        perspective_id="PERSP-RESEARCH-001",
        title="Research perspective",
        owner="research",
        lifecycle_state="active",
        intent="research-quality cross-source synthesis",
        producer_id="trace-test",
        status="active",
    )
    memo = ZettelMemo(
        memo_id=make_id(IdNamespace.MEMO, "HERMES-001"),
        title="Contradicting reports for claim X",
        summary="Two sources conflict on claim X.",
        body="Linked to observation and signal; no raw payload copied.",
        source_refs=[hermes_source.source_id],
        signal_refs=[signal.signal_id],
        perspective_id=persp.perspective_id,
        confidence=0.6,
        producer_id="trace-test",
        status="draft",
    )

    # 5) Alert decision (low severity / non-escalation is still recorded).
    alert = AlertDecisionRecord(
        alert_id=make_id(IdNamespace.ALERT, "HERMES-001"),
        memo_refs=[memo.memo_id],
        signal_refs=[signal.signal_id],
        policy_version="v0.1",
        trigger_reason="contradiction across reliable sources",
        severity="medium",
        confidence=0.6,
        novelty="new",
        approval_status="not_required",
        action_taken="none",
        suppression_key=None,
        follow_up="DARS critique requested",
        producer_id="trace-test",
        status="pending",
    )

    # 6) AuditEvent capturing the run.
    audit = AuditEvent(
        audit_id=make_id(IdNamespace.AUDIT, "HERMES-001"),
        event_type="hermes_collection_run",
        actor_id="trace-test",
        record_refs=[
            hermes_source.source_id,
            obs.observation_id,
            signal.signal_id,
            memo.memo_id,
            alert.alert_id,
            trace.campaign_id,
        ],
        summary="end-to-end Hermes collection trace",
        result="success",
        producer_id="trace-test",
    )

    # ---- Assertions on the path ----

    # Evidence vs interpretation separation (HISYS-DATA-002).
    assert obs.payload_ref and not memo.body.endswith(repr(result.payload))
    assert signal.observation_refs == [obs.observation_id]
    assert memo.signal_refs == [signal.signal_id]
    assert memo.source_refs == [hermes_source.source_id]
    assert alert.memo_refs == [memo.memo_id]

    # Hermes hierarchical fields are populated on both the trace and on the
    # observation's provenance bundle (HISYS-DATA-005, HISYS-T-005A).
    pb = obs.provenance_bundle
    for field in (
        pb.campaign_id,
        pb.hermes_parent_run_id,
        pb.user_input_ref,
        pb.prompt_or_query_ref,
        pb.tool_output_ref,
        pb.boundary_record_ref,
        pb.scope_policy_ref,
        pb.approval_state,
    ):
        assert field, "missing Hermes provenance field"
    assert trace.raw_observation_refs == [obs.observation_id]
    assert trace.delegated_task_id == hermes_inputs.delegated_task_id
    assert trace.delegated_subagent_preapproval_ref == hermes_inputs.delegated_subagent_preapproval_ref

    # Boundary record path follows controlled convention.
    assert trace.boundary_record_ref.startswith(
        "hisys/runtime-boundary/hermes/"
    )

    # Audit event ties everything together.
    assert hermes_source.source_id in audit.record_refs
    assert obs.observation_id in audit.record_refs
    assert memo.memo_id in audit.record_refs
    assert alert.alert_id in audit.record_refs
