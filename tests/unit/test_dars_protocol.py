"""DARS canonical protocol envelope tests.

Traceability: HISYS-DARS-CONTRACT-001, HISYS-FR-AGT-001..005,
HISYS-T-019, HISYS-T-020, HISYS-T-024.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from hisys.agents.dars_protocol import DarsRequestEnvelope, DarsResponseEnvelope


def _valid_request_payload() -> dict:
    return {
        "schema_id": "hisys.dars.request",
        "schema_version": "0.1.0",
        "request_id": "DARSREQ-001",
        "handoff_id": "HANDOFF-001",
        "created_at": "2026-05-09T00:00:00Z",
        "contract": {
            "output_schema_id": "hisys.dars.critique",
            "output_schema_version": "0.1.0",
            "allowed_actions": "advisory_only",
            "external_side_effects_allowed": False,
            "mutation_allowed": False,
            "requires_structured_output": True,
        },
        "prompt_bundle_ref": {
            "prompt_bundle_id": "pb-dars-logical-conservative-devil",
            "prompt_bundle_version": "0.1.0",
            "registry_backend": "file",
            "tenant_scope": "sysailab-default",
            "status": "approved",
            "sha256": "0" * 64,
        },
        "role": {
            "role_id": "logical_conservative_devil",
            "kind": "devil_advocate",
            "profession": "logic_reviewer",
            "persona": "conservative_critic",
            "knowledge_scope": ["formal_logic", "evidence_quality"],
            "stance": "skeptical_but_constructive",
            "strictness": "high",
            "creativity": "low",
            "verbosity": "concise_structured",
            "critique_dimensions": ["logical_validity", "unsupported_claims"],
            "prompt": {
                "objective": "Find logical gaps and unsupported claims.",
                "focus": "Improve alternatives without blocking execution.",
            },
        },
        "sampling": {"temperature": 0.2, "top_p": 0.9, "max_output_tokens": 2000},
        "decision_process": {
            "mode": "progressive_adversarial",
            "objective": "improve_solution",
            "blocking_policy": "advisory_only",
            "round_index": 1,
            "max_rounds": 3,
            "stop_condition": "no_high_severity_unresolved_findings",
        },
        "rubric_refs": [
            {
                "rubric_id": "dars-progressive-decision",
                "rubric_version": "0.1.0",
                "artifact_ref": "harness/rubrics/dars/progressive-decision-v0.1.0.json",
                "sha256": "1" * 64,
                "applies_to_roles": ["logical_conservative_devil"],
            }
        ],
        "critic_panel": [
            {
                "role_id": "logical_conservative_devil",
                "profession": "logic_reviewer",
                "persona": "conservative_critic",
                "knowledge_scope": ["formal_logic"],
            }
        ],
        "handoff": {
            "handoff_type": "critique",
            "requester": "chief_editor",
            "task": "Review this alternative set.",
            "context_summary": "Fixture bounded context.",
            "expected_output": "DarsCritiqueRecord",
            "due_condition": None,
        },
        "record_refs": {
            "sources": ["SRC-001"],
            "observations": [],
            "signals": [],
            "memos": ["MEMO-001"],
            "alerts": [],
            "requirements": ["HISYS-FR-AGT-001"],
            "runtime_boundary": ["runtime-boundary/dars/20260509/request.json"],
        },
        "evidence": {
            "bundles": [
                {
                    "evidence_ref": "EVID-001",
                    "artifact_ref": "data/signals/SIG-001.json",
                    "sha256": "2" * 64,
                    "summary": "Fixture evidence summary.",
                    "relevance": "primary",
                }
            ],
            "limitations": ["Fixture data only."],
        },
        "constraints": {
            "requirement_refs": ["HISYS-FR-AGT-001", "HISYS-T-019"],
            "policy_refs": ["HISYS-CON-010", "HISYS-CON-011", "HISYS-CON-012"],
            "prohibited_actions": ["external_call", "file_write", "alert_send", "software_trigger"],
            "approval_state": "not_required",
            "approval_ref": None,
        },
        "user_focus": {"prompt": "Focus on unsupported claims."},
    }


def _valid_response_payload() -> dict:
    return {
        "schema_id": "hisys.dars.response",
        "schema_version": "0.1.0",
        "response_id": "DARSRESP-001",
        "request_id": "DARSREQ-001",
        "handoff_id": "HANDOFF-001",
        "created_at": "2026-05-09T00:01:00Z",
        "producer": {
            "backend_id": "loopback_placeholder",
            "backend_kind": "loopback",
            "role_id": "logical_conservative_devil",
            "model": None,
            "external_call_made": False,
        },
        "critique": {
            "critique_id": "CRIT-001",
            "status": "received",
            "critique_summary": "Evidence supports the alternative but confidence should be lower.",
            "confidence_assessment": "medium",
            "severity": "medium",
            "requires_human_review": True,
            "unsupported_claims": [
                {
                    "claim_ref": "CLAIM-001",
                    "statement": "The alternative is production ready.",
                    "reason": "No release evidence was referenced.",
                    "evidence_refs": ["EVID-001"],
                    "severity": "medium",
                }
            ],
            "counterarguments": [],
            "risk_findings": [],
            "recommended_actions": [
                {
                    "action_id": "RECACT-001",
                    "action_type": "request_more_evidence",
                    "statement": "Collect release evidence before approval.",
                    "priority": "medium",
                    "requires_approval": True,
                    "allowed_to_execute": False,
                }
            ],
            "linked_record_refs": {"sources": ["SRC-001"], "memos": ["MEMO-001"], "handoffs": ["HANDOFF-001"]},
        },
        "decision_trace": {
            "process_mode": "progressive_adversarial",
            "round_index": 1,
            "critic_role_id": "logical_conservative_devil",
            "critic_profession": "logic_reviewer",
            "critic_persona": "conservative_critic",
            "prompt_bundle_ref": "pb-dars-logical-conservative-devil@0.1.0",
            "rubric_refs": ["dars-progressive-decision@0.1.0"],
            "improvement_direction": "revise_candidate",
            "blocks_decision": False,
            "unresolved_high_severity_findings": 0,
            "synthesis_summary": "Lower confidence and request release evidence.",
        },
        "rubric_scores": [
            {
                "axis_id": "logical_validity",
                "score": 3,
                "max_score": 5,
                "severity": "medium",
                "confidence": "high",
                "rationale": "One claim is not supported by release evidence.",
                "evidence_refs": ["EVID-001"],
                "improvement_recommendation": "Add release evidence or lower confidence.",
            }
        ],
        "validation": {"schema_valid": True, "warnings": [], "rejected_fields": []},
        "boundary": {
            "allowed_actions": "advisory_only",
            "action_taken": "none",
            "mutation_requested": False,
            "mutation_performed": False,
            "external_side_effects_requested": False,
            "external_side_effects_performed": False,
        },
    }


def test_dars_request_envelope_accepts_canonical_advisory_contract():
    envelope = DarsRequestEnvelope.model_validate(_valid_request_payload())

    assert envelope.schema_id == "hisys.dars.request"
    assert envelope.contract.allowed_actions == "advisory_only"
    assert envelope.contract.external_side_effects_allowed is False
    assert envelope.contract.mutation_allowed is False
    assert envelope.decision_process.blocking_policy == "advisory_only"
    assert envelope.constraints.prohibited_actions == ["external_call", "file_write", "alert_send", "software_trigger"]


def test_dars_request_envelope_rejects_mutating_contract():
    payload = _valid_request_payload()
    payload["contract"]["mutation_allowed"] = True

    with pytest.raises(ValidationError) as exc_info:
        DarsRequestEnvelope.model_validate(payload)

    assert "mutation_allowed" in str(exc_info.value)


def test_dars_response_envelope_accepts_structured_advisory_critique():
    envelope = DarsResponseEnvelope.model_validate(_valid_response_payload())

    assert envelope.schema_id == "hisys.dars.response"
    assert envelope.critique.recommended_actions[0].allowed_to_execute is False
    assert envelope.decision_trace.blocks_decision is False
    assert envelope.boundary.action_taken == "none"
    assert envelope.boundary.external_side_effects_performed is False


def test_dars_response_envelope_rejects_execution_or_blocking_behavior():
    payload = _valid_response_payload()
    payload["critique"]["recommended_actions"][0]["allowed_to_execute"] = True
    payload["decision_trace"]["blocks_decision"] = True
    payload["boundary"]["action_taken"] = "file_write"

    with pytest.raises(ValidationError) as exc_info:
        DarsResponseEnvelope.model_validate(payload)

    message = str(exc_info.value)
    assert "allowed_to_execute" in message
    assert "blocks_decision" in message
    assert "action_taken" in message
