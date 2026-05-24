# DARS R5 canary-mode contract — local-safe implementation

Date: 2026-05-24
Task: `DARS-LIVE-RELEASE-R5-CANARY-MODE-PREP`

## Request context

The operator requested that R5 be completed through an RLOO Claude subprocess after the previous canary execution attempt was blocked by the dry-run-only R5 PREP runner.

## Evidence scope

This increment implements a distinct local canary-mode contract for the bounded unattended runner. It does not perform a live canary execution. It only defines and tests the request/policy shape that a later human-gated canary attempt must satisfy.

Changed implementation artifacts:

- `src/hisys/agents/dars_unattended_policy.py`
- `src/hisys/operations/dars_unattended_runner.py`
- `docs/examples/dars/unattended-standing-approval-canary.example.json`
- `docs/runbooks/dars-unattended-advisory-operation.md`
- `tests/unit/test_dars_unattended_policy.py`
- `tests/unit/test_dars_unattended_runner.py`
- `tests/unit/test_dars_unattended_docs.py`

## Implemented contract

The unattended runner now represents two modes:

```text
mode=dry_run
mode=canary
```

`mode=dry_run` remains the existing R5 PREP path and accepts only `dars_live_provider_advisory_dry_run`.

`mode=canary` accepts only request class `dars_live_provider_advisory_canary` and validates the standing approval with canary-specific preconditions:

- `canary_action_decision_packet_ref` is present and matches the request;
- `canary_post_run_reviewer_ref` is present;
- `canary_window_start` and `canary_window_end` are finite and active for the request time;
- `canary_max_runs` is positive and does not exceed `max_runs`;
- `requires_post_canary_human_review=true`;
- `request_class_allowlist` includes `dars_live_provider_advisory_canary`;
- mutation, publication, and external-action authority remain false.

The canary path still routes through the R2 fail-closed adapter in `dry_run` mode with `FakeLiveProviderTransport`. The ledger records the requested canary mode while also recording `adapter_mode=dry_run` and `transport_kind=fake_injected_provider_transport`.

## Claim boundary

Accepted claim:

```text
r5_canary_mode_contract_prepared_for_human_review
```

Preserved false claims:

```text
r5_live_canary_executed=false
standing_unattended_approval_activated=false
bounded_unattended_advisory_operation_ready=false
release_candidate_ready=false
live_provider_model_call_made=false
raw_provider_api_call_by_hisys=false
credential_lookup_by_hisys=false
mutation_performed=false
publication_performed=false
external_action_performed=false
```

## Validation status

Focused validation:

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_unattended_runner.py tests/unit/test_dars_unattended_policy.py tests/unit/test_dars_unattended_docs.py tests/unit/test_governance_docs_current_state.py -q
# 49 passed
```

Full validation is recorded in the final RLOO report after repository-level gates complete.

## Next safe task

```text
DARS-LIVE-RELEASE-R5-CANARY-EXECUTION-HUMAN-GATE
```

A later canary execution attempt remains separately human-gated. This report does not authorize live provider/model calls, raw provider APIs, credential lookup, standing unattended approval activation, release action, deployment, publication, external notification, mutation, or human-review removal.
