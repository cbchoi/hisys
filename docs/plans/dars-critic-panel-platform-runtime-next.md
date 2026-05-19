# DARS Critic Panel — Platform/Runtime Boundary Next-Increment Plan

> **For Ralph/Hermes:** This document is a `document_red` planning artifact authored for MB-DARS-CP-T004 (Milestone Bootstrap v0.0.1, milestone MB-DARS-CP-M3). It describes the next-increment design surface for extending the fixture-local panel runtime (committed via MB-DARS-CP-T001 at `src/hisys/agents/dars_panel.py`) toward a platform/runtime-boundary contract. No live DARS dispatch, browser/network connector, credential resolution, publication, deployment, or remote push is authorized by this plan.

## Decision context

- Branch: `dars` tracking `origin/dars`.
- Baseline at authoring: `02d2436 feat: add fixture-local DARS critic panel runtime` (MB-DARS-CP-T001 GREEN).
- Controlled anchors:
  - SRS: `docs/requirements/dars-critic-panel-runtime-requirements.md` (HISYS-FR-DARS-CP-001..008, HISYS-NFR-DARS-CP-001..002).
  - SDD: `docs/design/dars-critic-panel-runtime-sdd.md`.
  - STD: `docs/test/dars-critic-panel-runtime-std.md`.
  - RTM: `docs/traceability/dars-critic-panel-runtime-traceability.md`.
  - Existing DARS line: `src/hisys/agents/dars.py`, `src/hisys/agents/dars_backend.py`, `src/hisys/agents/dars_config.py`, `src/hisys/agents/dars_dispatch.py`, `src/hisys/agents/dars_protocol.py`, `src/hisys/agents/dars_trace.py`, `src/hisys/agents/appraiser_separation.py`.
  - Local DARS / ByeSys provenance plan: `docs/plans/2026-05-16-local-dars-byesys-provenance.md`.
  - DARS integration design: `docs/plans/dars-integration-design.md`.
  - Bootstrap overlay: `docs/milestone-bootstrap/reports/milestone_plan_v0.0.1.md` (milestone MB-DARS-CP-M3).
  - Bootstrap quality gate: `docs/milestone-bootstrap/gates/quality_gate_v0.0.1.md`.

## Goal

Define the next-increment design surface that lifts the panel runtime from a fixed serial-only executor with hard-coded fixture-dispatch heuristics (`backend_id.startswith("external-")`, `"fail" in backend_id`) to a small platform-kernel surface with explicit `CriticAdapterRegistry`, `ToolExecutionRuntime`, and execution-graph/process-boundary records. The increment shall keep the entire surface advisory-only, fixture-local, and no-live-action.

The plan is a `document_red` artifact: it describes the contract, the RED tests to write before implementation, and the safety invariants. It does not yet add production code, tests, or a CLI command.

## Architecture

The proposed next increment introduces three new modules (all advisory-only, all fixture-local):

| Module | Responsibility | Existing analog |
|---|---|---|
| `hisys.agents.dars_panel.adapters.CriticAdapterRegistry` | Validate and resolve `critic_role -> CriticAdapter` mappings; reject duplicates, reject any adapter without an explicit fixture-or-loopback class. | `hisys.agents.dars_backend` (fixture-file backend); `hisys.agents.dars_dispatch.DarsDispatchGate` (allow/block decision). |
| `hisys.agents.dars_panel.runtime.ToolExecutionRuntime` | Execute a `DarsCriticTask` through a resolved adapter; record per-task `ExecutionBoundaryRecord` artifacts; preserve all existing `DarsTaskResult` fields. | `hisys.agents.dars.DarsRuntime` (loopback placeholder); `hisys.agents.dars_dispatch.DarsDispatchGate.evaluate(...)`. |
| `hisys.agents.dars_panel.graph.ExecutionGraphPlan` | Strongly type the `DarsRoundPlan` -> executable graph projection: node/edge records, ready-set selection, bounded-parallel scheduling primitive. | Existing inlined dataclasses (`DarsCriticTask`, `DarsSynthesisTask`, `DarsRoundEdge`) in `src/hisys/agents/dars_panel.py`. |

Concretely:

```text
DarsCriticPanelConfig
        |
        v
DarsRoundPlan  ---->  ExecutionGraphPlan (typed nodes + edges + ready-sets)
                              |
                              v
                    ToolExecutionRuntime
                       |              |
                       v              v
              CriticAdapterRegistry  ExecutionBoundaryRecord
                       |              (per-task boundary artifact)
                       v
                  CriticAdapter
                  (fixture/loopback only;
                   no external dispatch by default)
                       |
                       v
                DarsCritiqueRecord  (unchanged contract)
```

## Tech stack

- Python 3.11.
- Pydantic v2 (mirrors existing DARS module conventions in `dars.py` and `dars_protocol.py`).
- Dataclasses where the model is purely structural (mirrors current `dars_panel.py`).
- pytest, with focused suites under `tests/unit/test_dars_critic_panel_*.py`.
- No new third-party runtime dependency.

## Boundary record

This plan authorizes documentation/planning only.

Future implementation must hold all of the following invariants:

- No live external DARS service call.
- No browser/network adapter activation; no `requests.*`, `httpx.*`, `urllib3.*`, `webbrowser.*`, or live LLM endpoint call.
- No credential read, persistence, or resolution.
- No mutation of caller-supplied candidate, evidence, rubric, or critique data.
- No publication, alert delivery, autonomous approval, or software trigger execution.
- All persisted artifacts continue to set `advisory_only=true`, `requires_human_review=true`, `action_authorized=false`, `external_call_made=false`, `mutation_performed=false`, and `human_approved=false`.
- The runtime writes only under the runtime instance root, never outside it. `yyyymmdd` and `request_id` are slug-validated before composing any path (mirrors `_validate_slug` in `src/hisys/operations/codebase_analysis.py`).
- Any change to `DarsCriticPanelConfig`, `DarsRoundPlan`, `DarsCriticTask`, `DarsRoundResult`, `DarsCritiqueSynthesis`, or `DarsRoundTrace` shall remain backwards-compatible with `tests/unit/test_dars_critic_panel_runtime.py` (HISYS-T-DARS-CP-001..009).

## Accepted requirements

Each requirement below maps to one SRS/STD anchor and is paired with a RED test to be authored before implementation.

1. **Critic adapter registry validates explicit fixture/loopback class** (HISYS-FR-DARS-CP-001, HISYS-FR-DARS-CP-007).
   - The registry resolves a `critic_role` plus `backend_id` into a typed `CriticAdapter` only when the adapter declares an explicit `adapter_class` in `{"fixture", "loopback"}`.
   - Duplicate registration for the same `(critic_role, backend_id)` raises a typed `ValueError`.
   - Adapters declaring `adapter_class="external"` are stored but never resolved unless an explicit `approval_ref` is present and `external_dispatch_allowed=true` is set at registry-build time (the registry's allow-flag is independent of any single critic's `external_call_allowed`).
   - RED test sketch: `test_critic_adapter_registry_blocks_external_without_explicit_allow_flag`.

2. **Tool execution runtime persists an execution-boundary record per task** (HISYS-FR-DARS-CP-003, HISYS-FR-DARS-CP-004, HISYS-FR-AGT-004).
   - Each invocation records an `ExecutionBoundaryRecord` JSON artifact under `<instance>/runtime-boundary/dars-panel/<YYYYMMDD>/<REQUEST_ID>/<TASK_ID>.json` with: `task_id`, `critic_id`, `critic_role`, `adapter_class`, `backend_id`, `dispatch_decision` (`allowed`/`blocked`), `dispatch_reason`, `started_at`, `completed_at`, `external_call_made=false`, `mutation_performed=false`, `approval_ref` if any, and a pointer to the resulting `critique_ref` (or `null` for blocked/failed).
   - RED test sketch: `test_tool_execution_runtime_writes_per_task_boundary_record`.

3. **Execution graph plan exposes ready-set scheduling primitive** (HISYS-FR-DARS-CP-006, HISYS-NFR-DARS-CP-001).
   - `ExecutionGraphPlan.ready_set(completed_task_ids)` returns the deterministic, sorted list of critic-task IDs whose dependencies are satisfied. The synthesis task appears in the ready-set only after every critic task has completed *or* terminated (failed/blocked).
   - `ExecutionGraphPlan.bounded_parallel_chunks(max_parallel)` returns deterministic, sorted chunks of the ready-set respecting `max_parallel` and `concurrency_group="dars-critics"`.
   - The serial executor in `DarsCriticPanelRuntime.run_round` becomes a degenerate case (`max_parallel=1`).
   - RED test sketch: `test_execution_graph_plan_ready_set_is_deterministic_and_sorted`.

4. **Failure-policy enum replaces the `fail`-substring heuristic** (HISYS-NFR-DARS-CP-001, HISYS-FR-DARS-CP-007).
   - Introduce `BackendDispatchOutcome` (`completed`, `failed`, `blocked`, `skipped`) and a `FixtureCriticAdapter.fixture_outcome` field so HISYS-T-DARS-CP-009-style failure isolation no longer depends on `"fail" in backend_id`.
   - The existing `_is_fixture_failure` shortcut in `dars_panel.py` is removed once the adapter contract is in place; the panel runtime delegates failure classification to the adapter.
   - RED test sketch: `test_fixture_critic_adapter_records_declared_outcome` and `test_panel_runtime_isolates_failed_adapter_outcome_without_keyword_match`.

5. **Slug validation on `yyyymmdd` and `request_id`** (HISYS-NFR-DARS-CP-002, HISYS-NFR-SEC-001).
   - Re-use the `_DATE_PATTERN` / `_REQUEST_ID_PATTERN` style from `src/hisys/operations/codebase_analysis.py`. Empty, absolute, or `..`-bearing values are rejected before any path is composed under the runtime instance root.
   - RED test sketch: `test_panel_runtime_rejects_traversal_in_request_id_and_date`.

6. **Secret-scan invariant on new fixtures** (HISYS-NFR-DARS-CP-002).
   - All new fixtures, ExecutionBoundaryRecord samples, and per-task adapter sketches added in the next increment shall remain clean under `python3 scripts/scan_secrets.py`.
   - RED test sketch: `test_no_credential_value_in_new_panel_fixtures` (file-list scan during pytest).

## Milestones (proposed, document_red only)

The next-increment work fits into three contiguous Ralph milestones. None of these is authorized for execution by this plan — each must be Prepare-checked under Section 6 before any production code is written.

### M-CP-EXT-1 — Critic adapter registry and fixture adapter contract

Targets requirements (1) and (4). Adds `CriticAdapterRegistry`, `CriticAdapter` (abstract), and `FixtureCriticAdapter` (concrete). Removes the `"fail" in backend_id` heuristic from `dars_panel.py` by routing failure outcomes through the adapter. The existing `DarsCriticPanelRuntime.run_round` keeps its public signature.

Exit criteria:

- `PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_runtime.py -q` still passes.
- `PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py -q` (new) passes.
- No live external adapter class exists.
- `git diff --check`, `validate_traceability.py`, and `scan_secrets.py` all clean.

### M-CP-EXT-2 — Tool execution runtime and execution-boundary record

Targets requirements (2) and (5). Adds `ToolExecutionRuntime` and the `ExecutionBoundaryRecord` JSON writer. Slug validation lands here.

Exit criteria:

- Existing panel suite passes.
- New `tests/unit/test_dars_critic_panel_tool_execution_runtime.py` covers boundary-record persistence, slug rejection, and adapter-class enforcement.
- All recorded `ExecutionBoundaryRecord` artifacts validate `external_call_made=false` and `mutation_performed=false`.

### M-CP-EXT-3 — Execution graph plan and bounded-parallel scheduler primitive

Targets requirement (3). Adds `ExecutionGraphPlan` and the deterministic ready-set / bounded-parallel-chunks primitives. The serial executor in `run_round` is rewritten to consume the plan but defaults to `max_parallel=1`, so the production behavior remains serial.

Exit criteria:

- Existing panel suite passes.
- New `tests/unit/test_dars_critic_panel_execution_graph_plan.py` covers ready-set determinism, ordering, synthesis-after-critics, and bounded-parallel chunking.
- Bounded-parallel execution is *not* enabled by default; activation requires a future explicit increment with its own RED gate.

## RED test surface (sketch only)

The following test modules are proposed for the milestones above. They do not exist yet; this plan does not write them.

- `tests/unit/test_dars_critic_panel_adapters.py`
- `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`
- `tests/unit/test_dars_critic_panel_execution_graph_plan.py`

Each module shall begin with imports that intentionally fail until the matching module under `src/hisys/agents/dars_panel/` is added, mirroring the RED pattern in `tests/unit/test_dars_critic_panel_runtime.py`.

## Out of scope

- Live external DARS dispatch (intentionally absent; out of scope for the full M-CP-EXT line).
- Remote push, deployment, publication, or release engineering.
- LLM model selection, prompt registry mutation, or evaluation rubric mutation.
- Credential management, secret storage, or env-var resolution.
- Bounded-parallel execution activation (the primitive lands in M-CP-EXT-3 but is left disabled).
- Hermes/TUI integration of the panel runtime.

## Open questions

- Should `CriticAdapterRegistry` live under `src/hisys/agents/dars_panel/adapters/` (package split) or remain in the single `dars_panel.py` module? Split is preferred once the M-CP-EXT-1 surface grows beyond ~400 lines.
- Should `ExecutionBoundaryRecord` reuse the existing `runtime-boundary/` subtree convention from `src/hisys/operations/codebase_analysis.py`, or share the `data/dars-panel/` subtree currently used for critique/synthesis/trace artifacts? Recommendation: reuse `runtime-boundary/dars-panel/...` because boundary records describe execution boundaries, not advisory critique content.
- Should the M-CP-EXT line introduce a `hisys run-dars-panel` CLI? Recommendation: defer until M-CP-EXT-3 lands so the CLI surface can consume the typed `ExecutionGraphPlan` directly.

## Stop conditions

This plan authorizes nothing executable. Stop and request a fresh Prepare before:

- writing any production code under `src/hisys/agents/dars_panel*`;
- writing any of the proposed RED test modules;
- modifying `DarsCriticPanelConfig`, `DarsRoundPlan`, `DarsRoundResult`, `DarsCritiqueSynthesis`, or `DarsRoundTrace` in a way that breaks the HISYS-T-DARS-CP-001..009 contract;
- adding any module that imports a network library (`requests`, `httpx`, `urllib3`) or a browser library (`webbrowser`, `selenium`);
- removing any of the advisory-only invariants from the current panel runtime.

The next-increment line shall remain inside the bootstrap-quality-gate boundaries described in `docs/milestone-bootstrap/gates/quality_gate_v0.0.1.md`.
