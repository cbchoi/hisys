"""Schema validation tests.

Traceability: HISYS-SCHEMA-001, HISYS-T-001 (source registry schema),
HISYS-T-002 (compliance gate), HISYS-T-005A (Hermes provenance fields),
HISYS-T-008 (raw observation provenance), HISYS-T-009 (signal traceability),
HISYS-T-016 (alert decision audit), HISYS-T-018 (approval gate).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from hisys.core.time import utc_now
from hisys.schemas import (
    AgentHandoffPackage,
    AlertDecisionRecord,
    AuditEvent,
    BrowserDarsRevisionResolution,
    BrowserDarsRevisionResolutionReport,
    ExtractedSignal,
    FinalBrowserAcceptanceReview,
    FinalBrowserAcceptanceReviewReport,
    HermesCollectionTrace,
    PerspectiveProfile,
    ProvenanceBundle,
    DataQuality,
    RawObservation,
    SourceRegistryEntry,
    ZettelMemo,
)


def test_source_compliance_gate_blocks_unreviewed_web_news():
    # HISYS-T-002, HISYS-NFR-SEC-005
    with pytest.raises(ValidationError) as exc:
        SourceRegistryEntry(
            source_id="SRC-WEB-X-001",
            source_type="web_news",
            display_name="Unreviewed feed",
            owner="ops",
            lifecycle_state="approved",
            access_method="rss",
            cadence="PT1H",
            rate_limit="6/min",
            retention_rule="P30D",
            producer_id="t",
        )
    assert "compliance_review_ref" in str(exc.value)


def test_source_id_prefix_required():
    with pytest.raises(ValidationError):
        SourceRegistryEntry(
            source_id="WRONG-001",
            source_type="hardware_sensor",
            display_name="x",
            owner="x",
            access_method="device",
            cadence="P1H",
            rate_limit="60/min",
            retention_rule="P7D",
            producer_id="t",
        )


def test_hermes_tool_source_requires_scope_policy_when_active():
    # HISYS-FR-DS-006: scope policy must be in place before non-proposed state.
    with pytest.raises(ValidationError):
        SourceRegistryEntry(
            source_id="SRC-HERMES-X-001",
            source_type="hermes_tool",
            display_name="x",
            owner="x",
            lifecycle_state="experimental",
            access_method="hermes_tool",
            cadence="PT1H",
            rate_limit="10/min",
            retention_rule="P30D",
            producer_id="t",
        )


def test_hermes_provenance_requires_hierarchical_fields():
    # HISYS-DATA-005, HISYS-T-005A
    with pytest.raises(ValidationError):
        ProvenanceBundle(collector_kind="hermes_tool")


def test_raw_observation_round_trip(hardware_adapter):
    # HISYS-T-008 raw observation provenance
    result = hardware_adapter.collect()
    obs = hardware_adapter.to_observation(result, producer_id="test")
    assert isinstance(obs, RawObservation)
    assert obs.observation_id.startswith("OBS-")
    assert obs.source_id == "SRC-HW-MOCK-001"
    assert obs.payload_hash and obs.payload_ref
    assert obs.data_quality.source_confidence == 0.9


def test_extracted_signal_requires_observation_refs():
    # HISYS-T-009: signal must reference at least one observation
    with pytest.raises(ValidationError):
        ExtractedSignal(
            signal_id="SIG-X-001",
            observation_refs=[],
            signal_type="claim",
            claim_or_event="x",
            confidence=0.5,
            uncertainty="bounded",
            extraction_method="manual",
            producer_id="t",
            status="proposed",
        )


def test_zettel_memo_links_evidence_and_perspective():
    memo = ZettelMemo(
        memo_id="MEM-001",
        title="Anomaly note",
        summary="Anomaly observed",
        body="See linked signal.",
        source_refs=["SRC-HW-MOCK-001"],
        signal_refs=["SIG-HW-ANOM-001"],
        perspective_id="PERSP-OPS-001",
        confidence=0.7,
        producer_id="t",
        status="draft",
    )
    assert memo.memo_id == "MEM-001"


def test_alert_high_severity_requires_approval_when_sent():
    # HISYS-T-018, HISYS-FR-CE-006, HISYS-NFR-SEC-004
    with pytest.raises(ValidationError):
        AlertDecisionRecord(
            alert_id="ALERT-001",
            memo_refs=["MEM-001"],
            policy_version="v0.1",
            trigger_reason="severity high without approval",
            severity="high",
            confidence=0.8,
            novelty="new",
            approval_status="not_required",
            action_taken="sent",
            producer_id="t",
        )


def test_alert_with_approval_sends():
    rec = AlertDecisionRecord(
        alert_id="ALERT-002",
        memo_refs=["MEM-002"],
        policy_version="v0.1",
        trigger_reason="approved escalation",
        severity="high",
        confidence=0.9,
        novelty="new",
        approval_status="approved",
        action_taken="sent",
        producer_id="t",
    )
    assert rec.action_taken == "sent"


def test_handoff_advisory_default():
    pkg = AgentHandoffPackage(
        handoff_id="HANDOFF-001",
        target_agent_system="DARS",
        task="critique",
        context="signal contradicts source A",
        evidence_bundle=["OBS-001"],
        expected_output="critique",
        producer_id="t",
    )
    assert pkg.allowed_actions == "advisory_only"


def test_hermes_trace_boundary_path_enforced(hermes_inputs):
    bad = HermesCollectionTrace.model_construct
    with pytest.raises(ValidationError):
        HermesCollectionTrace(
            campaign_id=hermes_inputs.campaign_id,
            hermes_parent_run_id=hermes_inputs.hermes_parent_run_id,
            source_scope=hermes_inputs.source_scope,
            prompt_or_query_ref=hermes_inputs.prompt_or_query_ref,
            tool_output_ref=hermes_inputs.tool_output_ref,
            boundary_record_ref="not-a-valid-path",
            working_directory=hermes_inputs.working_directory,
            scope_policy_ref=hermes_inputs.scope_policy_ref,
            approval_state="preapproved",
            producer_id="t",
        )


def test_hermes_trace_delegated_requires_preapproval():
    with pytest.raises(ValidationError):
        HermesCollectionTrace(
            campaign_id="CAMP-HERMES-001",
            hermes_parent_run_id="run-1",
            delegated_task_id="task-1",
            source_scope="x",
            prompt_or_query_ref="p",
            tool_output_ref="o",
            boundary_record_ref=(
                "hisys/runtime-boundary/hermes/20260508/CAMP-HERMES-001/"
                "tool_output-001.md"
            ),
            working_directory="/tmp",
            scope_policy_ref="S",
            approval_state="preapproved",
            producer_id="t",
        )


def test_browser_dars_revision_resolution_schema_enforces_ready_gates():
    payload = {
        "schema_id": "hisys.browser_dars_revision_resolution",
        "schema_version": "0.1.0",
        "request_id": "HISYS-REQ-BROWSER-SCHEMA-001",
        "dars_review_ref": "data/dars-browser-reviews/20260510/DARS-REVIEW-HISYS-REQ-BROWSER-SCHEMA-001-BROWSER.json",
        "chief_editor_review_ref": "data/chief-editor-reviews/20260510/CHIEF-REVIEW-HISYS-REQ-BROWSER-SCHEMA-001-BROWSER.json",
        "competitive_matrix_ref": "data/competitive-matrices/20260510/MATRIX-HISYS-REQ-BROWSER-SCHEMA-001-BROWSER.json",
        "decision": "ready_for_final_acceptance_review",
        "segment_normalization_status": "complete",
        "corroboration_mapping_status": "complete",
        "segment_normalization_rows": [
            {
                "row_index": 1,
                "company_or_source": "DUNLEE | LMB Tube Technology",
                "normalized_segment": "ct",
                "basis": "explicit_row_segment",
            }
        ],
        "corroboration_mapping_rows": [
            {
                "row_index": 1,
                "company_or_source": "DUNLEE | LMB Tube Technology",
                "competitive_signal_strength": "high",
                "corroborating_evidence_class": "patent",
                "independent_corroboration_present": True,
                "evidence_refs": ["EV-DUNLEE-PATENT"],
            }
        ],
        "resolved_dars_revision_items": ["Normalize conclusions by segment."],
        "remaining_blockers": [],
        "final_acceptance_allowed": True,
        "allowed_actions": "advisory_only",
        "external_call_made": False,
        "mutation_performed": False,
        "producer_id": "schema-test",
    }

    rec = BrowserDarsRevisionResolution.model_validate(payload)

    assert rec.decision == "ready_for_final_acceptance_review"
    assert rec.final_acceptance_allowed is True
    BrowserDarsRevisionResolutionReport.model_validate(
        {
            "schema_id": "hisys.browser_dars_revision_resolution.report",
            "schema_version": "0.1.0",
            "request_id": rec.request_id,
            "dars_review_ref": rec.dars_review_ref,
            "revision_resolution_ref": "data/browser-dars-revision-resolutions/20260510/REVISION-HISYS-REQ-BROWSER-SCHEMA-001-BROWSER.json",
            "decision": rec.decision,
            "segment_normalization_status": rec.segment_normalization_status,
            "corroboration_mapping_status": rec.corroboration_mapping_status,
            "external_call_made": False,
            "mutation_performed": False,
        }
    )
    bad = {**payload, "remaining_blockers": ["still blocked"]}
    with pytest.raises(ValidationError):
        BrowserDarsRevisionResolution.model_validate(bad)


def test_final_browser_acceptance_schema_preserves_human_review_boundary():
    payload = {
        "schema_id": "hisys.chief_editor.final_browser_acceptance_review",
        "schema_version": "0.1.0",
        "request_id": "HISYS-REQ-BROWSER-SCHEMA-002",
        "revision_resolution_ref": "data/browser-dars-revision-resolutions/20260510/REVISION-HISYS-REQ-BROWSER-SCHEMA-002-BROWSER.json",
        "dars_review_ref": "data/dars-browser-reviews/20260510/DARS-REVIEW-HISYS-REQ-BROWSER-SCHEMA-002-BROWSER.json",
        "chief_editor_review_ref": "data/chief-editor-reviews/20260510/CHIEF-REVIEW-HISYS-REQ-BROWSER-SCHEMA-002-BROWSER.json",
        "competitive_matrix_ref": "data/competitive-matrices/20260510/MATRIX-HISYS-REQ-BROWSER-SCHEMA-002-BROWSER.json",
        "decision": "accept_for_human_reviewed_use",
        "accepted_conditions": [
            "segment_normalization_complete",
            "independent_corroboration_mapping_complete",
        ],
        "acceptance_scope": "browser_investigation_evidence_package_for_human_reviewed_use",
        "dars_role": "advisory_only_non_executable",
        "publication_or_live_action_approved": False,
        "human_approval_required_for_consequential_use": True,
        "external_call_made": False,
        "mutation_performed": False,
        "action_taken": "none",
        "producer_id": "schema-test",
    }

    rec = FinalBrowserAcceptanceReview.model_validate(payload)

    assert rec.decision == "accept_for_human_reviewed_use"
    assert rec.publication_or_live_action_approved is False
    FinalBrowserAcceptanceReviewReport.model_validate(
        {
            "schema_id": "hisys.chief_editor.final_browser_acceptance_review.report",
            "schema_version": "0.1.0",
            "request_id": rec.request_id,
            "revision_resolution_ref": rec.revision_resolution_ref,
            "final_review_ref": "data/chief-editor-final-browser-reviews/20260510/FINAL-CHIEF-REVIEW-HISYS-REQ-BROWSER-SCHEMA-002-BROWSER.json",
            "decision": rec.decision,
            "publication_or_live_action_approved": False,
            "external_call_made": False,
            "mutation_performed": False,
        }
    )
    bad = {**payload, "publication_or_live_action_approved": True}
    with pytest.raises(ValidationError):
        FinalBrowserAcceptanceReview.model_validate(bad)


def test_audit_event_minimum_fields():
    ev = AuditEvent(
        audit_id="AUDIT-001",
        event_type="collection_run",
        actor_id="hisys-test",
        record_refs=["OBS-001"],
        summary="captured payload",
        producer_id="t",
    )
    assert ev.result == "success"


def test_perspective_profile_lifecycle():
    p = PerspectiveProfile(
        perspective_id="PERSP-OPS-001",
        title="Operations",
        owner="ops",
        intent="operational risk view",
        producer_id="t",
    )
    assert p.lifecycle_state == "draft"
