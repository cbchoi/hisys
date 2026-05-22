# DARS-LIVE-EXECUTION-AUTH-PREP Task Plan

> **Row:** This document is the artifact produced by Ralph row
> `DARS-LIVE-EXECUTION-AUTH-PREP`. It binds the user authorization recorded in
> `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.44.md`
> ("live dars execution approve") to the existing controlled DARS live
> backend plan and localhost smoke runbook. It defines the exact execution
> packet, validation commands, runtime-boundary record path, and explicit
> stop conditions that must be satisfied before the Ralph loop crosses a
> DARS model/backend boundary.
>
> This row is **docs/control only**. It authors no production code, no
> tests, no fixtures, no runtime-boundary artifacts, and no live DARS
> execution. It does not enable any HTTP call, credential lookup, model
> invocation, or remote action.

## 1. Authorization envelope

- User instruction: `live dars execution approve`
  (Discord, 2026-05-22).
- Readiness decision record: `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.44.md`.
- Allowed scope (this opening checkpoint and the immediate execution
  row that follows it):
  - localhost-only `openai_compatible` DARS backend rehearsal against an
    **operator-supplied already-running localhost endpoint**;
  - advisory-only critique; no mutation, publication, deployment, or
    release authority;
  - capture a runtime-boundary record under the partition declared in
    Section 6 of this plan;
  - reuse the existing M-DARS-BE-1..4 surfaces already in the repo:
    - `src/hisys/agents/dars_backend_activation.py`
      (`validate_dars_backend_activation_packet`),
    - `src/hisys/agents/dars.py` (`DarsRuntime.run_configured_critique`
      with `backend_activation_packet_ref`),
    - `src/hisys/agents/dars_backend_boundary.py`,
    - `src/hisys/cli/main.py` (`request-dars-critique --backend
      configured --backend-activation-packet …`),
    - `docs/runbooks/dars-live-backend-localhost-smoke.md`,
    - `docs/examples/dars/backend-activation-localhost.example.json`.
- **Out of scope for this authorization envelope** (each item still
  requires fresh, explicit, named user authorization):
  - any non-loopback / external API DARS backend call;
  - Codex / Claude subscription provider execution beyond the existing
    injected-executor fail-closed harness;
  - any credential reference resolution, raw token, Authorization header,
    or environment-variable secret lookup;
  - any DARS-driven mutation, publication, deployment, tag, release,
    or browser / search / tool execution by the local model;
  - any change to remote configuration, branch alignment, or destructive
    Git history;
  - DARS completion claim upgrade beyond
    `local_fixture_localhost_controlled_advisory_complete` until a later
    GREEN/GATE row captures a successful runtime-boundary record.

## 2. Controlled anchors

| Short name | Path |
|---|---|
| Readiness decision (this authorization) | `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.44.md` |
| DARS live backend plan | `docs/plans/dars-live-backend-implementation-plan.md` |
| Localhost smoke runbook | `docs/runbooks/dars-live-backend-localhost-smoke.md` |
| Local activation packet example | `docs/examples/dars/backend-activation-localhost.example.json` |
| Activation validator | `src/hisys/agents/dars_backend_activation.py` |
| Runtime enforcement chokepoint | `src/hisys/agents/dars.py` (`DarsRuntime.run_configured_critique`) |
| Backend-boundary record writer | `src/hisys/agents/dars_backend_boundary.py` |
| CLI pass-through | `src/hisys/cli/main.py` (`request-dars-critique`, flag `--backend-activation-packet`) |
| DARS config schema | `src/hisys/agents/dars_config.py` |
| DARS dispatch gate | `src/hisys/agents/dars_dispatch.py` |
| Backend boundary tests | `tests/unit/test_dars_runtime.py`, `tests/unit/test_dars_backend_activation.py`, `tests/unit/test_dars_backend_boundary.py`, `tests/unit/test_dars_live_backend_runbook.py` |
| Bootstrap profile pin | `docs/milestone-bootstrap/profile.yaml` |
| Governance current-state test | `tests/unit/test_governance_docs_current_state.py` |
| Traceability index | `docs/traceability/README.md` |
| Ralph control plan | `ralph.md` |

## 3. Accepted decisions for this PREP row

1. **Docs/control only.** This PREP authors no production code, no tests,
   no fixtures, and no runtime artifacts. The existing M-DARS-BE-1..4
   surfaces are sufficient for the execution row; this PREP binds them
   to the user authorization rather than re-implementing them.
2. **Operator-supplied prerequisites.** Three values must be supplied by
   the operator out of band before any execution row may run:
   - `HISYS_DARS_LOCAL_ENDPOINT` — already-running loopback URL of the
     form `http://127.0.0.1:<port>/v1/chat/completions`;
   - `HISYS_INSTANCE` — Hisys instance root that owns the DARS config;
   - a fresh activation packet path (`--backend-activation-packet`) that
     points to a JSON file matching
     `docs/examples/dars/backend-activation-localhost.example.json` shape
     with current `approval_ref` and `expires_at` values.
   Ralph/Hermes shall not synthesize, install, start, or download a
   model runner, model artifact, or endpoint. The operator owns the
   model boundary.
3. **No credential surface.** The localhost endpoint must accept the
   request without any `Authorization` header, API key, token, or
   credential. The activation packet validator rejects raw secret-like
   fields and raw secret-like string values per
   `dars_backend_activation.py`. The operator confirms no credential
   demand before the execution row begins.
4. **No tool / search / browser permission.** The local model runner must
   have no tool execution, web search, browser access, or filesystem
   mutation authority. DARS critic output is advisory only.
5. **No mutation request.** The execution row stops on any mutation
   request that arises from the operator, the local model output, or any
   downstream consumer of the DARS critic.
6. **Fresh activation packet per execution.** A new activation packet
   ref (with a current `expires_at` window) is required for every
   execution row instance; expired packets fail closed with
   `activation_expired` in
   `validate_dars_backend_activation_packet(..., now=<iso8601>)`.
7. **Deterministic runtime-boundary record.** Each successful execution
   writes a JSON + Markdown pair under the partition declared in
   Section 6. The record fields are advisory-only and must satisfy the
   M-DARS-BE-3 record contract.
8. **Bounded repair.** If the execution row's focused gates fail, repair
   under the existing Ralph bounded-repair rule (≤ 5 focused repair
   loops) before re-asking the operator. Failures that require a new
   endpoint, credential, package install, runner change, mutation
   authority, browser/search/tool permission, or any non-loopback target
   are non-delegable; stop and ask the user.
9. **No remote subscription provider execution.** Codex/Claude
   subscription provider execution remains bounded by the existing
   M-DARS-BE-5 / M-DARS-BE-6 injected-executor harness. This PREP and
   the immediately following execution row do not authorize real
   subscription provider calls. Upgrading the harness from injected
   fakes to a real Codex/Claude subscription call requires a separate
   user authorization that names the provider, the operator, the egress
   scope, the redaction policy, and the expiry.
10. **No automatic completion-claim upgrade.** Even after a successful
    execution row, the DARS completion claim remains
    `local_fixture_localhost_controlled_advisory_complete` until the
    Ralph loop authors and reviews a GREEN/GATE row that records the
    runtime-boundary evidence and re-classifies the queue.

## 4. Exact execution packet contract

The execution row that follows this PREP must use the following inputs
and only the following inputs. Field names match
`src/hisys/agents/dars_backend_activation.py` and the existing CLI
surface in `src/hisys/cli/main.py`.

### 4.1 Operator-supplied environment

```text
HISYS_DARS_LOCAL_ENDPOINT=http://127.0.0.1:<port>/v1/chat/completions
HISYS_INSTANCE=<absolute path to the Hisys instance root>
```

Both values are operator-supplied out of band. Ralph/Hermes shall not
choose `<port>`, shall not start a model runner, and shall not synthesize
the instance root.

### 4.2 Operator-supplied activation packet

A JSON file matching the existing example
(`docs/examples/dars/backend-activation-localhost.example.json`) with
the following fields. The validator at
`validate_dars_backend_activation_packet(..., now=<iso8601>)` enforces
the codes listed in Section 4.4.

```json
{
  "activation_id":          "DARS-BE-ACT-<YYYYMMDD>-LOCALHOST-<seq>",
  "backend_id":             "local_llm_dars",
  "backend_kind":           "openai_compatible",
  "endpoint_scope":         "localhost_only",
  "allowed_actions":        "advisory_only",
  "human_approved":         true,
  "approval_ref":           "APPROVAL-DARS-BE-LOCALHOST-<YYYYMMDD>-<seq>",
  "expires_at":             "<ISO-8601 UTC future>"
}
```

Field rules:

- `activation_id` is opaque to Ralph and shall match the operator's
  approval record naming convention.
- `backend_id` and `backend_kind` must match the `local_llm_dars`
  `openai_compatible` configured backend in
  `$HISYS_INSTANCE/config/dars.json`. Mismatches fail closed at the
  runtime with `activation_backend_id_mismatch` /
  `activation_backend_kind_mismatch`.
- `endpoint_scope` must be `localhost_only`. Any other value fails
  closed with `invalid_endpoint_scope` (validator) or
  `activation_endpoint_scope_mismatch` (runtime).
- `allowed_actions` must be `advisory_only`. Any other value fails
  closed with `invalid_allowed_actions`.
- `human_approved` must be `true`. Any other value fails closed with
  `human_approval_required`.
- `approval_ref` must be a non-empty operator approval reference and
  must match the CLI's `--approval-ref` value. Mismatches fail closed
  with `activation_approval_ref_mismatch`.
- `expires_at` must be in the future per the validator's injected
  `now`. Expired packets fail closed with `activation_expired`.
- No raw secret-like field name (`api_key`, `token`, `secret`,
  `password`, `credential`, etc.) and no raw secret-like value (matching
  the existing prefix set in `dars_backend_activation.py`) may appear in
  the packet — those fail closed with `raw_secret_value_not_allowed`.

### 4.3 Operator-supplied DARS configuration

`$HISYS_INSTANCE/config/dars.json` must declare:

- `default_backend = local_llm_dars`;
- `local_llm_dars.kind = openai_compatible`;
- `local_llm_dars.endpoint = $HISYS_DARS_LOCAL_ENDPOINT`;
- `local_llm_dars.mode = local_network_only`;
- no `Authorization` header, no credential field, and no remote scope.

### 4.4 Validator and runtime issue codes

The validator (M-DARS-BE-1) returns a deterministic
`ConfigValidationReport` keyed to `hisys.dars.backend.activation`.
Required issue codes that may surface during the execution row:

```text
missing_required_field
invalid_endpoint_scope
invalid_allowed_actions
missing_approval_ref
human_approval_required
invalid_expires_at
activation_expired
external_backend_requires_remote_policy_packet
raw_secret_value_not_allowed
```

The runtime (M-DARS-BE-2) layers these additional mismatch codes that
may surface inside `DarsRuntime.run_configured_critique(...)`:

```text
backend_activation_packet_required
activation_backend_id_mismatch
activation_backend_kind_mismatch
activation_endpoint_scope_mismatch
activation_approval_ref_mismatch
```

Any of these issue codes is a fail-closed signal: do not proceed with
any HTTP call to the operator endpoint. The execution row records the
issue, reports it to the operator, and waits for a corrected packet.

## 5. Exact execution row commands (operator-driven)

The execution row that follows this PREP shall use exactly these
commands and shall not invent additional flags or alternate code paths.
Ralph/Hermes drives steps 1, 2, 4, and 5; the operator drives step 0
and step 3.

```text
Step 0 (operator): start the localhost model runner outside Hisys.
                   confirm http://127.0.0.1:<port>/v1/chat/completions
                   responds without any Authorization header demand.
                   confirm the runner has no tool/search/browser
                   permission and no mutation authority. supply
                   HISYS_DARS_LOCAL_ENDPOINT and HISYS_INSTANCE to the
                   operator session out of band.

Step 1: confirm CLI parser accepts the pass-through (no model call):

  PYTHONPATH=src:. python3 -m hisys.cli.main request-dars-critique --help

Step 2: rehearse the no-op fixture path first (no model call):

  PYTHONPATH=src:. python3 -m hisys.cli.main request-dars-critique \
    --instance "$HISYS_INSTANCE" \
    --date <YYYYMMDD> \
    --source-execution-id EXEC-LOCAL-LIVE-<seq> \
    --critique-text "fixture critique for live rehearsal" \
    --producer-id dars-local-live-rehearsal

Step 3 (operator gate): visually confirm every Section 7 precondition
                        is green before authorizing Step 4.

Step 4: cross the model boundary against the operator endpoint:

  PYTHONPATH=src:. python3 -m hisys.cli.main request-dars-critique \
    --instance "$HISYS_INSTANCE" \
    --date <YYYYMMDD> \
    --source-execution-id EXEC-LOCAL-LIVE-<seq> \
    --producer-id dars-local-live-rehearsal \
    --backend configured \
    --approval-ref APPROVAL-DARS-BE-LOCALHOST-<YYYYMMDD>-<seq> \
    --backend-activation-packet <path to activation packet json>

Step 5: re-run focused + traceability + secret scan gates and inspect
        the runtime-boundary record under the partition declared in
        Section 6.
```

The runtime is the enforcement boundary. The CLI only passes
`--backend-activation-packet` and `--approval-ref` through. Direct
Python calls to `DarsRuntime.run_configured_critique(...)` cannot
bypass activation; the M-DARS-BE-2 helper fails closed without a valid
packet ref.

## 6. Runtime-boundary record path

Each successful execution row writes a JSON + Markdown pair under the
following partition (the existing M-DARS-BE-3 convention):

```text
$HISYS_INSTANCE/runtime-boundary/dars-backends/<YYYYMMDD>/<SOURCE_EXECUTION_ID>/<BACKEND_ID>.json
$HISYS_INSTANCE/runtime-boundary/dars-backends/<YYYYMMDD>/<SOURCE_EXECUTION_ID>/<BACKEND_ID>.md
```

Required record fields (carried by `dars_backend_boundary.py`):

```text
schema_id              = hisys.dars.backend_boundary
backend_id             = local_llm_dars
backend_kind           = openai_compatible
endpoint_scope         = localhost_only
approval_ref           = <approval ref>
activation_ref         = <activation packet ref>
model_boundary_crossed = true
local_model_call_made  = true
external_call_made     = false
mutation_performed     = false
publication_performed  = false
allowed_actions        = advisory_only
requires_human_review  = true
```

No raw model prompt body, no raw model response body, no credential, no
endpoint URL with credential material, and no operator PII may appear
in the boundary record beyond what the existing
`dars_backend_boundary.py` writer already supports.

## 7. Stop-condition matrix (apply before and during the execution row)

The execution row stops, the operator is notified, and no further
command runs on any of these signals. Each condition maps to the
existing runbook stop list in
`docs/runbooks/dars-live-backend-localhost-smoke.md` and the M-DARS-BE-1
/ M-DARS-BE-2 deterministic codes.

| Signal | Effect | Existing surface |
|---|---|---|
| Non-loopback endpoint (any `HISYS_DARS_LOCAL_ENDPOINT` not resolving to a loopback address) | Stop before any HTTP call | runbook §Preconditions; runtime config check |
| Missing or unreadable activation packet | Stop before any HTTP call | runtime returns `backend_activation_packet_required` |
| Invalid activation packet (any issue in §4.4) | Stop before any HTTP call | validator returns `ConfigValidationReport(valid=false)` |
| Expired activation packet | Stop before any HTTP call | validator returns `activation_expired` |
| Mismatched approval refs between CLI and packet | Stop before any HTTP call | runtime returns `activation_approval_ref_mismatch` |
| Mismatched `backend_id` / `backend_kind` / `endpoint_scope` between config and packet | Stop before any HTTP call | runtime returns `activation_backend_id_mismatch` / `activation_backend_kind_mismatch` / `activation_endpoint_scope_mismatch` |
| Raw secret-like field or value in the activation packet | Stop before any HTTP call | validator returns `raw_secret_value_not_allowed` |
| `Authorization` header, API key, token, or credential demand from the operator endpoint | Stop before any HTTP call | runbook §Preconditions |
| Tool / search / browser permission requested by the local model runner | Stop before Step 4 | runbook §Preconditions |
| Mutation request from operator or model output | Stop before any further critique | runbook §Stop conditions |
| Secret scan failure (`python3 scripts/scan_secrets.py` → `hit_count > 0`) | Stop before any further critique | runbook §Preconditions |
| Operator uncertainty about any precondition | Stop before any further critique | runbook §Preconditions |
| Working tree dirty in a non-execution surface | Stop before commit/push | Ralph §10.3 |
| Branch / upstream is not `dars` / `origin/dars` | Stop before push | Ralph §10.3 |
| Any focused gate red after 5 bounded repair loops | Stop and ask | Ralph bounded-repair rule |

## 8. Validation commands for this PREP row

This PREP authors no behavior change, so the focused gates are governance
and traceability only. The execution row that follows this PREP will run
the broader DARS focused cohort.

```bash
PYTHONPATH=src:. pytest tests/unit/test_governance_docs_current_state.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
git status --short --branch
```

Expected:

- governance current-state test passes with the new `profile_version`
  and `next_safe_task` values authored by this PREP row;
- traceability validator: `OK`;
- secret scan: `hit_count=0`;
- `git diff --check`: clean (no whitespace damage in edits);
- `git status --short --branch`: branch `dars`, upstream `origin/dars`,
  only this PREP increment's files modified.

The execution row that follows shall additionally run, post-Step 5,
the focused DARS cohort:

```bash
PYTHONPATH=src:. pytest \
  tests/unit/test_dars_runtime.py \
  tests/unit/test_dars_backend_activation.py \
  tests/unit/test_dars_backend_boundary.py \
  tests/unit/test_dars_config.py \
  tests/unit/test_dars_dispatch.py \
  tests/unit/test_dars_live_backend_runbook.py \
  tests/unit/test_dars_critic_panel_cli.py \
  tests/unit/test_dars_critic_panel_adapters.py \
  tests/unit/test_dars_critic_panel_runtime.py \
  tests/unit/test_dars_critic_panel_tool_execution_runtime.py \
  tests/unit/test_dars_critic_panel_execution_graph_plan.py \
  tests/unit/test_dars_remote_subscription_dispatch.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

## 9. Files this PREP row touches

This PREP row touches docs/control surfaces only:

- `docs/plans/dars-live-execution-auth-prep-tasks.md` (this file; new).
- `docs/milestone-bootstrap/profile.yaml` — version bump and
  `next_safe_task` advance.
- `tests/unit/test_governance_docs_current_state.py` — assertion update
  to match the new profile state.
- `docs/traceability/README.md` — prepend a
  `DARS-LIVE-EXECUTION-AUTH-PREP` row.
- `ralph.md` — Section 16 next-row update and Reflection Log entry.

No file under `src/`, `tests/unit/test_dars_*.py`, fixture trees,
`docs/runbooks/`, `docs/examples/dars/`, `docs/contracts/`, or runtime
boundary partitions is modified by this PREP row.

## 10. Next safe Ralph row after this PREP commits

```text
DARS-LIVE-EXECUTION-AUTH-EXECUTE-OPERATOR-PREREQUISITES
```

This next row is **non-delegable**. It can advance only when the
operator has supplied:

- `HISYS_DARS_LOCAL_ENDPOINT` (loopback URL) out of band, and confirmed
  the endpoint responds without any `Authorization` header demand;
- `HISYS_INSTANCE` (Hisys instance root with the matching
  `config/dars.json`);
- a fresh activation packet path (matching §4.2) with a current
  `expires_at` window;
- explicit confirmation that the local model runner has no tool /
  search / browser permission and no mutation authority;
- explicit confirmation that the operator is decisive about every
  Section 7 precondition.

Until these prerequisites land, the Ralph loop must stop at this PREP
and wait. The `next_safe_task` field in `profile.yaml` advances to
`DARS-LIVE-EXECUTION-AUTH-EXECUTE-OPERATOR-PREREQUISITES`, which is a
documented stop-and-ask gate, not an action Ralph can self-supply.

## 11. Resume checkpoint convention

Append a Resume checkpoint after this PREP commits and after every
subsequent execution-row attempt, matching the format in `ralph.md`
§5.1.1. Required fields:

```text
Current HEAD:        <git rev-parse --short HEAD with subject>
Working tree:        <clean or exact file list>
Last completed task: DARS-LIVE-EXECUTION-AUTH-PREP
Next safe target:    DARS-LIVE-EXECUTION-AUTH-EXECUTE-OPERATOR-PREREQUISITES
Stop condition:      operator must supply HISYS_DARS_LOCAL_ENDPOINT,
                     HISYS_INSTANCE, activation packet path, and
                     Section 7 precondition confirmations.
```
