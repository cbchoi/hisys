# Hisys MCP Live LLM final-check record

Traceability: docs/plans/hisys-mcp-full-live-dars-altas-judge-drloo-plan.md

## Current status

**Dry-run / fake-live only.** The Hisys MCP live tool lanes
(`altas_search_live`, `run_dars_panel_live`, `judge_advisory_live`) have been
exercised end to end through a fake-live adapter contract and a Full Live
Dry-Run Harness. **No controlled live smoke has been performed.** No real
provider/network call has been made. No raw credentials have been resolved.

The system is **not** in full live mode. It is in fake-live dry-run mode only.

## Increment coverage

| Increment | Scope | Status |
| --- | --- | --- |
| 1 | Local fixture disclosure baseline | Done |
| 2 | Live LLM adapter contract RED tests | Done |
| 3 | MCP live tool exposure gate | Done |
| 4 | Full Live Dry-Run Harness | Done (this record) |
| 5 | Controlled live smoke | **Gated — not run** |

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

## Validation

Focused gate:

```bash
PYTHONPATH=src:. pytest tests/integration/test_mcp_live_dry_run.py -q
```

Result: `7 passed`.

Adjacent MCP gate:

```bash
PYTHONPATH=src:. pytest \
  tests/unit/test_mcp_tools.py \
  tests/unit/test_mcp_live_adapters.py \
  tests/integration/test_mcp_server_smoke.py \
  tests/integration/test_mcp_live_dry_run.py -q
```

Result: `56 passed`.

## Claim boundary

This increment does **not**:

- implement a real provider client,
- resolve credentials,
- open a socket to a provider,
- enable live tools on the default MCP server,
- mutate Hermes config,
- publish anything, or
- perform a controlled live smoke for any subsystem.

It does:

- prove that the live-mode routing surface produces a live-shaped envelope
  when a fake transport is injected,
- prove the runtime-boundary record carries the user/tool/agent/runtime
  fields, approval/provider/credential refs, cost/quota boundary, and
  human-review boundary, and
- prove dry-run records are distinguishable from controlled live runs via
  the explicit `provider_transport=fake/dry_run` and
  `real_external_call_made=false` markers.

## Remaining gate for Increment 5

Increment 5 (controlled live smoke) remains blocked until **all** of the
following are recorded as decision packets in writing:

1. Explicit human approval for one live smoke per selected subsystem.
2. Provider URL refs and credential refs for each approved subsystem,
   stored as references (no raw secrets in the repo or diffs).
3. Cost/quota ceiling and allowed operation scope per subsystem.
4. Real provider transport implementation that distinguishes real provider
   responses from any fake response, plus a manual smoke test entry point
   (e.g. `tests/integration/test_mcp_live_smoke_manual.py` gated on
   `-m live_manual`).
5. Failure-mode contract: on provider error / rate limit / auth failure the
   envelope must return `needs_more_evidence` or `blocked` and never
   fabricate a success.

Until the gate above is satisfied, the Hisys MCP live lanes operate only in
fake-live dry-run mode.

## Human approval state

The user approved the dry-run harness DRLOO/TDD lane. This approval covers
local code/tests/docs and local validation only. It does **not** cover live
provider activation, credential resolution, network egress, Hermes profile
mutation, publication, or external actions.
