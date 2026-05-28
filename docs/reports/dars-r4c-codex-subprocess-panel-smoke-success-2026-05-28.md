# DARS R4C Codex subprocess multi-critic panel smoke success — 2026-05-28

## Request context

The operator stated that the Codex CLI authentication state had been restored and approved a bounded Codex-backed multi-critic live panel smoke using the previously stated scope: read-only, advisory-only, no mutation, no publication, no deployment, no release, no browser/search/tool authority, no credential lookup, no claim upgrade, and `requires_human_review=true`.

## Preflight

Repository state before execution:

```text
branch: dars...origin/dars
HEAD: 970a786 docs: approve local artifact scope review
working tree: clean
codex: /usr/bin/codex
codex version: codex-cli 0.134.0
```

Auth/CLI probe succeeded before the panel smoke:

```bash
codex --ask-for-approval never exec --sandbox read-only --cd /home/cbchoi/workspaces/develop/repos/hisys -- "Say OK only."
# returned OK
```

Focused preflight gates passed:

```bash
PYTHONPATH=src:. pytest \
  tests/unit/test_dars_codex_cli_subprocess.py \
  tests/unit/test_dars_remote_subscription_dispatch.py::test_remote_subscription_multi_critic_panel_dispatch_writes_aggregate_boundary \
  tests/unit/test_dars_remote_subscription_dispatch.py::test_codex_cli_subprocess_multi_critic_panel_prep_packet_matches_dispatch_contract \
  tests/unit/test_dars_remote_subscription_dispatch.py::test_codex_cli_subprocess_multi_critic_evidence_packet_prep_includes_claim_and_evidence \
  tests/unit/test_governance_docs_current_state.py \
  -q
# 49 passed

python3 scripts/validate_traceability.py
# OK: schemas, trace test, and Hermes boundary convention pass traceability checks

python3 scripts/scan_secrets.py
# secret_scan: scanned_files=1004 skipped_files=0 hit_count=0

git diff --check
# pass
```

## Execution

A governed temporary instance was used:

```text
/tmp/hisys-r4c-codex-panel-smoke-20260528-002-r049wku8
```

Control packet refs:

```text
/tmp/hisys-r4c-codex-panel-smoke-20260528-002-r049wku8/control-packets/r4c-codex-panel-policy.json
/tmp/hisys-r4c-codex-panel-smoke-20260528-002-r049wku8/control-packets/r4c-codex-panel-activation.json
```

The panel was executed through `run_dars_remote_subscription_panel_dispatch(...)` with `build_codex_cli_prompt_mode_executor(...)`, which invokes Codex in prompt mode using the bounded command shape:

```text
codex --ask-for-approval never exec --sandbox read-only --cd /home/cbchoi/workspaces/develop/repos/hisys -- <redacted bounded DARS critic prompt packet>
```

No raw provider API call, SDK import, credential lookup, provider-account configuration, browser/search authority, mutation, publication, deployment, or release action was performed by Hisys.

## Runtime-boundary evidence

Aggregate panel boundary record:

```text
/tmp/hisys-r4c-codex-panel-smoke-20260528-002-r049wku8/runtime-boundary/dars-remote-subscription-panels/20260528/REQ-DARS-CODEX-PANEL-SMOKE-20260528-002/PANEL-DARS-CODEX-SUBPROCESS-20260528-002.json
```

Aggregate boundary fields:

```text
schema_id=hisys.dars.remote_subscription_panel_dispatch
request_id=REQ-DARS-CODEX-PANEL-SMOKE-20260528-002
panel_id=PANEL-DARS-CODEX-SUBPROCESS-20260528-002
critic_count=2
completed_critic_count=2
provider_ids=[codex]
adapter_classes=[codex_subscription]
transport_kind=injected_subscription_executor_panel
external_call_made=true
model_boundary_crossed=true
local_model_call_made=false
mutation_performed=false
publication_performed=false
allowed_actions=advisory_only
requires_human_review=true
```

Per-critic boundary records:

```text
/tmp/hisys-r4c-codex-panel-smoke-20260528-002-r049wku8/runtime-boundary/dars-remote-subscriptions/20260528/REQ-DARS-CODEX-PANEL-SMOKE-20260528-002/codex_subscription_dars_critic-EXEC-DARS-R4C-CODEX-LOGICAL-CONSISTENCY-CRITIC-20260528-002.json
/tmp/hisys-r4c-codex-panel-smoke-20260528-002-r049wku8/runtime-boundary/dars-remote-subscriptions/20260528/REQ-DARS-CODEX-PANEL-SMOKE-20260528-002/codex_subscription_dars_critic-EXEC-DARS-R4C-CODEX-EVIDENCE-GOVERNANCE-CRITIC-20260528-002.json
```

Per-critic records both preserved:

```text
provider_id=codex
adapter_class=codex_subscription
transport_kind=codex_cli_subprocess_prompt_mode
endpoint_scope=external_api
external_call_made=true
model_boundary_crossed=true
local_model_call_made=false
mutation_performed=false
publication_performed=false
allowed_actions=advisory_only
requires_human_review=true
```

## Advisory findings preview

Logical-consistency critic preview:

```text
The bounded claim mostly follows from the evidence summary: critic_count=2 and completed_critic_count=2 support that the two-critic panel completed, and known_findings includes substantive findings from both critics. The claim's negative scope is supported by mutation_performed=false, publication_performed=false, requires_human_review=true, and completion_claim_upgrade_requested=false. A minor consistency caveat remains around old evidence-summary references in the reused packet context.
```

Evidence-governance critic preview:

```text
Boundary preservation appears satisfied for advisory-only scope: mutation_performed=false and publication_performed=false. No completion-claim upgrade is preserved: completion_claim_upgrade_requested=false and requires_human_review=true. Human review remains correctly required; do not treat the smoke as a DARS completion claim. The packet records external_call_made=true and model_boundary_crossed=true, compatible with the approved live smoke boundary.
```

## Post-execution checks

Repository working tree remained clean immediately after the smoke run. A secret-marker scan over the temporary instance found no raw credential markers:

```text
search path: /tmp/hisys-r4c-codex-panel-smoke-20260528-002-r049wku8
secret-like hit count: 0
```

## Accepted claim boundary

Accepted narrow claim:

```text
r4c_codex_subscription_multi_critic_panel_smoke_completed_with_findings
```

The claim is limited to one human-approved, read-only, advisory-only, two-critic Codex CLI subprocess panel smoke with preserved boundary records.

Rejected or still not accepted:

```text
DARS completion-claim upgrade
bounded unattended advisory operation ready
R5 live unattended canary accepted
R6 live operations readiness
release execution authorization
publication/deployment/package upload authorization
human-review removal
credential lookup by Hisys
raw provider API readiness
```

`requires_human_review=true` remains in force.
