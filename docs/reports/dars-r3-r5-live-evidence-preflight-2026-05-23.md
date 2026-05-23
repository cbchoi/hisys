# DARS R3-R5 live evidence preflight and stop record — 2026-05-23

## Request

최창범 교수 requested R3-R5 live evidence execution in the Discord Hisys thread.

## Conclusion

R3-R5 live evidence was not executed. The governed preflight reached a hard stop before any live provider/model call, credential lookup, standing unattended approval activation, mutation, publication, deployment, release, or external notification.

The stop is required by the controlled runbooks and current implementation state:

- R3 requires a fresh human-approved decision packet and a separately approved real-provider transport. The current R2 adapter explicitly routes both `dry_run` and `live` mode through `FakeLiveProviderTransport` and records `external_call_made=false` / `model_boundary_crossed=false`.
- R4 requires reviewed R3 ACTION evidence (`live_provider_advisory_smoked`) before any panel smoke. That prerequisite is absent.
- R5 ACTION requires R4 accepted multi-critic live-provider evidence and a separate standing unattended approval/canary decision. The current runner accepts only R5 PREP `dry_run` request class through fake/injected transport.

## Preconditions inspected

Controlled anchors inspected:

- `docs/runbooks/dars-live-provider-single-smoke.md`
- `docs/runbooks/dars-live-provider-panel-smoke.md`
- `docs/runbooks/dars-unattended-advisory-operation.md`
- `src/hisys/agents/dars_live_provider_adapter.py`
- `src/hisys/operations/dars_unattended_runner.py`
- `ralph.md`

Repository state at preflight:

```text
branch: dars
head: d7f4365 feat: add dars live status rollback readiness
upstream: origin/dars
working tree before report: clean
```

Codex CLI availability was checked only as environment capability, not used for this R3-R5 action:

```text
/usr/bin/codex
codex-cli 0.128.0
```

This did not resolve credentials and did not invoke a provider/model subprocess.

## Packet validation evidence

The existing example packet templates still validate at PREP scope using fixed `now=2026-05-23T00:00:00Z`:

```text
docs/examples/dars/live-provider-single-smoke.policy.example.json
  errors=[]
  warnings=[live_provider_dispatch_not_authorized_by_policy_alone]

docs/examples/dars/live-provider-panel-smoke.policy.example.json
  errors=[]
  warnings=[live_provider_dispatch_not_authorized_by_policy_alone]

docs/examples/dars/live-provider-single-smoke.activation.example.json
  errors=[]
  warnings=[]

docs/examples/dars/live-provider-panel-smoke.activation.example.json
  errors=[]
  warnings=[]

docs/examples/dars/unattended-standing-approval.example.json
  errors=[]
  warnings=[standing_approval_does_not_authorize_live_action_by_itself]
```

These validations establish template shape only. They do not authorize live dispatch or standing unattended operation.

## Fail-closed boundary evidence generated

A controlled local preflight attempted the R3 adapter in `mode=live` without enabling the live env gate. This is a fail-closed check, not live evidence:

```json
{
  "boundary_ref": "runtime-boundary/dars-live-provider-adapter/20260523/DARS-LP-REQ-R3-LIVE-EVIDENCE-20260523/dars-live-claude-single-smoke-001-src-exec-r3-preflight-001.json",
  "external_call_made": false,
  "failure_code": "live_provider_env_gate_missing",
  "mode": "live",
  "model_boundary_crossed": false,
  "mutation_performed": false,
  "publication_performed": false,
  "requires_human_review": true,
  "status": "failed"
}
```

Temporary instance root:

```text
/tmp/hisys-r3-r5-live-evidence-20260523
```

Generated temporary refs:

```text
runtime-boundary/dars-live-provider-adapter/20260523/DARS-LP-REQ-R3-LIVE-EVIDENCE-20260523/dars-live-claude-single-smoke-001-src-exec-r3-preflight-001.json
runtime-boundary/dars-live-provider-adapter/20260523/DARS-LP-REQ-R3-LIVE-EVIDENCE-20260523/dars-live-claude-single-smoke-001-src-exec-r3-preflight-001.md
```

## R5 PREP dry-run evidence generated

A bounded R5 PREP dry-run was executed under fake/injected transport only. This confirms the unattended runner remains local-safe; it is not R5 ACTION canary evidence:

```json
{
  "adapter_boundary_ref": "runtime-boundary/dars-live-provider-adapter/20260523/DARS_UNATTENDED_REQ_R5_PREP_20260523/dars-live-claude-panel-smoke-001-DARS_UNATTENDED_SRC_R5_PREP_001.json",
  "external_action_performed": false,
  "external_call_made": false,
  "failure_code": null,
  "ledger_ref": "runtime-boundary/dars-unattended-advisory/20260523/DARS-UNATTENDED-STANDING-PREP-20260523-001/DARS_UNATTENDED_REQ_R5_PREP_20260523.json",
  "model_boundary_crossed": false,
  "mutation_performed": false,
  "publication_performed": false,
  "requires_post_run_human_review": true,
  "status": "completed"
}
```

## Local status evidence generated

`hisys dars-live-status` was run against the same temporary instance. It wrote:

```text
reports/run-summaries/20260523/dars-live-status.json
reports/run-summaries/20260523/dars-live-status.md
```

The status packet preserved refs-only privacy and boundary flags:

```text
external_call_made=false
credential_lookup_performed=false
mutation_performed=false
publication_performed=false
live_action_authorized=false
standing_approval_activated=false
rollback.readiness=documented
```

## Focused validation

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_live_provider_policy.py tests/unit/test_dars_live_provider_transport.py tests/unit/test_dars_live_provider_adapter.py tests/unit/test_dars_live_provider_single_smoke_runbook.py tests/unit/test_dars_live_provider_panel_smoke_runbook.py tests/unit/test_dars_unattended_policy.py tests/unit/test_dars_unattended_runner.py tests/unit/test_dars_unattended_docs.py tests/unit/test_dars_live_status.py -q
# 95 passed
```

## Stop decision

Stop before R3 ACTION / R4 ACTION / R5 ACTION live evidence.

Required next artifacts before any actual live evidence attempt:

1. Fresh R3 decision packet that names approval ref, provider/model refs, bounded prompt/output/rate/cost refs, redaction policy, reviewer, rollback procedure, and controlled instance root.
2. Separately approved real-provider transport implementation or operator-supplied executor mapped to the R3/R4 runbooks, with tests and stop-condition handling.
3. R3 single-critic live smoke execution and post-run human review accepting `live_provider_advisory_smoked`.
4. Only after accepted R3 evidence, a fresh R4 panel decision packet and execution path.
5. Only after accepted R4 evidence, a fresh R5 standing unattended canary decision packet and runner path that is explicitly outside the current PREP-only dry-run runner.

No claim transition was made. Current claim remains below `live_provider_advisory_smoked`.
