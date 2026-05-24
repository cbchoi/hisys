# DARS R4H Hermes-mediated panel advisory — 2026-05-24

## Result

The blocked R4 Codex subprocess panel path was split from a new Hermes-mediated advisory path. The Hermes-mediated path completed a two-critic advisory panel and is accepted only under the following bounded claim:

```text
r4_hermes_mediated_multi_critic_panel_advisory_completed_with_findings
```

This is not a Codex CLI subprocess success claim. It does not complete the R4-C Codex subscription subprocess smoke, does not prove raw provider API readiness, and does not prove adapter-native readiness.

## Request context

- Operator asked whether Codex subprocess execution was required: `codex subprocess실행까지 해야하지 않나??`
- The R4 Codex subprocess panel smoke was attempted and retried under bounded scope.
- Both attempts stopped before critique output because Codex CLI refresh state returned `refresh_token_reused`.
- Operator then accepted the recommended split: `추천하는데로 해보자`.
- Action time: `2026-05-24T08:08:46Z`
- Repository branch: `dars`
- Baseline before R4H advisory artifact: `039e00e docs: record dars r4 codex panel retry auth stop`

## Transport split

```text
R4-C: codex_cli_subprocess_prompt_mode
status: attempted/retried, auth-blocked, no critique output, no panel boundary evidence

R4H: hermes_mediated_model_advisory
status: completed advisory-only 2-critic panel through Hermes runtime
```

## R4H boundary

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
human_review_required_for_consequential_use=true
```

Artifact:

```text
docs/examples/dars/hermes-mediated-r4h-multi-critic-panel.advisory.json
```

## Critic findings

### logical_consistency_critic

The logical-consistency critic found that R4H is coherent only as a separate Hermes-mediated advisory path. The prior R4 Codex CLI subprocess attempts produced no critique output or panel boundary evidence, so they cannot support `r4_codex_subscription_multi_critic_panel_smoke_completed_with_findings`. The R4H claim is acceptable only if it remains bounded to Hermes-mediated advisory evidence and is not upgraded into Codex subprocess success, raw provider API readiness, adapter-native readiness, R5 readiness, R7 readiness, or R8 readiness.

### evidence_governance_critic

The evidence-governance critic found that the proposed R4H evidence preserves the advisory boundary if the record explicitly states `codex_cli_subprocess_call=false`, `raw_provider_api_call_by_hisys=false`, `credential_lookup_by_hisys=false`, `allowed_actions=advisory_only`, `mutation_performed=false`, `publication_performed=false`, and `requires_human_review=true`. The main risk is claim inflation: the Hermes-mediated panel must not be interpreted as a Codex CLI subprocess success or as readiness for unattended, release-candidate, or release execution.

## Accepted claim

```text
r4_hermes_mediated_multi_critic_panel_advisory_completed_with_findings
```

Scope:

```text
Hermes-mediated model advisory only;
advisory-only findings for human review;
no mutation, publication, release, external notification, credential lookup, raw provider API call by Hisys, or Codex CLI subprocess call.
```

## Rejected or not accepted claims

- `r4_codex_subscription_multi_critic_panel_smoke_completed_with_findings`
- `codex_cli_subprocess_prompt_mode_completed`
- `live_provider_panel_advisory_smoked` for raw provider/API or adapter-native paths
- raw provider API readiness
- adapter-native readiness
- bounded unattended advisory operation readiness
- release-candidate readiness
- controlled release execution readiness

## Boundary assessment

- The R4-C Codex subprocess path remains blocked by Codex CLI refresh-state reconciliation outside Hisys.
- The R4H Hermes-mediated path is useful as a DARS tool/advisory product path, but its critic independence is weaker than separate subprocess/provider-boundary evidence.
- The completed R4H advisory can guide human review and claim-ladder design only.
- No Hisys credential lookup, raw provider API call, Codex subprocess execution, mutation, publication, deployment, release, external notification, R5 action, R7 action, R8 action, or human-review removal is introduced by this artifact.

## Next safe task

```text
DARS-LIVE-RELEASE-R4H-HERMES-MEDIATED-PANEL-ADVISORY-REVIEW-GATE
```

The review gate may inspect this R4H artifact and decide whether to keep Hermes-mediated advisory as a separate product path. It must not claim R4-C subprocess completion or advance to R5/R7/R8 without separate approved evidence.
