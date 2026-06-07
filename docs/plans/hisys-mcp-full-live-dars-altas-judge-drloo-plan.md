# Hisys MCP Full Live Altas/DARS/Judge DRLOO Implementation Plan

> **For Hermes:** Use TDD + DRLOO/Claude Code for implementation increments. Claude outputs are advisory until Hermes verifies focused tests, full validation, runtime-boundary fields, and git diff.

**Goal:** Enable Hisys MCP Altas, DARS, and Judge to operate in full live LLM/provider mode under explicit approval gates while preserving local-fixture disclosure and fail-closed behavior when live LLM service is unavailable.

**Architecture:** Keep local fixture transport as the default safe path. Add a separate live-adapter path selected only by controlled config and explicit runtime approval. Every MCP result must declare `execution_mode`, `result_basis`, `llm_service_used`, `external_call_made`, provider/reference metadata, and human-review authority fields.

**Tech Stack:** Python, Hisys CLI/MCP wrappers, pytest, local fixture adapters, future live provider adapters via config/env references only.

**Context Packet:**
- MCP wrapper seam: `src/hisys/mcp/tools.py`
- MCP server/tool exposure: `src/hisys/mcp/server.py`
- CLI seam: `src/hisys/cli/main.py`
- Existing MCP tests: `tests/unit/test_mcp_tools.py`, `tests/integration/test_mcp_*`
- Traceability refs: `docs/traceability/dars-critic-panel-runtime-traceability.md`, `docs/design/hisys-subsystem-architecture.md`
- Local fixture disclosure increment: MCP payloads use `result_basis: Local fixture`, `execution_mode: local_fixture`, `llm_service_used: false`

**Boundary Record:**
- Fixture/local changes may be implemented and tested locally.
- Live LLM/provider calls are gated. Do not perform live calls in CI. Do not persist raw credentials. Store only `credential_ref` / `provider_url_ref`, redacted provider identity, request IDs, and cost/quota metadata.
- Any live adapter activation requires explicit human approval and a decision packet/final-check record before external calls.

---

## Design Candidates

1. **Single wrapper with mode field**
   - Add `mode=local_fixture|live_llm` to existing MCP tools.
   - Pros: small API surface.
   - Cons: higher risk of accidental live path in existing fixture callers.

2. **Separate live tools**
   - Keep `altas_search`, `run_dars_panel_golden`, `judge_advisory` fixture-default; add `altas_search_live`, `run_dars_panel_live`, `judge_advisory_live` behind exposure flag.
   - Pros: stronger safety boundary and clearer tool catalog.
   - Cons: more tool definitions and tests.

3. **Backend adapter registry with explicit transport selection**
   - Add adapter registry and typed transport contracts; wrappers call selected adapter after policy validation.
   - Pros: scalable for providers and deterministic fixture/live parity.
   - Cons: larger first increment.

**Recommendation:** Use candidate 2 for the first full-live increment, backed by candidate 3 internally as the implementation grows. This keeps fixture tools stable and makes live use auditable.

---

## Increment 1 — Local Fixture Disclosure Baseline

**Objective:** Ensure every non-live Altas/DARS/Judge MCP result explicitly says it is based on a local fixture and did not use an LLM service.

**Files:**
- Modify: `src/hisys/mcp/tools.py`
- Test: `tests/unit/test_mcp_tools.py`

**Acceptance Criteria:**
- Fixture outputs include:
  - `result_basis: Local fixture`
  - `execution_mode: local_fixture`
  - `llm_service_used: false`
  - operator-visible notice containing `Local fixture`
- Judge markdown also includes `Local fixture`.
- `external_call_made` remains false.

**Verification:**
```bash
PYTHONPATH=src:. pytest \
  tests/unit/test_mcp_tools.py::test_altas_search_payload_discloses_local_fixture_when_llm_is_not_used \
  tests/unit/test_mcp_tools.py::test_dars_and_judge_payloads_disclose_local_fixture_when_llm_is_not_used -q
```

---

## Increment 2 — Live LLM Adapter Contract RED Tests

**Objective:** Define the live contract without making live calls.

**Files:**
- Create or modify: `src/hisys/mcp/live_adapters.py`
- Modify: `src/hisys/mcp/tools.py`
- Test: `tests/unit/test_mcp_live_adapters.py`

**RED tests:**
1. A live adapter request with no approval returns `blocked` before provider invocation.
2. A live adapter request with missing provider URL/credential refs returns `needs_more_evidence` or `blocked` and `external_call_made: false`.
3. Runtime approval verification checks a decision packet or approval ledger entry before any provider invocation. The approval record must identify the human approver role, approved tool/subsystem, allowed provider refs, date/time window, cost/quota boundary, and approval artifact path; invalid or missing `approval_ref` returns `blocked`.
4. A fake live adapter success returns:
   - `execution_mode: live_llm`
   - `result_basis: Live LLM/provider`
   - `llm_service_used: true`
   - `external_call_made: true`
   - `provider_ref`, `credential_ref`, `approval_ref`, and redacted telemetry
   - `requires_human_review: true`
4. Secrets are not persisted in payloads or artifacts.

**Implementation:**
- Define a typed request/result shape for live adapters.
- Implement only fake transport first.
- Use dependency injection so tests can assert whether provider invocation occurred.

**Verification:**
```bash
PYTHONPATH=src:. pytest tests/unit/test_mcp_live_adapters.py -q
```

---

## Increment 3 — MCP Live Tool Exposure Gate

**Objective:** Expose live tools only when explicitly requested.

**Files:**
- Modify: `src/hisys/mcp/tools.py`
- Modify: `src/hisys/mcp/server.py`
- Test: `tests/unit/test_mcp_tools.py`, `tests/integration/test_mcp_server_smoke.py`

**Acceptance Criteria:**
- Default tool catalog does not expose live tools.
- `expose_live_tools=True` or a controlled env/config flag exposes:
  - `altas_search_live`
  - `run_dars_panel_live`
  - `judge_advisory_live`
- Future/status placeholders remain fail-closed.
- Tool schemas document live approval requirements and `Local fixture` vs live result basis fields.

**Verification:**
```bash
PYTHONPATH=src:. pytest tests/unit/test_mcp_tools.py -q
PYTHONPATH=src:. pytest tests/integration/test_mcp_server_smoke.py -q
```

---

## Increment 4 — Full Live Dry-Run Harness

**Objective:** Add a dry-run harness that exercises live-mode routing without external service calls.

**Files:**
- Create: `tests/integration/test_mcp_live_dry_run.py`
- Modify: `src/hisys/mcp/tools.py`
- Modify or create: `docs/release/hisys-mcp-live-llm-final-check.md`

**Acceptance Criteria:**
- Fake-live transport produces live-shaped payloads and artifacts.
- No real network is called.
- Runtime-boundary record includes user/tool/agent/runtime fields.
- Artifact refs are relative and safe.

**Verification:**
```bash
PYTHONPATH=src:. pytest tests/integration/test_mcp_live_dry_run.py -q
```

---

## Increment 5 — Controlled Live Smoke

**Objective:** Perform one manually approved live smoke for each subsystem.

**Gate:** Stop before this increment unless the human provides explicit live approval, provider refs, cost/quota boundary, and allowed operation scope.

**Acceptance Criteria:**
- One live call per selected subsystem at most.
- Payloads/artifacts record:
  - `execution_mode: live_llm`
  - `result_basis: Live LLM/provider`
  - `llm_service_used: true`
  - `external_call_made: true`
  - provider/credential refs only, no secret values
  - cost/quota/latency telemetry when available
  - human-review requirement
- On provider failure/rate limit/auth failure, result is `needs_more_evidence` or `blocked`, not fabricated.

**Verification:**
```bash
# exact command to be filled after provider adapter and approval refs exist
PYTHONPATH=src:. pytest tests/integration/test_mcp_live_smoke_manual.py -q -m live_manual
```

---

## DRLOO Execution Pattern

For each increment:
1. Hermes writes or verifies the RED test.
2. Run the focused RED test and preserve the failure.
3. Delegate to Claude Code with bounded write permissions for the one increment.
4. Hermes inspects the diff, runs focused tests, then related MCP tests.
5. Claude performs read-only review for safety/traceability if the increment touches live boundaries.
6. Hermes runs final validation and records the result.
7. Commit only after tests and secret checks pass, unless the current branch has pre-existing unrelated uncommitted work that must be separated first.

## Stop Conditions

- Live call would occur without explicit approval.
- Provider credentials or raw secrets appear in diffs/artifacts.
- Fixture path loses `Local fixture` disclosure.
- `external_call_made` is true in any fixture/dry-run test.
- Claude reaches max turns with unresolved diff or failing tests.
