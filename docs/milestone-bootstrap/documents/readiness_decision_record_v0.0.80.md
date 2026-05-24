# Readiness decision record v0.0.80 — R4H selected for continuation, R4C deferred

## Decision

Accepted review-gate claim:

```text
r4h_hermes_mediated_advisory_path_selected_for_continuation
```

The operator instructed:

```text
R4H로 진행 R4C는 추후 작업으로
```

R4H is now the active continuation path. R4C is deferred to a later transport-evidence task and must not block R4H productization prep.

## Evidence refs

- `docs/reports/dars-r4h-hermes-mediated-panel-review-gate-proceed-2026-05-24.md`
- `docs/reports/dars-r4h-hermes-mediated-panel-advisory-2026-05-24.md`
- `docs/examples/dars/hermes-mediated-r4h-multi-critic-panel.advisory.json`
- `docs/reports/dars-r4-codex-subprocess-panel-smoke-auth-stop-2026-05-24.md`

## Branch disposition

```text
active_branch=R4H
active_transport_kind=hermes_mediated_model_advisory
deferred_branch=R4C
deferred_transport_kind=codex_cli_subprocess_prompt_mode
deferred_reason=codex_refresh_token_reused
future_r4c_task=DARS-LIVE-RELEASE-R4C-CODEX-REFRESH-STATE-RECONCILIATION-OUTSIDE-HISYS
```

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

## Next safe task

```text
DARS-LIVE-RELEASE-R4H-HERMES-MEDIATED-PANEL-PRODUCTIZATION-PREP
```
