---
doc_id: HISYS-DARS-CP-STD-001
title: DARS Critic Panel Runtime Software Test Description
version: 0.1.0
document_status: draft-for-tdd
created: 2026-05-19
updated: 2026-05-19
requirements_source: docs/requirements/dars-critic-panel-runtime-requirements.md
design_source: docs/design/dars-critic-panel-runtime-sdd.md
---

# DARS Critic Panel Runtime Software Test Description

## 1. Test strategy

The first implementation increment shall use strict TDD. Tests are written before production runtime code. Initial tests intentionally fail because `hisys.agents.dars_panel` does not yet exist. All tests use local tmp-path fixtures and make no live external calls.

## 2. Test cases

| Test ID | Title | Objective | Primary requirements | Pytest anchor |
|---|---|---|---|---|
| HISYS-T-DARS-CP-001 | Critic panel config validation | Validate role IDs, output contract, duplicate detection, and advisory-only defaults. | HISYS-FR-DARS-CP-001, HISYS-FR-AGT-003 | `test_dars_critic_panel_config_validates_two_advisory_roles` |
| HISYS-T-DARS-CP-002 | Round plan construction | Convert candidate/evidence/rubric refs into critic tasks plus synthesis edge. | HISYS-FR-DARS-CP-002, HISYS-FR-DOM-003 | `test_dars_round_plan_creates_independent_critic_tasks_before_synthesis` |
| HISYS-T-DARS-CP-003 | Fixture critic execution | Execute two local fixture critics and write advisory critique artifacts. | HISYS-FR-DARS-CP-003, HISYS-FR-AGT-001..003 | `test_dars_panel_runtime_writes_advisory_critique_artifacts` |
| HISYS-T-DARS-CP-004 | Round trace persistence | Persist candidate-to-task-to-critique-to-synthesis lineage. | HISYS-FR-DARS-CP-004, HISYS-T-024 | `test_dars_panel_runtime_persists_round_trace_lineage` |
| HISYS-T-DARS-CP-005 | Critique synthesis | Deduplicate findings and preserve critic role provenance without approval authority. | HISYS-FR-DARS-CP-005, HISYS-FR-DARS-CP-008 | `test_dars_critique_synthesis_is_advisory_and_preserves_role_provenance` |
| HISYS-T-DARS-CP-006 | Serial-compatible execution policy | Ensure round plan carries max-parallel policy while serial execution remains valid. | HISYS-FR-DARS-CP-006 | `test_dars_round_plan_is_serial_compatible_with_bounded_parallel_policy` |
| HISYS-T-DARS-CP-007 | External backend blocked by default | Block disabled/external critic backend without approval and record no external call. | HISYS-FR-DARS-CP-007, HISYS-NFR-SEC-004 | `test_dars_panel_blocks_external_backend_without_approval` |
| HISYS-T-DARS-CP-008 | Advisory-human decision separation | Ensure artifacts require human review and never mark approval/action authority. | HISYS-FR-DARS-CP-008, HISYS-FR-AGT-003 | `test_dars_panel_artifacts_preserve_advisory_human_decision_separation` |
| HISYS-T-DARS-CP-009 | Critic failure isolation | One failed critic does not erase completed critic evidence; synthesis requests more evidence. | HISYS-NFR-DARS-CP-001, HISYS-NFR-REL-001 | `test_dars_panel_isolates_one_critic_failure_and_reports_partial_evidence` |
| HISYS-T-DARS-CP-010 | Secret/redaction protection | New panel fixtures/artifacts contain no credential values. | HISYS-NFR-DARS-CP-002, HISYS-NFR-SEC-001 | secret scan command over changed files |

## 3. RED baseline

Run before production implementation:

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_runtime.py -q
```

Expected RED result for this increment: collection/import failure or missing-symbol failure for `hisys.agents.dars_panel`, proving the panel runtime has not been implemented before the tests.

## 4. GREEN acceptance for future implementation

The future implementation increment shall make the same tests pass without enabling external calls, writing outside the tmp instance root, or granting DARS approval authority. All emitted critique artifacts shall preserve `advisory_only` behavior.
