# Readiness decision record v0.0.79 — DARS R4H Hermes-mediated panel advisory

## Decision

Accepted bounded advisory claim:

```text
r4_hermes_mediated_multi_critic_panel_advisory_completed_with_findings
```

This record introduces R4H as a separate Hermes-mediated model advisory path after the R4-C Codex CLI subprocess panel path remained auth-blocked. It does not reclassify the blocked Codex subprocess attempts as successful.

## Evidence refs

- `docs/reports/dars-r4h-hermes-mediated-panel-advisory-2026-05-24.md`
- `docs/examples/dars/hermes-mediated-r4h-multi-critic-panel.advisory.json`
- `docs/reports/dars-r4-codex-subprocess-panel-smoke-auth-stop-2026-05-24.md`
- `docs/reports/dars-r4-action-decision-packet-mapped-subscription-panel-2026-05-24.md`

## Boundary

```text
transport_kind=hermes_mediated_model_advisory
provider_runtime=openai-codex via Hermes runtime
critic_count=2
completed_critic_count=2
codex_cli_subprocess_call=false
raw_provider_api_call_by_hisys=false
credential_lookup_by_hisys=false
allowed_actions=advisory_only
mutation_performed=false
publication_performed=false
external_notification_performed=false
release_action_performed=false
requires_human_review=true
```

## Explicitly rejected claim upgrades

- `r4_codex_subscription_multi_critic_panel_smoke_completed_with_findings`
- `codex_cli_subprocess_prompt_mode_completed`
- raw provider API readiness
- adapter-native readiness
- R5 unattended readiness
- R7 release-candidate readiness
- R8 release execution readiness

## Next safe task

```text
DARS-LIVE-RELEASE-R4H-HERMES-MEDIATED-PANEL-ADVISORY-REVIEW-GATE
```
