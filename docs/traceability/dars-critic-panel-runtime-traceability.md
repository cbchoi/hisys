---
doc_id: HISYS-DARS-CP-RTM-001
title: DARS Critic Panel Runtime Traceability Matrix
version: 0.14.0
document_status: draft-for-tdd
created: 2026-05-19
updated: 2026-05-21
---

# DARS Critic Panel Runtime Traceability Matrix

Source Hisys packet: `/tmp/hisys-dars-critic-panel-instance/runtime-boundary/agent-workflows/20260519/SPEC-DARS-CRITIC-PANEL-001.json`.

| Requirement ID | SDD element | STD testcase | Pytest anchor | Status |
|---|---|---|---|---|
| HISYS-FR-DARS-CP-001 | `DarsCriticPanelConfig`, config validator, `CriticAdapterRegistry` (M-CP-EXT-1), read-only `hisys run-dars-panel` CLI wrapper (M-CP-EXT-6), activation-packet-gated local-model CLI rehearsal (M-CP-LIVE-3), human-gated localhost smoke runbook (M-CP-LIVE-4), operator-facing advisory round report writer (M-CP-PROD-REPORT-1) | HISYS-T-DARS-CP-001 | `test_dars_critic_panel_config_validates_two_advisory_roles`, `test_critic_adapter_registry_rejects_duplicate_role_backend_pair`, `test_run_dars_panel_cli_persists_fixture_round_and_prints_json`, `test_run_dars_panel_cli_requires_activation_packet_for_local_model_mode`, `test_run_dars_panel_cli_rehearses_local_model_with_activation_packet`, `test_live_panel_local_smoke_runbook_requires_operator_supplied_localhost_endpoint`, `test_run_dars_panel_cli_writes_operator_report_without_live_actions` | GREEN (MB-DARS-CP-T001 + M-CP-EXT-1 + M-CP-EXT-6 + M-CP-LIVE-3 + M-CP-LIVE-4 + M-CP-LIVE-5 + M-CP-PROD-REPORT-1) |
| HISYS-FR-DARS-CP-002 | `DarsRoundPlan`, `DarsCriticTask`, edges | HISYS-T-DARS-CP-002 | `test_dars_round_plan_creates_independent_critic_tasks_before_synthesis` | GREEN (MB-DARS-CP-T001) |
| HISYS-FR-DARS-CP-003 | fixture critic executor, critique writer, `ExecutionBoundaryRecord` per-task writer (M-CP-EXT-2), injectable clock seam (M-CP-EXT-5), read-only `hisys run-dars-panel` CLI wrapper (M-CP-EXT-6), per-task distinct `started_at`/`completed_at` (M-CP-EXT-8), derived per-task `duration_ms` (M-CP-EXT-9) | HISYS-T-DARS-CP-003 | `test_dars_panel_runtime_writes_advisory_critique_artifacts`, `test_panel_runtime_writes_one_boundary_record_per_task`, `test_panel_runtime_with_injected_clock_yields_byte_identical_boundary_records`, `test_panel_runtime_rejects_naive_clock`, `test_run_dars_panel_cli_persists_fixture_round_and_prints_json`, `test_panel_runtime_records_distinct_started_and_completed_per_task`, `test_panel_runtime_records_duration_ms_per_task`, `test_panel_runtime_clamps_negative_duration_ms_to_zero` | GREEN (MB-DARS-CP-T001 + M-CP-EXT-2 + M-CP-EXT-5 + M-CP-EXT-6 + M-CP-EXT-8 + M-CP-EXT-9) |
| HISYS-FR-DARS-CP-004 | `DarsRoundTrace` writer, `ExecutionBoundaryRecord` per-task writer (M-CP-EXT-2), per-task distinct `started_at`/`completed_at` lineage (M-CP-EXT-8), derived per-task `duration_ms` lineage (M-CP-EXT-9) | HISYS-T-DARS-CP-004 | `test_dars_panel_runtime_persists_round_trace_lineage`, `test_panel_runtime_writes_one_boundary_record_per_task`, `test_panel_runtime_records_distinct_started_and_completed_per_task`, `test_panel_runtime_records_duration_ms_per_task` | GREEN (MB-DARS-CP-T001 + M-CP-EXT-2 + M-CP-EXT-8 + M-CP-EXT-9) |
| HISYS-FR-DARS-CP-005 | `DarsCritiqueSynthesis` | HISYS-T-DARS-CP-005 | `test_dars_critique_synthesis_is_advisory_and_preserves_role_provenance` | GREEN (MB-DARS-CP-T001) |
| HISYS-FR-DARS-CP-006 | execution mode policy, `ExecutionGraphPlan` ready-set determinism / synthesis-after-terminal-critics / bounded-parallel chunking (M-CP-EXT-3) | HISYS-T-DARS-CP-006 | `test_dars_round_plan_is_serial_compatible_with_bounded_parallel_policy`, `test_execution_graph_plan_ready_set_is_deterministic_and_sorted`, `test_execution_graph_plan_synthesis_waits_until_all_critics_terminal`, `test_execution_graph_plan_treats_failed_blocked_and_skipped_as_terminal`, `test_execution_graph_plan_bounded_parallel_chunks_are_deterministic`, `test_execution_graph_plan_rejects_invalid_max_parallel`, `test_execution_graph_plan_rejects_unknown_dependency_node`, `test_execution_graph_plan_rejects_dependency_cycle`, `test_execution_graph_plan_from_round_plan_preserves_critic_before_synthesis_edges`, `test_dars_panel_reexports_execution_graph_plan_for_compatibility`, `test_dars_panel_runtime_remains_serial_after_graph_integration` | GREEN (MB-DARS-CP-T001 + M-CP-EXT-3) |
| HISYS-FR-DARS-CP-007 | backend dispatch gate, `CriticAdapterRegistry` external block, typed `FixtureCriticAdapter.fixture_outcome` (M-CP-EXT-1), `ExecutionBoundaryRecord.dispatch_decision` (M-CP-EXT-2), typed adapter-missing `LookupError` -> `status=blocked` (M-CP-EXT-4), unresolved `adapter_class` marker on boundary records (M-CP-EXT-7), CLI surface preserves blocked external-style backend invariant (M-CP-EXT-6), live-panel activation packet gate (M-CP-LIVE-1), localhost-only local-model panel adapter bridge (M-CP-LIVE-2), activation-packet-gated local-model CLI rehearsal (M-CP-LIVE-3), human-gated localhost smoke runbook (M-CP-LIVE-4), remote subscription dispatch fail-closed completion guard (M-CP-LIVE-5 / M-DARS-BE-5) | HISYS-T-DARS-CP-007 | `test_dars_panel_blocks_external_backend_without_approval`, `test_critic_adapter_registry_blocks_external_without_explicit_allow_flag`, `test_fixture_critic_adapter_records_declared_outcome_without_keyword_match`, `test_panel_runtime_writes_one_boundary_record_per_task`, `test_panel_runtime_emits_blocked_when_registry_has_no_adapter_for_role`, `test_panel_runtime_marks_unresolved_adapter_class_for_disabled_critic`, `test_fixture_critic_adapter_rejects_unresolved_adapter_class`, `test_run_dars_panel_cli_blocks_external_backend_without_live_dispatch`, `test_live_panel_activation_requires_human_approval_ref`, `test_live_panel_activation_rejects_remote_scope_and_mutation_authority`, `test_live_panel_activation_rejects_raw_secret_fields`, `test_live_panel_adapter_calls_fake_local_model_and_records_model_boundary`, `test_live_panel_adapter_rejects_remote_endpoint_before_http_request`, `test_live_panel_adapter_rejects_missing_activation_approval_before_http_request`, `test_run_dars_panel_cli_requires_activation_packet_for_local_model_mode`, `test_run_dars_panel_cli_rehearses_local_model_with_activation_packet`, `test_live_panel_local_smoke_runbook_requires_operator_supplied_localhost_endpoint`, `test_live_panel_local_smoke_runbook_preserves_stop_conditions_and_boundaries`, `test_critic_adapter_registry_blocks_external_dispatch_even_with_policy_approval` | GREEN (MB-DARS-CP-T001 + M-CP-EXT-1 + M-CP-EXT-2 + M-CP-EXT-4 + M-CP-EXT-6 + M-CP-EXT-7 + M-CP-LIVE-1 + M-CP-LIVE-2 + M-CP-LIVE-3 + M-CP-LIVE-4 + M-CP-LIVE-5) |
| HISYS-FR-DARS-CP-008 | advisory/human-decision fields | HISYS-T-DARS-CP-008 | `test_dars_panel_artifacts_preserve_advisory_human_decision_separation` | GREEN (MB-DARS-CP-T001) |
| HISYS-NFR-DARS-CP-001 | failure policy and partial synthesis, adapter-outcome-driven isolation (M-CP-EXT-1), per-task boundary record on failed/blocked branches (M-CP-EXT-2), typed adapter-missing isolation (M-CP-EXT-4), CLI preserves typed advisory exit-code semantics (M-CP-EXT-6), non-negative `duration_ms` clamp preserves record stability under backward clocks (M-CP-EXT-9), local-model response failure isolation (M-CP-LIVE-2), local-model CLI fail-closed activation guard (M-CP-LIVE-3), human-gated local smoke stop conditions (M-CP-LIVE-4) | HISYS-T-DARS-CP-009 | `test_dars_panel_isolates_one_critic_failure_and_reports_partial_evidence`, `test_panel_runtime_isolates_failed_adapter_outcome_without_keyword_match`, `test_panel_runtime_writes_one_boundary_record_per_task`, `test_panel_runtime_emits_blocked_when_registry_has_no_adapter_for_role`, `test_run_dars_panel_cli_blocks_external_backend_without_live_dispatch`, `test_panel_runtime_clamps_negative_duration_ms_to_zero`, `test_live_panel_adapter_isolates_local_model_failure_as_failed_task`, `test_run_dars_panel_cli_requires_activation_packet_for_local_model_mode`, `test_live_panel_local_smoke_runbook_preserves_stop_conditions_and_boundaries`, `test_critic_adapter_registry_blocks_external_dispatch_even_with_policy_approval` | GREEN (MB-DARS-CP-T001 + M-CP-EXT-1 + M-CP-EXT-2 + M-CP-EXT-4 + M-CP-EXT-6 + M-CP-EXT-9 + M-CP-LIVE-2 + M-CP-LIVE-3 + M-CP-LIVE-4 + M-CP-LIVE-5) |
| HISYS-NFR-DARS-CP-002 | redaction/secret-scan gate, slug validation on date/request_id/task_id (M-CP-EXT-2), naive-datetime clock rejection (M-CP-EXT-5), live activation raw-secret rejection and local-model request slug validation (M-CP-LIVE-1/M-CP-LIVE-2), smoke runbook secret/no-credential guardrails (M-CP-LIVE-4) | HISYS-T-DARS-CP-010 | changed-file secret scan, `test_write_execution_boundary_record_rejects_invalid_slug`, `test_write_execution_boundary_record_rejects_traversal_in_task_id`, `test_panel_runtime_rejects_invalid_slug`, `test_panel_runtime_rejects_naive_clock`, `test_live_panel_activation_rejects_raw_secret_fields`, `test_live_panel_adapter_calls_fake_local_model_and_records_model_boundary`, `test_live_panel_local_smoke_runbook_preserves_stop_conditions_and_boundaries` | GREEN (MB-DARS-CP-T001 + M-CP-EXT-2 + M-CP-EXT-5 + M-CP-LIVE-1 + M-CP-LIVE-2 + M-CP-LIVE-4) |


## DARS-CLOSE-1/2/3 — Productization closure increments (2026-05-21)

- Scope: closed the local DARS panel productization line with three local-safe
  increments before returning to the codebase-analysis queue.
  - DARS-CLOSE-1 added the checked-in golden fixture under
    `tests/fixtures/dars_panel/golden_basic/` and the
    `test_run_dars_panel_cli_golden_fixture_writes_stable_operator_report`
    pytest anchor that pins the operator-report contract.
  - DARS-CLOSE-2 added the `hisys run-dars-panel-golden` wrapper, the
    `tests/unit/test_dars_critic_panel_cli.py::test_dars_panel_golden_run_cli_*`
    pytest anchors, and the operator runbook
    `docs/runbooks/dars-panel-fixture-operator-run.md`.
  - DARS-CLOSE-3 added `src/hisys/operations/dars_panel_readiness.py`, the
    `hisys dars-panel-readiness` CLI, and
    `tests/unit/test_dars_panel_readiness.py`. The readiness surface emits a
    locked advisory JSON/text snapshot with `schema_id`
    `hisys.dars_panel.readiness_status` and the closure pointer
    `next_queue_after_closure="MB-CODEBASE-M21-6-PREP"`.
- Completion claim boundary: the closure means
  `local_fixture_localhost_controlled_advisory_complete`. Live external
  provider execution is **not** smoked or implemented; that work remains
  outside this productization line and requires a separately approved
  governed plan.
- Boundary: no live model call, real remote provider call, credential
  lookup, raw secret capture, browser/search/tool execution, publication,
  deployment, schema/data migration against non-fixture data, force push,
  new remote configuration, or destructive operation is introduced by any
  of these increments.

## M-CP-PROD-REPORT-1 — Operator-facing advisory round report (2026-05-21)

- Scope: productized the read-only `hisys run-dars-panel` surface with an optional
  `--write-report` flag. When supplied, the command writes
  `reports/run-summaries/<YYYYMMDD>/dars-panel-round-report.json` and a Markdown
  companion report while preserving the existing stdout summary contract.
- Report semantics: the report carries `schema_id="hisys.dars_panel.round_report"`,
  request/panel/execution metadata, task statuses, critique/synthesis/trace and
  boundary refs, plus explicit advisory safety fields: `advisory_only=true`,
  `requires_human_review=true`, `external_call_made=false` for fixture mode,
  `mutation_performed=false`, `publication_performed=false`, and
  `live_external_action_authorized=false`.
- Test anchor: `tests/unit/test_dars_critic_panel_cli.py::test_run_dars_panel_cli_writes_operator_report_without_live_actions`
  observes RED on the missing `--write-report` CLI flag and GREEN after the JSON
  and Markdown report writer are connected.
- Boundary: no live model call, no remote/external API, no credential lookup, no
  browser/search/tool authorization, no publication/deployment, no repository
  mutation beyond local runtime report files for the selected Hisys instance, and
  no remote push authority is introduced.

## M-CP-LIVE-5 / M-DARS-BE-5 — Remote subscription dispatch fail-closed completion guard (2026-05-21)

- Scope: closed the DARS critic-panel remote-dispatch boundary by making `CriticAdapterRegistry` reject external adapters even when `external_dispatch_allowed=True` and an `approval_ref` is supplied. These fields are now explicit precondition markers only; they do not authorize remote subscription dispatch.
- Test anchor: `tests/unit/test_dars_critic_panel_adapters.py::test_critic_adapter_registry_blocks_external_dispatch_even_with_policy_approval` observes the fail-closed behavior with an `external-claude-subscription` adapter.
- Relationship to M-DARS-BE-5: a valid Codex/Claude remote subscription policy packet remains schema/control preparation only. The panel runtime does not consume that packet to cross a remote provider boundary.
- Boundary semantics: no HTTP request, remote API call, credential lookup, provider account use, mutation, publication, or deployment is introduced. A later remote subscription implementation requires a new controlled plan, RED tests, decision packet, and explicit human approval.

## M-CP-LIVE-4 — Human-gated localhost smoke runbook (2026-05-20)

- Scope: added `docs/runbooks/dars-live-panel-localhost-smoke.md` and
  `tests/unit/test_dars_critic_panel_live_runbook.py` to document and verify the
  operator-gated local smoke procedure after fake-server adapter and CLI
  rehearsal gates.
- Operator boundary: the runbook requires an already-running localhost-only model
  endpoint supplied by the operator through `HISYS_DARS_LOCAL_ENDPOINT`. It does
  not install, start, download, configure, or select a model runner.
- Command boundary: the copy-paste command uses `hisys run-dars-panel` with
  `--local-model-endpoint`, `--local-model`, and `--activation-packet`, and
  writes only under the chosen `$HISYS_INSTANCE` runtime root.
- Stop conditions: non-loopback endpoint, missing activation packet, credential
  requirement, tool/search/browser permission, mutation request, failed secret
  scan, human uncertainty, remote API request, raw secret/Authorization header,
  publication, deployment, or push request.
- Boundary semantics: the documented acceptable smoke requires
  `endpoint_scope=localhost_only`, `model_boundary_crossed=true`,
  `local_model_call_made=true`, `external_call_made=false`,
  `mutation_performed=false`, `publication_performed=false`, and
  `allowed_actions=advisory_only` in the reviewed output/boundary records.
- This increment is documentation/tests only. It performs no real local model
  smoke, no HTTP request, no credential lookup, no remote API call, no runtime
  mutation, no publication/deployment, and no remote push.
- Next queued increment: M21.5 codebase regression benchmark fixtures, returning
  to the codebase-analysis queue after local-DARS safety gates are established.

## M-CP-LIVE-3 — CLI activation rehearsal (2026-05-20)

- Scope: extended `hisys run-dars-panel` with an explicit local-model
  rehearsal surface: `--local-model-endpoint`, `--local-model`, and
  `--activation-packet`. Existing fixture-local mode remains unchanged when no
  local-model endpoint is supplied.
- Fail-closed gate: local-model mode exits with code `2` and reports
  `--activation-packet is required` before any socket opens when the endpoint is
  supplied without an activation packet.
- Approved rehearsal path: with a valid M-CP-LIVE-1 activation packet, the CLI
  routes configured critics through `LocalModelPanelAdapter` and reports
  `execution_mode="local_model_rehearsal"`, `model_boundary_crossed=true`,
  `local_model_call_made=true`, `external_call_made=false`,
  `mutation_performed=false`, `publication_performed=false`, and
  `allowed_actions="advisory_only"`.
- Fixture boundary: tests use only `tests/unit/helpers/fake_openai_server.py`
  bound to `127.0.0.1` on an ephemeral port. No real local model runner,
  credential lookup, Authorization header, remote endpoint, publication,
  deployment, or external API call is introduced.
- Example config: added
  `docs/examples/dars/live-panel-localhost-config.example.json` with only
  localhost-rehearsal-ready placeholders and no secrets.
- Tests: `tests/unit/test_dars_critic_panel_cli.py` covers the missing
  activation fail-closed path and an activation-packet-approved localhost fake
  server rehearsal.
- Next queued increment: M-CP-LIVE-4 local smoke runbook. That work remains a
  runbook/approval increment; any real local model smoke requires operator
  supplied localhost endpoint and explicit human approval.

## M-CP-LIVE-2 — Fake-server local model panel adapter bridge (2026-05-20)

- Scope: added `LocalModelPanelAdapter`, `LocalModelCriticRequest`, and
  `LocalModelCriticResult` in `src/hisys/agents/dars_panel_live_adapter.py`.
  The bridge routes one critic task to an OpenAI-compatible endpoint only after a
  valid M-CP-LIVE-1 activation packet and only when the endpoint classifies as
  loopback/localhost.
- Fake-server boundary: tests use `tests/unit/helpers/fake_openai_server.py`,
  which binds to `127.0.0.1` on an ephemeral port. This increment performs only
  that fixture loopback HTTP call. It does not contact a real model runner,
  external API, remote endpoint, or credential source.
- Request payload: each call includes advisory-only instructions, no browser,
  no search, no tool authorization, no mutation/publication authority, plus the
  critic role, candidate ref, evidence refs, rubric ref, and critique dimensions.
- Boundary record: each task writes
  `runtime-boundary/dars-panel-live/<YYYYMMDD>/<REQUEST_ID>/<TASK_ID>.json`
  with `approval_ref`, `adapter_class="local_model"`,
  `endpoint_scope="localhost_only"`, `model_boundary_crossed=true`,
  `local_model_call_made=true`, `external_call_made=false`,
  `mutation_performed=false`, `allowed_actions="advisory_only"`, and
  `duration_ms`.
- Rejections/failure isolation: remote endpoint and invalid activation packet
  cases fail before any HTTP request; local non-2xx/malformed/missing response
  failures become task-level `failed` results with no external call or mutation.
- Tests: `tests/unit/test_dars_critic_panel_live_adapter.py` covers successful
  fake-server dispatch/boundary record, remote endpoint pre-HTTP rejection,
  missing activation approval pre-HTTP rejection, and local model failure
  isolation.
- Next queued increment: M-CP-LIVE-3 CLI activation rehearsal. The CLI must
  remain disabled/fail-closed unless an activation packet is supplied and must
  still use fake/localhost-only rehearsal before any real local model smoke.

## M-CP-LIVE-1 — Live panel activation packet (2026-05-20)

- Scope: added `LiveDarsPanelActivationPacket` and
  `validate_live_dars_panel_activation_packet` as the first controlled live-panel
  gate. The packet requires `approval_ref`, `operator_id`,
  `approved_endpoint_scope="localhost_only"`, `allowed_actions="advisory_only"`,
  `human_approved=true`, `expires_at`, a requested backend id, and
  `requested_adapter_class="local_model"`.
- Boundary semantics: this increment authorizes only the declarative activation
  packet. It records that a future localhost model boundary may be authorized by
  a human packet, while preserving `live_external_action_authorized=false`,
  `mutation_authorized=false`, `external_call_made=false`, and
  `requires_human_review=true`. It performs no model call, network call,
  credential lookup, publication, remote push, or runtime mutation.
- Rejections: missing approval, non-local endpoint scope, non-advisory actions,
  non-local adapter class, missing human approval, and raw secret/credential-like
  fields are reported as validation issues before any adapter can run.
- Tests: `tests/unit/test_dars_critic_panel_live_config.py` covers missing
  approval, valid localhost advisory packets, remote/mutation rejection,
  raw-secret rejection, and extra secret-field Pydantic rejection.
- Next queued increment: M-CP-LIVE-2 fake-server local model panel adapter
  bridge. That future work must still start with RED and must use only
  loopback/fake-server tests before any real local model smoke.

## M-CP-EXT-9 — Per-task duration_ms boundary timing (2026-05-20)

- Scope: closed the M-CP-EXT-8 open item (b) by adding a derived integer
  `duration_ms` field to every persisted `ExecutionBoundaryRecord`. The unit
  is milliseconds. The value is computed from the timezone-aware
  `task_started` and `task_completed` clock readings before formatting, so
  sub-second intervals are preserved even though `started_at` and
  `completed_at` remain second-truncated UTC `...Z` strings.
- Runtime change: `DarsCriticPanelRuntime.run_round` now binds each
  per-task clock read to a `datetime` (`task_started = self._clock()`,
  `task_completed = self._clock()`), formats them with
  `_format_iso_timestamp`, and derives
  `task_duration_ms = max(0, int((task_completed.astimezone(timezone.utc) -
  task_started.astimezone(timezone.utc)).total_seconds() * 1000))`. The
  derived integer is threaded into `ExecutionBoundaryRecord(...)` via the
  new `duration_ms` keyword argument.
- Schema change: `ExecutionBoundaryRecord.duration_ms: int` is added
  immediately after `completed_at: str` with a default of `0`. Persisted
  JSON now carries a new top-level `duration_ms` integer field per
  boundary record. No other field is renamed, removed, or reordered. No
  CLI flag, config schema, or `hisys run-dars-panel` output contract is
  changed by this increment.
- Non-negative invariant: a backward-moving clock is clamped to `0`
  rather than producing a negative `duration_ms`. This preserves advisory
  record stability and is characterized by
  `test_panel_runtime_clamps_negative_duration_ms_to_zero`.
- Serial-execution and safety envelope preserved: the runtime continues
  to iterate `zip(plan.critic_tasks, panel_config.critics, strict=True)`
  serially; `external_call_made`, `mutation_performed`,
  `action_authorized`, `advisory_only`, and `requires_human_review`
  invariants on the record remain locked exactly as before.
- New tests:
  `test_panel_runtime_records_duration_ms_per_task` (injects a counter
  clock that returns four monotonically increasing offsets per call and
  asserts `[record["duration_ms"] for record in boundary_records] == [250, 750]`
  and that every persisted value is an `int`);
  `test_panel_runtime_clamps_negative_duration_ms_to_zero` (injects a
  backward-moving clock and asserts the persisted `duration_ms` is `0`).
- Existing tests preserved:
  `tests/unit/test_dars_critic_panel_runtime.py` (9 passed, unchanged),
  `tests/unit/test_dars_critic_panel_adapters.py` (5 passed, unchanged),
  `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`
  (now 22 passed, +2 new),
  `tests/unit/test_dars_critic_panel_execution_graph_plan.py`
  (10 passed, unchanged),
  `tests/unit/test_dars_critic_panel_cli.py` (2 passed, unchanged).
- Boundary: no live DARS dispatch, no credential resolution, no remote
  push, no external call, no mutation, no clock seam change, no CLI
  surface change, no parallel execution activation. The persisted record
  schema field set expands by exactly one derived advisory integer.
  Validation commands recorded in the ralph.md Reflection Log entry for
  M-CP-EXT-9.

## M-CP-EXT-8 — Per-task distinct started_at/completed_at (2026-05-20)

- Scope: closed the M-CP-EXT-5 open item (a) by moving the M-CP-EXT-5
  clock-seam read from a single pre-loop call to two per-task calls inside
  `DarsCriticPanelRuntime.run_round`. Each persisted `ExecutionBoundaryRecord`
  now carries a distinct `started_at` and `completed_at` value drawn from
  `self._clock` — naturally increasing under the default wall-clock lambda,
  strictly distinct under an injected counter clock.
- Runtime change: `run_round` no longer reads the round-level
  `timestamp = _format_iso_timestamp(self._clock())` before the critic loop.
  Inside the `for plan_task, critic in zip(...)` loop body the runtime reads
  `task_started_at = _format_iso_timestamp(self._clock())` first, then
  `task_completed_at = _format_iso_timestamp(self._clock())` immediately
  before constructing the `ExecutionBoundaryRecord`, and threads those values
  into the record's `started_at` / `completed_at` keyword arguments.
- Seam reuse: no constructor signature change, no new clock parameter, no new
  schema field. The naive-datetime rejection invariant from M-CP-EXT-5
  remains because both per-task reads still flow through
  `_format_iso_timestamp`. Tests that pin byte-identical boundary records
  under a constant clock continue to pass because a constant clock returns
  the same value on consecutive reads.
- Serial-execution invariant preserved: the runtime continues to iterate
  `zip(plan.critic_tasks, panel_config.critics, strict=True)` serially. No
  worker, thread, async task, or subprocess is spawned by this increment.
- New tests:
  `test_panel_runtime_records_distinct_started_and_completed_per_task` (uses
  an injected counter clock that advances by one second per call; asserts
  `started_at != completed_at` per persisted boundary record and that
  consecutive tasks observe distinct `started_at` / `completed_at` values).
- Existing tests preserved:
  `tests/unit/test_dars_critic_panel_runtime.py` (9 passed, unchanged),
  `tests/unit/test_dars_critic_panel_adapters.py` (5 passed, unchanged),
  `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`
  (now 20 passed, +1 new),
  `tests/unit/test_dars_critic_panel_execution_graph_plan.py`
  (10 passed, unchanged),
  `tests/unit/test_dars_critic_panel_cli.py` (2 passed, unchanged).
- Boundary: no live DARS dispatch, no credential resolution, no remote push,
  no external call, no mutation, no clock seam change, no CLI surface change,
  no schema field added or removed. Validation commands recorded in the
  ralph.md Reflection Log entry for M-CP-EXT-8.

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
