# Readiness Decision Record v0.0.87 — DARS R5 Canary Action Decision Packet Ready for Human Review

## Request context

The operator-selected scope from v0.0.85 is `R5진행 R4C는 이번 release에서 제외`
and the prepared canary packet was recorded in v0.0.86. This record executes
the local-safe `DARS-LIVE-RELEASE-R5-CANARY-ACTION-DECISION-PACKET` step only.
It connects the prepared R5 canary packet to a human-gated action decision
without executing the bounded unattended live canary.

formal_hisys_result=r5_canary_action_decision_packet_ready_for_human_review
local_advisory_result=R5_CANARY_ACTION_DECISION_PACKET_READY_FOR_HUMAN_REVIEW
next_safe_task=DARS-LIVE-RELEASE-R5-CANARY-ACTION-HUMAN-REVIEW-GATE

## Evidence scope

- The R5 canary packet preparation
  (`docs/release/dars-r5-canary-packet-prep-v0.0.86.md`) and the R5 canary
  scope decision (`docs/release/dars-r5-canary-scope-decision-v0.0.85.md`)
  remain the prior controlled inputs to this record.
- The R5 PREP policy validator (`src/hisys/agents/dars_unattended_policy.py`),
  the dry-run runner (`src/hisys/operations/dars_unattended_runner.py`), and
  the standing-approval example policy
  (`docs/examples/dars/unattended-standing-approval.example.json`) remain
  GREEN as the reference base for the canary action decision packet.
- R6 local status and rollback runbooks
  (`docs/runbooks/dars-live-operations.md` and
  `docs/runbooks/dars-live-rollback.md`) remain GREEN and are referenced by
  the canary action decision packet.
- R4H continues as the scoped human-review advisory substitute; R4C remains
  deferred and is not a release blocker for this packet.
- No R5 canary action evidence is produced by this record; canary execution
  remains a separately HUMAN-GATED action.

## Boundary flags

```text
r5_canary_action_decision_packet_ready=true
r5_live_canary_executed=false
standing_unattended_approval_activated=false
live_provider_model_call_made=false
codex_cli_subprocess_call=false
raw_provider_api_call_by_hisys=false
credential_lookup_by_hisys=false
mutation_performed=false
publication_performed=false
bounded_unattended_advisory_operation_ready=false
release_candidate_ready=false
released_for_controlled_advisory_use=false
requires_human_review=true
live_model_call_authorized=false
live_external_action_authorized=false
release_action_authorized=false
credential_lookup_authorized=false
publication_authorized=false
r4c_in_this_release=false
r4c_future_work_allowed=true
r4c_codex_subprocess_completion_required_for_this_release=false
```

## Decision

The R5 canary action decision packet is recorded as a reference-only packet
for human review. It enumerates the standing-approval fields, request-class
scope, budget/rate/prompt/output caps, kill-switch reference, audit-retention
reference, post-run human review, stop conditions, and R6 status/rollback
references that a later separate HUMAN-GATED canary execution must satisfy.
It does not authorize live canary execution, standing unattended approval
activation, credential lookup, Codex subprocess re-execution, raw provider
API readiness, adapter-native readiness, or any release action. The next safe
step is to record the human-review gate decision for this action packet
before any canary execution.
