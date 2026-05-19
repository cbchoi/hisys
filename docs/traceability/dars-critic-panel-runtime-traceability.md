---
doc_id: HISYS-DARS-CP-RTM-001
title: DARS Critic Panel Runtime Traceability Matrix
version: 0.1.0
document_status: draft-for-tdd
created: 2026-05-19
updated: 2026-05-19
---

# DARS Critic Panel Runtime Traceability Matrix

Source Hisys packet: `/tmp/hisys-dars-critic-panel-instance/runtime-boundary/agent-workflows/20260519/SPEC-DARS-CRITIC-PANEL-001.json`.

| Requirement ID | SDD element | STD testcase | Pytest anchor | Status |
|---|---|---|---|---|
| HISYS-FR-DARS-CP-001 | `DarsCriticPanelConfig`, config validator | HISYS-T-DARS-CP-001 | `test_dars_critic_panel_config_validates_two_advisory_roles` | test skeleton RED |
| HISYS-FR-DARS-CP-002 | `DarsRoundPlan`, `DarsCriticTask`, edges | HISYS-T-DARS-CP-002 | `test_dars_round_plan_creates_independent_critic_tasks_before_synthesis` | test skeleton RED |
| HISYS-FR-DARS-CP-003 | fixture critic executor, critique writer | HISYS-T-DARS-CP-003 | `test_dars_panel_runtime_writes_advisory_critique_artifacts` | test skeleton RED |
| HISYS-FR-DARS-CP-004 | `DarsRoundTrace` writer | HISYS-T-DARS-CP-004 | `test_dars_panel_runtime_persists_round_trace_lineage` | test skeleton RED |
| HISYS-FR-DARS-CP-005 | `DarsCritiqueSynthesis` | HISYS-T-DARS-CP-005 | `test_dars_critique_synthesis_is_advisory_and_preserves_role_provenance` | test skeleton RED |
| HISYS-FR-DARS-CP-006 | execution mode policy | HISYS-T-DARS-CP-006 | `test_dars_round_plan_is_serial_compatible_with_bounded_parallel_policy` | test skeleton RED |
| HISYS-FR-DARS-CP-007 | backend dispatch gate | HISYS-T-DARS-CP-007 | `test_dars_panel_blocks_external_backend_without_approval` | test skeleton RED |
| HISYS-FR-DARS-CP-008 | advisory/human-decision fields | HISYS-T-DARS-CP-008 | `test_dars_panel_artifacts_preserve_advisory_human_decision_separation` | test skeleton RED |
| HISYS-NFR-DARS-CP-001 | failure policy and partial synthesis | HISYS-T-DARS-CP-009 | `test_dars_panel_isolates_one_critic_failure_and_reports_partial_evidence` | test skeleton RED |
| HISYS-NFR-DARS-CP-002 | redaction/secret-scan gate | HISYS-T-DARS-CP-010 | changed-file secret scan | pending verification |

## Existing baseline links

- Parent SRS: `HISYS-FR-AGT-001..005`, `HISYS-FR-DOM-003..004`, `HISYS-NFR-REL-001`, `HISYS-NFR-SEC-001`, `HISYS-NFR-SEC-004`.
- Existing DARS plan: `docs/plans/dars-integration-design.md`.
- Existing DARS contracts: `docs/contracts/dars-data-format.md`, `docs/contracts/dars-evaluation-rubrics.md`, `docs/contracts/dars-prompt-registry.md`.

## TDD verdict

`YES_WITH_CONTROLS`: the controlled package is TDD-ready for a fixture/local-only DARS critic panel runtime increment. It is not approval to enable live DARS dispatch, external agent calls, mutation, publication, or autonomous decision authority. The invariant is `advisory_only` critic output until separate Hisys governance and human approval convert evidence into a downstream decision.
