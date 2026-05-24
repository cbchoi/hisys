---
doc_id: HISYS-DARS-CP-RTM-001
title: DARS Critic Panel Runtime Traceability Matrix
version: 0.38.0
document_status: draft-for-tdd
created: 2026-05-19
updated: 2026-05-24
---

# DARS Critic Panel Runtime Traceability Matrix

Source Hisys packet: `/tmp/hisys-dars-critic-panel-instance/runtime-boundary/agent-workflows/20260519/SPEC-DARS-CRITIC-PANEL-001.json`.

## DARS-LIVE-RELEASE-R5-CANARY-ACTION-DECISION-PACKET — R5 canary action decision packet ready for human review (2026-05-24)

- Scope: recorded the action decision packet that connects the prepared R5 canary packet (v0.0.86) and the R5 canary scope decision (v0.0.85) to a separately HUMAN-GATED canary execution decision. The packet enumerates the standing-approval fields, request-class scope, budget/rate/prompt/output caps, kill-switch ref, audit-retention ref, post-run human review, stop conditions, and R6 status/rollback refs that a later canary execution must satisfy.
- Artifacts: `docs/release/dars-r5-canary-action-decision-packet-v0.0.87.md`, `docs/release/dars-panel-release-notes-v0.0.87.md`, `docs/release/dars-panel-release-candidate-checklist.md`, `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.87.md`, `tests/unit/test_dars_r5_canary_action_decision_packet.py`, `docs/milestone-bootstrap/profile.yaml`, `ralph.md`, and `tests/unit/test_governance_docs_current_state.py`.
- Evidence contract: accepted claim is `r5_canary_action_decision_packet_ready_for_human_review`; `r5_canary_action_decision_packet_ready=true`; `r5_live_canary_executed=false`; `standing_unattended_approval_activated=false`; `bounded_unattended_advisory_operation_ready=false`; `release_candidate_ready=false`; `requires_human_review=true`. R4C remains excluded from this release scope.
- Traceability: HISYS-FR-DARS-CP-013 / HISYS-T-DARS-CP-015 now has an action decision packet ready for human-review gate; the next safe task is `DARS-LIVE-RELEASE-R5-CANARY-ACTION-HUMAN-REVIEW-GATE`.
- Boundary: no live provider/model call, Codex subprocess call, raw provider API call, credential lookup, standing unattended approval activation, release tag/package/upload/deploy/publication, external notification, mutation outside repository docs/tests/control files, or human-review removal is introduced.

## DARS-LIVE-RELEASE-R5-CANARY-PACKET-PREP — R5 canary packet prepared for human review (2026-05-24)

- Scope: assembled a reference-only bounded unattended canary packet that aggregates the existing R5 PREP standing-approval validator, dry-run unattended runner, example standing-approval policy, and R6 local status/rollback runbooks for human review.
- Artifacts: `docs/release/dars-r5-canary-packet-prep-v0.0.86.md`, `docs/release/dars-panel-release-notes-v0.0.86.md`, `docs/release/dars-panel-release-candidate-checklist.md`, `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.86.md`, `tests/unit/test_dars_r5_canary_packet_prep.py`, `docs/milestone-bootstrap/profile.yaml`, `ralph.md`, and `tests/unit/test_governance_docs_current_state.py`.
- Evidence contract: accepted claim is `r5_canary_packet_prepared_for_human_review`; `r5_canary_packet_prepared=true`; `r5_live_canary_executed=false`; `standing_unattended_approval_activated=false`; `bounded_unattended_advisory_operation_ready=false`; `release_candidate_ready=false`; `requires_human_review=true`. The packet records finite standing-approval refs, request-class scope, budget/rate/prompt/output caps, kill-switch ref, audit-retention ref, post-run human review, stop conditions, and R6 status/rollback refs.
- Traceability: HISYS-FR-DARS-CP-013 / HISYS-T-DARS-CP-015 now has a PREP packet ready for canary action decision review; the next safe task is `DARS-LIVE-RELEASE-R5-CANARY-ACTION-DECISION-PACKET`.
- Boundary: no live provider/model call, Codex subprocess call, raw provider API call, credential lookup, standing unattended approval activation, release tag/package/upload/deploy/publication, external notification, mutation outside repository docs/tests/control files, or human-review removal is introduced.

## DARS-LIVE-RELEASE-R5-CANARY-SCOPE-DECISION — R5 selected, R4C excluded from this release (2026-05-24)

- Scope: after the operator instructed `R5진행 R4C는 이번 release에서 제외`, selected R5 canary packet preparation as the active next release-evidence row and excluded R4C Codex subprocess panel completion from this release scope.
- Artifacts: `docs/release/dars-r5-canary-scope-decision-v0.0.85.md`, `docs/release/dars-panel-release-candidate-checklist.md`, `docs/release/dars-panel-release-notes-v0.0.85.md`, `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.85.md`, `tests/unit/test_dars_r5_canary_scope.py`, `docs/milestone-bootstrap/profile.yaml`, `ralph.md`, and `tests/unit/test_governance_docs_current_state.py`.
- Evidence contract: accepted claim is `r5_canary_scope_selected_with_r4c_excluded_from_this_release`; `r5_live_canary_executed=false`; `bounded_unattended_advisory_operation_ready=false`; `release_candidate_ready=false`; `r4c_codex_subprocess_completion_required_for_this_release=false`.
- Traceability: HISYS-FR-DARS-CP-013 / HISYS-T-DARS-CP-015 moves from PREP-GREEN to canary packet prep planned; HISYS-FR-DARS-CP-015 / HISYS-T-DARS-CP-017 records that R4C is excluded from this release scope and not an RC blocker.
- Boundary: no live provider/model call, Codex subprocess call, raw provider API call, credential lookup, standing unattended approval activation, release tag/package/upload/deploy/publication, external notification, mutation outside repository docs/tests/control files, or human-review removal is introduced.

## DARS-LIVE-RELEASE-R7-RC-SCOPE-DECISION — RC scope recorded for human review (2026-05-24)

- Scope: after the operator instructed `go`, recorded the release-candidate package scope following R4H harness closure while preserving that release-candidate readiness remains false until the RC packet accepts evidence completeness and residual risk.
- Artifacts: `docs/release/dars-panel-rc-scope-decision-v0.0.84.md`, `docs/release/dars-panel-release-candidate-checklist.md`, `docs/release/dars-panel-release-notes-v0.0.84.md`, `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.84.md`, `tests/unit/test_dars_release_candidate_scope.py`, `docs/milestone-bootstrap/profile.yaml`, `ralph.md`, and `tests/unit/test_governance_docs_current_state.py`.
- Evidence contract: accepted claim is `r7_rc_scope_decision_recorded_for_human_review`; `release_candidate_ready=false`; `bounded_unattended_advisory_operation_ready=false`; R5 ACTION canary evidence remains missing; R4C Codex subprocess completion remains deferred.
- Traceability: HISYS-FR-DARS-CP-015 / HISYS-T-DARS-CP-017 now has a scope-decision checkpoint and checklist for a future RC packet; the next safe task is `DARS-LIVE-RELEASE-R7-RC-PACKET-PREP`.
- Boundary: no live provider/model call, Codex subprocess retry, raw provider API call, credential lookup, standing unattended approval activation, release tag/package/upload/deploy/publication, external notification, mutation outside repository docs/tests/control files, or human-review removal is introduced.

## DARS-LIVE-RELEASE-R4H-HERMES-MEDIATED-PANEL-REQUEST-RESPONSE-HARNESS — R4H contract closed for human review (2026-05-24)

- Scope: after the operator instructed `R4H를 닫을 때까지 rloo 실행`, implemented and ran a local fixture-injected request/response harness for the R4H Hermes-mediated advisory contract.
- Artifacts: `src/hisys/operations/dars_r4h_productization.py`, `src/hisys/cli/main.py`, `tests/unit/test_dars_r4h_productization_prep.py`, `docs/examples/dars/hermes-mediated-r4h-request-response-harness.request.example.json`, `docs/examples/dars/hermes-mediated-r4h-request-response-harness.example.json`, `docs/reports/dars-r4h-hermes-mediated-request-response-harness-2026-05-24.md`, `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.83.md`, `docs/milestone-bootstrap/profile.yaml`, `ralph.md`, and `tests/unit/test_governance_docs_current_state.py`.
- Evidence contract: accepted claim is `r4h_hermes_mediated_request_response_harness_closed_for_human_review`; request schema is `hisys.dars.r4h_hermes_mediated_request`; response schema is `hisys.dars.r4h_hermes_mediated_response`; request validation rejects unsafe authority fields and unsupported critics before fixture response synthesis.
- Traceability: HISYS-FR-DARS-CP-012 / HISYS-T-DARS-CP-014 now has a local/read-only R4H harness closure surface and CLI command `hisys dars-r4h-request-response-harness`; the next safe task is `DARS-LIVE-RELEASE-R7-RC-SCOPE-DECISION`.
- Boundary: fixture-injected harness only; no Hermes-mediated model call, Codex CLI subprocess call/completion claim, raw provider API call/readiness, adapter-native readiness, R5/R7/R8 readiness, credential lookup, mutation, publication, external notification, release action, or human-review removal is introduced.

## DARS-LIVE-RELEASE-R4C-FUTURE-DEFERRED-CLOSURE — record-only branch closure (2026-05-24)

- Scope: after the operator instructed `R4C는 미래로 넘긴다는 기록만 남기고 닫자`, closed the active R4C branch for the current work loop as future/deferred work only.
- Artifacts: `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.82.md`, `docs/milestone-bootstrap/profile.yaml`, `ralph.md`, and `tests/unit/test_governance_docs_current_state.py`.
- Evidence contract: accepted record-only claim is `r4c_codex_subprocess_path_closed_as_future_deferred_work`; future R4C work remains `DARS-LIVE-RELEASE-R4C-CODEX-REFRESH-STATE-RECONCILIATION-OUTSIDE-HISYS`; active continuation remains R4H request/response harness validation.
- Boundary: no Codex CLI subprocess retry/completion claim, raw provider API call/readiness, adapter-native readiness, credential lookup, mutation, publication, external notification, release action, or human-review removal is introduced.

## DARS-LIVE-RELEASE-R4H-HERMES-MEDIATED-PANEL-PRODUCTIZATION-PREP — governed request/response contract (2026-05-24)

- Scope: after the operator instructed `go`, defined the governed Hermes-mediated DARS productization-prep path for R4H while keeping R4C deferred as separate Codex subprocess transport-evidence work.
- Artifacts: `src/hisys/operations/dars_r4h_productization.py`, `tests/unit/test_dars_r4h_productization_prep.py`, `docs/examples/dars/hermes-mediated-r4h-productization-prep.example.json`, `docs/reports/dars-r4h-hermes-mediated-productization-prep-2026-05-24.md`, `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.81.md`, `docs/milestone-bootstrap/profile.yaml`, `ralph.md`, and `tests/unit/test_governance_docs_current_state.py`.
- Evidence contract: accepted claim is `r4h_hermes_mediated_productization_prep_ready_for_human_review`; request schema is `hisys.dars.r4h_hermes_mediated_request`; response schema is `hisys.dars.r4h_hermes_mediated_response`; supported critics are `logical_consistency_critic` and `evidence_governance_critic`.
- Traceability: HISYS-FR-DARS-CP-012 / HISYS-T-DARS-CP-014 now has a local/read-only productization-prep surface and CLI command `hisys dars-r4h-productization-prep`; the next safe task is request/response harness validation.
- Boundary: no Codex CLI subprocess call/completion claim, raw provider API call/readiness, adapter-native readiness, R5/R7/R8 readiness, credential lookup, mutation, publication, external notification, release action, or human-review removal is introduced.

## DARS-LIVE-RELEASE-R4H-HERMES-MEDIATED-PANEL-ADVISORY-REVIEW-GATE — R4H selected, R4C deferred (2026-05-24)

- Scope: after the operator instructed `R4H로 진행 R4C는 추후 작업으로`, selected R4H as the active continuation branch and parked R4C as later transport-evidence work.
- Artifacts: `docs/reports/dars-r4h-hermes-mediated-panel-review-gate-proceed-2026-05-24.md`, `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.80.md`, `docs/milestone-bootstrap/profile.yaml`, `ralph.md`, and `tests/unit/test_governance_docs_current_state.py`.
- Evidence contract: accepted claim is `r4h_hermes_mediated_advisory_path_selected_for_continuation`; active branch is `R4H`; deferred branch is `R4C`; future R4C work is `DARS-LIVE-RELEASE-R4C-CODEX-REFRESH-STATE-RECONCILIATION-OUTSIDE-HISYS`.
- Traceability: HISYS-FR-DARS-CP-012 / HISYS-T-DARS-CP-014 now proceeds on the R4H Hermes-mediated advisory branch; R4C subprocess completion remains rejected and deferred.
- Boundary: no Codex CLI subprocess completion claim, raw provider API readiness, adapter-native readiness, R5/R7/R8 readiness, credential lookup, mutation, publication, external notification, release action, or human-review removal is introduced.

## DARS-LIVE-RELEASE-R4H-HERMES-MEDIATED-PANEL-ADVISORY-ACTION — Hermes-mediated advisory completed (2026-05-24)

- Scope: after the operator accepted the recommended split, recorded R4H as a separate Hermes-mediated model advisory path rather than as a Codex CLI subprocess completion.
- Artifacts: `docs/reports/dars-r4h-hermes-mediated-panel-advisory-2026-05-24.md`, `docs/examples/dars/hermes-mediated-r4h-multi-critic-panel.advisory.json`, `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.79.md`, `docs/milestone-bootstrap/profile.yaml`, `ralph.md`, and `tests/unit/test_governance_docs_current_state.py`.
- Evidence contract: accepted claim is `r4_hermes_mediated_multi_critic_panel_advisory_completed_with_findings`; transport is `hermes_mediated_model_advisory`; critic count is 2; completed critic count is 2.
- Traceability: HISYS-FR-DARS-CP-012 / HISYS-T-DARS-CP-014 now has an additional R4H advisory branch `R4H-HARNESS-CLOSED-FOR-HUMAN-REVIEW + R4C-DEFERRED + HUMAN-REVIEW-REQUIRED`, while the R4-C subprocess completion claim remains blocked.
- Boundary: no Codex CLI subprocess call, raw provider API call by Hisys, credential lookup by Hisys, mutation, publication, release, external notification, R5/R7/R8 action, or human-review removal is introduced.

## DARS-LIVE-RELEASE-R4-CODEX-SUBPROCESS-PANEL-SMOKE-RETRY-AUTH-STOP — Retry blocked by Codex refresh state (2026-05-24)

- Scope: after the operator asked `지금 다시 해볼래?`, Hisys retried the same bounded R4 Codex CLI subprocess prompt-mode panel path.
- Artifacts: `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.78.md`, appended retry evidence in `docs/reports/dars-r4-codex-subprocess-panel-smoke-auth-stop-2026-05-24.md`, `docs/milestone-bootstrap/profile.yaml`, and `tests/unit/test_governance_docs_current_state.py`.
- Evidence contract: focused preflight passed (`48 passed`); `/usr/bin/codex` was present as `codex-cli 0.128.0`; the subprocess returned `refresh_token_reused` with `401 Unauthorized` before any per-critic or aggregate boundary record was written.
- Boundary: Hisys did not inspect credentials, call a raw provider API, produce critique output, write panel evidence, mutate, publish, deploy, release, execute R5/R7/R8, or remove human review.

## DARS-LIVE-RELEASE-R4-CODEX-SUBPROCESS-PANEL-SMOKE-TOKEN-REFRESH-STOP — Attempted live panel smoke blocked by Codex refresh-token reuse (2026-05-24)

- Scope: after explicit approval for `R4 Codex subprocess panel smoke`, Hisys attempted the governed Codex CLI subprocess prompt-mode panel path using the existing Codex subscription-auth state and stopped on `refresh_token_reused` before critique output.
- Artifacts: `docs/reports/dars-r4-codex-subprocess-panel-smoke-auth-stop-2026-05-24.md`, `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.77.md`, `docs/milestone-bootstrap/profile.yaml`, `ralph.md`, and `tests/unit/test_governance_docs_current_state.py`.
- Evidence contract: focused preflight passed; `/usr/bin/codex` was present as `codex-cli 0.128.0`; the subprocess returned `refresh_token_reused` before any per-critic or aggregate boundary record was written.
- Traceability: HISYS-FR-DARS-CP-012 / HISYS-T-DARS-CP-014 is now `LIVE-ACTION-ATTEMPTED + REFRESH-STATE-BLOCKED + HUMAN-RECONCILIATION-REQUIRED` for the R4 mapped-subscription panel path.
- Boundary: Codex CLI found/used its existing subscription-auth state, attempted refresh, and failed with `refresh_token_reused`. Hisys did not inspect credentials, call a raw provider API, produce critique output, write panel evidence, mutate, publish, deploy, release, execute R5/R7/R8, or remove human review.

## DARS-LIVE-RELEASE-R4-PANEL-MAPPED-SUBSCRIPTION-ACTION-DECISION-PACKET — Action packet ready, live action blocked (2026-05-24)

- Scope: recorded the operator instruction `go` as a human-review decision packet for the configured R4 mapped-subscription panel path, while stopping before any new live call.
- Artifacts: `docs/reports/dars-r4-action-decision-packet-mapped-subscription-panel-2026-05-24.md`, `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.76.md`, `docs/milestone-bootstrap/profile.yaml`, `ralph.md`, and `tests/unit/test_governance_docs_current_state.py`.
- Evidence contract: the accepted packet claim is `r4_mapped_subscription_panel_action_packet_ready_for_human_review`; the only executed harness evidence in this step is the local injected-executor pytest preflight over remote-subscription panel aggregation and prep/evidence packet shapes.
- Traceability: HISYS-FR-DARS-CP-012 / HISYS-T-DARS-CP-014 is now `ACTION-PACKET-READY + HARNESS-PREFLIGHT-PLANNED + HUMAN-GATED LIVE ACTION BLOCKED` for the R4 mapped-subscription panel path.
- Boundary: no live provider/model call, no Codex subprocess call, no raw provider API call, no credential lookup, no R4 live action, no R5 action, no release-candidate transition, no deployment/publication/release action, and no human-review removal was introduced.

## DARS-LIVE-RELEASE-R4-PANEL-MAPPED-SUBSCRIPTION-PREP — Named Hisys panel config (2026-05-24)

- Scope: moved R4 mapped-subscription panel composition into Hisys DARS config instead of requiring an ad-hoc sidecar panel JSON.
- Artifacts: `src/hisys/agents/dars_config.py`, `src/hisys/cli/main.py`, `examples/instance/config/dars.json`, `tests/unit/test_dars_config.py`, `tests/unit/test_dars_critic_panel_cli.py`, `docs/runbooks/dars-live-provider-panel-smoke.md`, `docs/milestone-bootstrap/profile.yaml`, and `ralph.md`.
- Evidence contract: `spec.panels.r4_mapped_subscription_panel` names the panel, critics, backend ids, rubric refs, dimensions, advisory-only status, and output contract. Config validation rejects unknown panel backends, non-advisory panels, mutating critics, and non-`DarsCritiqueRecord` output contracts. `hisys run-dars-panel --panel-key` loads the named panel from `$HISYS_INSTANCE/config/dars.json`; `--panel-config` remains available for fixture compatibility.
- Traceability: HISYS-FR-DARS-CP-012 / HISYS-T-DARS-CP-014 is now `CONFIG-PREP-GREEN + HUMAN-GATED ACTION PLANNED` for the R4 mapped-subscription panel path.
- Boundary: no live provider/model call, no Codex subprocess call, no raw provider API call, no credential lookup, no R4/R5 action, no release-candidate transition, no deployment/publication/release action, and no human-review removal was introduced.

## DARS-LIVE-RELEASE-R3-ACTION-DECISION-PACKET — Mapped subscription bridge selected (2026-05-23)

- Scope: selected `mapped_subscription` after the operator instruction `mapped로 가자`.
- Artifacts: `docs/reports/dars-r3-action-decision-packet-mapped-subscription-2026-05-23.md`, `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.74.md`, `docs/milestone-bootstrap/profile.yaml`, `ralph.md`, and `tests/unit/test_governance_docs_current_state.py`.
- Accepted claim: `r3_mapped_subscription_transport_live_smoke_ready_for_human_review`; scoped ladder claim is `live_provider_advisory_smoked` only for `codex_subscription_subprocess_transport_only`, with `raw_provider_api_readiness=false` and `adapter_native_readiness=false`.
- Traceability: HISYS-FR-DARS-CP-011 / HISYS-T-DARS-CP-013 is now `MAPPED-SUBSCRIPTION-R3-GREEN + HUMAN-REVIEW-READY`.
- Boundary: no new live provider/model call, Codex subprocess call, raw provider API call, credential lookup, standing unattended approval activation, R4/R5 action, release-candidate transition, deployment/publication/release action, or human-review removal was introduced.

## DARS-LIVE-RELEASE-R3-ACTION-TRANSPORT-PREP — R3 bridge rule for live-release intent (2026-05-23)

- Scope: recorded the operator's `go for live release` instruction as release intent while preserving the non-skippable claim ladder.
- Artifacts: `docs/reports/dars-r3-action-transport-prep-2026-05-23.md`, `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.73.md`, `docs/milestone-bootstrap/profile.yaml`, `ralph.md`, and `tests/unit/test_governance_docs_current_state.py`.
- Bridge rule: future `live_provider_advisory_smoked` acceptance requires either `adapter_native` evidence through `hisys.dars.live_provider_adapter` or an explicit `mapped_subscription` decision packet that maps the reviewed Codex subscription subprocess path without claiming raw-provider API readiness.
- Traceability: HISYS-FR-DARS-CP-011 / HISYS-T-DARS-CP-013 is now `BRIDGE-PREP-GREEN + HUMAN-GATED ACTION PLANNED`.
- Boundary: no live provider/model call, no Codex subprocess call, no raw provider API call, no credential lookup, no standing unattended approval activation, no R4/R5 action, no release-candidate transition, no deployment/publication/release action, and no human-review removal was introduced.


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
| HISYS-FR-DARS-CP-009 | `LiveProviderPolicyPacket`, credential-reference validation, provider/model allowlist, budget/rate bounds, raw-secret rejection (DARS-LIVE-RELEASE-R1-POLICY) | HISYS-T-DARS-CP-011 | `test_live_provider_policy_rejects_raw_secret_fields`, `test_live_provider_policy_accepts_credential_reference_only`, `test_live_provider_policy_rejects_missing_credential_reference`, `test_live_provider_policy_rejects_unknown_credential_ref_scheme`, `test_live_provider_policy_rejects_mutation_or_publication_authority`, `test_live_provider_policy_rejects_non_advisory_allowed_actions`, `test_live_provider_policy_rejects_disabled_external_call_or_human_review`, `test_live_provider_policy_rejects_unbounded_prompt_output_or_rate_limit`, `test_live_provider_policy_rejects_expired_packet`, `test_live_provider_policy_rejects_non_allowlisted_provider`, `test_live_provider_policy_rejects_missing_approval_or_cost_budget_ref`, `test_live_provider_policy_emits_dispatch_warning_even_when_valid`, `test_live_provider_policy_schema_constants_are_stable` | GREEN (DARS-LIVE-RELEASE-R1-POLICY) |
| HISYS-FR-DARS-CP-010 | `DarsLiveProviderTransportRequest`/`Result`, `FakeLiveProviderTransport`, `LiveProviderTransportFailure`, redacted-payload executor seam (DARS-LIVE-RELEASE-R1-POLICY); `DarsLiveProviderAdapterRequest`/`Result`, `run_dars_live_provider_adapter`, env-gated dry-run and live mode entry points (DARS-LIVE-RELEASE-R2-ADAPTER) | HISYS-T-DARS-CP-012 | `test_live_provider_transport_uses_fake_executor_without_external_call`, `test_live_provider_transport_rejects_missing_transport`, `test_live_provider_transport_rejects_raw_prompt_text_field`, `test_live_provider_transport_request_rejects_invalid_allowed_actions`, `test_live_provider_transport_request_rejects_mutation_authority`, `test_live_provider_transport_request_rejects_disabled_external_call_allowed`, `test_live_provider_transport_request_rejects_disabled_human_review`, `test_live_provider_transport_request_rejects_unbounded_prompt_or_output`, `test_live_provider_transport_request_rejects_oversized_prompt_byte_count`, `test_live_provider_transport_rejects_unknown_transport_kind`, `test_live_provider_transport_records_failure_code_when_executor_raises_failure`, `test_live_provider_transport_rejects_oversized_output`, `test_live_provider_transport_rejects_empty_executor_output`, `test_live_provider_transport_rejects_executor_output_with_raw_secret_marker`, `test_live_provider_transport_rejects_unauthorized_authority_claim_in_output`, `test_live_provider_transport_schema_constants_are_stable`, `test_dars_live_provider_adapter_schema_constants_are_stable`, `test_live_provider_adapter_requires_policy_approval_and_credential_ref`, `test_live_provider_adapter_fails_closed_without_transport`, `test_live_provider_adapter_fails_closed_on_policy_without_credential_ref`, `test_live_provider_adapter_fails_closed_on_policy_with_raw_secret`, `test_live_provider_adapter_fails_closed_on_activation_without_human_approval`, `test_live_provider_adapter_fails_closed_on_approval_ref_mismatch`, `test_live_provider_adapter_fails_closed_on_policy_approval_mismatch`, `test_live_provider_adapter_fails_closed_on_missing_env_gate_in_live_mode`, `test_live_provider_adapter_live_mode_allowed_when_env_gate_set`, `test_live_provider_adapter_fails_closed_on_mutation_authority_in_policy`, `test_live_provider_adapter_writes_boundary_record`, `test_live_provider_adapter_propagates_transport_failure_code`, `test_live_provider_adapter_fails_closed_when_packet_files_missing`, `test_live_provider_adapter_rejects_unknown_mode`, `test_live_provider_adapter_rejects_invalid_yyyymmdd`, `test_live_provider_adapter_fails_closed_on_backend_id_mismatch` | GREEN (DARS-LIVE-RELEASE-R1-POLICY contract + fake transport + R2 fail-closed adapter; real-provider transport still PLANNED) |
| HISYS-FR-DARS-CP-011 | single-critic live-provider smoke runbook (`docs/runbooks/dars-live-provider-single-smoke.md`), example policy/activation packets, decision-packet preconditions, env-gate procedure (PREP), reviewed Codex subscription subprocess smoke evidence, and R3 action transport bridge rule. Future R3 ACTION must choose `adapter_native` or `mapped_subscription` in a decision packet before `live_provider_advisory_smoked` can be accepted. | HISYS-T-DARS-CP-013 | `test_live_provider_single_smoke_runbook_exists`, `test_live_provider_single_smoke_runbook_requires_decision_packet_and_budget`, `test_live_provider_single_smoke_runbook_documents_stop_conditions`, `test_live_provider_single_smoke_runbook_anchors_r1_r2_artifacts`, `test_live_provider_single_smoke_runbook_does_not_authorize_live_call_by_itself`, `test_live_provider_single_smoke_example_policy_passes_r1_validator`, `test_live_provider_single_smoke_example_policy_uses_only_credential_reference`, `test_live_provider_single_smoke_example_activation_passes_validator`, `test_live_provider_single_smoke_example_activation_matches_example_policy`; `test_governance_profile_and_ralph_checkpoint_match_current_head`; reviewed runtime-boundary evidence and bridge decision packet (R3 ACTION) | MAPPED-SUBSCRIPTION-R3-GREEN + HUMAN-REVIEW-READY (DARS-LIVE-RELEASE-R3-ACTION-DECISION-PACKET selected mapped_subscription; raw-provider API and adapter-native readiness remain false) |
| HISYS-FR-DARS-CP-012 | multi-critic live-provider panel smoke runbook (`docs/runbooks/dars-live-provider-panel-smoke.md`), example policy/activation packets, per-critic + panel-level boundary record requirements, failure-isolation expectations (PREP), named Hisys DARS config panel (`spec.panels.r4_mapped_subscription_panel`) for the mapped-subscription R4 path, R4 mapped-subscription action decision packet, attempted/retried Codex subprocess panel smoke auth-stop evidence, separate R4H Hermes-mediated advisory evidence, R4H productization-prep contract, and local fixture-injected R4H request/response harness closure. | HISYS-T-DARS-CP-014 | `test_live_provider_panel_smoke_runbook_exists`, `test_live_provider_panel_smoke_runbook_requires_multi_critic_governance`, `test_live_provider_panel_smoke_runbook_documents_stop_conditions`, `test_live_provider_panel_smoke_runbook_anchors_prior_increments`, `test_live_provider_panel_smoke_runbook_does_not_authorize_live_call_by_itself`, `test_live_provider_panel_smoke_runbook_requires_r3_single_smoke_precondition`, `test_live_provider_panel_smoke_example_policy_passes_r1_validator`, `test_live_provider_panel_smoke_example_policy_uses_only_credential_reference`, `test_live_provider_panel_smoke_example_activation_passes_validator`, `test_live_provider_panel_smoke_example_activation_matches_example_policy`, `test_hisys_dars_config_can_define_named_panel_without_sidecar_file`, `test_hisys_dars_config_rejects_panel_unknown_backend`, `test_run_dars_panel_cli_loads_named_panel_from_hisys_config`, `test_remote_subscription_multi_critic_panel_dispatch_writes_aggregate_boundary`, `test_remote_subscription_multi_critic_panel_rejects_mixed_request_ids_before_executor`, `test_codex_cli_subprocess_multi_critic_panel_prep_packet_matches_dispatch_contract`, `test_codex_cli_subprocess_multi_critic_evidence_packet_prep_includes_claim_and_evidence`, `test_r4h_productization_prep_contract_preserves_branch_boundaries`, `test_r4h_productization_prep_cli_writes_json_and_markdown`, `test_r4h_request_response_harness_validates_fixture_response_boundary`, `test_r4h_request_response_harness_rejects_unsafe_request_fields`, `test_r4h_request_response_harness_cli_writes_json_and_markdown`; Codex subprocess attempt/retry evidence in `docs/reports/dars-r4-codex-subprocess-panel-smoke-auth-stop-2026-05-24.md` and `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.78.md`; `test_live_provider_panel_dispatch_writes_panel_boundary`, `test_live_provider_panel_isolates_one_failed_critic` (future successful R4 live action) | LIVE-ACTION-RETRIED + AUTH-BLOCKED + REFRESH-STATE-RECONCILIATION-REQUIRED (Codex CLI refresh_token_reused/401 before critique/boundary evidence) |
| HISYS-FR-DARS-CP-013 | R5 documentation PREP runbook (`docs/runbooks/dars-unattended-advisory-operation.md`), standing approval example (`docs/examples/dars/unattended-standing-approval.example.json`), `validate_standing_approval_policy`, `DarsUnattendedAdvisoryRunner`, audit ledger, budget/rate caps, kill switch, circuit breakers, post-run human review | HISYS-T-DARS-CP-015 | `test_unattended_operation_runbook_defines_standing_approval_contract`, `test_unattended_operation_runbook_defines_runner_and_dry_run_boundaries`, `test_unattended_operation_runbook_documents_circuit_breakers_and_stop_conditions`, `test_unattended_standing_approval_example_has_required_safe_fields`, `test_standing_approval_example_policy_passes_validator`, `test_standing_approval_policy_rejects_inactive_validity_window`, `test_standing_approval_policy_rejects_missing_request_class_allowlist`, `test_standing_approval_policy_rejects_live_canary_in_prep_example`, `test_standing_approval_policy_rejects_missing_budget_rate_and_kill_switch`, `test_standing_approval_policy_rejects_missing_audit_retention`, `test_standing_approval_policy_rejects_authority_flags`, `test_standing_approval_policy_rejects_raw_secret_fields`, `test_standing_approval_policy_rejects_secret_looking_nested_values`, `test_unattended_runner_blocks_expired_policy_and_writes_ledger`, `test_unattended_runner_requires_kill_switch_and_budget_caps`, `test_unattended_runner_rejects_mutation_publication_or_external_action_authority`, `test_unattended_runner_executes_dry_run_fake_transport_and_writes_audit_ledger`, `test_unattended_runner_trips_repeated_failure_circuit_breaker`, `test_unattended_runner_trips_cost_threshold_circuit_breaker`, `test_unattended_runner_blocks_secret_scan_hit`, `test_unattended_runner_blocks_policy_mismatch`, `test_unattended_runner_records_output_redaction_failure`; reviewed unattended canary ledger (R5 ACTION) | PREP-GREEN + HUMAN-GATED ACTION PLANNED (DARS-LIVE-RELEASE-R5-UNATTENDED-PREP done; R5 ACTION reserved for human approval) |
| HISYS-FR-DARS-CP-014 | `hisys.operations.dars_live_status`, `hisys dars-live-status`, kill-switch state, latest boundary refs, budget/circuit-breaker state, rollback runbooks (`docs/runbooks/dars-live-operations.md`, `docs/runbooks/dars-live-rollback.md`) | HISYS-T-DARS-CP-016 | `test_dars_live_status_reports_kill_switch_and_latest_boundary_refs_without_secrets`, `test_dars_live_status_writes_json_and_markdown_report`, `test_dars_live_status_cli_writes_report_and_prints_json`, `test_dars_live_operations_and_rollback_runbooks_define_disable_recovery_and_privacy` | GREEN (DARS-LIVE-RELEASE-R6-STATUS-ROLLBACK; local status/rollback readiness only) |
| HISYS-FR-DARS-CP-015 | release checklist, release notes, release scope decision packet, future RC decision packet, post-release smoke evidence | HISYS-T-DARS-CP-017 | `test_release_candidate_checklist_requires_prior_live_unattended_and_rollback_evidence`; `test_rc_scope_decision_preserves_claim_ladder_and_blocks_release_actions`; release decision packet review | SCOPE-DECISION-RECORDED + HUMAN-GATED RC PACKET PLANNED (DARS-LIVE-RELEASE-R7; `release_candidate_ready=false`) |
| HISYS-NFR-DARS-CP-003 | claim-ladder and decision-packet enforcement for live-provider, unattended, release-candidate, and release claims | HISYS-T-DARS-CP-017 | release decision packet review and traceability gate | PLANNED (DARS-LIVE-RELEASE-R0..R8) |


## DARS-LIVE-RELEASE-R5-UNATTENDED-PREP-DOCS — Bounded unattended documentation checkpoint (2026-05-23)

- Scope: authored the R5 documentation PREP artifacts for bounded unattended advisory operation. The runbook defines the finite standing approval policy contract, the planned unattended advisory runner contract, fake/injected dry-run rehearsal procedure, audit ledger requirements, circuit breaker matrix, post-run human review, and stop conditions.
- Artifacts: `docs/runbooks/dars-unattended-advisory-operation.md`, `docs/examples/dars/unattended-standing-approval.example.json`, and `tests/unit/test_dars_unattended_docs.py`.
- Traceability: HISYS-FR-DARS-CP-013 / HISYS-T-DARS-CP-015 is now `DOCS-PREP + IMPLEMENTATION PLANNED + HUMAN-GATED ACTION PLANNED`. R5 implementation remains planned for `src/hisys/agents/dars_unattended_policy.py`, `src/hisys/operations/dars_unattended_runner.py`, and their RED→GREEN tests.
- Boundary: this checkpoint performs no live provider/model call, no credential lookup, no activation of standing unattended approval, no mutation, no publication, no deployment, no release, no external notification, and no human-review removal. R5 ACTION, the bounded unattended live canary, remains separately HUMAN-GATED.

## DARS-LIVE-RELEASE-R6-STATUS-ROLLBACK — Local live status and rollback readiness (2026-05-23)

- Scope: implemented the local DARS live/unattended operations status surface and rollback-readiness runbooks.
- Artifacts: `src/hisys/operations/dars_live_status.py`, `tests/unit/test_dars_live_status.py`, `docs/runbooks/dars-live-operations.md`, `docs/runbooks/dars-live-rollback.md`, and the `hisys dars-live-status` CLI.
- Evidence contract: status reports include policy refs, standing approval ref, kill-switch state, budget/circuit-breaker state, failed-run count, latest boundary refs, rollback runbook ref, release/version ref, and explicit boundary flags showing no external call, no credential lookup, no mutation, no publication, no live action authorization, and no standing approval activation.
- Traceability: HISYS-FR-DARS-CP-014 / HISYS-T-DARS-CP-016 is now `GREEN` for local status/rollback readiness.
- Boundary: no live provider/model call, credential lookup, standing unattended approval activation, rollback execution, mutation, publication, deployment, release, external notification, or human-review removal was introduced.

## DARS-LIVE-RELEASE-R5-UNATTENDED-PREP — Bounded unattended dry-run runner (2026-05-23)

- Scope: implemented the bounded standing approval policy validator and unattended advisory runner for local dry-run rehearsal through fake/injected transports only.
- Artifacts: `src/hisys/agents/dars_unattended_policy.py`, `src/hisys/operations/dars_unattended_runner.py`, `tests/unit/test_dars_unattended_policy.py`, and `tests/unit/test_dars_unattended_runner.py`. The R2 adapter now treats equivalent filesystem policy refs as coherent while preserving URI and mismatched-path failure behavior.
- Evidence contract: standing approval validation enforces finite validity, request-class allowlist, budget/rate/prompt/output caps, kill-switch and audit-retention refs, post-run human review, advisory-only authority, and raw-secret rejection. The runner writes `<instance>/runtime-boundary/dars-unattended-advisory/<YYYYMMDD>/<policy_id>/<request_id>.{json,md}` for completed, blocked, failed, or circuit-broken runs, and preserves `external_call_made=false`, `model_boundary_crossed=false`, `mutation_performed=false`, `publication_performed=false`, `external_action_performed=false`, `advisory_only=true`, `requires_human_review=true`, and `requires_post_run_human_review=true`.
- Traceability: HISYS-FR-DARS-CP-013 / HISYS-T-DARS-CP-015 is now `PREP-GREEN + HUMAN-GATED ACTION PLANNED`. R5 ACTION, the bounded unattended live canary, remains separately HUMAN-GATED.
- Boundary: no live provider/model call, credential lookup, standing unattended approval activation, mutation, publication, deployment, release, external notification, or human-review removal was introduced.

## DARS-PANEL-RLOOP-OPT-1 — Local completion audit (2026-05-21)

- Scope: ran the fixture-local `hisys run-dars-panel-golden` and
  `hisys dars-panel-readiness --write-report` surfaces against a private
  `mktemp` instance root and recorded the deterministic JSON/Markdown
  evidence and the field-level mapping of the readiness surface to the
  four required completion boundaries (fixture complete; localhost
  rehearsal human-gated; remote subscription injected-executor-only;
  live provider execution not smoked).
- Audit artifact: `docs/reports/dars-panel-local-completion-audit.md`.
  This is the controlled local-completion audit produced before the
  Ralph queue returns to `MB-CODEBASE-M21-6-PREP`.
- Result: no additional safe local DARS panel completion candidate
  remains. The DARS panel productization line is closed for
  `local_fixture_localhost_controlled_advisory_complete`. Live external
  provider execution remains unimplemented and unproven and is not
  authorized by this audit.
- Boundary: no live model call, real remote provider call, credential
  lookup, raw secret capture, browser/search/tool execution, publication,
  deployment, schema/data migration against non-fixture data, force
  push, new remote configuration, or destructive operation is introduced.

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
## DARS-LIVE-RELEASE-R4-PANEL-SMOKE-PREP — Multi-critic live-provider panel smoke runbook and example packets (2026-05-23)

- Scope: authored the controlled R4 PREP runbook and the example
  policy/activation packets that future R4 ACTION will consume. PREP
  produces only docs/control artifacts; no live provider call, model
  call, credential lookup, network request, mutation, publication,
  deployment, or remote push beyond the normal `git push origin dars`
  checkpoint is performed.
- New artifacts:
  - `docs/runbooks/dars-live-provider-panel-smoke.md` — multi-critic
    panel smoke runbook documenting preconditions (reviewed R3 single
    smoke as a hard precondition, decision packet, R1 policy
    validation, activation packet, approval/backend/policy-ref
    coherence, per-critic redaction, per-critic
    `max_prompt_bytes`/`max_output_bytes`/`rate_limit_per_minute`,
    panel-level `cost_budget_ref`, R2 env gate, controlled instance
    root, operator certainty), the multi-critic procedure (two or more
    critics under one decision packet, unique
    `source_execution_id` per critic, shared `request_id`/`panel_id`),
    the per-critic + panel-level boundary record requirements with
    explicit failure-isolation expectations
    (`mutation_performed=false`, `publication_performed=false`,
    `advisory_only=true`, `requires_human_review=true`,
    `external_call_made=true`,
    `model_boundary_crossed=true`, `allowed_actions=advisory_only`,
    advisory `synthesis` may report `needs_more_evidence` when fewer
    critics complete than the decision packet requires), the post-run
    human review steps, and an exhaustive stop-condition list including
    duplicate `source_execution_id`, mismatched `request_id`, and
    cross-critic policy mismatches. The runbook explicitly does not by
    itself authorize the live call and explicitly records that R4
    ACTION requires a fresh human-approved decision packet plus a
    separately approved real-provider transport (out of scope for
    PREP).
  - `docs/examples/dars/live-provider-panel-smoke.policy.example.json`
    — credential-reference-only sample policy that passes
    `validate_live_provider_policy_packet` with zero errors and the
    deterministic `live_provider_dispatch_not_authorized_by_policy_alone`
    warning.
  - `docs/examples/dars/live-provider-panel-smoke.activation.example.json`
    — matching activation packet that passes
    `validate_dars_backend_activation_packet`, declares
    `endpoint_scope=external_api`, `allowed_actions=advisory_only`,
    `human_approved=true`, and references the example policy.
- New tests:
  - `tests/unit/test_dars_live_provider_panel_smoke_runbook.py` — 10
    focused tests covering runbook existence, required-phrase coverage
    (multi-critic, two or more critics, panel_id, per-critic + panel-
    level boundary record, failure isolation, advisory synthesis,
    decision packet, approval/credential refs, redaction policy,
    `max_prompt_bytes`/`max_output_bytes`/`rate_limit_per_minute`,
    `cost_budget_ref`, env gate, boundary record flags, post-run human
    review), stop-condition coverage (missing decision packet, raw
    secret, credential lookup, mutation/publication/tool/browser/search
    authority, budget/rate-limit violation, secret-scan hit, output
    redaction failure, duplicate `source_execution_id`, cross-critic
    policy mismatch, operator uncertainty), R1+R2+R3 module/anchor
    anchoring, the explicit "does not by itself authorize" assertion,
    the R3 reviewed single-smoke + `live_provider_advisory_smoked`
    precondition assertion, R1 policy validator acceptance of the
    example policy (with the deterministic warning), the
    credential-reference-only invariant in the example policy, the
    activation validator acceptance of the example activation, and the
    cross-packet matching between the example policy and activation.
- Validation commands (all GREEN):

  ```bash
  PYTHONPATH=src:. pytest tests/unit/test_dars_live_provider_policy.py tests/unit/test_dars_live_provider_transport.py tests/unit/test_dars_live_provider_adapter.py tests/unit/test_dars_live_provider_single_smoke_runbook.py tests/unit/test_dars_live_provider_panel_smoke_runbook.py -q
  # 65 passed
  PYTHONPATH=src:. pytest tests/unit -q -k dars
  # 340 passed, 836 deselected
  python3 scripts/validate_traceability.py
  # OK: schemas, trace test, and Hermes boundary convention pass traceability checks
  python3 scripts/scan_secrets.py
  # secret_scan: scanned_files=802 skipped_files=0 hit_count=0
  git diff --check
  ```

- Boundary: no live provider/model call, credential lookup, standing
  unattended approval, release artifact publication, deployment,
  package upload, external notification, mutation outside the
  repository docs/control files, destructive Git operation, or
  human-review removal. The R4 PREP runbook explicitly preserves R4
  ACTION as a separately approved HUMAN-GATED row that additionally
  requires a reviewed R3 ACTION smoke (`live_provider_advisory_smoked`)
  as a precondition.
- Next safe task: `DARS-LIVE-RELEASE-R5-UNATTENDED-PREP` — the
  bounded standing-approval policy + unattended runner contract +
  dry-run rehearsal evidence. R5 ACTION (limited live unattended
  canary) remains HUMAN-GATED.

## DARS-LIVE-RELEASE-R3-SINGLE-SMOKE-PREP — Single-critic live-provider smoke runbook and example packets (2026-05-23)

- Scope: authored the controlled R3 PREP runbook and the example
  policy/activation packets that future R3 ACTION will consume. PREP
  produces only docs/control artifacts; no live provider call, model
  call, credential lookup, network request, mutation, publication,
  deployment, or remote push beyond the normal `git push origin dars`
  checkpoint is performed.
- New artifacts:
  - `docs/runbooks/dars-live-provider-single-smoke.md` — single-critic
    live-provider smoke runbook documenting preconditions
    (decision packet, R1 policy validation, activation packet,
    approval-ref / backend-id / policy-ref coherence, credential
    reference scheme, bounded prompt/output/rate limits,
    `cost_budget_ref`, redaction policy, R2 env gate, controlled
    instance root, operator certainty), the single-call procedure, the
    boundary-record requirements
    (`schema_id=hisys.dars.live_provider_adapter`, `mode=live`,
    `external_call_made=true`, `mutation_performed=false`,
    `publication_performed=false`, `allowed_actions=advisory_only`,
    `advisory_only=true`, `requires_human_review=true`), the post-run
    human review steps, and an exhaustive stop-condition list. The
    runbook explicitly records that it does not by itself authorize the
    live call and that R3 ACTION requires a fresh human-approved
    decision packet plus a separately approved real-provider transport.
  - `docs/examples/dars/live-provider-single-smoke.policy.example.json`
    — credential-reference-only sample policy that passes
    `validate_live_provider_policy_packet` with zero errors and the
    deterministic `live_provider_dispatch_not_authorized_by_policy_alone`
    warning.
  - `docs/examples/dars/live-provider-single-smoke.activation.example.json`
    — matching activation packet that passes
    `validate_dars_backend_activation_packet`, declares
    `endpoint_scope=external_api`, `allowed_actions=advisory_only`,
    `human_approved=true`, and references the example policy.
- New tests:
  - `tests/unit/test_dars_live_provider_single_smoke_runbook.py` — 9
    focused tests covering runbook existence, required-phrase coverage
    (decision packet, approval/credential refs, redaction policy,
    bounded prompt/output/rate-limit fields, `cost_budget_ref`, env
    gate, boundary record flags, post-run human review), stop-condition
    coverage (missing decision packet, raw secret, credential lookup,
    mutation/publication/tool/browser/search authority, budget/rate
    violation, secret-scan hit, output redaction failure, operator
    uncertainty), R1+R2 module/anchor anchoring, the explicit "does not
    by itself authorize" assertion, R1 policy validator acceptance of
    the example policy (with the deterministic warning), the
    credential-reference-only invariant in the example policy, the
    activation validator acceptance of the example activation, and the
    cross-packet matching between the example policy and activation.
- Validation commands (all GREEN):

  ```bash
  PYTHONPATH=src:. pytest tests/unit/test_dars_live_provider_policy.py tests/unit/test_dars_live_provider_transport.py tests/unit/test_dars_live_provider_adapter.py tests/unit/test_dars_live_provider_single_smoke_runbook.py -q
  # 55 passed
  PYTHONPATH=src:. pytest tests/unit -q -k dars
  # 330 passed, 836 deselected
  python3 scripts/validate_traceability.py
  # OK: schemas, trace test, and Hermes boundary convention pass traceability checks
  python3 scripts/scan_secrets.py
  # secret_scan: scanned_files=798 skipped_files=0 hit_count=0
  git diff --check
  ```

- Boundary: no live provider/model call, credential lookup, standing
  unattended approval, release artifact publication, deployment, package
  upload, external notification, mutation outside the repository
  docs/control files, destructive Git operation, or human-review
  removal. The R3 PREP runbook explicitly preserves R3 ACTION as a
  separately approved HUMAN-GATED row: R3 ACTION requires a fresh
  human-approved decision packet, a separately approved real-provider
  transport (out of scope for R3 PREP), the operator-managed env gate,
  and a post-run human reviewer.
- Next safe task: `DARS-LIVE-RELEASE-R4-PANEL-SMOKE-PREP` — the
  multi-critic live-provider panel smoke runbook and example packets.
  R4 ACTION remains HUMAN-GATED.

## DARS-LIVE-RELEASE-R2 — Fail-closed live-provider adapter (2026-05-23)

- Scope: implemented the R2 fail-closed live-provider adapter that
  composes the R1 policy validator
  (`hisys.agents.dars_live_provider_policy`), the existing backend
  activation validator (`hisys.agents.dars_backend_activation`), and the
  R1 fake/injected transport seam
  (`hisys.agents.dars_live_provider_transport`) into a single fail-closed
  entry point. The work satisfies the R2 milestone defined in
  `docs/plans/dars-panel-live-provider-unattended-release-final-plan.md`.
- New module:
  - `src/hisys/agents/dars_live_provider_adapter.py` exports
    `DARS_LIVE_PROVIDER_ADAPTER_SCHEMA_ID`,
    `DARS_LIVE_PROVIDER_ADAPTER_SCHEMA_VERSION`,
    `DARS_LIVE_PROVIDER_LIVE_TRANSPORT_ENV_VAR`,
    `DarsLiveProviderAdapterRequest`, `DarsLiveProviderAdapterResult`,
    and `run_dars_live_provider_adapter`. The adapter validates the
    policy packet, validates the activation packet, cross-checks
    approval_ref / backend_id / activation endpoint_scope /
    remote_policy_packet_ref coherence, and (for live mode) requires the
    `HISYS_DARS_LIVE_PROVIDER_LIVE_TRANSPORT_ENABLED=true` environment
    gate before any transport call is reachable. Both supported modes
    (`dry_run` and `live`) currently route through the injected
    `FakeLiveProviderTransport`; a real-provider transport requires a
    separately approved later increment.
- Safety envelope: every persisted boundary record under
  `<instance>/runtime-boundary/dars-live-provider-adapter/<YYYYMMDD>/<request_id>/<backend_id>-<source_execution_id>.{json,md}`
  carries `external_call_made=false`,
  `model_boundary_crossed=false`, `mutation_performed=false`,
  `publication_performed=false`, `advisory_only=true`,
  `requires_human_review=true`, and `allowed_actions=advisory_only`. The
  record never contains `credential_ref`, raw tokens, authorization
  headers, or any other secret material. Boundary records are written
  for both completed and failed runs so audit evidence is preserved on
  every gate rejection.
- Deterministic failure codes:
  `live_provider_transport_required` (raised before any work when no
  transport is supplied), `live_provider_policy_packet_unreadable`,
  `live_provider_activation_packet_unreadable`,
  `live_provider_policy_invalid` (with `policy_issue_codes` carrying the
  R1 validator codes), `live_provider_activation_invalid` (with
  `activation_issue_codes` carrying the activation validator codes),
  `live_provider_approval_ref_mismatch`,
  `live_provider_backend_id_mismatch`,
  `live_provider_activation_scope_mismatch`,
  `live_provider_activation_policy_ref_mismatch`,
  `live_provider_env_gate_missing`, plus any transport-level failure
  code propagated from `run_live_provider_transport`.
- New tests:
  - `tests/unit/test_dars_live_provider_adapter.py` — 17 focused tests
    covering schema-constant stability, baseline policy/approval/
    credential-ref acceptance, missing-transport fail-closed behaviour,
    policy without credential-ref / with raw secret rejection,
    activation without human approval rejection, approval-ref mismatch
    (request vs activation, policy vs request), backend-id mismatch,
    env-gate missing in live mode, env-gate present in live mode
    success, mutation-authority rejection in policy, boundary-record
    writer correctness (path under instance root, schema-id, safety
    envelope, no credential leakage), transport-failure-code
    propagation with boundary record, packet-file unreadable
    fail-closed behaviour, unknown-mode rejection, invalid yyyymmdd
    rejection.
- Validation commands (all GREEN):

  ```bash
  PYTHONPATH=src:. pytest tests/unit/test_dars_live_provider_policy.py tests/unit/test_dars_live_provider_transport.py tests/unit/test_dars_live_provider_adapter.py -q
  # 46 passed
  PYTHONPATH=src:. pytest tests/unit -q -k dars
  # 321 passed, 836 deselected
  python3 scripts/validate_traceability.py
  # OK: schemas, trace test, and Hermes boundary convention pass traceability checks
  python3 scripts/scan_secrets.py
  # secret_scan: scanned_files=794 skipped_files=0 hit_count=0
  git diff --check
  ```

- Boundary: no live provider/model call, credential lookup, standing
  unattended approval, release artifact publication, deployment, package
  upload, external notification, mutation outside the controlled
  Hisys runtime instance root, destructive Git operation, or
  human-review removal. The R2 adapter authorizes only a future
  separately-approved real-provider transport to be wired behind the
  same gates; merely importing or wiring the R2 module cannot perform a
  live provider call.
- Next safe task: `DARS-LIVE-RELEASE-R3-SINGLE-SMOKE-PREP` — the
  single-critic live-provider smoke runbook and decision packet
  template that documents the conditions a human must satisfy before the
  one real-provider call is attempted under R3.

## DARS-LIVE-RELEASE-R1 — Live-provider policy and fake transport contract (2026-05-23)

- Scope: implemented the R1 controlled live-provider policy validator and the
  R1 live-provider transport request/result contract with a fake/injected
  executor seam. The work satisfies the R1 RED baselines defined in
  `docs/test/dars-critic-panel-runtime-std.md` §3 and the R1 milestone defined
  in `docs/plans/dars-panel-live-provider-unattended-release-final-plan.md`.
- New modules:
  - `src/hisys/agents/dars_live_provider_policy.py` exports
    `LIVE_PROVIDER_POLICY_SCHEMA_ID`,
    `LIVE_PROVIDER_POLICY_SCHEMA_VERSION`, and
    `validate_live_provider_policy_packet`. The validator rejects raw secret
    fields/values, requires a controlled credential reference scheme
    (`env://`, `secret-manager-ref://`, `vault://`,
    `subscription-account-ref://`, `keychain-ref://`), forbids mutation /
    publication authority, requires `allowed_actions=advisory_only`,
    `external_call_allowed=true`, and `requires_human_review=true`, enforces
    positive `max_prompt_bytes` / `max_output_bytes` / `rate_limit_per_minute`,
    requires an `approval_ref` / `cost_budget_ref` / `redaction_policy_ref` /
    `audit_required=true`, and emits the deterministic warning
    `live_provider_dispatch_not_authorized_by_policy_alone` even when the
    packet is structurally valid.
  - `src/hisys/agents/dars_live_provider_transport.py` exports
    `LIVE_PROVIDER_TRANSPORT_SCHEMA_ID`,
    `LIVE_PROVIDER_TRANSPORT_SCHEMA_VERSION`,
    `LiveProviderTransportRequest`, `LiveProviderTransportResult`,
    `FakeLiveProviderTransport`, `LiveProviderTransportFailure`, and
    `run_live_provider_transport`. The request dataclass rejects invalid
    transport kinds, non-advisory actions, mutation/publication authority,
    disabled `external_call_allowed`, disabled `requires_human_review`, raw
    prompt text (only the controlled redacted prompt-packet schemes
    `redacted://`, `prompt-ref://`, `policy-redacted://` are accepted),
    non-positive max prompt/output bytes, and prompt sizes that exceed
    `max_prompt_bytes`. The executor payload deliberately excludes any
    credential, token, authorization, or raw-secret field; provider/model
    refs, redaction-policy refs, and approval refs are the only context the
    injected executor receives.
- Safety envelope: every transport result preserves
  `advisory_only=true`, `requires_human_review=true`,
  `mutation_performed=false`, `publication_performed=false`,
  `external_call_made=false`, and `model_boundary_crossed=false`. The fake
  transport never opens a socket, never resolves a credential reference, and
  never calls a provider. Output validation enforces deterministic failure
  codes: `live_provider_empty_output`, `live_provider_output_too_long`,
  `live_provider_output_not_redacted`,
  `live_provider_output_claims_unauthorized_authority`,
  `live_provider_invalid_executor_payload`,
  `live_provider_invalid_output_byte_count`, and
  `live_provider_transport_unhandled_error`.
- New tests:
  - `tests/unit/test_dars_live_provider_policy.py` — 13 focused tests
    covering credential-reference acceptance, raw-secret rejection across
    `api_key`, `token`, `password`, `authorization`, secret-shaped
    `provider_token_value`, and secret-prefixed `credential_ref` values
    (`sk-*` / `hf_*`), missing-credential rejection, unknown credential-ref
    scheme rejection, mutation/publication authority rejection, non-advisory
    `allowed_actions` rejection, disabled `external_call_allowed` and
    `requires_human_review` rejection, non-positive max prompt/output bytes
    and rate-limit rejection, expired packet rejection, non-allowlisted
    provider rejection (only `codex` and `claude` are accepted in R1),
    missing-approval/cost-budget-ref rejection, and the deterministic
    dispatch-warning invariant.
  - `tests/unit/test_dars_live_provider_transport.py` — 16 focused tests
    covering schema-constant stability, fake-executor success without
    external call, missing-transport fail-closed behaviour, raw-prompt-text
    rejection, invalid-allowed-actions / mutation-authority /
    disabled-`external_call_allowed` / disabled-`requires_human_review`
    rejection, unbounded prompt/output rejection, oversized prompt-byte
    rejection, unknown-transport-kind rejection, executor-raised
    `LiveProviderTransportFailure` propagation as a deterministic failure
    code, oversized-output rejection, empty-output rejection,
    raw-secret-marker rejection in output, and unauthorized-authority claim
    rejection in output.
  - Test fixtures that exercise the raw-secret rejection paths use the
    `FAKE_`/`sk-fake_*`/`hf_fake_*` prefixes recognised by
    `hisys.security.secret_scan.SAFE_VALUE_PREFIXES` and the `[REDACTED]`
    sentinel handling, so `scripts/scan_secrets.py` reports `hit_count=0`
    across the full repository.
- Validation commands (all GREEN):

  ```bash
  PYTHONPATH=src:. pytest tests/unit/test_dars_live_provider_policy.py tests/unit/test_dars_live_provider_transport.py -q
  # 29 passed
  PYTHONPATH=src:. pytest tests/unit -q -k dars
  # 304 passed, 836 deselected
  python3 scripts/validate_traceability.py
  # OK: schemas, trace test, and Hermes boundary convention pass traceability checks
  python3 scripts/scan_secrets.py
  # secret_scan: scanned_files=792 skipped_files=0 hit_count=0
  git diff --check
  ```

- Boundary: no live provider/model call, credential lookup, standing
  unattended approval, release artifact publication, deployment, package
  upload, external notification, mutation outside the repository, destructive
  Git operation, or human-review removal is introduced by this increment. The
  R1 policy validator and transport contract authorize only a future R2
  fail-closed adapter to consume them; merely importing or wiring these
  modules cannot perform a live provider call.
- Next safe task: `DARS-LIVE-RELEASE-R2-ADAPTER` — the fail-closed live
  provider adapter that requires policy + activation + credential-reference +
  decision-packet gates before any real transport entry point can be
  reached.

## DARS-LIVE-RELEASE-R0 — Final live-provider/unattended/release controlled-document update (2026-05-23)

- Scope: archived the prior active `ralph.md` into `ralph.history.md`, created a short active DARS live-provider release controller, and updated SRS/SDD/STD/RTM documents to define the final claim ladder and verification gates.
- Plan anchor: `docs/plans/dars-panel-live-provider-unattended-release-final-plan.md`.
- Decision record: `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.68.md`.
- New claim ladder:

```text
local_fixture_localhost_controlled_advisory_complete
  -> live_provider_advisory_smoked
  -> multi_critic_live_provider_advisory_complete
  -> bounded_unattended_advisory_operation_ready
  -> release_candidate_ready
  -> released_for_controlled_advisory_use
```

- Boundary: this R0 update is documentation/control only. It performs no live provider/model call, credential lookup, standing unattended approval, release, deployment, package upload, external notification, mutation outside the repository docs/control files, destructive Git action, or human-review removal.
- Next safe task: `DARS-LIVE-RELEASE-R1-POLICY`, which starts with RED tests for live-provider policy and fake/injected transport contracts.
