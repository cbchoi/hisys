# Readiness decision record v0.0.81 — R4H Hermes-mediated productization prep

## Decision

Accepted prep claim:

```text
r4h_hermes_mediated_productization_prep_ready_for_human_review
```

The operator instructed `go` after R4H was selected as the active continuation path and R4C was deferred. This record defines the governed Hermes-mediated DARS tool path contract for R4H productization prep.

## Evidence refs

- `src/hisys/operations/dars_r4h_productization.py`
- `tests/unit/test_dars_r4h_productization_prep.py`
- `docs/examples/dars/hermes-mediated-r4h-productization-prep.example.json`
- `docs/reports/dars-r4h-hermes-mediated-productization-prep-2026-05-24.md`
- `docs/reports/dars-r4h-hermes-mediated-panel-review-gate-proceed-2026-05-24.md`

## Productization-prep contract

```text
active_branch=R4H
active_transport_kind=hermes_mediated_model_advisory
request_schema=hisys.dars.r4h_hermes_mediated_request
response_schema=hisys.dars.r4h_hermes_mediated_response
supported_critic_roles=logical_consistency_critic,evidence_governance_critic
next_safe_task=DARS-LIVE-RELEASE-R4H-HERMES-MEDIATED-PANEL-REQUEST-RESPONSE-HARNESS
```

## Deferred branch relation

```text
deferred_branch=R4C
deferred_transport_kind=codex_cli_subprocess_prompt_mode
deferred_reason=codex_refresh_token_reused
future_r4c_task=DARS-LIVE-RELEASE-R4C-CODEX-REFRESH-STATE-RECONCILIATION-OUTSIDE-HISYS
r4c_is_not_blocker_for_r4h_productization_prep=true
```

## Boundary

```text
codex_cli_subprocess_call=false
codex_cli_subprocess_completion_claim=false
raw_provider_api_call_by_hisys=false
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
human_review_required_for_consequential_use=true
```

This is not a Codex CLI subprocess success claim. It is a local/read-only productization-prep contract for the R4H Hermes-mediated advisory branch.
