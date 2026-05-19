---
doc_id: HISYS-DARS-CP-RTM-001
title: DARS Critic Panel Runtime Traceability Matrix
version: 0.8.0
document_status: draft-for-tdd
created: 2026-05-19
updated: 2026-05-20
---

# DARS Critic Panel Runtime Traceability Matrix

Source Hisys packet: `/tmp/hisys-dars-critic-panel-instance/runtime-boundary/agent-workflows/20260519/SPEC-DARS-CRITIC-PANEL-001.json`.

| Requirement ID | SDD element | STD testcase | Pytest anchor | Status |
|---|---|---|---|---|
| HISYS-FR-DARS-CP-001 | `DarsCriticPanelConfig`, config validator, `CriticAdapterRegistry` (M-CP-EXT-1), read-only `hisys run-dars-panel` CLI wrapper (M-CP-EXT-6) | HISYS-T-DARS-CP-001 | `test_dars_critic_panel_config_validates_two_advisory_roles`, `test_critic_adapter_registry_rejects_duplicate_role_backend_pair`, `test_run_dars_panel_cli_persists_fixture_round_and_prints_json` | GREEN (MB-DARS-CP-T001 + M-CP-EXT-1 + M-CP-EXT-6) |
| HISYS-FR-DARS-CP-002 | `DarsRoundPlan`, `DarsCriticTask`, edges | HISYS-T-DARS-CP-002 | `test_dars_round_plan_creates_independent_critic_tasks_before_synthesis` | GREEN (MB-DARS-CP-T001) |
| HISYS-FR-DARS-CP-003 | fixture critic executor, critique writer, `ExecutionBoundaryRecord` per-task writer (M-CP-EXT-2), injectable clock seam (M-CP-EXT-5), read-only `hisys run-dars-panel` CLI wrapper (M-CP-EXT-6) | HISYS-T-DARS-CP-003 | `test_dars_panel_runtime_writes_advisory_critique_artifacts`, `test_panel_runtime_writes_one_boundary_record_per_task`, `test_panel_runtime_with_injected_clock_yields_byte_identical_boundary_records`, `test_panel_runtime_rejects_naive_clock`, `test_run_dars_panel_cli_persists_fixture_round_and_prints_json` | GREEN (MB-DARS-CP-T001 + M-CP-EXT-2 + M-CP-EXT-5 + M-CP-EXT-6) |
| HISYS-FR-DARS-CP-004 | `DarsRoundTrace` writer, `ExecutionBoundaryRecord` per-task writer (M-CP-EXT-2) | HISYS-T-DARS-CP-004 | `test_dars_panel_runtime_persists_round_trace_lineage`, `test_panel_runtime_writes_one_boundary_record_per_task` | GREEN (MB-DARS-CP-T001 + M-CP-EXT-2) |
| HISYS-FR-DARS-CP-005 | `DarsCritiqueSynthesis` | HISYS-T-DARS-CP-005 | `test_dars_critique_synthesis_is_advisory_and_preserves_role_provenance` | GREEN (MB-DARS-CP-T001) |
| HISYS-FR-DARS-CP-006 | execution mode policy, `ExecutionGraphPlan` ready-set determinism / synthesis-after-terminal-critics / bounded-parallel chunking (M-CP-EXT-3) | HISYS-T-DARS-CP-006 | `test_dars_round_plan_is_serial_compatible_with_bounded_parallel_policy`, `test_execution_graph_plan_ready_set_is_deterministic_and_sorted`, `test_execution_graph_plan_synthesis_waits_until_all_critics_terminal`, `test_execution_graph_plan_treats_failed_blocked_and_skipped_as_terminal`, `test_execution_graph_plan_bounded_parallel_chunks_are_deterministic`, `test_execution_graph_plan_rejects_invalid_max_parallel`, `test_execution_graph_plan_rejects_unknown_dependency_node`, `test_execution_graph_plan_rejects_dependency_cycle`, `test_execution_graph_plan_from_round_plan_preserves_critic_before_synthesis_edges`, `test_dars_panel_reexports_execution_graph_plan_for_compatibility`, `test_dars_panel_runtime_remains_serial_after_graph_integration` | GREEN (MB-DARS-CP-T001 + M-CP-EXT-3) |
| HISYS-FR-DARS-CP-007 | backend dispatch gate, `CriticAdapterRegistry` external block, typed `FixtureCriticAdapter.fixture_outcome` (M-CP-EXT-1), `ExecutionBoundaryRecord.dispatch_decision` (M-CP-EXT-2), typed adapter-missing `LookupError` -> `status=blocked` (M-CP-EXT-4), unresolved `adapter_class` marker on boundary records (M-CP-EXT-7), CLI surface preserves blocked external-style backend invariant (M-CP-EXT-6) | HISYS-T-DARS-CP-007 | `test_dars_panel_blocks_external_backend_without_approval`, `test_critic_adapter_registry_blocks_external_without_explicit_allow_flag`, `test_fixture_critic_adapter_records_declared_outcome_without_keyword_match`, `test_panel_runtime_writes_one_boundary_record_per_task`, `test_panel_runtime_emits_blocked_when_registry_has_no_adapter_for_role`, `test_panel_runtime_marks_unresolved_adapter_class_for_disabled_critic`, `test_fixture_critic_adapter_rejects_unresolved_adapter_class`, `test_run_dars_panel_cli_blocks_external_backend_without_live_dispatch` | GREEN (MB-DARS-CP-T001 + M-CP-EXT-1 + M-CP-EXT-2 + M-CP-EXT-4 + M-CP-EXT-6 + M-CP-EXT-7) |
| HISYS-FR-DARS-CP-008 | advisory/human-decision fields | HISYS-T-DARS-CP-008 | `test_dars_panel_artifacts_preserve_advisory_human_decision_separation` | GREEN (MB-DARS-CP-T001) |
| HISYS-NFR-DARS-CP-001 | failure policy and partial synthesis, adapter-outcome-driven isolation (M-CP-EXT-1), per-task boundary record on failed/blocked branches (M-CP-EXT-2), typed adapter-missing isolation (M-CP-EXT-4), CLI preserves typed advisory exit-code semantics (M-CP-EXT-6) | HISYS-T-DARS-CP-009 | `test_dars_panel_isolates_one_critic_failure_and_reports_partial_evidence`, `test_panel_runtime_isolates_failed_adapter_outcome_without_keyword_match`, `test_panel_runtime_writes_one_boundary_record_per_task`, `test_panel_runtime_emits_blocked_when_registry_has_no_adapter_for_role`, `test_run_dars_panel_cli_blocks_external_backend_without_live_dispatch` | GREEN (MB-DARS-CP-T001 + M-CP-EXT-1 + M-CP-EXT-2 + M-CP-EXT-4 + M-CP-EXT-6) |
| HISYS-NFR-DARS-CP-002 | redaction/secret-scan gate, slug validation on date/request_id/task_id (M-CP-EXT-2), naive-datetime clock rejection (M-CP-EXT-5) | HISYS-T-DARS-CP-010 | changed-file secret scan, `test_write_execution_boundary_record_rejects_invalid_slug`, `test_write_execution_boundary_record_rejects_traversal_in_task_id`, `test_panel_runtime_rejects_invalid_slug`, `test_panel_runtime_rejects_naive_clock` | GREEN (MB-DARS-CP-T001 + M-CP-EXT-2 + M-CP-EXT-5) |

## M-CP-EXT-6 — Read-only run-dars-panel CLI (2026-05-20)

- Scope: added a read-only `hisys run-dars-panel` argparse subcommand that
  wraps the already-implemented fixture-local `DarsCriticPanelRuntime.run_round`
  surface. The CLI loads a local panel-config JSON file into
  `DarsCriticPanelConfig` / `DarsCriticRoleConfig`, constructs
  `DarsCriticPanelRuntime(instance=InstanceRoot(...))` with the default fixture
  policy, calls `run_round`, persists the existing advisory artifacts under the
  instance root, and prints either a JSON or text bounded summary. No new
  service module, no clock seam, no adapter-registry flag, no external
  dispatch enable flag.
- Surface change: `src/hisys/cli/main.py` gains `_load_dars_panel_config`,
  `_cmd_run_dars_panel`, and a `run-dars-panel` subparser dispatched from
  `main(...)`. The DARS panel runtime imports add
  `DarsCriticPanelConfig`, `DarsCriticPanelRuntime`, and `DarsCriticRoleConfig`
  alongside the existing `DarsRuntime` import.
- Safety envelope preserved: typed `blocked` outcomes for `external-*` backends
  flow through the existing `_DefaultFixturePolicy` -> `PermissionError`
  arm of `run_round`; the CLI never enables external dispatch, never spawns
  workers, never approves downstream decisions, and never mutates the
  candidate/evidence/rubric inputs. The CLI returns exit code `0` whenever
  `run_round` persists the round, even if individual critic tasks are
  `blocked` or `failed`. Non-zero exit codes remain reserved for argparse
  rejections and uncaught runtime invariant errors.
- Output shape: the JSON summary exposes `request_id`, `panel_id`,
  `execution_mode` (mirrors `serial` / `bounded_parallel` from the panel
  config's `max_parallel_critics`), `task_statuses` (mapping persistent task
  ids to typed statuses), `critique_refs`, `synthesis_ref`, `round_trace_ref`,
  and `execution_boundary_refs`. The text mode prints the same fields in an
  operator-readable layout.
- New tests:
  `test_run_dars_panel_cli_persists_fixture_round_and_prints_json` (writes a
  panel-config JSON, runs the CLI with `--format json`, asserts the bounded
  summary fields, and verifies every persisted ref exists under the instance
  root) and
  `test_run_dars_panel_cli_blocks_external_backend_without_live_dispatch`
  (panel-config with `backend_id=external-cli-backend`; CLI exits 0, task
  status is `blocked`, no critique ref is produced, and the persisted boundary
  record has the locked safety envelope with `adapter_class="unresolved"`).
- Existing tests preserved:
  `tests/unit/test_dars_critic_panel_runtime.py` (9 passed, unchanged),
  `tests/unit/test_dars_critic_panel_adapters.py` (5 passed, unchanged),
  `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`
  (19 passed, unchanged),
  `tests/unit/test_dars_critic_panel_execution_graph_plan.py`
  (10 passed, unchanged).
- Deferred to follow-on increments: per-task `started_at` / `completed_at`
  distinct from the round-level clock tick; package split of the increasingly
  large `src/hisys/agents/dars_panel.py`; actual bounded-parallel execution
  activation (separate governance/approval increment).
- Boundary: no live DARS dispatch, no credential resolution, no remote push,
  no external call, no mutation, no clock seam change, no adapter registry
  override flag. Validation commands recorded in the ralph.md Reflection Log
  entry for M-CP-EXT-6.

## M-CP-EXT-7 — Unresolved adapter class literal (2026-05-20)

- Scope: closed the M-CP-EXT-2 open item (d) and the M-CP-EXT-4 open item (a)
  about the structural `adapter_class="fixture"` default for boundary records
  on the `disabled` / `PermissionError` / `LookupError` branches (when no
  adapter is resolved). The `AdapterClass` `Literal` is widened to include
  `"unresolved"`, and `DarsCriticPanelRuntime.run_round` now persists
  `adapter_class="unresolved"` on every boundary record whose
  `adapter is None`. Reviewers can now distinguish "the role was bound to a
  fixture adapter and the adapter chose this outcome" from "no adapter
  resolution attempt yielded an adapter for this role".
- Runtime change: a single substitution inside `run_round` —
  `adapter_class=adapter.adapter_class if adapter is not None else "unresolved"`
  (was `... else "fixture"`). The `AdapterClass` type alias is now
  `Literal["fixture", "loopback", "external", "unresolved"]`.
- Reserved-marker invariant: `FixtureCriticAdapter.__post_init__` continues
  to reject `adapter_class` values outside `{"fixture", "loopback",
  "external"}`. `"unresolved"` is reserved for `ExecutionBoundaryRecord`
  reporting; it never describes a real adapter binding and is never returned
  by `CriticAdapterRegistry.resolve(...)`.
- New tests:
  `test_panel_runtime_marks_unresolved_adapter_class_for_disabled_critic`
  (two-critic config — one disabled, one missing-from-registry — both
  boundary records assert `adapter_class="unresolved"` with the safety
  envelope intact) and `test_fixture_critic_adapter_rejects_unresolved_adapter_class`
  (constructing a `FixtureCriticAdapter` with `adapter_class="unresolved"`
  raises `ValueError("adapter_class must be fixture|loopback|external; got
  unresolved")`).
- Existing tests preserved:
  `tests/unit/test_dars_critic_panel_runtime.py` (9 passed, unchanged),
  `tests/unit/test_dars_critic_panel_adapters.py` (5 passed, unchanged
  post-M-CP-EXT-4),
  `tests/unit/test_dars_critic_panel_tool_execution_runtime.py` (now 19
  passed, +2 new),
  `tests/unit/test_dars_critic_panel_execution_graph_plan.py` (10 passed,
  unchanged).
- Audit trail: the M-CP-EXT-2 RTM section still documents the original
  `"fixture"` structural default; this M-CP-EXT-7 section is the
  forward-pointing record of the replacement.
- Boundary: no live DARS dispatch, no credential resolution, no remote push,
  no external call, no mutation, no CLI activation, no schema field added or
  removed. Validation commands recorded in the ralph.md Reflection Log entry
  for M-CP-EXT-7.

## M-CP-EXT-5 — Deterministic clock injection seam (2026-05-20)

- Scope: replaced the hard-coded wall-clock `datetime.now(timezone.utc)` call
  inside `DarsCriticPanelRuntime.run_round` with a constructor-injected
  `Callable[[], datetime]` seam (`clock` parameter on `__init__`). Production
  callers that do not pass `clock` continue to read the wall clock; tests can
  now inject a fixed clock and assert byte-identical
  `ExecutionBoundaryRecord` JSON output across `run_round` invocations.
- Runtime change: `DarsCriticPanelRuntime.__init__` accepts an optional
  `clock: Callable[[], datetime] | None = None`; when omitted, the runtime
  uses `lambda: datetime.now(timezone.utc)` (no behavior change for existing
  callers). The single `timestamp = ...` line inside `run_round` is now
  `timestamp = _format_iso_timestamp(self._clock())`, where the new private
  helper `_format_iso_timestamp` enforces timezone-awareness on every clock
  reading and converts the result to a deterministic UTC ISO-8601 string
  (`...Z` suffix, microseconds truncated).
- Safety envelope: a caller-supplied naive `datetime` (no `tzinfo`) raises
  `ValueError("clock must return timezone-aware datetime")` from
  `_format_iso_timestamp`. This prevents ambiguous wall-clock readings from
  being persisted to boundary records. The default lambda always returns a
  timezone-aware UTC datetime, so production callers are unaffected.
- Per-task timing scope: the clock is still read once per round; per-task
  `started_at == completed_at` is preserved (real per-task timing remains a
  deferred increment). The injection seam keeps that future increment cheap
  because the clock is now a per-runtime dependency rather than a hard-coded
  module-level call.
- New tests:
  `test_panel_runtime_with_injected_clock_yields_byte_identical_boundary_records`
  (fixed clock, two consecutive `run_round` invocations, JSON payloads compared
  by `started_at`/`completed_at`) and `test_panel_runtime_rejects_naive_clock`
  (naive `datetime` clock raises `ValueError("...timezone-aware...")` from
  `run_round`).
- Existing tests preserved:
  `tests/unit/test_dars_critic_panel_runtime.py` (9 passed, unchanged),
  `tests/unit/test_dars_critic_panel_adapters.py` (5 passed, unchanged
  post-M-CP-EXT-4),
  `tests/unit/test_dars_critic_panel_tool_execution_runtime.py` (now 17
  passed, +2 new), and
  `tests/unit/test_dars_critic_panel_execution_graph_plan.py` (10 passed,
  unchanged).
- Boundary: no live DARS dispatch, no credential resolution, no remote push,
  no external call, no mutation, no CLI activation, no parallel execution.
  Validation commands recorded in the ralph.md Reflection Log entry for
  M-CP-EXT-5.

## M-CP-EXT-4 — Typed adapter-missing blocked increment (2026-05-20)

- Scope: converted the previously uncaught `CriticAdapterRegistry.resolve(...)`
  `LookupError` path (raised when an explicit caller-supplied registry has no
  adapter for a `(critic_role, backend_id)` pair) into a typed per-task
  `DarsTaskResult(status="blocked")` plus a matching
  `ExecutionBoundaryRecord(dispatch_decision="blocked",
  dispatch_reason=<LookupError text>)` so a missing registration no longer
  crashes the round. The registry contract is unchanged: `resolve` still raises
  `LookupError` for callers other than `run_round`.
- Runtime change: `DarsCriticPanelRuntime.run_round` now catches
  `(LookupError, PermissionError)` from the adapter-resolution call in a single
  sibling `except` arm. Both arms emit the same task-result and
  boundary-record shape with `external_call_made=False`,
  `mutation_performed=False`, `action_authorized=False`, `advisory_only=True`,
  and `requires_human_review=True`. The `adapter_class="fixture"` structural
  default already used by the `disabled` and `PermissionError` branches applies
  to the new `LookupError` branch as well; a non-structural
  `adapter_class="unresolved"` literal remains deferred (open item from
  M-CP-EXT-2 reflection).
- Default fallback registry unaffected: `_DefaultFixturePolicy` synthesizes
  adapters on demand, so it never raises `LookupError`. Only explicit
  caller-supplied `CriticAdapterRegistry` instances with missing
  `(role, backend_id)` pairs reach the new branch.
- New tests: `test_panel_runtime_emits_blocked_when_registry_has_no_adapter_for_role`
  in `tests/unit/test_dars_critic_panel_adapters.py` (asserts task status,
  empty critique refs, `external_call_made=False`, exception-text propagation
  into both the task result `error_message` and the persisted boundary record
  `dispatch_reason`, and the locked safety-envelope fields on the boundary
  record JSON payload).
- Existing tests preserved:
  `tests/unit/test_dars_critic_panel_runtime.py` (9 passed, unchanged),
  `tests/unit/test_dars_critic_panel_adapters.py` (now 5 passed, +1 new),
  `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`
  (15 passed, unchanged), and
  `tests/unit/test_dars_critic_panel_execution_graph_plan.py`
  (10 passed, unchanged).
- Boundary: no live DARS dispatch, no credential resolution, no remote push,
  no external call, no mutation, no CLI activation, no clock-injection seam.
  Validation commands recorded in the ralph.md Reflection Log entry for
  M-CP-EXT-4.

## M-CP-EXT-3 — Execution graph plan increment (2026-05-20)

- Scope: added a pure, timestamp-free `ExecutionGraphPlan` plus deterministic
  ready-set and bounded-parallel chunking primitives in a new sidecar module
  `src/hisys/agents/dars_panel_graph.py`. The graph primitive does not execute
  critics, spawn workers, call external services, or activate bounded-parallel
  runtime execution. The advisory-only invariants from M-CP-EXT-1/2 remain
  mandatory.
- New module exports (from `hisys.agents.dars_panel_graph` and re-exported by
  `hisys.agents.dars_panel`): `ExecutionGraphPlan`, `ExecutionGraphNode`,
  `ExecutionGraphEdge`, `TERMINAL_TASK_STATUSES`,
  `DARS_CRITICS_CONCURRENCY_GROUP`, `DARS_SYNTHESIS_CONCURRENCY_GROUP`.
- Ready-set semantics: terminal statuses are `completed`, `failed`, `blocked`,
  `skipped`. A task is ready when not terminal, not in progress, and all
  dependencies are terminal. The ready-set is returned in deterministic lexical
  `task_id` order. Synthesis becomes ready only after every critic task is
  terminal.
- Bounded-parallel chunking: `bounded_parallel_chunks(max_parallel=N)` chunks
  the current sorted ready-set into deterministic lists of at most `N` task
  IDs. `max_parallel < 1` raises `ValueError`.
- Graph construction safety: `__post_init__` raises `ValueError` for duplicate
  task IDs, unknown dependency endpoints, and dependency cycles.
- Runtime wiring: `DarsCriticPanelRuntime.run_round` constructs
  `ExecutionGraphPlan.from_round_plan(plan)` and asserts that the start-of-round
  ready-set equals the sorted critic task IDs. The runtime remains serial; the
  graph acts only as a structural consistency guard. Execution order, output
  artifacts, and boundary records are unchanged.
- Deferred to follow-on increments: deterministic clock injection
  (M-CP-EXT-5), typed adapter-missing `LookupError` → `status=blocked`
  (M-CP-EXT-4), `hisys run-dars-panel` CLI (M-CP-EXT-6), actual bounded-parallel
  runtime execution (separate governance/approval increment).
- New tests: `tests/unit/test_dars_critic_panel_execution_graph_plan.py`
  (10 tests covering ready-set determinism, synthesis readiness, terminal-status
  contract, bounded-parallel chunks, invalid `max_parallel`, unknown dependency
  endpoints, dependency cycles, `from_round_plan` bridge, `dars_panel`
  re-export compatibility, and serial-runtime regression guard).
- Existing tests preserved: `tests/unit/test_dars_critic_panel_runtime.py`
  (9 passed, unchanged), `tests/unit/test_dars_critic_panel_adapters.py`
  (4 passed, unchanged), and
  `tests/unit/test_dars_critic_panel_tool_execution_runtime.py` (15 passed,
  unchanged).
- Boundary: no live DARS dispatch, no credential resolution, no remote push,
  no external call, no mutation, no CLI activation, no actual bounded-parallel
  runtime execution. Validation commands recorded in the ralph.md Reflection
  Log entry for M-CP-EXT-3.

## M-CP-EXT-2 — Execution boundary record increment (2026-05-19)

- Scope: persisted a per-task `ExecutionBoundaryRecord` JSON artifact for every
  critic dispatch decision (`allowed`/`blocked`) and enforced slug validation
  on `yyyymmdd` and `request_id` (and `task_id` inside the writer) before any
  path is composed under the runtime instance root.
- New module exports: `ExecutionBoundaryRecord`, `write_execution_boundary_record`,
  `DispatchDecision`, `RUNTIME_BOUNDARY_SUBTREE`.
- Runtime change: `DarsCriticPanelRuntime.run_round` writes one boundary record
  per critic task (enabled/disabled, completed/failed/blocked) under
  `<instance>/runtime-boundary/dars-panel/<YYYYMMDD>/<REQUEST_ID>/<TASK_ID>.json`,
  and exposes the resulting refs on `DarsRoundResult.execution_boundary_refs`.
- Safety envelope: every `ExecutionBoundaryRecord` locks
  `external_call_made=False`, `mutation_performed=False`,
  `action_authorized=False`, `advisory_only=True`, `requires_human_review=True`.
  Any construction attempt with an unsafe override raises `ValueError`.
- Slug discipline: `_validate_slug` (mirroring
  `src/hisys/operations/codebase_analysis.py`) is enforced at the top of
  `run_round`, inside `_panel_dir`, and inside `write_execution_boundary_record`.
  Empty strings, hyphenated `YYYY-MM-DD` dates, absolute paths (`/abs`), and
  traversal segments (`..`) are rejected before any directory is created.
- New tests: `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`
  (15 tests covering dataclass defaults, writer round-trip determinism, writer
  slug rejection, task-id traversal rejection, run-round boundary-records-per-task,
  and run-round slug rejection).
- Existing tests preserved: `tests/unit/test_dars_critic_panel_adapters.py`
  (4 passed, unchanged) and `tests/unit/test_dars_critic_panel_runtime.py`
  (9 passed, unchanged).
- Boundary: no live DARS dispatch, no credential resolution, no remote push,
  no external call, no mutation. Validation commands recorded in the ralph.md
  Reflection Log entry for M-CP-EXT-2.

## M-CP-EXT-1 — Critic adapter registry increment (2026-05-19)

- Scope: replaced the `"fail" in backend_id` substring failure heuristic and the
  inline `backend_id.startswith("external-")` external classification in
  `DarsCriticPanelRuntime.run_round` with an explicit `CriticAdapterRegistry`
  plus `FixtureCriticAdapter` (typed `adapter_class` and `fixture_outcome`).
- New module exports: `AdapterClass`, `BackendDispatchOutcome`,
  `CriticAdapterRegistry`, `FixtureCriticAdapter`.
- Runtime change: `DarsCriticPanelRuntime.__init__` now accepts an optional
  `adapter_registry`. Without one it falls back to a closed,
  fixture/loopback-only default policy that preserves `MB-DARS-CP-T001`-era
  backend conventions (`fixture-failing-critic` → typed `failed` outcome;
  other fixture/loopback → `completed`).
- External invariant: external adapters require the registry's
  `external_dispatch_allowed=True` *and* a truthy `approval_ref`. The default
  fallback policy never enables external dispatch.
- New tests: `tests/unit/test_dars_critic_panel_adapters.py` (4 tests).
- Existing tests preserved: `tests/unit/test_dars_critic_panel_runtime.py`
  (9 passed, unchanged).
- Boundary: no live DARS dispatch, no credential resolution, no remote push,
  no external call, no mutation. Validation commands recorded in the ralph.md
  Reflection Log entry for M-CP-EXT-1.

## Existing baseline links

- Parent SRS: `HISYS-FR-AGT-001..005`, `HISYS-FR-DOM-003..004`, `HISYS-NFR-REL-001`, `HISYS-NFR-SEC-001`, `HISYS-NFR-SEC-004`.
- Existing DARS plan: `docs/plans/dars-integration-design.md`.
- Existing DARS contracts: `docs/contracts/dars-data-format.md`, `docs/contracts/dars-evaluation-rubrics.md`, `docs/contracts/dars-prompt-registry.md`.

## TDD verdict

`YES_WITH_CONTROLS`: the controlled package is TDD-ready for a fixture/local-only DARS critic panel runtime increment. It is not approval to enable live DARS dispatch, external agent calls, mutation, publication, or autonomous decision authority. The invariant is `advisory_only` critic output until separate Hisys governance and human approval convert evidence into a downstream decision.
