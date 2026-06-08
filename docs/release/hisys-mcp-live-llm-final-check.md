# Hisys MCP Live LLM final-check record

Traceability: docs/plans/hisys-mcp-full-live-dars-altas-judge-drloo-plan.md

## Current status

**Full-live-capable, gated manual-smoke validated.** The Hisys MCP live tool lanes
(`altas_search_live`, `run_dars_panel_live`, `judge_advisory_live`) have been
exercised end to end through a fake-live adapter contract, a Full Live Dry-Run
Harness, and an Increment 5 controlled live-smoke seam. One operator-approved
Codex CLI controlled live smoke was executed with provider/credential references
only; no raw credentials were resolved or persisted.

The default MCP server is **not** in full live mode. Full live is possible only
through the explicit manual smoke harness with an injected real transport,
operator approval refs, provider/credential refs, and env-gated test execution.

## Increment coverage

| Increment | Scope | Status |
| --- | --- | --- |
| 1 | Local fixture disclosure baseline | Done |
| 2 | Live LLM adapter contract RED tests | Done |
| 3 | MCP live tool exposure gate | Done |
| 4 | Full Live Dry-Run Harness | Done |
| 5 | Controlled live smoke | **Done — manual Codex CLI smoke passed; default live exposure still gated** |

## Increment 4 evidence scope

Local repository changes only:

- `src/hisys/mcp/tools.py` — added `run_hisys_live_dry_run` harness and the
  `_runtime_boundary_record` helper.
- `tests/integration/test_mcp_live_dry_run.py` — new focused integration
  tests for the dry-run harness.
- `docs/release/hisys-mcp-live-llm-final-check.md` — this record.

The harness:

- Routes each live tool through the existing live-adapter contract with an
  **explicitly injected** fake transport. The default MCP server registration
  still never resolves credentials and still never contacts any provider.
- Records every dry-run in a runtime-boundary artifact under
  `runtime-boundary/<date>/live-dry-run-<tool>-<request_id>.json` plus its
  Markdown companion.
- The runtime-boundary record explicitly declares
  `provider_transport=fake/dry_run` and `real_external_call_made=false` so a
  dry-run cannot be mistaken for a controlled live smoke even though the
  envelope-level `external_call_made` flag remains `true` as the fake-live
  adapter contract marker.
- Surfaces `user`, `tool`, `agent`, `runtime`, `approval_ref`,
  `provider_url_ref`, `credential_ref` (refs only — never raw values), a
  `cost_quota_boundary` (ceiling + observed), and a `human_review_boundary`.
- Artifact refs are relative, contained inside the configured instance root,
  and contain no `..` segments.
- Raw secrets that appear in caller-side prompt text are scrubbed before the
  runtime-boundary record is written.

## Increment 5 evidence scope

Local repository changes only:

- `src/hisys/mcp/live_adapters.py` — added `CodexCliLiveProviderTransport`, an
  opt-in Codex CLI subprocess transport that requires an explicit executable,
  rejects known mutating args, does not resolve credential refs, scrubs
  secret-shaped output excerpts, and fails closed on non-zero exit/timeout.
- `src/hisys/mcp/tools.py` — added `run_hisys_live_smoke_manual`, a controlled
  live-smoke harness that writes `live-smoke-...` runtime-boundary records with
  `controlled_live_smoke=true` and caller-declared
  `real_external_call_made` truth.
- `tests/integration/test_mcp_live_smoke_manual.py` — added CI-safe fake
  transport tests plus one skipped-by-default real Codex CLI smoke test gated on
  `HISYS_ALLOW_LIVE_MCP_SMOKE=1`, `HISYS_CODEX_CLI_PATH`,
  `HISYS_LIVE_MCP_APPROVAL_REF`, `HISYS_LIVE_MCP_PROVIDER_URL_REF`, and
  `HISYS_LIVE_MCP_CREDENTIAL_REF`.

The manual harness makes full-live smoke possible, but it does not enable live
MCP tool exposure by default and does not run a real provider unless the manual
environment gates are explicitly set by the operator.

Manual live smoke evidence from this DRLOO run:

```json
{
  "status": "ok",
  "payload_execution_mode": "live_llm",
  "payload_result_basis": "Live LLM/provider",
  "record_provider_transport": "codex_cli/codex",
  "record_real_external_call_made": true,
  "record_controlled_live_smoke": true,
  "redacted_output_excerpt": "HISYS_MCP_LIVE_SMOKE_OK\\n"
}
```

## Validation

Focused gate:

```bash
PYTHONPATH=src:. pytest tests/integration/test_mcp_live_dry_run.py -q
```

Result: `7 passed`.

Controlled live-smoke harness gate:

```bash
PYTHONPATH=src:. pytest \
  tests/unit/test_mcp_live_adapters.py \
  tests/integration/test_mcp_live_smoke_manual.py -q
```

Result: `27 passed, 1 skipped` (real Codex CLI smoke skipped unless manual env gates are set).

Manual Codex CLI live smoke:

```bash
HISYS_ALLOW_LIVE_MCP_SMOKE=1 \
HISYS_CODEX_CLI_PATH=/usr/bin/codex \
HISYS_LIVE_MCP_APPROVAL_REF=APPROVAL-MCP-LIVE-SMOKE-CODEX-20260608-005 \
HISYS_LIVE_MCP_PROVIDER_URL_REF=provider://codex-cli/subscription \
HISYS_LIVE_MCP_CREDENTIAL_REF=credstore://existing-auth/codex-subscription \
PYTHONPATH=src:. pytest \
  tests/integration/test_mcp_live_smoke_manual.py::test_controlled_live_smoke_with_real_codex_cli_subprocess -q
```

Result: `1 passed`.

Adjacent MCP gate:

```bash
PYTHONPATH=src:. pytest \
  tests/unit/test_mcp_tools.py \
  tests/unit/test_mcp_live_adapters.py \
  tests/integration/test_mcp_server_smoke.py \
  tests/integration/test_mcp_live_dry_run.py \
  tests/integration/test_mcp_live_smoke_manual.py \
  tests/integration/test_mcp_http_local_client_smoke.py \
  tests/integration/test_mcp_streamable_http_sdk_binding_smoke.py -q
```

Result: `81 passed, 1 skipped`.

## Claim boundary

This increment does **not**:

- resolve credentials,
- enable live tools on the default MCP server,
- mutate Hermes config,
- publish anything, or
- approve downstream publication/live action beyond the bounded smoke call.

It does:

- prove that the live-mode routing surface produces a live-shaped envelope
  when a fake transport is injected,
- prove the runtime-boundary record carries the user/tool/agent/runtime
  fields, approval/provider/credential refs, cost/quota boundary, and
  human-review boundary,
- prove dry-run records are distinguishable from controlled live runs via
  the explicit `provider_transport=fake/dry_run` and
  `real_external_call_made=false` markers,
- provide an opt-in Codex CLI subprocess transport for controlled live smoke,
  and
- prove a bounded Codex CLI smoke can return `status=ok`,
  `execution_mode=live_llm`, and `real_external_call_made=true` without raw
  credential persistence.

## Remaining gate after Increment 5

The implementation is full-live-capable for a bounded Codex CLI smoke. Remaining
gates before broader/live-default use are:

1. Keep default MCP live tool exposure disabled unless a separate decision
   packet approves exposure.
2. Record explicit human approval for each additional subsystem or provider.
3. Continue storing provider URL refs and credential refs as references only
   (no raw secrets in the repo or diffs).
4. Preserve cost/quota ceilings and allowed operation scope per subsystem.
5. Preserve the failure-mode contract: on provider error / rate limit / auth
   failure the envelope must return `needs_more_evidence` or `blocked` and never
   fabricate a success.

Until a separate exposure decision is approved, the Hisys MCP default server
remains fail-closed for live lanes even though controlled manual full-live smoke
is now possible and validated.

## Human approval state

The user approved proceeding until full-live is possible for this DRLOO/TDD lane.
This approval covered bounded Codex CLI controlled smoke with provider and
credential references only. It does **not** cover credential resolution, default
live tool exposure, Hermes profile mutation, publication, or downstream external
actions.
