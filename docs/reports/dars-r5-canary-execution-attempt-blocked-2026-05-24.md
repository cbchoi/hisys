---
doc_id: HISYS-DARS-R5-CANARY-EXECUTION-ATTEMPT-BLOCKED-001
title: DARS R5 Canary Execution Attempt Blocked Report
version: v0.0.88
status: blocked-before-live-canary
created: 2026-05-24
---

# DARS R5 Canary Execution Attempt Blocked Report

## Request context

Operator instruction: `canary실행`.

Hisys interpreted the instruction as authority to attempt the next R5 canary execution gate under the existing R5 canary action decision packet:

- `docs/release/dars-r5-canary-action-decision-packet-v0.0.87.md`
- next safe task before this attempt: `DARS-LIVE-RELEASE-R5-CANARY-ACTION-HUMAN-REVIEW-GATE`

## Result

```text
formal_hisys_result=r5_canary_execution_attempt_blocked_before_live_action
status=blocked
failure_code=request_class_not_allowlisted
failure_detail=dars_live_provider_advisory_canary
```

The attempt did not execute a live canary. The current R5 unattended runner is still the PREP runner and accepts only the dry-run request class. The example standing approval policy is also a prep policy and does not authorize the canary class.

## Runtime evidence

The local controlled attempt used the existing R5 unattended runner with a fake/injected transport seam and a canary request class:

```text
instance_root=/tmp/hisys-r5-canary-execution-attempt-20260524
ledger_ref=runtime-boundary/dars-unattended-advisory/20260524/DARS-UNATTENDED-STANDING-PREP-20260523-001/DARS_R5_CANARY_ATTEMPT_20260524_001.json
request_id=DARS_R5_CANARY_ATTEMPT_20260524_001
source_execution_id=DARS_R5_CANARY_ATTEMPT_SRC_20260524_001
request_class=dars_live_provider_advisory_canary
standing_approval_policy_ref=docs/examples/dars/unattended-standing-approval.example.json
provider_policy_ref=docs/examples/dars/live-provider-panel-smoke.policy.example.json
activation_packet_ref=docs/examples/dars/live-provider-panel-smoke.activation.example.json
```

Observed ledger boundary flags:

```text
external_call_made=false
model_boundary_crossed=false
mutation_performed=false
publication_performed=false
external_action_performed=false
advisory_only=true
requires_human_review=true
requires_post_run_human_review=true
adapter_boundary_ref=null
transport_kind=fake_injected_provider_transport
```

## Stop reason

The runner enforces the R5 PREP boundary:

```text
_ALLOWED_PREP_MODE=dry_run
_ALLOWED_PREP_REQUEST_CLASS=dars_live_provider_advisory_dry_run
```

A canary request class is therefore blocked before the adapter boundary:

```text
request_class=dars_live_provider_advisory_canary
failure_code=request_class_not_allowlisted
adapter_boundary_ref=null
```

## Claim boundary

Accepted only:

```text
r5_canary_execution_attempt_blocked_before_live_action
```

Rejected claims:

```text
r5_live_canary_executed=false
standing_unattended_approval_activated=false
live_provider_model_call_made=false
codex_cli_subprocess_call=false
raw_provider_api_call_by_hisys=false
credential_lookup_by_hisys=false
bounded_unattended_advisory_operation_ready=false
release_candidate_ready=false
```

## Next safe task

```text
DARS-LIVE-RELEASE-R5-CANARY-MODE-PREP
```

The next increment should add a controlled, human-gated canary-mode contract before any later attempt can cross a model/provider boundary. That increment must define a canary-specific standing approval packet, canary request class acceptance, post-run review evidence, stop conditions, and explicit live-transport boundary handling. R4C remains excluded from this release scope unless separately reopened by explicit operator instruction.
