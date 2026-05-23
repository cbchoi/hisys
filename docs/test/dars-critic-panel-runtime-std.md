---
doc_id: HISYS-DARS-CP-STD-001
title: DARS Critic Panel Runtime Software Test Description
version: 0.2.0
document_status: draft-for-tdd
created: 2026-05-19
updated: 2026-05-23
requirements_source: docs/requirements/dars-critic-panel-runtime-requirements.md
design_source: docs/design/dars-critic-panel-runtime-sdd.md
release_plan: docs/plans/dars-panel-live-provider-unattended-release-final-plan.md
---

# DARS Critic Panel Runtime Software Test Description

## 1. Test strategy

The first implementation increment used strict TDD with local tmp-path fixtures and no live external calls. The live-provider release line keeps that rule: every provider, unattended, and release-readiness behavior starts with RED tests over fake/injected transports and local documents before any human-approved live smoke.

Live provider calls, unattended canaries, and release execution are not unit-test side effects. They are human-gated evidence actions with runbooks, decision packets, runtime-boundary records, and post-run review.

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
| HISYS-T-DARS-CP-011 | Live provider policy validation | Reject raw secrets and unbounded provider authority while accepting credential references and finite limits. | HISYS-FR-DARS-CP-009, HISYS-NFR-DARS-CP-002 | `test_live_provider_policy_rejects_raw_secret_fields`; `test_live_provider_policy_accepts_credential_reference_only` |
| HISYS-T-DARS-CP-012 | Live provider transport fail-closed contract | Exercise fake/injected transport without external calls and prove real transport entry points fail closed without gates. | HISYS-FR-DARS-CP-010 | `test_live_provider_transport_uses_fake_executor_without_external_call`; `test_live_provider_adapter_requires_policy_approval_and_credential_ref` |
| HISYS-T-DARS-CP-013 | Single-critic live provider smoke gate | Document and review exactly one human-approved live provider/model boundary crossing. | HISYS-FR-DARS-CP-011 | `test_live_provider_single_smoke_runbook_requires_decision_packet_and_budget` plus reviewed runtime-boundary evidence |
| HISYS-T-DARS-CP-014 | Multi-critic live provider panel smoke gate | Verify panel-level live boundary records and partial failure isolation for at least two critics. | HISYS-FR-DARS-CP-012, HISYS-NFR-DARS-CP-001 | `test_live_provider_panel_dispatch_writes_panel_boundary`; `test_live_provider_panel_isolates_one_failed_critic` |
| HISYS-T-DARS-CP-015 | Bounded unattended advisory runner | Enforce expiry, allowlists, budget/rate caps, kill switch, audit ledger, circuit breakers, and post-run review. | HISYS-FR-DARS-CP-013 | `test_unattended_policy_expires_and_blocks_runner`; `test_unattended_runner_requires_kill_switch_and_budget_caps` |
| HISYS-T-DARS-CP-016 | Live operations status and rollback | Report policy refs, kill-switch state, latest evidence refs, and rollback instructions without secrets. | HISYS-FR-DARS-CP-014 | `test_dars_live_status_reports_kill_switch_and_latest_boundary_refs_without_secrets` |
| HISYS-T-DARS-CP-017 | Release candidate and controlled release gate | Require full validation, release evidence, decision packet, release refs, post-release smoke, and rollback pointer before release claims. | HISYS-FR-DARS-CP-015, HISYS-NFR-DARS-CP-003 | `test_release_candidate_checklist_requires_live_unattended_and_rollback_evidence`; release decision packet review |

## 3. RED baselines

Existing local panel runtime baseline:

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_runtime.py -q
```

Live-provider R1 baseline:

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_live_provider_policy.py::test_live_provider_policy_rejects_raw_secret_fields -q
PYTHONPATH=src:. pytest tests/unit/test_dars_live_provider_transport.py::test_live_provider_transport_uses_fake_executor_without_external_call -q
```

Expected RED before R1 implementation: missing test/module/symbol for `hisys.agents.dars_live_provider_policy` and `hisys.agents.dars_live_provider_transport`.

## 4. GREEN acceptance for future implementation

Future implementation increments shall make focused tests pass without enabling external calls in unit tests, writing outside controlled tmp instance roots, persisting raw credentials, or granting DARS approval authority. All emitted critique and boundary artifacts shall preserve `advisory_only=true`, `requires_human_review=true`, `mutation_performed=false`, and `publication_performed=false` unless a later controlled requirement and human decision packet changes the claim boundary.

## 5. Human-gated evidence tests

The following cannot be satisfied by unit tests alone and require runbooks plus reviewed evidence:

- `live_provider_advisory_smoked`: one approved live provider/model call;
- `multi_critic_live_provider_advisory_complete`: approved multi-critic live provider panel smoke;
- `bounded_unattended_advisory_operation_ready`: approved unattended live canary under a finite standing policy;
- `release_candidate_ready`: accepted release-candidate decision packet;
- `released_for_controlled_advisory_use`: approved release action and post-release smoke.
