# DARS Integration Design and Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task after the design is accepted. Keep Ralph/TDD loops active until this queue is finished, a new queue is required, or token/session limit is reached.

**Goal:** Replace the current DARS loopback placeholder with a controlled, disabled-by-default DARS integration architecture that can ingest structured critique as advisory evidence before any real external DARS call is enabled.

**Architecture:** Hisys remains the system of record. DARS is an external advisory agent behind a narrow adapter boundary: Hisys builds an `AgentHandoffPackage`, dispatches it only through a configured adapter, validates a `DarsCritiqueRecord`, links the critique back to source execution/memo/alert/evidence, and records every boundary crossing. The first executable increments stay fixture/local-only; real DARS dispatch is enabled only after mock contract tests, safety gates, traceability, and human approval controls pass.

**Tech Stack:** Python 3.11, Pydantic v2 schemas, runtime-local JSON/Markdown artifacts, pytest, existing `InstanceRoot`, `AgentHandoffPackage`, `DarsRuntime`, traceability validator, secret scanner.

---

## 1. Current Baseline

Current implementation:

- `src/hisys/schemas/handoff.py` defines `AgentHandoffPackage` with `allowed_actions`, approval, boundary refs, result refs, and status.
- `src/hisys/agents/dars.py` implements `DarsRuntime` loopback/fixture critique behavior.
- `tests/unit/test_dars_runtime.py` verifies local handoff/critique artifacts.
- README and traceability docs explicitly state DARS itself is not implemented.

Current safety posture:

- `dars_backend=loopback_placeholder`
- `external_call_made=false`
- `allowed_actions=advisory_only`
- `action_taken=none`
- DARS cannot directly trigger external software or alert actions.

Controlled anchors:

- `HISYS-DARS-CONTRACT-001`
- `HISYS-FR-AGT-001..005`
- `HISYS-T-005`, `HISYS-T-019`, `HISYS-T-020`, `HISYS-T-024`
- `HISYS-CON-010`, `HISYS-CON-011`, `HISYS-CON-012`

---

## 2. Target DARS Boundary

### 2.1 Roles

| Role | Responsibility | May perform live action? |
|---|---|---|
| Hisys `DarsRuntime` | Owns request preparation, adapter selection, validation, persistence, linking, reports | No direct live action except through adapter gate |
| DARS adapter | Converts a validated handoff package into a backend-specific request and returns raw response envelope | Only if enabled and approved |
| Critique ingester | Validates/normalizes DARS output into controlled records | No |
| Chief Editor / human reviewer | Decides whether critique affects alert, memo, CAPA, or requirement status | Only through existing approval gate |

### 2.2 Boundary Rule

DARS output is **advisory evidence**, not an approved decision. It may create review items or recommendation records, but must not mutate alerts, memos, connectors, requirements, or software triggers without explicit downstream approval.

### 2.3 Backend Modes

| Mode | Purpose | External call | Default |
|---|---|---:|---:|
| `loopback_placeholder` | Current no-DARS placeholder | false | yes until replaced |
| `fixture_file` | Local deterministic DARS response fixture | false | allowed in tests |
| `mock_http` | Local/mock endpoint contract test | false or local-only | later test increment |
| `real_dars_disabled` | Configured real backend but blocked | false | required before live |
| `real_dars_enabled` | Actual DARS backend | true | future explicit approval only |

---

## 3. Data Model Design

### 3.1 Existing Handoff Package

Keep `AgentHandoffPackage` as the outbound request object. Strengthen use of existing fields before adding new schema fields:

- `handoff_id`
- `target_agent_system="DARS"`
- `task`
- `context`
- `evidence_bundle`
- `constraints`
- `expected_output`
- `allowed_actions="advisory_only"`
- `approval_state`
- `source_registry_refs`
- `scope_policy_ref`
- `boundary_record_refs`
- `collection_output_refs`
- `prohibited_actions`
- `result_refs`
- `status`

Potential later additions only if tests prove necessary:

- `handoff_type`: `critique | risk_review | requirements_review | evidence_gap_review`
- `requester`
- explicit structured `record_refs` object

### 3.2 DARS Critique Record

Evolve `DarsCritiqueRecord` from plain text into structured advisory evidence.

Target fields:

```yaml
critique_id: CRITIQUE-...
handoff_ref: HANDOFF-...
source_execution_ref: EXEC-...
target_agent_system: DARS
dars_backend: loopback_placeholder | fixture_file | mock_http | real_dars_disabled | real_dars_enabled
external_call_made: boolean
allowed_actions: advisory_only
action_taken: none
status: received | linked | rejected | closed
producer_id: string
critique_summary: string
unsupported_claims: list[string]
counterarguments: list[string]
risk_findings: list[string]
confidence_assessment: none | low | medium | high | unknown
recommended_actions: list[string]
requires_human_review: boolean
linked_record_refs:
  sources: list[string]
  observations: list[string]
  signals: list[string]
  memos: list[string]
  alerts: list[string]
validation_warnings: list[string]
policy_refs: list[string]
```

### 3.3 DARS Dispatch Decision

Before any adapter is called, write a runtime-boundary dispatch decision.

```yaml
decision_id: DARS-DISPATCH-...
handoff_ref: HANDOFF-...
backend_mode: fixture_file | mock_http | real_dars_disabled | real_dars_enabled
adapter_id: string
enabled: boolean
approval_ref: string | null
allowed_actions: advisory_only
external_call_permitted: boolean
external_call_made: false
blocked_reasons: list[string]
action_taken: none
```

This mirrors the live connector safety decision pattern and makes DARS dispatch auditable.

---

## 4. Runtime Flow

### 4.1 Fixture/Mock Flow

1. Load source execution / alert / memo context.
2. Build `AgentHandoffPackage`.
3. Write handoff JSON/Markdown to `data/agent-handoffs/<YYYYMMDD>/`.
4. Evaluate DARS dispatch decision.
5. If backend is `fixture_file`, load local fixture response.
6. Validate response into structured `DarsCritiqueRecord`.
7. Link critique to execution/memo/alert/evidence refs.
8. Write critique JSON/Markdown to `data/agent-critiques/<YYYYMMDD>/`.
9. Write dispatch/report artifacts to:
   - `runtime-boundary/dars/<YYYYMMDD>/`
   - `reports/run-summaries/<YYYYMMDD>/dars-critique-report.{json,md}`

### 4.2 Real Backend Flow — Future Only

Real dispatch remains blocked until all are true:

- DARS backend config exists and is explicitly enabled.
- Adapter action is allow-listed.
- Handoff `allowed_actions` remains `advisory_only` unless a later controlled policy changes it.
- Human or controlled-policy approval ref exists.
- Secrets are loaded only from local-only secret storage, never committed.
- Mock/fixture tests and traceability gate pass.
- Runtime-boundary dispatch decision records `external_call_permitted=true` before adapter execution.

Even then, DARS response remains advisory and cannot directly trigger downstream action.

---

## 5. Failure and Safety Rules

1. Missing source execution -> report skipped execution; no handoff dispatch.
2. Disabled backend -> write blocked dispatch decision; no external call.
3. Missing approval for real backend -> blocked dispatch decision.
4. Malformed DARS response -> write rejected critique with validation warnings; do not link as accepted evidence.
5. DARS timeout/error -> bounded failure record; unrelated workflows continue.
6. Secret-like values in DARS payload/response -> redact in Markdown/report output; secret scan must remain clean.
7. Recommended actions from DARS are advisory strings only; never executed by DARS ingestion.

---

## 6. Ralph/TDD Implementation Queue

### Task DARS-A: Structured critique ingestion schema

**Objective:** Add structured critique fields while preserving current loopback tests.

**Files:**

- Modify: `src/hisys/agents/dars.py`
- Modify: `tests/unit/test_dars_runtime.py`
- Modify: `docs/traceability/README.md`

**RED:** Add tests asserting `unsupported_claims`, `counterarguments`, `risk_findings`, `recommended_actions`, `requires_human_review`, and `linked_record_refs` are persisted.

**GREEN:** Extend `DarsCritiqueRecord` with defaults and fixture parser.

**Verify:**

```bash
python3 -m pytest tests/unit/test_dars_runtime.py -q
python3 -m pytest
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py --json .
```

**Commit:** `feat: structure dars critique ingestion`

---

### Task DARS-B: Dispatch decision gate

**Objective:** Add runtime-boundary DARS dispatch decisions before backend selection.

**Files:**

- Create: `src/hisys/agents/dars_dispatch.py` or extend `src/hisys/agents/dars.py`
- Modify: `tests/unit/test_dars_runtime.py`
- Modify: `examples/instance/harness/guidelines/dars.md`

**RED:** Add tests for disabled real backend and fixture backend decision artifacts.

**GREEN:** Persist `DarsDispatchDecision` Markdown/JSON under `runtime-boundary/dars/<YYYYMMDD>/`.

**Commit:** `feat: add dars dispatch safety decisions`

---

### Task DARS-C: Fixture-file DARS backend

**Objective:** Replace ad hoc `--critique-text` fixture path with a deterministic fixture backend contract.

**Files:**

- Add fixture under `examples/instance/harness/fixtures/dars/`
- Modify: `src/hisys/agents/dars.py`
- Modify: CLI command for `request-dars-critique` if needed
- Test: `tests/unit/test_dars_runtime.py`

**RED:** Test fixture response ingestion with multiple structured critique lists.

**GREEN:** Load fixture file and validate into `DarsCritiqueRecord`.

**Commit:** `feat: add fixture dars backend contract`

---

### Task DARS-D: Malformed critique rejection

**Objective:** Reject unsafe/malformed DARS responses without breaking the run.

**Files:**

- Modify: `src/hisys/agents/dars.py`
- Test: `tests/unit/test_dars_runtime.py`

**RED:** Test missing summary, invalid severity, or action-like recommendation that violates allowed actions.

**GREEN:** Mark critique `status=rejected`, preserve warnings, keep `action_taken=none`.

**Commit:** `fix: reject malformed dars critiques safely`

---

### Task DARS-E: End-to-end trace link

**Objective:** Extend trace-path evidence so DARS critique is reconstructable from source execution/memo/alert.

**Files:**

- Modify: `tests/integration/test_trace_path.py`
- Modify: `src/hisys/operations/release_readiness.py` if needed
- Modify: `docs/traceability/README.md`

**RED:** Test source -> observation/signal/memo/alert -> DARS handoff -> critique refs.

**GREEN:** Add missing refs/report fields only where necessary.

**Commit:** `feat: link dars critique in trace path`

---

### Task DARS-F: Mock endpoint adapter, disabled by default

**Objective:** Add adapter interface and local/mock transport without enabling real DARS.

**Files:**

- Create: `src/hisys/agents/dars_adapters.py`
- Modify: `src/hisys/agents/dars.py`
- Test: `tests/unit/test_dars_adapters.py`

**RED:** Test disabled mock adapter blocks external-style calls unless config explicitly selects local mock.

**GREEN:** Implement adapter protocol and local mock response path.

**Commit:** `feat: add disabled dars adapter interface`

---

## 7. Acceptance Criteria for Design Phase

The design is ready for implementation when:

- The first executable increment is local-only and testable.
- Real DARS calls are explicitly deferred behind disabled-by-default config and approval.
- DARS output cannot directly mutate records or trigger connectors.
- Structured critique fields satisfy `HISYS-DARS-CONTRACT-001` expected output.
- The queue supports Ralph/TDD execution in small commits.

---

## 8. Recommended Next Ralph Start

Start with **Task DARS-A: Structured critique ingestion schema**.

Reason:

- It closes the biggest gap in `HISYS-T-019` without network or live DARS.
- It preserves current loopback behavior.
- It creates the stable input/output shape required before adapter design becomes meaningful.
