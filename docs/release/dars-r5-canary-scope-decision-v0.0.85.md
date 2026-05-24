---
doc_id: HISYS-DARS-R5-CANARY-SCOPE-DECISION-001
title: DARS R5 Canary Scope Decision with R4C Release Exclusion
version: v0.0.85
status: scope-decision-for-human-review
created: 2026-05-24
---

# DARS R5 Canary Scope Decision with R4C Release Exclusion

## Request context

The operator instructed `R5진행 R4C는 이번 release에서 제외`. This record selects the R5 bounded unattended canary path as the active next release-evidence row and excludes R4C Codex subprocess panel completion from this release scope.

accepted_claim=r5_canary_scope_selected_with_r4c_excluded_from_this_release

## Scope decision

R5 proceeds as the next evidence line through a canary packet preparation task. This decision does not execute the canary, activate standing unattended approval, call a live provider/model, or run a Codex subprocess. It records the release-scope rule that R4C is not required for this release candidate path because R4H is the scoped human-review substitute for the multi-critic advisory branch.

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

## R5 packet preparation requirements

The next safe task prepares the R5 canary packet from existing R5 PREP policy/runner evidence and the R6 local status/rollback surfaces. The packet must include finite standing-approval refs, request-class scope, budget/rate/prompt/output caps, kill-switch ref, audit-retention ref, post-run human review, and explicit stop conditions.

The packet may produce local docs/tests/control records only. The later R5 canary execution remains a separate human-gated action that must validate standing approval and runtime boundaries immediately before execution.

## R4C release exclusion rule

R4C Codex subprocess panel completion is excluded from this release. It remains future work only and may be reopened later by a separate explicit operator instruction and decision packet. The current release line may use R4H evidence as the scoped substitute while preserving `raw_provider_api_readiness=false`, `adapter_native_readiness=false`, and `r4c_codex_subprocess_completion_required_for_this_release=false`.

## Boundary

This decision performs no live provider/model call, no Codex subprocess call, no raw provider API call, no credential lookup, no standing unattended approval activation, no mutation outside repository docs/tests/control files, no publication, no release action, no deployment, no external notification, and no human-review removal.

next_safe_task: `DARS-LIVE-RELEASE-R5-CANARY-PACKET-PREP`.
