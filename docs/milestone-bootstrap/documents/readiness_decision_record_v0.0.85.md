# Readiness decision record v0.0.85 — R5 canary scope selected; R4C excluded from this release

## Operator instruction

`R5진행 R4C는 이번 release에서 제외`

## Decision

formal_hisys_result=r5_canary_scope_selected_with_r4c_excluded_from_this_release
local_advisory_result=R5_CANARY_SCOPE_SELECTED_R4C_EXCLUDED_FROM_THIS_RELEASE
next_safe_task=DARS-LIVE-RELEASE-R5-CANARY-PACKET-PREP

The R5 bounded unattended canary packet becomes the active next evidence row. R4C Codex subprocess panel completion is excluded from this release scope and is not a blocker for this release candidate path. R4C remains future work only.

```text
r4c_in_this_release=false
r4c_future_work_allowed=true
r4c_codex_subprocess_completion_required_for_this_release=false
r5_canary_packet_prep_selected=true
r5_live_canary_executed=false
bounded_unattended_advisory_operation_ready=false
release_candidate_ready=false
released_for_controlled_advisory_use=false
standing_unattended_approval_activated=false
live_provider_model_call_made=false
codex_cli_subprocess_call=false
raw_provider_api_call_by_hisys=false
credential_lookup_by_hisys=false
mutation_performed=false
publication_performed=false
requires_human_review=true
```

## Evidence basis

Existing R5 PREP evidence includes the standing approval policy validator, local dry-run unattended runner, audit ledger writer, budget/rate caps, kill-switch checks, circuit breakers, and post-run human review requirements. Existing R6 evidence includes local status and rollback readiness surfaces. This record authorizes only the packet-preparation step that assembles those controls for human review.

## Boundary

No live provider/model call, Codex subprocess call, raw provider API call, credential lookup, standing unattended approval activation, mutation, publication, release action, deployment, external notification, or human-review removal is authorized or performed by this decision record.
