---
doc_id: HISYS-DARS-CP-SDD-001
title: DARS Critic Panel Runtime Software Design Description
version: 0.1.0
document_status: draft-for-tdd
created: 2026-05-19
updated: 2026-05-19
requirements_source: docs/requirements/dars-critic-panel-runtime-requirements.md
---

# DARS Critic Panel Runtime Software Design Description

## 1. Design intent

DARS critic panel runtime turns a single critique call into a governed multi-agent review graph. Hisys owns request validation, planning, execution boundaries, artifact persistence, synthesis, and decision gating. Critic agents only produce advisory critique artifacts.

## 2. Component model

```text
Candidate artifact + evidence refs + rubric ref
        |
        v
DarsCriticPanelRuntime
  - validate DarsCriticPanelConfig
  - build DarsRoundPlan
  - evaluate governance policy
  - execute critic tasks through local fixture/loopback adapters first
  - persist DarsCritiqueRecord artifacts
  - persist DarsRoundTrace
  - run DarsCritiqueSynthesizer
        |
        v
DarsCritiqueSynthesis / HumanReviewPacket input
```

## 3. Planned modules

| Module | Responsibility | Requirement trace |
|---|---|---|
| `hisys.agents.dars_panel.DarsCriticPanelConfig` | Panel roles, backend refs, rubric refs, contracts, and governance flags. | HISYS-FR-DARS-CP-001 |
| `hisys.agents.dars_panel.DarsRoundPlan` | Round-level execution graph: critic tasks plus synthesis dependency edge. | HISYS-FR-DARS-CP-002, HISYS-FR-DARS-CP-006 |
| `hisys.agents.dars_panel.DarsCriticTask` | One critic role invocation with candidate/evidence/rubric refs and expected `DarsCritiqueRecord`. | HISYS-FR-DARS-CP-002..003 |
| `hisys.agents.dars_panel.DarsRoundTrace` | Persisted lineage record for candidate, task refs, critique refs, synthesis ref, and stop condition. | HISYS-FR-DARS-CP-004 |
| `hisys.agents.dars_panel.DarsCritiqueSynthesis` | Deterministic merge of findings with critic provenance and advisory disposition. | HISYS-FR-DARS-CP-005, HISYS-FR-DARS-CP-008 |
| `hisys.agents.dars_panel.DarsCriticPanelRuntime` | Runtime façade for validate -> plan -> execute -> synthesize -> persist. | HISYS-FR-DARS-CP-001..008 |

## 4. Data contracts

### 4.1 `DarsCriticPanelConfig`

Required fields:

- `panel_id`
- `round_policy.max_rounds`
- `round_policy.max_parallel_critics`
- `critics[]`
- `default_output_contract="DarsCritiqueRecord"`
- `advisory_only=true`

Each critic requires:

- `critic_id`
- `critic_role`: `logical_devil | evidence_governance_devil | safety_privacy_devil | process_traceability_devil | domain_devil`
- `backend_id`
- `rubric_ref`
- `critique_dimensions[]`
- `enabled`
- `external_call_allowed=false` by default
- `mutation_allowed=false`
- `output_contract="DarsCritiqueRecord"`

### 4.2 `DarsRoundPlan`

Required fields:

- `round_id`
- `candidate_ref`
- `evidence_refs[]`
- `critic_tasks[]`
- `synthesis_task_ref`
- `edges[]`
- `max_parallel_critics`
- `failure_policy`
- `traceability_ids[]`

### 4.3 `DarsRoundTrace`

Required fields:

- `round_id`
- `candidate_ref`
- `critic_task_refs[]`
- `critique_refs[]`
- `failed_task_refs[]`
- `synthesis_ref`
- `unresolved_findings[]`
- `stop_condition_met`
- `advisory_only=true`
- `requires_human_review=true`

## 5. Execution design

The first implementation uses a serial executor over the same plan shape that later bounded-parallel execution will consume. Independent critic tasks have no data dependency between each other; all feed the synthesis task. Failure policy defaults to `continue_collect_errors` for advisory panels so completed critiques are not discarded.

## 6. Governance design

- Critic tasks cannot approve, publish, deliver, mutate, or execute software triggers.
- External backends are disabled by default and require explicit approval refs before dispatch.
- `external_call_allowed` records policy permission; `external_call_made` records actual behavior.
- All output remains advisory evidence until Hisys governance and human review convert it into an approved downstream decision.

## 7. SRS-to-design/test traceability

| Requirement | Design elements | Primary test |
|---|---|---|
| HISYS-FR-DARS-CP-001 | `DarsCriticPanelConfig`, config validator | HISYS-T-DARS-CP-001 |
| HISYS-FR-DARS-CP-002 | `DarsRoundPlan`, `DarsCriticTask`, dependency edges | HISYS-T-DARS-CP-002 |
| HISYS-FR-DARS-CP-003 | fixture/loopback critic executor, `DarsCritiqueRecord` persistence | HISYS-T-DARS-CP-003 |
| HISYS-FR-DARS-CP-004 | `DarsRoundTrace` writer | HISYS-T-DARS-CP-004 |
| HISYS-FR-DARS-CP-005 | `DarsCritiqueSynthesis`, deduplication by finding ID and role provenance | HISYS-T-DARS-CP-005 |
| HISYS-FR-DARS-CP-006 | execution mode abstraction over serial and bounded-parallel policies | HISYS-T-DARS-CP-006 |
| HISYS-FR-DARS-CP-007 | backend dispatch gate and blocked task result | HISYS-T-DARS-CP-007 |
| HISYS-FR-DARS-CP-008 | advisory-only fields in all panel artifacts | HISYS-T-DARS-CP-008 |
| HISYS-NFR-DARS-CP-001 | failure policy and partial synthesis path | HISYS-T-DARS-CP-009 |
| HISYS-NFR-DARS-CP-002 | redaction/secret-scan gate | HISYS-T-DARS-CP-010 |
