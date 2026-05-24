---
doc_id: HISYS-DARS-R5-CANARY-EXECUTION-HUMAN-GATE-001
title: DARS R5 Canary Execution Human Gate
version: v0.0.90
status: awaiting-exact-scoped-human-approval
created: 2026-05-24
---

# DARS R5 Canary Execution Human Gate

## Request context

The operator instructed `human gate로 넘어가` after the R5 canary-mode contract was implemented and verified. This record enters the human gate for `DARS-LIVE-RELEASE-R5-CANARY-EXECUTION-HUMAN-GATE` and performs only local preflight/approval-text preparation.

accepted_claim=r5_canary_execution_human_gate_entered

This record does not execute the canary, activate standing unattended approval, call a live provider/model, run a Codex subprocess, perform a raw provider API call, look up credentials, mutate outside controlled repository documents, publish, deploy, release, or notify external systems.

## Gate evidence reviewed

- `docs/release/dars-r5-canary-action-decision-packet-v0.0.87.md`
- `docs/examples/dars/unattended-standing-approval-canary.example.json`
- `src/hisys/agents/dars_unattended_policy.py`
- `src/hisys/operations/dars_unattended_runner.py`
- `docs/reports/dars-r5-canary-mode-contract-2026-05-24.md`
- `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.89.md`

## Local preflight result

The canary standing approval example was validated locally with:

```bash
PYTHONPATH=src:. python3 - <<'PY'
from hisys.agents.dars_unattended_policy import validate_standing_approval_policy
# policy: docs/examples/dars/unattended-standing-approval-canary.example.json
# now: 2026-05-24T12:00:00Z
# mode: canary
PY
```

Observed preflight summary:

```yaml
policy_ref: docs/examples/dars/unattended-standing-approval-canary.example.json
policy_id: DARS-UNATTENDED-STANDING-CANARY-20260524-001
approval_ref: APPROVAL-DARS-UNATTENDED-CANARY-20260524-001
valid: true
errors: []
warnings:
  - standing_approval_does_not_authorize_live_action_by_itself
request_class_allowlist:
  - dars_live_provider_advisory_dry_run
  - dars_live_provider_advisory_canary
canary_action_decision_packet_ref: docs/release/dars-r5-canary-action-decision-packet-v0.0.87.md
post_run_reviewer_ref: reviewer://operator/cbchoi
canary_post_run_reviewer_ref: reviewer://operator/cbchoi
canary_window_start: 2026-05-24T00:00:00Z
canary_window_end: 2026-06-23T00:00:00Z
max_runs: 1
canary_max_runs: 1
kill_switch_ref: ops://hisys/dars/unattended/kill-switch/manual
advisory_only: true
mutation_allowed: false
publication_allowed: false
external_action_allowed: false
requires_post_canary_human_review: true
```

The deterministic warning is intentional: a valid standing-approval schema still does not authorize action by itself. The next step requires exact scoped human approval.

## Exact approval text required to execute the bounded canary

To execute one bounded R5 canary run, the operator should approve the following scope exactly or provide corrected field values. Without this exact approval, the canary remains unexecuted.

```text
APPROVE DARS-LIVE-RELEASE-R5-CANARY-EXECUTION-HUMAN-GATE
canary_action_decision_packet_ref=docs/release/dars-r5-canary-action-decision-packet-v0.0.87.md
standing_approval_policy_ref=docs/examples/dars/unattended-standing-approval-canary.example.json
policy_id=DARS-UNATTENDED-STANDING-CANARY-20260524-001
approval_ref=APPROVAL-DARS-UNATTENDED-CANARY-20260524-001
operator_id=operator:cbchoi
post_run_reviewer_ref=reviewer://operator/cbchoi
canary_post_run_reviewer_ref=reviewer://operator/cbchoi
canary_window_start=2026-05-24T00:00:00Z
canary_window_end=2026-06-23T00:00:00Z
request_class=dars_live_provider_advisory_canary
mode=canary
max_runs=1
canary_max_runs=1
max_runs_per_hour=1
rate_limit_per_minute=1
max_parallel_critics=1
max_critics_per_run=2
max_prompt_bytes_per_run=4096
max_output_bytes_per_run=4096
kill_switch_ref=ops://hisys/dars/unattended/kill-switch/manual
kill_switch_state=armed
audit_ledger_ref=runtime-boundary/dars-unattended-advisory
audit_retention_ref=retention://hisys/dars/unattended-ledger/90d
redaction_policy_ref=policy://hisys/dars/live-provider-redaction-v1
cost_budget_ref=budget://hisys/dars/unattended/canary/2026-05
mutation_allowed=false
publication_allowed=false
external_action_allowed=false
advisory_only=true
requires_post_run_human_review=true
requires_post_canary_human_review=true
```

## Execution boundary after approval

Current implementation executes canary mode through the fake/injected provider transport and the adapter dry-run mode only. If approved, the allowed next action is one bounded local canary-mode runner execution that must preserve:

```yaml
adapter_mode: dry_run
transport_kind: fake_injected_provider_transport
external_call_made: false
model_boundary_crossed: false
live_provider_model_call_made: false
raw_provider_api_call_by_hisys: false
credential_lookup_by_hisys: false
mutation_performed: false
publication_performed: false
external_action_performed: false
advisory_only: true
requires_human_review: true
requires_post_run_human_review: true
```

This gate does not authorize raw-provider API transport, adapter-native real provider transport, release-candidate transition, release execution, deployment, publication, or external notification.

## Boundary flags

```yaml
r5_canary_execution_human_gate_entered: true
r5_canary_execution_exact_approval_received: false
r5_live_canary_executed: false
standing_unattended_approval_activated: false
bounded_unattended_advisory_operation_ready: false
release_candidate_ready: false
live_provider_model_call_made: false
raw_provider_api_call_by_hisys: false
credential_lookup_by_hisys: false
mutation_performed: false
publication_performed: false
external_action_performed: false
requires_human_review: true
```

## Next safe task

```text
DARS-LIVE-RELEASE-R5-CANARY-EXECUTION-RUN-AFTER-EXACT-HUMAN-APPROVAL
```
