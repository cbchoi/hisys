"""MCP boundary contract tests for the Hisys sidecar gateway.

Traceability: docs/plans/hisys-mcp-docker-service-implementation-tasks.md
Task 1.2, Claude review S0 and safety revisions.
"""

from __future__ import annotations

import importlib
import json


def _contracts_module():
    return importlib.import_module("hisys.mcp.contracts")


def _to_dict(model: object) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")  # type: ignore[attr-defined]
    if hasattr(model, "dict"):
        return model.dict()  # type: ignore[attr-defined]
    raise AssertionError(f"contract object is not serializable as a model: {type(model)!r}")


def test_mcp_result_defaults_are_fail_closed() -> None:
    contracts = _contracts_module()

    result = contracts.McpToolResultEnvelope(status="ok", tool_name="health_status")
    payload = _to_dict(result)

    assert payload["external_call_made"] is False
    assert payload["mutation_performed"] is False
    assert payload["publication_or_live_action_approved"] is False
    assert payload["human_approval_required"] is True
    assert payload["artifact_refs"] == []
    assert payload["payload"] == {}


def test_safety_flags_default_false() -> None:
    contracts = _contracts_module()

    flags = contracts.McpSafetyFlags()
    payload = _to_dict(flags)

    assert payload == {
        "external_call_allowed": False,
        "mutation_allowed": False,
        "publication_allowed": False,
        "live_provider_allowed": False,
    }


def test_request_envelope_approval_ref_does_not_enable_live_or_mutation_flags() -> None:
    contracts = _contracts_module()

    request = contracts.McpRequestEnvelope(
        request_id="REQ-MCP-APPROVAL-IGNORED-001",
        trace_id="TRACE-MCP-001",
        tool_name="health_status",
        approval_ref="APPROVAL-CANDIDATE-ONLY",
    )
    payload = _to_dict(request)

    assert payload["approval_ref"] == "APPROVAL-CANDIDATE-ONLY"
    assert payload["safety"] == {
        "external_call_allowed": False,
        "mutation_allowed": False,
        "publication_allowed": False,
        "live_provider_allowed": False,
    }


def test_result_json_serialization_is_deterministic_for_snapshot_checks() -> None:
    contracts = _contracts_module()

    result = contracts.McpToolResultEnvelope(
        status="needs_more_evidence",
        tool_name="investigate_domain",
        request_id="REQ-MCP-DET-001",
        artifact_refs=["reports/run-summaries/20260605/hisys-health-status.json"],
        payload={"z": 1, "a": {"b": 2}},
    )
    first = json.dumps(_to_dict(result), ensure_ascii=False, sort_keys=True)
    second = json.dumps(_to_dict(result), ensure_ascii=False, sort_keys=True)

    assert first == second
    assert "REQ-MCP-DET-001" in first
