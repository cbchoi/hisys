# DARS R4H review gate — proceed with Hermes-mediated path, defer R4C — 2026-05-24

## Decision

The operator selected the R4H path as the active continuation and explicitly deferred R4C to later work:

```text
R4H로 진행 R4C는 추후 작업으로
```

Accepted review-gate claim:

```text
r4h_hermes_mediated_advisory_path_selected_for_continuation
```

This decision keeps the completed R4H Hermes-mediated advisory panel as the active product/workflow branch. It parks the R4C Codex CLI subprocess panel smoke as a future task blocked on Codex refresh-state reconciliation outside Hisys.

## Evidence scope

Reviewed prerequisite artifacts:

- `docs/reports/dars-r4h-hermes-mediated-panel-advisory-2026-05-24.md`
- `docs/examples/dars/hermes-mediated-r4h-multi-critic-panel.advisory.json`
- `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.79.md`
- `docs/reports/dars-r4-codex-subprocess-panel-smoke-auth-stop-2026-05-24.md`

## Active branch

```text
active_branch=R4H
active_transport_kind=hermes_mediated_model_advisory
active_claim=r4_hermes_mediated_multi_critic_panel_advisory_completed_with_findings
continuation_claim=r4h_hermes_mediated_advisory_path_selected_for_continuation
```

R4H may proceed as a Hermes-mediated advisory product/tool path. It remains advisory-only and human-review-required.

## Deferred branch

```text
deferred_branch=R4C
deferred_transport_kind=codex_cli_subprocess_prompt_mode
deferred_reason=Codex CLI refresh_token_reused before critique output or panel boundary evidence
future_task=DARS-LIVE-RELEASE-R4C-CODEX-REFRESH-STATE-RECONCILIATION-OUTSIDE-HISYS
```

R4C remains useful as a separate transport-independence and subprocess-boundary evidence path, but it is no longer the active blocker for R4H continuation.

## Boundary

```text
codex_cli_subprocess_completion_claim=false
raw_provider_api_readiness=false
adapter_native_readiness=false
r5_unattended_readiness=false
r7_release_candidate_readiness=false
r8_release_execution_readiness=false
credential_lookup_by_hisys=false
mutation_performed=false
publication_performed=false
external_notification_performed=false
release_action_performed=false
requires_human_review=true
```

## Accepted claim

```text
r4h_hermes_mediated_advisory_path_selected_for_continuation
```

## Not accepted

- `r4_codex_subscription_multi_critic_panel_smoke_completed_with_findings`
- `codex_cli_subprocess_prompt_mode_completed`
- raw provider API readiness
- adapter-native readiness
- R5 unattended readiness
- R7 release-candidate readiness
- R8 release execution readiness

## Next safe task

```text
DARS-LIVE-RELEASE-R4H-HERMES-MEDIATED-PANEL-PRODUCTIZATION-PREP
```

The next step should define how R4H becomes a governed Hermes-mediated DARS tool path, including request/response contract, boundary fields, supported use cases, review requirements, and how R4C remains a later optional transport-evidence work item.
