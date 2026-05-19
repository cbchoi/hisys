---
doc_id: HISYS-DARS-CP-RTM-001
title: DARS Critic Panel Runtime Traceability Matrix
version: 0.2.0
document_status: draft-for-tdd
created: 2026-05-19
updated: 2026-05-19
---

# DARS Critic Panel Runtime Traceability Matrix

Source Hisys packet: `/tmp/hisys-dars-critic-panel-instance/runtime-boundary/agent-workflows/20260519/SPEC-DARS-CRITIC-PANEL-001.json`.

| Requirement ID | SDD element | STD testcase | Pytest anchor | Status |
|---|---|---|---|---|
| HISYS-FR-DARS-CP-001 | `DarsCriticPanelConfig`, config validator, `CriticAdapterRegistry` (M-CP-EXT-1) | HISYS-T-DARS-CP-001 | `test_dars_critic_panel_config_validates_two_advisory_roles`, `test_critic_adapter_registry_rejects_duplicate_role_backend_pair` | GREEN (MB-DARS-CP-T001 + M-CP-EXT-1) |
| HISYS-FR-DARS-CP-002 | `DarsRoundPlan`, `DarsCriticTask`, edges | HISYS-T-DARS-CP-002 | `test_dars_round_plan_creates_independent_critic_tasks_before_synthesis` | GREEN (MB-DARS-CP-T001) |
| HISYS-FR-DARS-CP-003 | fixture critic executor, critique writer | HISYS-T-DARS-CP-003 | `test_dars_panel_runtime_writes_advisory_critique_artifacts` | GREEN (MB-DARS-CP-T001) |
| HISYS-FR-DARS-CP-004 | `DarsRoundTrace` writer | HISYS-T-DARS-CP-004 | `test_dars_panel_runtime_persists_round_trace_lineage` | GREEN (MB-DARS-CP-T001) |
| HISYS-FR-DARS-CP-005 | `DarsCritiqueSynthesis` | HISYS-T-DARS-CP-005 | `test_dars_critique_synthesis_is_advisory_and_preserves_role_provenance` | GREEN (MB-DARS-CP-T001) |
| HISYS-FR-DARS-CP-006 | execution mode policy | HISYS-T-DARS-CP-006 | `test_dars_round_plan_is_serial_compatible_with_bounded_parallel_policy` | GREEN (MB-DARS-CP-T001) |
| HISYS-FR-DARS-CP-007 | backend dispatch gate, `CriticAdapterRegistry` external block, typed `FixtureCriticAdapter.fixture_outcome` (M-CP-EXT-1) | HISYS-T-DARS-CP-007 | `test_dars_panel_blocks_external_backend_without_approval`, `test_critic_adapter_registry_blocks_external_without_explicit_allow_flag`, `test_fixture_critic_adapter_records_declared_outcome_without_keyword_match` | GREEN (MB-DARS-CP-T001 + M-CP-EXT-1) |
| HISYS-FR-DARS-CP-008 | advisory/human-decision fields | HISYS-T-DARS-CP-008 | `test_dars_panel_artifacts_preserve_advisory_human_decision_separation` | GREEN (MB-DARS-CP-T001) |
| HISYS-NFR-DARS-CP-001 | failure policy and partial synthesis, adapter-outcome-driven isolation (M-CP-EXT-1) | HISYS-T-DARS-CP-009 | `test_dars_panel_isolates_one_critic_failure_and_reports_partial_evidence`, `test_panel_runtime_isolates_failed_adapter_outcome_without_keyword_match` | GREEN (MB-DARS-CP-T001 + M-CP-EXT-1) |
| HISYS-NFR-DARS-CP-002 | redaction/secret-scan gate | HISYS-T-DARS-CP-010 | changed-file secret scan | GREEN (MB-DARS-CP-T001: `scripts/scan_secrets.py` hit_count=0 over 477 files) |

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
