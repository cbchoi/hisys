---
doc_id: HISYS-DARS-R5-CANARY-ACTION-DECISION-PACKET-001
title: DARS R5 Bounded Unattended Canary Action Decision Packet
version: v0.0.87
status: action-decision-packet-for-human-review
created: 2026-05-24
---

# DARS R5 Bounded Unattended Canary Action Decision Packet

## Request context

This packet executes only `DARS-LIVE-RELEASE-R5-CANARY-ACTION-DECISION-PACKET`.
It records, for human review only, the action decision that follows the prepared
R5 canary packet recorded in
`docs/release/dars-r5-canary-packet-prep-v0.0.86.md` and the prior scope
decision recorded in
`docs/release/dars-r5-canary-scope-decision-v0.0.85.md`. R4C is excluded from
this release scope;
future reactivation requires separate explicit operator instruction and a
fresh decision packet.

accepted_claim=r5_canary_action_decision_packet_ready_for_human_review

This packet does not by itself authorize a live provider/model call, a Codex
CLI subprocess call, a raw provider API call by Hisys, a credential lookup by
Hisys, activation of a standing unattended approval policy, mutation outside
repository docs/tests/control files, publication, deployment, release action,
or removal of `requires_human_review=true`. The bounded unattended live canary
remains a separately HUMAN-GATED action and may only be initiated by a later
exact scoped operator approval that references this packet.

## Decision

Chosen R5 action path:

```text
bounded_unattended_advisory_canary_dry_run_then_human_review
```

The decision packet adopts the canary packet prep contract as-is. It records
that the canary class `dars_live_provider_advisory_canary` and the standing
approval policy required to execute it remain pending separately gated human
review and approval. The packet authorizes only the local act of recording
this human-review action decision and updating the controlled docs/tests/
control files described below. It does not authorize a Codex subprocess
re-execution, an `adapter_native` real-provider transport bring-up, a credential
lookup by Hisys, R5 canary execution, R7 release-candidate transition, or R8
release execution.

## Evidence scope

Reviewed and accepted prerequisite refs:

- `docs/release/dars-r5-canary-packet-prep-v0.0.86.md`
- `docs/release/dars-r5-canary-scope-decision-v0.0.85.md`
- `docs/runbooks/dars-unattended-advisory-operation.md`
- `docs/examples/dars/unattended-standing-approval.example.json`
- `src/hisys/agents/dars_unattended_policy.py`
- `src/hisys/operations/dars_unattended_runner.py`
- `docs/runbooks/dars-live-operations.md`
- `docs/runbooks/dars-live-rollback.md`
- `docs/release/dars-panel-release-candidate-checklist.md`

The packet aggregates these refs by name only. No raw secrets, credential
values, or raw provider payloads are persisted in any of the listed artifacts.

## Standing approval requirements

A separately HUMAN-GATED canary execution may use this action decision packet
only when the standing approval policy presented at run time satisfies
`validate_standing_approval_policy` in `src/hisys/agents/dars_unattended_policy.py`
and records all of the following fields explicitly:

- `policy_id`, `approval_ref`, `operator_id`, `post_run_reviewer_ref`;
- `valid_from`, `expires_at` (finite window);
- `provider_policy_refs`, `activation_packet_refs`;
- `kill_switch_ref` and `kill_switch_required=true`;
- `audit_ledger_ref`, `audit_retention_ref`, `redaction_policy_ref`;
- `cost_budget_ref`, `rate_limit_per_minute`;
- `max_runs`, `max_runs_per_hour`;
- `max_prompt_bytes_per_run`, `max_output_bytes_per_run`;
- `max_parallel_critics`, `max_critics_per_run`;
- `request_class_allowlist` containing `dars_live_provider_advisory_canary`
  (and optionally the rehearsal class `dars_live_provider_advisory_dry_run`);
- `requires_post_run_human_review=true`;
- `mutation_allowed=false`, `publication_allowed=false`,
  `external_action_allowed=false`, `advisory_only=true`.

The approval ladder reference must be explicit, finite, and reviewer-signed
outside Hisys. The example ladder reference
`APPROVAL-DARS-UNATTENDED-PREP-20260523-001` from the packet prep is a
template only and does not authorize canary execution by itself.

## Canary execution boundary

The canary action may only be initiated after a separate operator instruction
records an exact scoped approval that names every field listed under
"Standing approval requirements", confirms the post-run reviewer is available,
and pins the canary execution time window. The canary action is bounded by:

- exactly one bounded unattended advisory canary run per scoped approval,
  using `request_class_allowlist={dars_live_provider_advisory_canary}` or the
  rehearsal class `dars_live_provider_advisory_dry_run`;
- no mutation, no publication, no external action, no browser, no search, and
  no tool authority beyond the advisory critic call;
- every per-run record must contain `mutation_performed=false`,
  `publication_performed=false`, `external_action_performed=false`,
  `advisory_only=true`, and `requires_human_review=true`;
- post-run reviewer must verify `external_call_made`, `model_boundary_crossed`,
  and all advisory-only flags before any ladder claim is promoted.

The canary path is fail-closed on any standing-approval validator failure,
kill-switch trigger, budget exhaustion, rate violation, circuit breaker open,
post-run reviewer unavailability, or validation regression.

## Stop conditions

Stop before any later canary execution if any of the following holds:

1. the standing approval policy is missing, expired, not yet valid, or fails
   `validate_standing_approval_policy`;
2. any required cap, kill-switch ref, audit ledger ref, audit retention ref,
   redaction policy ref, or circuit breaker is missing;
3. the requested run class is not in `request_class_allowlist`;
4. provider policy or activation packets contain a raw secret, raw token, raw
   Authorization header, or unrestricted raw prompt text;
5. the kill-switch is triggered, the cost budget is exhausted, the rate budget
   is exceeded, or any circuit breaker is open;
6. the runner cannot resolve a credential reference outside Hisys without
   performing a credential lookup inside Hisys;
7. any pre-run check would require mutation, publication, external action,
   browser, search, or tool authority;
8. the post-run reviewer is unavailable or the reviewer ref is missing;
9. validation evidence (focused tests, traceability, secret scan, diff-check)
   is not GREEN;
10. R4C release exclusion is contested without a separate explicit operator
    instruction reopening R4C.

## Non-goals and blocked claims

This packet does not authorize or accept:

- raw provider API transport readiness;
- `adapter_native` readiness;
- another provider/model call;
- Codex subprocess re-execution;
- credential lookup or secret resolution by Hisys;
- R5 canary execution (separately HUMAN-GATED);
- R7 release-candidate readiness;
- R8 release execution;
- tag/package/deploy/publication/external notification;
- mutation authority;
- removal of `requires_human_review=true`;
- reactivation of R4C within this release.

## Post-run human review

When a later canary execution does occur, the post-run reviewer named in the
scoped approval must:

- read every per-run runtime-boundary record produced by the unattended runner
  and confirm `mutation_performed=false`, `publication_performed=false`,
  `external_action_performed=false`, `advisory_only=true`, and
  `requires_human_review=true`;
- verify that the audit ledger entry was written for the run (completed,
  blocked, failed, or circuit-broken);
- confirm that no credential value, no raw token, and no raw provider payload
  was persisted in any record;
- record the review outcome in a separate readiness decision record before any
  later ladder claim transition.

## Packet boundary flags

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
requires_human_review=true
```

## R4C release exclusion (carried forward)

R4C is excluded from this release scope. R4H remains the scoped human-review
advisory substitute. The packet does not reopen R4C; future reactivation
requires separate explicit operator instruction and a fresh decision packet
that records the specific R4C transport-evidence scope and approval ladder.

## Boundary

This packet performs no live provider/model call, no Codex subprocess call,
no raw provider API call, no credential lookup,
no standing unattended approval activation,
no mutation outside repository docs/tests/control files, no publication, no
release action, no deployment, no external notification, and no human-review
removal.

next_safe_task: `DARS-LIVE-RELEASE-R5-CANARY-ACTION-HUMAN-REVIEW-GATE`.
