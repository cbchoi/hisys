"""RED tests for the Hisys MCP live LLM/provider adapter contract.

Traceability:
- docs/plans/hisys-mcp-full-live-dars-altas-judge-drloo-plan.md (Increment 2)

These tests define the live adapter contract without making any real network or
provider calls. They use a fake injected transport and a fake approval ledger so
that the production path remains fully testable in CI.

Requirements covered:
1. No approval -> blocked before provider invocation; external_call_made=false.
2. Missing provider_url_ref or credential_ref -> blocked / needs_more_evidence;
   external_call_made=false; transport must not be invoked.
3. Approval verification consults a decision packet / approval-ledger record
   that names approver role, approved tool/subsystem, allowed provider refs,
   time window, cost/quota boundary, and approval artifact ref; invalid or
   missing approval_ref returns blocked.
4. A fake live adapter success returns execution_mode=live_llm,
   result_basis='Live LLM/provider', llm_service_used=true,
   external_call_made=true, provider_ref/provider_url_ref/credential_ref/
   approval_ref, redacted telemetry, and requires_human_review=true.
5. Secrets are not persisted in payloads/artifacts.
"""

from __future__ import annotations

import importlib
from typing import Any


def _live_module():
    return importlib.import_module("hisys.mcp.live_adapters")


def _to_dict(model_or_mapping: object) -> dict[str, Any]:
    if isinstance(model_or_mapping, dict):
        return model_or_mapping
    if hasattr(model_or_mapping, "model_dump"):
        return model_or_mapping.model_dump(mode="json")  # type: ignore[attr-defined]
    raise AssertionError(
        f"live adapter result is not a dict/model envelope: {type(model_or_mapping)!r}"
    )


def _valid_approval_record() -> dict[str, Any]:
    return {
        "approval_ref": "APPROVAL-MCP-LIVE-ALTAS-001",
        "approver_role": "release_steward",
        "approved_tool": "altas_search_live",
        "approved_subsystem": "altas",
        "allowed_provider_refs": ["provider://fake-live-search"],
        "approval_window_start": "2026-06-01T00:00:00Z",
        "approval_window_end": "2026-12-31T23:59:59Z",
        "cost_quota_ceiling_usd": 1.0,
        "approval_artifact_ref": (
            "data/approvals/2026/APPROVAL-MCP-LIVE-ALTAS-001.json"
        ),
        "human_approved": True,
    }


def _valid_request(**overrides: Any) -> dict[str, Any]:
    request: dict[str, Any] = {
        "subsystem": "altas",
        "tool_name": "altas_search_live",
        "request_id": "REQ-LIVE-ALTAS-001",
        "approval_ref": "APPROVAL-MCP-LIVE-ALTAS-001",
        "provider_url_ref": "provider://fake-live-search",
        "credential_ref": "credstore://altas/live-search/v1",
        "prompt_summary": "advisory live altas_search rehearsal",
    }
    request.update(overrides)
    return request


def _approval_ledger(*records: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {record["approval_ref"]: record for record in records}


class _SpyFakeTransport:
    """Fake transport that records every invocation; never makes a network call."""

    def __init__(
        self,
        *,
        response: dict[str, Any] | None = None,
        raise_error: Exception | None = None,
    ) -> None:
        self.invocations: list[dict[str, Any]] = []
        self._response = response or {
            "provider_request_id": "fake-provider-req-001",
            "provider_ref": "fake-live-llm/v1",
            "latency_ms": 42,
            "cost_usd": 0.0001,
            "tokens_in": 10,
            "tokens_out": 7,
            "redacted_output_excerpt": "advisory output (fake live transport)",
        }
        self._raise_error = raise_error

    def invoke(self, *, request: Any) -> dict[str, Any]:
        self.invocations.append({"request": request})
        if self._raise_error is not None:
            raise self._raise_error
        return dict(self._response)

    @property
    def invocation_count(self) -> int:
        return len(self.invocations)


# ---------------------------------------------------------------------------
# Requirement 1: no approval -> blocked before provider invocation
# ---------------------------------------------------------------------------


def test_live_adapter_without_approval_ref_is_blocked_before_provider_invocation() -> None:
    live = _live_module()
    transport = _SpyFakeTransport()
    request = _valid_request(approval_ref=None)

    envelope = _to_dict(
        live.invoke_live_adapter(
            request=request,
            transport=transport,
            approval_ledger=_approval_ledger(_valid_approval_record()),
        )
    )

    assert envelope["status"] == "blocked"
    assert envelope["tool_name"] == "altas_search_live"
    assert envelope["external_call_made"] is False
    assert envelope["mutation_performed"] is False
    assert envelope["publication_or_live_action_approved"] is False
    assert envelope["human_approval_required"] is True
    assert transport.invocation_count == 0
    payload = envelope["payload"]
    assert payload["external_call_made"] is False
    assert payload["llm_service_used"] is False
    assert payload["execution_mode"] != "live_llm"
    assert "approval" in (envelope.get("error") or "").lower()


def test_live_adapter_with_unknown_approval_ref_is_blocked_before_provider_invocation() -> None:
    live = _live_module()
    transport = _SpyFakeTransport()
    request = _valid_request(approval_ref="APPROVAL-UNKNOWN")

    envelope = _to_dict(
        live.invoke_live_adapter(
            request=request,
            transport=transport,
            approval_ledger=_approval_ledger(_valid_approval_record()),
        )
    )

    assert envelope["status"] == "blocked"
    assert envelope["external_call_made"] is False
    assert transport.invocation_count == 0
    assert "approval" in (envelope.get("error") or "").lower()


# ---------------------------------------------------------------------------
# Requirement 2: missing provider/credential refs -> blocked or needs_more_evidence
# ---------------------------------------------------------------------------


def test_live_adapter_without_provider_url_ref_blocks_without_invocation() -> None:
    live = _live_module()
    transport = _SpyFakeTransport()
    request = _valid_request(provider_url_ref=None)

    envelope = _to_dict(
        live.invoke_live_adapter(
            request=request,
            transport=transport,
            approval_ledger=_approval_ledger(_valid_approval_record()),
        )
    )

    assert envelope["status"] in {"blocked", "needs_more_evidence"}
    assert envelope["external_call_made"] is False
    assert envelope["payload"]["external_call_made"] is False
    assert envelope["payload"]["llm_service_used"] is False
    assert transport.invocation_count == 0
    assert "provider_url_ref" in (envelope.get("error") or "")


def test_live_adapter_without_credential_ref_blocks_without_invocation() -> None:
    live = _live_module()
    transport = _SpyFakeTransport()
    request = _valid_request(credential_ref=None)

    envelope = _to_dict(
        live.invoke_live_adapter(
            request=request,
            transport=transport,
            approval_ledger=_approval_ledger(_valid_approval_record()),
        )
    )

    assert envelope["status"] in {"blocked", "needs_more_evidence"}
    assert envelope["external_call_made"] is False
    assert envelope["payload"]["external_call_made"] is False
    assert transport.invocation_count == 0
    assert "credential_ref" in (envelope.get("error") or "")


# ---------------------------------------------------------------------------
# Requirement 3: approval verification reads structured decision packet
# ---------------------------------------------------------------------------


def test_live_adapter_rejects_approval_packet_missing_required_fields() -> None:
    live = _live_module()
    transport = _SpyFakeTransport()
    incomplete_record = {
        "approval_ref": "APPROVAL-MCP-LIVE-ALTAS-001",
        # missing approver_role, approved_tool, approved_subsystem,
        # allowed_provider_refs, time window, cost ceiling, artifact ref
    }
    request = _valid_request()

    envelope = _to_dict(
        live.invoke_live_adapter(
            request=request,
            transport=transport,
            approval_ledger=_approval_ledger(incomplete_record),
        )
    )

    assert envelope["status"] == "blocked"
    assert envelope["external_call_made"] is False
    assert transport.invocation_count == 0
    error_text = (envelope.get("error") or "").lower()
    assert "approval" in error_text


def test_live_adapter_rejects_approval_record_whose_tool_does_not_match_request() -> None:
    live = _live_module()
    transport = _SpyFakeTransport()
    record = _valid_approval_record()
    record["approved_tool"] = "judge_advisory_live"  # mismatch vs altas_search_live
    record["approved_subsystem"] = "judge"

    envelope = _to_dict(
        live.invoke_live_adapter(
            request=_valid_request(),
            transport=transport,
            approval_ledger=_approval_ledger(record),
        )
    )

    assert envelope["status"] == "blocked"
    assert envelope["external_call_made"] is False
    assert transport.invocation_count == 0


def test_live_adapter_rejects_approval_record_whose_provider_ref_is_not_allowed() -> None:
    live = _live_module()
    transport = _SpyFakeTransport()
    record = _valid_approval_record()
    record["allowed_provider_refs"] = ["provider://something-else"]

    envelope = _to_dict(
        live.invoke_live_adapter(
            request=_valid_request(),
            transport=transport,
            approval_ledger=_approval_ledger(record),
        )
    )

    assert envelope["status"] == "blocked"
    assert envelope["external_call_made"] is False
    assert transport.invocation_count == 0


def test_live_adapter_rejects_approval_record_with_human_approved_false() -> None:
    live = _live_module()
    transport = _SpyFakeTransport()
    record = _valid_approval_record()
    record["human_approved"] = False

    envelope = _to_dict(
        live.invoke_live_adapter(
            request=_valid_request(),
            transport=transport,
            approval_ledger=_approval_ledger(record),
        )
    )

    assert envelope["status"] == "blocked"
    assert envelope["external_call_made"] is False
    assert transport.invocation_count == 0


# ---------------------------------------------------------------------------
# Requirement 4: fake live adapter success returns live envelope fields
# ---------------------------------------------------------------------------


def test_fake_live_adapter_success_returns_live_envelope_fields() -> None:
    live = _live_module()
    transport = _SpyFakeTransport()

    envelope = _to_dict(
        live.invoke_live_adapter(
            request=_valid_request(),
            transport=transport,
            approval_ledger=_approval_ledger(_valid_approval_record()),
        )
    )

    assert envelope["status"] == "ok"
    assert envelope["tool_name"] == "altas_search_live"
    assert envelope["external_call_made"] is True
    assert envelope["human_approval_required"] is True
    assert envelope["mutation_performed"] is False
    assert envelope["publication_or_live_action_approved"] is False

    payload = envelope["payload"]
    assert payload["execution_mode"] == "live_llm"
    assert payload["result_basis"] == "Live LLM/provider"
    assert payload["llm_service_used"] is True
    assert payload["external_call_made"] is True
    assert payload["requires_human_review"] is True
    assert payload["advisory_only"] is True
    assert payload["mutation_performed"] is False
    assert payload["publication_or_live_action_approved"] is False

    assert payload["approval_ref"] == "APPROVAL-MCP-LIVE-ALTAS-001"
    assert payload["provider_url_ref"] == "provider://fake-live-search"
    assert payload["credential_ref"] == "credstore://altas/live-search/v1"
    assert payload["provider_ref"] == "fake-live-llm/v1"

    telemetry = payload["telemetry"]
    assert telemetry["provider_request_id"] == "fake-provider-req-001"
    assert telemetry["latency_ms"] == 42
    assert telemetry["cost_usd"] == 0.0001
    assert telemetry["tokens_in"] == 10
    assert telemetry["tokens_out"] == 7
    assert "redacted_output_excerpt" in telemetry

    assert transport.invocation_count == 1


def test_fake_live_adapter_failure_does_not_fabricate_success() -> None:
    live = _live_module()
    transport = _SpyFakeTransport(raise_error=RuntimeError("fake provider rate-limited"))

    envelope = _to_dict(
        live.invoke_live_adapter(
            request=_valid_request(),
            transport=transport,
            approval_ledger=_approval_ledger(_valid_approval_record()),
        )
    )

    assert envelope["status"] in {"needs_more_evidence", "blocked", "error"}
    payload = envelope["payload"]
    assert payload["llm_service_used"] is False or payload["llm_service_used"] is True
    assert payload["execution_mode"] != "live_llm" or envelope["status"] != "ok"
    assert payload["mutation_performed"] is False
    assert payload["publication_or_live_action_approved"] is False
    assert transport.invocation_count == 1


# ---------------------------------------------------------------------------
# Requirement 5: secrets are not persisted in payloads
# ---------------------------------------------------------------------------


def test_live_adapter_does_not_persist_raw_secret_values_in_payload() -> None:
    live = _live_module()
    raw_secret = "sk" + "-LIVE-RAW-SECRET-VALUE-FAKE-001"
    transport = _SpyFakeTransport(
        response={
            "provider_request_id": "fake-provider-req-002",
            "provider_ref": "fake-live-llm/v1",
            "latency_ms": 33,
            "cost_usd": 0.0002,
            "tokens_in": 11,
            "tokens_out": 5,
            # The transport tries to leak a raw secret in the output excerpt.
            "redacted_output_excerpt": (
                f"output containing {'to' + 'ken'}={raw_secret} and {'pass' + 'word'}={raw_secret}"
            ),
        }
    )
    request = _valid_request(
        prompt_summary=f"advisory prompt referencing {'to' + 'ken'}={raw_secret}",
        # An adapter caller may accidentally pass a raw secret in extras; the
        # adapter must not persist it verbatim.
        extras={"trace_log": f"Authorization: Bearer {raw_secret}"},
    )

    envelope = _to_dict(
        live.invoke_live_adapter(
            request=request,
            transport=transport,
            approval_ledger=_approval_ledger(_valid_approval_record()),
        )
    )

    serialized = repr(envelope)
    assert raw_secret not in serialized, "raw secret leaked into adapter envelope"

    payload = envelope["payload"]
    # credential_ref is a non-secret pointer and must be retained.
    assert payload.get("credential_ref") == "credstore://altas/live-search/v1"
    # The raw secret value must never appear in payload telemetry/prompt fields.
    assert raw_secret not in repr(payload)


def test_live_adapter_blocked_outputs_do_not_persist_credentials_or_secrets() -> None:
    live = _live_module()
    transport = _SpyFakeTransport()
    raw_secret = "sk" + "-BLOCKED-PATH-SECRET-FAKE-002"
    request = _valid_request(
        approval_ref=None,
        prompt_summary=f"prompt with {'to' + 'ken'}={raw_secret}",
        extras={"note": f"{'pass' + 'word'}={raw_secret}"},
    )

    envelope = _to_dict(
        live.invoke_live_adapter(
            request=request,
            transport=transport,
            approval_ledger=_approval_ledger(_valid_approval_record()),
        )
    )

    assert envelope["status"] == "blocked"
    assert raw_secret not in repr(envelope)


# ---------------------------------------------------------------------------
# Requirement 6 (Increment 5): Codex CLI subprocess transport for controlled
# live smoke. The transport must be opt-in, must never make a real subprocess
# call when a runner is injected, must refuse mutating CLI args, must scrub
# secrets from output, and must surface non-zero/timeout as errors so the
# adapter returns needs_more_evidence rather than fabricating success.
# ---------------------------------------------------------------------------


class _FakeCliRunner:
    """Injected runner that records invocations and never opens a subprocess."""

    def __init__(
        self,
        *,
        stdout: str = "advisory codex CLI fake output",
        stderr: str = "",
        returncode: int = 0,
        raise_error: Exception | None = None,
    ) -> None:
        self.calls: list[dict[str, Any]] = []
        self._stdout = stdout
        self._stderr = stderr
        self._returncode = returncode
        self._raise_error = raise_error

    def __call__(self, command: list[str], *, timeout_seconds: int) -> Any:
        self.calls.append({"command": list(command), "timeout_seconds": timeout_seconds})
        if self._raise_error is not None:
            raise self._raise_error
        from hisys.mcp.cli_adapter import CliInvocationResult

        return CliInvocationResult(
            args=tuple(command),
            stdout=self._stdout,
            stderr=self._stderr,
            returncode=self._returncode,
            timed_out=False,
        )


def test_codex_cli_transport_requires_explicit_executable_path(tmp_path: Any) -> None:
    live = _live_module()
    try:
        live.CodexCliLiveProviderTransport(
            executable="",
            read_only_args=("--print",),
            timeout_seconds=10,
            runner=_FakeCliRunner(),
        )
    except (ValueError, TypeError) as exc:
        assert "executable" in str(exc).lower()
        return
    raise AssertionError(
        "CodexCliLiveProviderTransport must require an explicit executable path"
    )


def test_codex_cli_transport_rejects_mutating_args_on_construction() -> None:
    live = _live_module()
    for forbidden in ("--write", "--apply", "--exec", "--commit", "--push", "--mutate"):
        runner = _FakeCliRunner()
        try:
            live.CodexCliLiveProviderTransport(
                executable="/usr/bin/echo",
                read_only_args=("exec", "--sandbox", "read-only", forbidden),
                timeout_seconds=10,
                runner=runner,
            )
        except ValueError as exc:
            assert forbidden in str(exc) or "mutating" in str(exc).lower()
            assert runner.calls == [], "transport must not invoke runner on construction"
            continue
        raise AssertionError(
            f"transport must reject mutating arg {forbidden!r} on construction"
        )


def test_codex_cli_transport_invoke_uses_injected_runner_with_read_only_args() -> None:
    live = _live_module()
    runner = _FakeCliRunner(stdout="advisory codex output (fake)")
    transport = live.CodexCliLiveProviderTransport(
        executable="/usr/bin/codex",
        read_only_args=("--ask-for-approval", "never", "exec", "--sandbox", "read-only"),
        timeout_seconds=15,
        runner=runner,
    )
    request = _valid_request(
        prompt_summary="advisory rehearsal: summarize MCP live boundary"
    )
    response = transport.invoke(request=request)
    assert len(runner.calls) == 1
    call = runner.calls[0]
    command = call["command"]
    assert command[0] == "/usr/bin/codex"
    assert "exec" in command
    assert "--sandbox" in command
    assert "read-only" in command
    assert "--ask-for-approval" in command
    assert "never" in command
    # Prompt body must reach the CLI somehow, but raw secret content stays gated
    # by the adapter's scrub layer above the transport. The transport itself is
    # just responsible for shaping the command and parsing the result.
    assert any("advisory rehearsal" in str(part) for part in command)
    assert response["provider_ref"].startswith("codex_cli/")
    assert "redacted_output_excerpt" in response


def test_codex_cli_transport_invoke_scrubs_secret_values_from_output_excerpt() -> None:
    live = _live_module()
    raw_secret = "sk" + "-CODEX-CLI-LEAK-FAKE-001"
    runner = _FakeCliRunner(stdout=f"{'to' + 'ken'}={raw_secret} and Authorization: Bearer {raw_secret}")
    transport = live.CodexCliLiveProviderTransport(
        executable="/usr/bin/codex",
        read_only_args=("--print",),
        timeout_seconds=10,
        runner=runner,
    )
    response = transport.invoke(request=_valid_request())
    excerpt = response["redacted_output_excerpt"]
    assert raw_secret not in excerpt


def test_codex_cli_transport_invoke_raises_on_non_zero_returncode() -> None:
    live = _live_module()
    runner = _FakeCliRunner(stdout="", stderr="codex auth failed", returncode=2)
    transport = live.CodexCliLiveProviderTransport(
        executable="/usr/bin/codex",
        read_only_args=("--print",),
        timeout_seconds=10,
        runner=runner,
    )
    try:
        transport.invoke(request=_valid_request())
    except RuntimeError as exc:
        # On error the adapter wraps this and returns needs_more_evidence.
        assert "codex" in str(exc).lower() or "exit" in str(exc).lower()
        return
    raise AssertionError("transport must raise on non-zero return code")


def test_codex_cli_transport_invoke_raises_on_runner_timeout() -> None:
    live = _live_module()
    import subprocess

    runner = _FakeCliRunner(raise_error=subprocess.TimeoutExpired(cmd="codex", timeout=1))
    transport = live.CodexCliLiveProviderTransport(
        executable="/usr/bin/codex",
        read_only_args=("--print",),
        timeout_seconds=1,
        runner=runner,
    )
    try:
        transport.invoke(request=_valid_request())
    except RuntimeError as exc:
        assert "timeout" in str(exc).lower()
        return
    raise AssertionError("transport must raise on runner timeout")


def test_codex_cli_transport_does_not_open_real_subprocess_when_runner_injected() -> None:
    live = _live_module()
    import subprocess

    runner = _FakeCliRunner()
    transport = live.CodexCliLiveProviderTransport(
        executable="/path/that/does/not/exist/codex-binary",
        read_only_args=("--print",),
        timeout_seconds=5,
        runner=runner,
    )
    sentinel: dict[str, bool] = {"real_run_called": False}

    original_run = subprocess.run

    def _spy(*args: Any, **kwargs: Any) -> Any:
        sentinel["real_run_called"] = True
        return original_run(*args, **kwargs)

    subprocess.run = _spy  # type: ignore[assignment]
    try:
        transport.invoke(request=_valid_request())
    finally:
        subprocess.run = original_run  # type: ignore[assignment]
    assert sentinel["real_run_called"] is False, (
        "injected runner must replace subprocess.run; no real subprocess allowed"
    )
    assert len(runner.calls) == 1


def test_codex_cli_transport_does_not_resolve_credential_ref_value() -> None:
    """The transport must treat credential_ref as a pointer, never resolve it.

    It must not read environment variables for secret values, and must not put
    the credential_ref string into the subprocess command line.
    """

    live = _live_module()
    runner = _FakeCliRunner()
    transport = live.CodexCliLiveProviderTransport(
        executable="/usr/bin/codex",
        read_only_args=("--print",),
        timeout_seconds=10,
        runner=runner,
    )
    transport.invoke(request=_valid_request(credential_ref="credstore://altas/live-search/v1"))
    command = runner.calls[0]["command"]
    joined = " ".join(str(part) for part in command)
    assert "credstore://" not in joined, (
        "credential_ref pointer must not be passed to the subprocess command"
    )


def test_codex_cli_transport_through_invoke_live_adapter_returns_needs_more_evidence_on_failure() -> None:
    """End-to-end: a failing Codex CLI run must not fabricate a live success."""

    live = _live_module()
    runner = _FakeCliRunner(returncode=1, stderr="codex unauthorized")
    transport = live.CodexCliLiveProviderTransport(
        executable="/usr/bin/codex",
        read_only_args=("--print",),
        timeout_seconds=10,
        runner=runner,
    )
    envelope = _to_dict(
        live.invoke_live_adapter(
            request=_valid_request(),
            transport=transport,
            approval_ledger=_approval_ledger(_valid_approval_record()),
        )
    )
    assert envelope["status"] in {"needs_more_evidence", "blocked", "error"}
    payload = envelope["payload"]
    assert payload["execution_mode"] != "live_llm"
    assert payload["publication_or_live_action_approved"] is False
    assert payload["mutation_performed"] is False


def test_codex_cli_transport_through_invoke_live_adapter_returns_live_envelope_on_success() -> None:
    """End-to-end: a successful Codex CLI run produces a live-shaped envelope."""

    live = _live_module()
    runner = _FakeCliRunner(stdout="advisory codex output")
    transport = live.CodexCliLiveProviderTransport(
        executable="/usr/bin/codex",
        read_only_args=("--print",),
        timeout_seconds=10,
        runner=runner,
    )
    envelope = _to_dict(
        live.invoke_live_adapter(
            request=_valid_request(),
            transport=transport,
            approval_ledger=_approval_ledger(_valid_approval_record()),
        )
    )
    assert envelope["status"] == "ok"
    payload = envelope["payload"]
    assert payload["execution_mode"] == "live_llm"
    assert payload["result_basis"] == "Live LLM/provider"
    assert payload["llm_service_used"] is True
    assert payload["provider_ref"].startswith("codex_cli/")
