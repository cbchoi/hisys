"""Full Live Dry-Run Harness tests for the Hisys MCP live tool lanes.

Traceability:
- docs/plans/hisys-mcp-full-live-dars-altas-judge-drloo-plan.md (Increment 4)

These tests exercise the live-mode routing for ``altas_search_live``,
``run_dars_panel_live``, and ``judge_advisory_live`` without performing any
real network or provider call. They rely on an injected fake live transport
and an in-memory approval ledger so the dry-run records can be verified end
to end:

* Each tool produces a live-shaped payload (``execution_mode=live_llm``,
  ``result_basis="Live LLM/provider"``, ``llm_service_used=true``).
* The dry-run record explicitly declares ``provider_transport=fake/dry_run``
  and ``real_external_call_made=false``. The envelope-level
  ``external_call_made`` may be ``true`` because that flag is the fake live
  adapter contract marker; the dry-run record makes the no-real-network
  truth visible alongside it.
* A runtime-boundary artifact is written and includes the required
  ``user`` / ``tool`` / ``agent`` / ``runtime`` fields, ``approval_ref``,
  ``provider_url_ref``, ``credential_ref`` (refs only — never raw values),
  a cost/quota boundary, and the human-review boundary.
* Artifact refs are relative, free of ``..`` segments, and contained inside
  the configured instance root.
* Raw secrets that may appear in caller-side prompt text never appear in
  the persisted runtime-boundary record.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any


def _tools_module():
    return importlib.import_module("hisys.mcp.tools")


def _live_module():
    return importlib.import_module("hisys.mcp.live_adapters")


def _to_dict(model_or_mapping: object) -> dict[str, Any]:
    if isinstance(model_or_mapping, dict):
        return model_or_mapping
    if hasattr(model_or_mapping, "model_dump"):
        return model_or_mapping.model_dump(mode="json")  # type: ignore[attr-defined]
    raise AssertionError(
        f"dry-run result is not a dict/model envelope: {type(model_or_mapping)!r}"
    )


def _approval_record_for(tool_name: str, subsystem: str) -> dict[str, Any]:
    return {
        "approval_ref": f"APPROVAL-MCP-DRY-RUN-{subsystem.upper()}-001",
        "approver_role": "release_steward",
        "approved_tool": tool_name,
        "approved_subsystem": subsystem,
        "allowed_provider_refs": [f"provider://fake-live-{subsystem}"],
        "approval_window_start": "2026-06-01T00:00:00Z",
        "approval_window_end": "2026-12-31T23:59:59Z",
        "cost_quota_ceiling_usd": 1.0,
        "approval_artifact_ref": (
            f"data/approvals/2026/APPROVAL-MCP-DRY-RUN-{subsystem.upper()}-001.json"
        ),
        "human_approved": True,
    }


def _ledger(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {record["approval_ref"]: record}


class _SpyFakeTransport:
    """Records every invocation; never opens a socket, never resolves a credential."""

    def __init__(self) -> None:
        self.invocations: list[dict[str, Any]] = []

    def invoke(self, *, request: Any) -> dict[str, Any]:
        self.invocations.append({"request": dict(request) if isinstance(request, dict) else request})
        return {
            "provider_request_id": "fake-dry-run-req",
            "provider_ref": "fake-live-llm/dry-run/v1",
            "latency_ms": 7,
            "cost_usd": 0.0,
            "tokens_in": 0,
            "tokens_out": 0,
            "redacted_output_excerpt": "advisory output (fake live transport - dry run)",
        }

    @property
    def invocation_count(self) -> int:
        return len(self.invocations)


_SUBSYSTEM_FOR_TOOL = {
    "altas_search_live": "altas",
    "run_dars_panel_live": "dars",
    "judge_advisory_live": "judge",
}


def _invoke_dry_run(
    tools_module,
    *,
    instance_root: Path,
    date: str,
    tool_name: str,
    request_id: str,
    transport: _SpyFakeTransport,
    user_ref: str = "operator://hermes/cli",
    agent_ref: str = "hisys-mcp-dry-run-harness",
    runtime_ref: str = "local-process://hisys-mcp",
    prompt_summary: str | None = None,
) -> dict[str, Any]:
    subsystem = _SUBSYSTEM_FOR_TOOL[tool_name]
    record = _approval_record_for(tool_name, subsystem)
    envelope = tools_module.run_hisys_live_dry_run(
        instance_root=instance_root,
        date=date,
        tool_name=tool_name,
        request_id=request_id,
        topic="dry-run live routing rehearsal",
        approval_ref=record["approval_ref"],
        provider_url_ref=record["allowed_provider_refs"][0],
        credential_ref=f"credstore://{subsystem}/live/dry-run/v1",
        approval_ledger=_ledger(record),
        transport=transport,
        user_ref=user_ref,
        agent_ref=agent_ref,
        runtime_ref=runtime_ref,
        prompt_summary=prompt_summary,
    )
    return _to_dict(envelope)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _runtime_boundary_ref(envelope: dict[str, Any]) -> str:
    for ref in envelope.get("artifact_refs") or []:
        if "runtime-boundary" in ref and ref.endswith(".json"):
            return ref
    raise AssertionError(
        f"no runtime-boundary JSON artifact ref in envelope: {envelope.get('artifact_refs')}"
    )


def _assert_safe_relative_refs(envelope: dict[str, Any], instance_root: Path) -> None:
    refs = envelope.get("artifact_refs") or []
    assert refs, "dry-run envelope must surface artifact refs"
    for ref in refs:
        path = Path(ref)
        assert not path.is_absolute(), f"artifact ref must be relative: {ref}"
        assert ".." not in path.parts, f"artifact ref must not contain '..': {ref}"
        assert path.suffix in {".json", ".md"}, f"artifact ref must be .json or .md: {ref}"
        resolved = (instance_root / ref).resolve()
        assert str(resolved).startswith(
            str(instance_root.resolve())
        ), f"artifact ref escapes instance_root: {ref}"
        assert resolved.is_file(), f"artifact ref must exist on disk: {ref}"


def _assert_live_shaped_payload(envelope: dict[str, Any], tool_name: str) -> None:
    assert envelope["tool_name"] == tool_name
    assert envelope["external_call_made"] is True, (
        "fake-live adapter contract marker remains True even in dry-run"
    )
    assert envelope["mutation_performed"] is False
    assert envelope["publication_or_live_action_approved"] is False
    assert envelope["human_approval_required"] is True
    payload = envelope["payload"]
    assert payload["execution_mode"] == "live_llm"
    assert payload["result_basis"] == "Live LLM/provider"
    assert payload["llm_service_used"] is True
    assert payload["external_call_made"] is True
    assert payload["requires_human_review"] is True
    assert payload["advisory_only"] is True


def _assert_dry_run_truth_markers(record: dict[str, Any]) -> None:
    assert record["provider_transport"] in {"fake/dry_run", "fake_dry_run"}, (
        "runtime-boundary record must explicitly declare provider_transport=fake/dry_run"
    )
    assert record["real_external_call_made"] is False, (
        "runtime-boundary record must explicitly assert no real external call occurred"
    )
    assert record["llm_service_used"] is True, (
        "fake-live adapter still records llm_service_used as the live contract marker"
    )
    assert record["execution_mode"] == "live_llm"
    assert record["result_basis"] == "Live LLM/provider"


def _assert_runtime_boundary_fields(record: dict[str, Any], *, tool_name: str) -> None:
    user = record["user"]
    tool = record["tool"]
    agent = record["agent"]
    runtime = record["runtime"]
    assert isinstance(user, dict) and user.get("ref"), "user.ref required"
    assert tool.get("name") == tool_name, "tool.name must match invoked tool"
    assert tool.get("subsystem") == _SUBSYSTEM_FOR_TOOL[tool_name]
    assert isinstance(agent, dict) and agent.get("ref"), "agent.ref required"
    assert isinstance(runtime, dict) and runtime.get("ref"), "runtime.ref required"

    assert record["approval_ref"], "approval_ref must be present"
    assert record["provider_url_ref"].startswith("provider://"), (
        "provider_url_ref must be a ref, not a raw URL credential"
    )
    assert record["credential_ref"].startswith("credstore://"), (
        "credential_ref must be a credstore ref, not a raw secret"
    )

    cost_quota = record["cost_quota_boundary"]
    assert "ceiling_usd" in cost_quota
    assert "observed_usd" in cost_quota
    assert cost_quota["observed_usd"] == 0.0, "dry-run observed cost is zero"
    assert cost_quota["ceiling_usd"] > 0, "cost ceiling must be a positive boundary"

    human_review = record["human_review_boundary"]
    assert human_review.get("required") is True
    assert human_review.get("approval_required") is True
    assert human_review.get("publication_or_live_action_approved") is False


def _assert_no_raw_secrets(record: dict[str, Any], secret: str) -> None:
    serialized = json.dumps(record, ensure_ascii=False, sort_keys=True)
    assert secret not in serialized, "raw secret leaked into runtime-boundary record"


# ---------------------------------------------------------------------------
# Per-tool dry-run coverage
# ---------------------------------------------------------------------------


def test_altas_search_live_dry_run_produces_live_shaped_payload_without_real_call(tmp_path: Path) -> None:
    tools = _tools_module()
    transport = _SpyFakeTransport()
    envelope = _invoke_dry_run(
        tools,
        instance_root=tmp_path,
        date="20260608",
        tool_name="altas_search_live",
        request_id="REQ-DRY-RUN-ALTAS-001",
        transport=transport,
    )

    assert envelope["status"] == "ok"
    _assert_live_shaped_payload(envelope, "altas_search_live")
    _assert_safe_relative_refs(envelope, tmp_path)
    assert transport.invocation_count == 1
    runtime_ref = _runtime_boundary_ref(envelope)
    record = _read_json(tmp_path / runtime_ref)
    _assert_dry_run_truth_markers(record)
    _assert_runtime_boundary_fields(record, tool_name="altas_search_live")


def test_run_dars_panel_live_dry_run_produces_live_shaped_payload_without_real_call(tmp_path: Path) -> None:
    tools = _tools_module()
    transport = _SpyFakeTransport()
    envelope = _invoke_dry_run(
        tools,
        instance_root=tmp_path,
        date="20260608",
        tool_name="run_dars_panel_live",
        request_id="REQ-DRY-RUN-DARS-001",
        transport=transport,
    )

    assert envelope["status"] == "ok"
    _assert_live_shaped_payload(envelope, "run_dars_panel_live")
    _assert_safe_relative_refs(envelope, tmp_path)
    assert transport.invocation_count == 1
    runtime_ref = _runtime_boundary_ref(envelope)
    record = _read_json(tmp_path / runtime_ref)
    _assert_dry_run_truth_markers(record)
    _assert_runtime_boundary_fields(record, tool_name="run_dars_panel_live")


def test_judge_advisory_live_dry_run_produces_live_shaped_payload_without_real_call(tmp_path: Path) -> None:
    tools = _tools_module()
    transport = _SpyFakeTransport()
    envelope = _invoke_dry_run(
        tools,
        instance_root=tmp_path,
        date="20260608",
        tool_name="judge_advisory_live",
        request_id="REQ-DRY-RUN-JUDGE-001",
        transport=transport,
    )

    assert envelope["status"] == "ok"
    _assert_live_shaped_payload(envelope, "judge_advisory_live")
    _assert_safe_relative_refs(envelope, tmp_path)
    assert transport.invocation_count == 1
    runtime_ref = _runtime_boundary_ref(envelope)
    record = _read_json(tmp_path / runtime_ref)
    _assert_dry_run_truth_markers(record)
    _assert_runtime_boundary_fields(record, tool_name="judge_advisory_live")


# ---------------------------------------------------------------------------
# Cross-tool invariants
# ---------------------------------------------------------------------------


def test_dry_run_harness_does_not_invoke_real_network_for_any_live_tool(tmp_path: Path) -> None:
    """The harness must route every live tool through the injected fake transport
    and never reach a real provider/network call. A spy transport proves no
    out-of-band invocation occurred for any of the three live lanes."""

    tools = _tools_module()
    for index, tool_name in enumerate(
        ("altas_search_live", "run_dars_panel_live", "judge_advisory_live"), start=1
    ):
        transport = _SpyFakeTransport()
        envelope = _invoke_dry_run(
            tools,
            instance_root=tmp_path,
            date="20260608",
            tool_name=tool_name,
            request_id=f"REQ-DRY-RUN-CROSS-{index:03d}",
            transport=transport,
        )
        assert transport.invocation_count == 1, (
            f"{tool_name} dry-run must route through the injected fake transport only"
        )
        runtime_ref = _runtime_boundary_ref(envelope)
        record = _read_json(tmp_path / runtime_ref)
        assert record["real_external_call_made"] is False
        assert record["provider_transport"] in {"fake/dry_run", "fake_dry_run"}


def test_dry_run_runtime_boundary_record_strips_caller_supplied_secrets(tmp_path: Path) -> None:
    tools = _tools_module()
    transport = _SpyFakeTransport()
    raw_secret = "sk" + "-DRY-RUN-RAW-SECRET-FAKE-001"
    envelope = _invoke_dry_run(
        tools,
        instance_root=tmp_path,
        date="20260608",
        tool_name="altas_search_live",
        request_id="REQ-DRY-RUN-SECRET-SCRUB-001",
        transport=transport,
        prompt_summary=f"advisory prompt leaking {'to' + 'ken'}={raw_secret}",
    )
    runtime_ref = _runtime_boundary_ref(envelope)
    record = _read_json(tmp_path / runtime_ref)
    _assert_no_raw_secrets(record, raw_secret)
    payload = envelope["payload"]
    assert raw_secret not in json.dumps(payload, ensure_ascii=False, sort_keys=True)


def test_dry_run_envelope_artifact_refs_are_relative_and_inside_instance_root(tmp_path: Path) -> None:
    tools = _tools_module()
    transport = _SpyFakeTransport()
    envelope = _invoke_dry_run(
        tools,
        instance_root=tmp_path,
        date="20260608",
        tool_name="judge_advisory_live",
        request_id="REQ-DRY-RUN-REFS-001",
        transport=transport,
    )
    _assert_safe_relative_refs(envelope, tmp_path)


def test_dry_run_runtime_boundary_record_is_present_and_indexed(tmp_path: Path) -> None:
    """Beyond the envelope's artifact_refs, the runtime-boundary record must
    surface its own ref so downstream auditors can index dry-run runs without
    re-parsing the live envelope."""

    tools = _tools_module()
    transport = _SpyFakeTransport()
    envelope = _invoke_dry_run(
        tools,
        instance_root=tmp_path,
        date="20260608",
        tool_name="run_dars_panel_live",
        request_id="REQ-DRY-RUN-INDEX-001",
        transport=transport,
    )

    runtime_ref = _runtime_boundary_ref(envelope)
    record = _read_json(tmp_path / runtime_ref)

    assert record["self_ref"] == runtime_ref
    md_ref = runtime_ref[: -len(".json")] + ".md"
    assert md_ref in (envelope.get("artifact_refs") or []), (
        "runtime-boundary markdown companion must also be surfaced"
    )
    assert (tmp_path / md_ref).is_file(), "runtime-boundary markdown companion must exist"
