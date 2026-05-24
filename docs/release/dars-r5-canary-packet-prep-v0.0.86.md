---
doc_id: HISYS-DARS-R5-CANARY-PACKET-PREP-001
title: DARS R5 Bounded Unattended Canary Packet Preparation
version: v0.0.86
status: packet-prep-for-human-review
created: 2026-05-24
---

# DARS R5 Bounded Unattended Canary Packet Preparation

## Request context

This packet executes only `DARS-LIVE-RELEASE-R5-CANARY-PACKET-PREP`. It assembles
controlled references for a future bounded unattended live-canary review packet
following the prior scope decision in
`docs/release/dars-r5-canary-scope-decision-v0.0.85.md`. R4C is excluded from
this release scope and may be reopened only by a later explicit operator
instruction and decision packet.

accepted_claim=r5_canary_packet_prepared_for_human_review

This packet does not by itself authorize a live provider/model call, a Codex CLI
subprocess call, a raw provider API call by Hisys, a credential lookup by Hisys,
activation of a standing unattended approval policy, mutation outside repository
docs/tests/control files, publication, deployment, release action, or removal of
`requires_human_review=true`. The bounded unattended live canary remains a
separately HUMAN-GATED action.

## Controlled anchors

| Short name | Path |
|---|---|
| Scope decision | `docs/release/dars-r5-canary-scope-decision-v0.0.85.md` |
| R5 PREP runbook | `docs/runbooks/dars-unattended-advisory-operation.md` |
| R5 standing approval example | `docs/examples/dars/unattended-standing-approval.example.json` |
| R5 policy validator | `src/hisys/agents/dars_unattended_policy.py` |
| R5 unattended runner | `src/hisys/operations/dars_unattended_runner.py` |
| R6 live operations runbook | `docs/runbooks/dars-live-operations.md` |
| R6 rollback runbook | `docs/runbooks/dars-live-rollback.md` |
| RC checklist | `docs/release/dars-panel-release-candidate-checklist.md` |

## Packet contents

The packet aggregates references only. No raw secrets, credential values, or raw
provider payloads are persisted in any of the listed artifacts.

### Standing approval references

- Finite standing approval policy example:
  `docs/examples/dars/unattended-standing-approval.example.json`
- Required validator: `validate_standing_approval_policy` in
  `src/hisys/agents/dars_unattended_policy.py`
- Required policy ladder fields: `policy_id`, `approval_ref`, `operator_id`,
  `post_run_reviewer_ref`, `valid_from`, `expires_at`,
  `provider_policy_refs`, `activation_packet_refs`, `kill_switch_ref`,
  `kill_switch_required=true`, `audit_ledger_ref`, `audit_retention_ref`,
  `redaction_policy_ref`, `circuit_breakers`,
  `requires_post_run_human_review=true`, `mutation_allowed=false`,
  `publication_allowed=false`, `external_action_allowed=false`,
  `advisory_only=true`.
- Approval ladder reference: `APPROVAL-DARS-UNATTENDED-PREP-20260523-001`
  (example only; the live canary requires a separately approved canary
  approval ref recorded in the later action decision packet).

### Request-class scope

- Allowed dry-run class: `dars_live_provider_advisory_dry_run` (rehearsal only).
- Reserved canary class for the later HUMAN-GATED action:
  `dars_live_provider_advisory_canary`. This packet does not authorize the
  canary class; it records the request-class boundary the later packet must
  respect.
- Out-of-scope classes for this packet: any production unattended class, any
  mutation/publication class, any browser/tool-authority class.

### Budget, rate, prompt, and output caps

The standing approval and runner must enforce, at minimum, the following finite
caps before any per-run dispatch:

- `max_runs` per standing approval window;
- `max_runs_per_hour`;
- `max_prompt_bytes_per_run` (per individual critic prompt);
- `max_output_bytes_per_run` (per critic output);
- `rate_limit_per_minute`;
- `max_parallel_critics` (no unbounded parallelism);
- `max_critics_per_run`;
- `cost_budget_ref` resolved to a finite budget envelope outside Hisys.

Defaults in the example policy keep all caps small (single-run dry-run scale).
The later canary action packet must record the explicit canary-time caps and
their reviewer-approved deltas, if any.

### Kill-switch reference

- `kill_switch_ref` is required and must resolve to an operator-controlled
  manual kill-switch outside Hisys.
- `kill_switch_required=true` is enforced by the standing approval validator.
- The runner must consult kill-switch state on every pre-run check and must
  abort with an audit-ledger entry if the kill-switch is triggered.

### Audit-retention reference

- `audit_ledger_ref` points to the bounded `runtime-boundary/dars-unattended-advisory`
  ledger root used for completed, failed, blocked, and circuit-broken runs.
- `audit_retention_ref` points to a finite retention rule (the example pins
  90 days). The packet does not authorize a longer retention window or any
  retention-policy change.
- Ledger entries are reference-only and must not contain raw secrets, raw
  prompt text, or raw provider payloads.

### Post-run human review

- `requires_post_run_human_review=true` is mandatory.
- The `post_run_reviewer_ref` field identifies the human reviewer who must
  read every run record before any claim transition.
- No automated reviewer or LLM-only reviewer is acceptable.
- The post-run review must verify `external_call_made`, `model_boundary_crossed`,
  `mutation_performed=false`, `publication_performed=false`,
  `external_action_performed=false`, `advisory_only=true`, and
  `requires_human_review=true` in every per-run record before promoting any
  ladder claim.

### Stop conditions

Stop before any later canary action if any of the following holds:

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
   is not GREEN.

### R6 status and rollback references

- Live operations status surface and operator runbook:
  `docs/runbooks/dars-live-operations.md`.
- Rollback readiness runbook: `docs/runbooks/dars-live-rollback.md`.
- The packet requires that the rollback sequence (revoke standing approval,
  disable provider policy, rotate credential outside Hisys, stop scheduler
  outside Hisys, verify no further runs) is reviewable before any later canary
  action.
- The packet requires that the live operations status report can be regenerated
  without external calls and without persisting raw secrets.

## Packet boundary flags

```text
r5_canary_packet_prepared=true
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
advisory substitute. The packet does not reopen R4C and does not claim
`raw_provider_api_readiness`, `adapter_native_readiness`, or
`r4c_codex_subprocess_completion_required_for_this_release`.

## Boundary

This packet performs no live provider/model call, no Codex subprocess call, no
raw provider API call, no credential lookup, no standing unattended approval
activation, no mutation outside repository docs/tests/control files, no
publication, no release action, no deployment, no external notification, and no
human-review removal.

next_safe_task: `DARS-LIVE-RELEASE-R5-CANARY-ACTION-DECISION-PACKET`.
