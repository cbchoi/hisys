---
doc_id: HISYS-DARS-CP-SDD-001
title: DARS Critic Panel Runtime Software Design Description
version: 0.2.0
document_status: draft-for-tdd
created: 2026-05-19
updated: 2026-05-23
requirements_source: docs/requirements/dars-critic-panel-runtime-requirements.md
release_plan: docs/plans/dars-panel-live-provider-unattended-release-final-plan.md
---

# DARS Critic Panel Runtime Software Design Description

## 1. Design intent

DARS critic panel runtime turns a single critique call into a governed multi-agent review graph. Hisys owns request validation, planning, execution boundaries, artifact persistence, synthesis, and decision gating. Critic agents only produce advisory critique artifacts.

The live-provider release line extends the existing local fixture and localhost rehearsal design with layered gates. Provider policy, credential-reference validation, fake/injected transports, live-provider adapters, unattended operation controls, status/rollback surfaces, and release evidence are separate design layers. This prevents a configuration change from implicitly becoming a live call, unattended action, or release claim.

## 2. Component model

```text
Candidate artifact + evidence refs + rubric ref
        |
        v
DarsCriticPanelRuntime
  - validate DarsCriticPanelConfig
  - build DarsRoundPlan / ExecutionGraphPlan
  - evaluate governance policy
  - execute critic tasks through fixture, localhost, or governed provider transports
  - persist DarsCritiqueRecord artifacts
  - persist per-task and panel boundary records
  - persist DarsRoundTrace
  - run DarsCritiqueSynthesizer
        |
        v
DarsCritiqueSynthesis / HumanReviewPacket input
```

Live-provider extension:

```text
LiveProviderPolicyPacket + BackendActivationPacket + DecisionPacket
        |
        v
DarsLiveProviderTransportRequest
        |
        +--> FakeInjectedProviderTransport     # unit tests and dry runs
        +--> CodexCliSubscriptionTransport     # governed CLI transport option
        +--> RealProviderAdapter               # disabled until policy/approval/credential-ref gates pass
        |
        v
LiveProviderBoundaryRecord + DarsCritiqueRecord
        |
        v
PanelLiveProviderBoundaryRecord
```

Bounded unattended operation extension:

```text
StandingApprovalPolicy
  + provider policy refs
  + request-class allowlist
  + budget/rate caps
  + kill switch
  + audit retention
        |
        v
DarsUnattendedAdvisoryRunner
        |
        v
Run audit ledger + status surface + post-run human review packet
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
| `hisys.agents.dars_live_provider_policy` | Provider/model allowlist, credential-reference, budget/rate, approval, and advisory-only validation. | HISYS-FR-DARS-CP-009, HISYS-NFR-DARS-CP-002 |
| `hisys.agents.dars_live_provider_transport` | Transport request/result contract and fake/injected executor seam for tests. | HISYS-FR-DARS-CP-010 |
| `hisys.agents.dars_live_provider_adapter` | Fail-closed real provider adapter entry point; no credential resolution until all gates pass. | HISYS-FR-DARS-CP-010..012 |
| `hisys.operations.dars_unattended_runner` | Bounded standing-approval runner with audit ledger and circuit breakers. | HISYS-FR-DARS-CP-013 |
| `hisys.operations.dars_live_status` | Status, kill-switch, latest evidence, and rollback-readiness surface. | HISYS-FR-DARS-CP-014 |
| `docs/release/*` | Release candidate checklist, release notes, decision packet, and post-release evidence. | HISYS-FR-DARS-CP-015 |

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

### 4.4 `LiveProviderPolicyPacket`

Required fields:

- `provider_id`
- `provider_kind`
- `model_id`
- `credential_ref`
- `credential_ref_kind`
- `endpoint_ref`
- `allowed_actions="advisory_only"`
- `external_call_allowed=true`
- `mutation_allowed=false`
- `publication_allowed=false`
- `requires_human_review=true`
- `max_prompt_bytes`
- `max_output_bytes`
- `rate_limit_per_minute`
- `cost_budget_ref`
- `approval_ref`
- `expires_at`

The packet stores references only. Raw secrets, provider tokens, authorization headers, and secret-looking values are invalid.

### 4.5 `DarsLiveProviderTransportRequest` / `Result`

The request carries request ID, source execution ID, backend ID, provider/model refs, approval refs, redacted prompt metadata, max output/cost settings, and boundary flags. The result carries status, critique text or failure code, provider/model refs, cost/token/latency metadata if available, and safety flags. Tests use fake/injected transports only.

### 4.6 `StandingApprovalPolicy`

The policy carries a finite approval ID, operator, validity window, provider policy refs, request-class allowlist, max runs, max critics, budget/rate caps, kill-switch ref, audit-retention ref, alert-on-failure ref, and `requires_post_run_human_review=true`.

## 5. Execution design

The first implementation uses a serial executor over the same plan shape that later bounded-parallel execution will consume. Independent critic tasks have no data dependency between each other; all feed the synthesis task. Failure policy defaults to `continue_collect_errors` for advisory panels so completed critiques are not discarded.

Live-provider execution is a transport substitution, not a scheduler rewrite. The panel runtime continues to own task planning, boundary refs, and synthesis. The provider transport owns one critic boundary crossing after policy and approval validation. Panel-level live smoke writes a summary boundary record that links per-critic boundary refs.

Unattended operation is not a stronger critic authority. It is only a bounded runner that invokes already-governed advisory requests within a finite standing approval policy and records audit evidence for post-run human review.

## 6. Governance design

- Critic tasks cannot approve, publish, deliver, mutate, or execute software triggers.
- External backends are disabled by default and require explicit approval refs before dispatch.
- `external_call_allowed` records policy permission; `external_call_made` records actual behavior.
- Credential references may be recorded; raw credentials must not be persisted.
- Live provider smoke, unattended canary, release candidate, and release execution require separate decision packets.
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
| HISYS-FR-DARS-CP-009 | `LiveProviderPolicyPacket`, raw-secret rejection, bounds validation | HISYS-T-DARS-CP-011 |
| HISYS-FR-DARS-CP-010 | `DarsLiveProviderTransportRequest`, fake transport, fail-closed adapter | HISYS-T-DARS-CP-012 |
| HISYS-FR-DARS-CP-011 | single-critic live smoke runbook and boundary record | HISYS-T-DARS-CP-013 |
| HISYS-FR-DARS-CP-012 | panel-level live provider boundary and partial failure isolation | HISYS-T-DARS-CP-014 |
| HISYS-FR-DARS-CP-013 | `StandingApprovalPolicy`, `DarsUnattendedAdvisoryRunner`, audit ledger | HISYS-T-DARS-CP-015 |
| HISYS-FR-DARS-CP-014 | `dars_live_status`, kill-switch and rollback surfaces | HISYS-T-DARS-CP-016 |
| HISYS-FR-DARS-CP-015 | release checklist, notes, decision packet, post-release smoke | HISYS-T-DARS-CP-017 |
| HISYS-NFR-DARS-CP-001 | failure policy and partial synthesis path | HISYS-T-DARS-CP-009, HISYS-T-DARS-CP-014 |
| HISYS-NFR-DARS-CP-002 | redaction, policy raw-secret rejection, secret-scan gate | HISYS-T-DARS-CP-010, HISYS-T-DARS-CP-011 |
| HISYS-NFR-DARS-CP-003 | decision packet and claim-ladder enforcement | HISYS-T-DARS-CP-017 |
