"""Increment 5: Controlled Live Smoke harness / manual test seam.

Traceability:
- docs/plans/hisys-mcp-full-live-dars-altas-judge-drloo-plan.md (Increment 5)

This module hosts the controlled-live-smoke seam for the Hisys MCP live tool
lanes. Almost every test uses a fake injected transport so the harness shape
itself can be validated in CI without any real network call. A single test
exercises the real Codex CLI subprocess transport in read-only prompt mode and
is **skipped by default**. It only runs when *all* of the following are set:

* ``HISYS_ALLOW_LIVE_MCP_SMOKE=1`` — explicit operator opt-in for this run.
* ``HISYS_CODEX_CLI_PATH=/path/to/codex`` — absolute path to a Codex CLI
  executable. The harness does not look up the binary on ``PATH`` and the
  transport refuses to construct without an explicit path.
* ``HISYS_LIVE_MCP_APPROVAL_REF`` — approval ledger key for this smoke.
* ``HISYS_LIVE_MCP_PROVIDER_URL_REF`` — provider URL ref (non-secret).
* ``HISYS_LIVE_MCP_CREDENTIAL_REF`` — credstore ref (non-secret pointer).

No secret values are ever read from the environment by this harness; only
non-secret reference strings are. Even when the manual smoke runs, the
runtime-boundary record captures provider/credential refs only — never raw
values.
"""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
from typing import Any

import pytest


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
        f"smoke result is not a dict/model envelope: {type(model_or_mapping)!r}"
    )


def _approval_record(
    *, tool_name: str, subsystem: str, approval_ref: str, provider_url_ref: str
) -> dict[str, Any]:
    return {
        "approval_ref": approval_ref,
        "approver_role": "release_steward",
        "approved_tool": tool_name,
        "approved_subsystem": subsystem,
        "allowed_provider_refs": [provider_url_ref],
        "approval_window_start": "2026-06-01T00:00:00Z",
        "approval_window_end": "2026-12-31T23:59:59Z",
        "cost_quota_ceiling_usd": 1.0,
        "approval_artifact_ref": (
            f"data/approvals/2026/{approval_ref}.json"
        ),
        "human_approved": True,
    }


def _ledger(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {record["approval_ref"]: record}


class _SpyFakeTransport:
    """Fake transport that records every invocation; never opens a socket."""

    def __init__(self) -> None:
        self.invocations: list[dict[str, Any]] = []

    def invoke(self, *, request: Any) -> dict[str, Any]:
        self.invocations.append({"request": dict(request) if isinstance(request, dict) else request})
        return {
            "provider_request_id": "fake-smoke-req",
            "provider_ref": "fake-live-llm/controlled-smoke/v1",
            "latency_ms": 9,
            "cost_usd": 0.0,
            "tokens_in": 0,
            "tokens_out": 0,
            "redacted_output_excerpt": "advisory output (fake controlled smoke transport)",
        }

    @property
    def invocation_count(self) -> int:
        return len(self.invocations)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _runtime_boundary_ref(envelope: dict[str, Any], *, prefix: str) -> str:
    for ref in envelope.get("artifact_refs") or []:
        if "runtime-boundary" in ref and ref.endswith(".json") and prefix in ref:
            return ref
    raise AssertionError(
        f"no runtime-boundary JSON artifact ref matching prefix={prefix!r}: "
        f"{envelope.get('artifact_refs')}"
    )


# ---------------------------------------------------------------------------
# Default exposure is unchanged: live tools are not registered by default.
# ---------------------------------------------------------------------------


def test_default_mcp_tool_listing_does_not_expose_live_tools() -> None:
    tools = _tools_module()
    names = tools.list_hisys_mcp_tool_names()
    for live_name in tools.LIVE_TOOL_NAMES:
        assert live_name not in names, (
            f"controlled-live-smoke seam must not flip the default exposure: "
            f"{live_name!r} appeared in default tool listing"
        )


# ---------------------------------------------------------------------------
# Controlled-live-smoke harness, exercised with a fake transport so CI can
# verify the seam without any real provider call.
# ---------------------------------------------------------------------------


def test_controlled_live_smoke_harness_with_fake_transport_records_provenance(
    tmp_path: Path,
) -> None:
    tools = _tools_module()
    transport = _SpyFakeTransport()
    approval_ref = "APPROVAL-MCP-LIVE-SMOKE-ALTAS-FAKE-001"
    provider_url_ref = "provider://fake-live-altas"
    credential_ref = "credstore://altas/live/manual-smoke/v1"
    record = _approval_record(
        tool_name="altas_search_live",
        subsystem="altas",
        approval_ref=approval_ref,
        provider_url_ref=provider_url_ref,
    )
    envelope = _to_dict(
        tools.run_hisys_live_smoke_manual(
            instance_root=tmp_path,
            date="20260608",
            tool_name="altas_search_live",
            request_id="REQ-LIVE-SMOKE-FAKE-001",
            approval_ref=approval_ref,
            provider_url_ref=provider_url_ref,
            credential_ref=credential_ref,
            approval_ledger=_ledger(record),
            transport=transport,
            user_ref="operator://release-steward",
            agent_ref="hisys-mcp-controlled-smoke-harness",
            runtime_ref="local-process://hisys-mcp",
            transport_label="fake/controlled_smoke",
            real_external_call_made=False,
            topic="controlled live smoke rehearsal (fake transport)",
            prompt_summary="advisory prompt — fake controlled smoke",
        )
    )
    assert envelope["status"] == "ok"
    assert envelope["tool_name"] == "altas_search_live"
    assert envelope["mutation_performed"] is False
    assert envelope["publication_or_live_action_approved"] is False
    assert envelope["human_approval_required"] is True
    assert transport.invocation_count == 1

    runtime_ref = _runtime_boundary_ref(envelope, prefix="live-smoke-")
    record_on_disk = _read_json(tmp_path / runtime_ref)
    assert record_on_disk["self_ref"] == runtime_ref
    assert record_on_disk["controlled_live_smoke"] is True
    assert record_on_disk["provider_transport"] == "fake/controlled_smoke"
    assert record_on_disk["real_external_call_made"] is False
    assert record_on_disk["execution_mode"] == "live_llm"
    assert record_on_disk["result_basis"] == "Live LLM/provider"
    assert record_on_disk["approval_ref"] == approval_ref
    assert record_on_disk["provider_url_ref"] == provider_url_ref
    assert record_on_disk["credential_ref"] == credential_ref
    assert record_on_disk["cost_quota_boundary"]["ceiling_usd"] == 1.0
    assert record_on_disk["human_review_boundary"]["required"] is True
    assert record_on_disk["human_review_boundary"]["publication_or_live_action_approved"] is False


def test_controlled_live_smoke_harness_is_fail_closed_without_transport(tmp_path: Path) -> None:
    tools = _tools_module()
    approval_ref = "APPROVAL-MCP-LIVE-SMOKE-ALTAS-FAKE-002"
    provider_url_ref = "provider://fake-live-altas"
    credential_ref = "credstore://altas/live/manual-smoke/v1"
    record = _approval_record(
        tool_name="altas_search_live",
        subsystem="altas",
        approval_ref=approval_ref,
        provider_url_ref=provider_url_ref,
    )
    envelope = _to_dict(
        tools.run_hisys_live_smoke_manual(
            instance_root=tmp_path,
            date="20260608",
            tool_name="altas_search_live",
            request_id="REQ-LIVE-SMOKE-FAIL-CLOSED-001",
            approval_ref=approval_ref,
            provider_url_ref=provider_url_ref,
            credential_ref=credential_ref,
            approval_ledger=_ledger(record),
            transport=None,
            user_ref="operator://release-steward",
            agent_ref="hisys-mcp-controlled-smoke-harness",
            runtime_ref="local-process://hisys-mcp",
            transport_label="fake/controlled_smoke",
            real_external_call_made=False,
        )
    )
    assert envelope["status"] == "blocked"
    assert envelope["external_call_made"] is False


def test_controlled_live_smoke_harness_rejects_unknown_tool(tmp_path: Path) -> None:
    tools = _tools_module()
    transport = _SpyFakeTransport()
    envelope = _to_dict(
        tools.run_hisys_live_smoke_manual(
            instance_root=tmp_path,
            date="20260608",
            tool_name="not_a_live_tool",
            request_id="REQ-LIVE-SMOKE-UNKNOWN-001",
            approval_ref="APPROVAL-MCP-LIVE-SMOKE-UNKNOWN-001",
            provider_url_ref="provider://fake-live-altas",
            credential_ref="credstore://altas/live/manual-smoke/v1",
            approval_ledger={},
            transport=transport,
            user_ref="operator://release-steward",
            agent_ref="hisys-mcp-controlled-smoke-harness",
            runtime_ref="local-process://hisys-mcp",
            transport_label="fake/controlled_smoke",
            real_external_call_made=False,
        )
    )
    assert envelope["status"] == "blocked"
    assert transport.invocation_count == 0


def test_controlled_live_smoke_harness_does_not_persist_caller_secret(tmp_path: Path) -> None:
    tools = _tools_module()
    transport = _SpyFakeTransport()
    raw_secret = "sk" + "-CONTROLLED-SMOKE-RAW-SECRET-001"
    approval_ref = "APPROVAL-MCP-LIVE-SMOKE-ALTAS-FAKE-003"
    provider_url_ref = "provider://fake-live-altas"
    record = _approval_record(
        tool_name="altas_search_live",
        subsystem="altas",
        approval_ref=approval_ref,
        provider_url_ref=provider_url_ref,
    )
    envelope = _to_dict(
        tools.run_hisys_live_smoke_manual(
            instance_root=tmp_path,
            date="20260608",
            tool_name="altas_search_live",
            request_id="REQ-LIVE-SMOKE-SECRET-001",
            approval_ref=approval_ref,
            provider_url_ref=provider_url_ref,
            credential_ref="credstore://altas/live/manual-smoke/v1",
            approval_ledger=_ledger(record),
            transport=transport,
            user_ref="operator://release-steward",
            agent_ref="hisys-mcp-controlled-smoke-harness",
            runtime_ref="local-process://hisys-mcp",
            transport_label="fake/controlled_smoke",
            real_external_call_made=False,
            prompt_summary=f"advisory prompt leaking {'to' + 'ken'}={raw_secret}",
        )
    )
    runtime_ref = _runtime_boundary_ref(envelope, prefix="live-smoke-")
    record_on_disk = _read_json(tmp_path / runtime_ref)
    serialized = json.dumps(record_on_disk, ensure_ascii=False, sort_keys=True)
    assert raw_secret not in serialized
    assert raw_secret not in json.dumps(envelope.get("payload") or {}, ensure_ascii=False, sort_keys=True)


# ---------------------------------------------------------------------------
# Manual live test seam: real Codex CLI subprocess transport. Skipped unless
# every gate env var is set. Never invoked in CI.
# ---------------------------------------------------------------------------


def _live_smoke_env_present() -> bool:
    if os.environ.get("HISYS_ALLOW_LIVE_MCP_SMOKE") != "1":
        return False
    for key in (
        "HISYS_CODEX_CLI_PATH",
        "HISYS_LIVE_MCP_APPROVAL_REF",
        "HISYS_LIVE_MCP_PROVIDER_URL_REF",
        "HISYS_LIVE_MCP_CREDENTIAL_REF",
    ):
        if not os.environ.get(key):
            return False
    return True


@pytest.mark.skipif(
    not _live_smoke_env_present(),
    reason=(
        "Controlled live MCP smoke is gated. Set HISYS_ALLOW_LIVE_MCP_SMOKE=1, "
        "HISYS_CODEX_CLI_PATH, HISYS_LIVE_MCP_APPROVAL_REF, "
        "HISYS_LIVE_MCP_PROVIDER_URL_REF, and HISYS_LIVE_MCP_CREDENTIAL_REF to run."
    ),
)
def test_controlled_live_smoke_with_real_codex_cli_subprocess(tmp_path: Path) -> None:
    tools = _tools_module()
    live = _live_module()
    codex_path = os.environ["HISYS_CODEX_CLI_PATH"]
    approval_ref = os.environ["HISYS_LIVE_MCP_APPROVAL_REF"]
    provider_url_ref = os.environ["HISYS_LIVE_MCP_PROVIDER_URL_REF"]
    credential_ref = os.environ["HISYS_LIVE_MCP_CREDENTIAL_REF"]

    transport = live.CodexCliLiveProviderTransport(
        executable=codex_path,
        read_only_args=(
            "--ask-for-approval",
            "never",
            "exec",
            "--sandbox",
            "read-only",
            "--cd",
            str(tmp_path),
            "--skip-git-repo-check",
        ),
        timeout_seconds=30,
    )
    record = _approval_record(
        tool_name="altas_search_live",
        subsystem="altas",
        approval_ref=approval_ref,
        provider_url_ref=provider_url_ref,
    )
    envelope = _to_dict(
        tools.run_hisys_live_smoke_manual(
            instance_root=tmp_path,
            date="20260608",
            tool_name="altas_search_live",
            request_id="REQ-LIVE-SMOKE-CODEX-001",
            approval_ref=approval_ref,
            provider_url_ref=provider_url_ref,
            credential_ref=credential_ref,
            approval_ledger=_ledger(record),
            transport=transport,
            user_ref="operator://release-steward",
            agent_ref="hisys-mcp-controlled-smoke-harness",
            runtime_ref="local-process://hisys-mcp",
            transport_label=f"codex_cli/{Path(codex_path).name}",
            real_external_call_made=True,
            topic="controlled live smoke — read-only Codex CLI prompt",
            prompt_summary="advisory: summarize the MCP live boundary",
        )
    )
    # The harness must not fabricate success on provider failure. Either the
    # live call succeeded (status=ok) or it returned needs_more_evidence /
    # blocked; we accept any non-fabricating outcome and only require that the
    # runtime-boundary record reflects a real-external-call attempt.
    assert envelope["status"] in {"ok", "needs_more_evidence", "blocked", "error"}
    runtime_ref = _runtime_boundary_ref(envelope, prefix="live-smoke-")
    record_on_disk = _read_json(tmp_path / runtime_ref)
    assert record_on_disk["controlled_live_smoke"] is True
    assert record_on_disk["real_external_call_made"] is True
    assert record_on_disk["provider_transport"].startswith("codex_cli/")
    assert record_on_disk["approval_ref"] == approval_ref
    assert record_on_disk["provider_url_ref"] == provider_url_ref
    assert record_on_disk["credential_ref"] == credential_ref
