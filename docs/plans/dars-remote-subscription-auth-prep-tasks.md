# DARS-REMOTE-SUBSCRIPTION-AUTH-PREP Task Plan

> **Row:** This document is the artifact produced by Ralph row
> `DARS-REMOTE-SUBSCRIPTION-AUTH-PREP`. It binds the user authorization
> recorded in
> `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.46.md`
> ("local은 아직 준비가 덜 되어 있지 않나? … subscription으로 진행") to the
> existing M-DARS-BE-5 remote subscription policy validator and the
> M-DARS-BE-6 injected-executor dispatch harness. It defines the exact
> execution packet, validator + runtime issue codes, runtime-boundary
> record path, focused validation commands, files this PREP row touches,
> and explicit stop conditions that must be satisfied before the Ralph
> loop crosses a Codex/Claude subscription provider boundary.
>
> This row is **docs/control only**. It authors no production code, no
> tests, no fixtures, no runtime-boundary artifacts, and no live Codex
> or Claude subscription call. It does not enable any HTTP call,
> credential lookup, vault resolution, model invocation, or remote
> action.

## 1. Authorization envelope

- User instruction:
  `local은 아직 준비가 덜 되어 있지 않나? 확인하고 준비가 되어 있으면 A 안되어 있면 C. subscription으로 진행`
  (Discord, 2026-05-22; reproduced verbatim in
  `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.46.md`).
- Local readiness evidence: `docs/reports/dars-local-readiness-check-2026-05-22.md`
  recorded the local path A as **not ready** —
  `HISYS_DARS_LOCAL_ENDPOINT` unset, `HISYS_INSTANCE` unset, no
  operator-provided live instance root, no fresh activation packet path.
- Readiness decision record:
  `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.46.md`.
- Allowed scope (this PREP row and the next stop-and-ask gate that
  follows it):
  - docs/control PREP that binds readiness decision v0.0.46 to the
    existing M-DARS-BE-5 / M-DARS-BE-6 surfaces;
  - bookkeeping advance of `docs/milestone-bootstrap/profile.yaml`,
    `tests/unit/test_governance_docs_current_state.py`,
    `docs/traceability/README.md`, and `ralph.md`;
  - no edit to `src/`, the existing remote subscription tests, fixtures,
    runbooks, or runtime-boundary partitions.
- **Out of scope for this authorization envelope** (each item still
  requires fresh, explicit, named user authorization):
  - any real Codex or Claude subscription provider call, even through
    the existing M-DARS-BE-6 injected-executor harness;
  - any credential reference resolution, vault lookup, raw token,
    `Authorization` header, API key, or environment-variable secret;
  - any provider account configuration, account creation, account
    linking, or subscription-account onboarding action;
  - expansion of the provider allowlist beyond `codex` / `claude` or the
    adapter-class allowlist beyond `codex_subscription` /
    `claude_subscription`;
  - any raw API-key, arbitrary OpenAI-compatible, arbitrary
    Anthropic-compatible, Gemini, Grok, pay-per-call, or
    custom-HTTP/local-proxy provider integration;
  - any DARS-driven mutation, publication, deployment, tag, release,
    or browser / search / tool execution authority granted to the
    subscription executor;
  - any change to remote configuration, branch alignment, or
    destructive Git history;
  - DARS completion claim upgrade beyond
    `local_fixture_localhost_controlled_advisory_complete` until a
    later GREEN/GATE row captures a successful runtime-boundary record
    under the partition declared in Section 6;
  - resumption of the dormant Section 10.3 branch-alignment between
    `feat/domain-adaptive-requirements-analysis` and the local `dars`
    checkout;
  - real OSS comparison/license adjudication execution (which remains
    future-roadmap only per the 2026-05-22 deferral).

## 2. Controlled anchors

| Short name | Path |
|---|---|
| Local readiness check | `docs/reports/dars-local-readiness-check-2026-05-22.md` |
| Readiness decision (this authorization) | `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.46.md` |
| Sibling DARS live execution PREP packet | `docs/plans/dars-live-execution-auth-prep-tasks.md` |
| DARS live backend plan (parent) | `docs/plans/dars-live-backend-implementation-plan.md` |
| Remote subscription policy contract | `docs/contracts/dars-remote-subscription-backend-policy.md` |
| Remote subscription policy validator (M-DARS-BE-5) | `src/hisys/agents/dars_remote_subscription_policy.py` |
| Remote subscription dispatch harness (M-DARS-BE-6) | `src/hisys/agents/dars_remote_subscription_dispatch.py` |
| Activation packet validator (M-DARS-BE-1) | `src/hisys/agents/dars_backend_activation.py` |
| DARS runtime chokepoint (M-DARS-BE-2) | `src/hisys/agents/dars.py` (`DarsRuntime.run_configured_critique`) |
| Backend-boundary record writer (M-DARS-BE-3) | `src/hisys/agents/dars_backend_boundary.py` |
| Local activation packet example | `docs/examples/dars/backend-activation-localhost.example.json` |
| Localhost smoke runbook (referenced for stop-condition shape) | `docs/runbooks/dars-live-backend-localhost-smoke.md` |
| Remote subscription policy tests | `tests/unit/test_dars_remote_subscription_policy.py` |
| Remote subscription dispatch tests | `tests/unit/test_dars_remote_subscription_dispatch.py` |
| Bootstrap profile pin | `docs/milestone-bootstrap/profile.yaml` |
| Governance current-state test | `tests/unit/test_governance_docs_current_state.py` |
| Traceability index | `docs/traceability/README.md` |
| Ralph control plan | `ralph.md` |

## 3. Accepted decisions for this PREP row

1. **Docs/control only.** This PREP authors no production code, no
   tests, no fixtures, and no runtime artifacts. The existing
   M-DARS-BE-5 (policy validator) and M-DARS-BE-6 (dispatch harness)
   surfaces are sufficient for the future execution row; this PREP
   binds them to the user authorization rather than re-implementing
   them.
2. **Operator-supplied prerequisites.** The following values must be
   supplied by the operator out of band before any execution row may
   run; Ralph/Hermes shall not synthesize, choose, or default any of
   them:
   - `provider_id` — `codex` or `claude`;
   - `operator_id` and operator approval reference;
   - `subscription_account_ref` — vault-style reference (e.g.
     `vault://...`) that resolves credentials **outside Hisys**;
   - `redaction_policy_ref` — operator-controlled redaction policy;
   - `egress_scope` — the egress label the operator's audit/network
     policy applies to subscription calls;
   - `expiry / revocation references` — `expires_at` window and
     `revocation_ref` for the policy packet;
   - **a separately governed subscription executor function** that
     performs the real provider call outside Hisys — supplied at
     dispatch time as the `executor=` argument to
     `run_dars_remote_subscription_dispatch(...)`;
   - operator audit-record path under the partition declared in
     Section 6.
3. **No credential surface inside Hisys.** Subscription access is
   mediated **only** through `subscription_account_ref`. The validator
   rejects raw secret-like field names (`api_key`, `apikey`,
   `auth_token`, `access_token`, `secret`, `password`, `credential`,
   `token`) and raw secret-looking values (prefixes `sk-`, `sk_`,
   `ghp_`, `xoxb-`, `xoxp-`, `hf_`) with code
   `raw_secret_value_not_allowed`. No `Authorization` header, API key,
   or token may be sent **by Hisys**; the injected executor is the only
   surface that may produce a provider-bound request, and Hisys passes
   it only the executor payload defined by
   `run_dars_remote_subscription_dispatch(...)`.
4. **No arbitrary endpoint.** The validator rejects `endpoint`,
   `endpoint_url`, `base_url`, `api_url`, and `api_base` fields with
   code `endpoint_url_not_allowed_for_subscription`. The subscription
   path must not be reshaped into an arbitrary OpenAI-/Anthropic-/
   Gemini-/Grok-/HTTP-/local-proxy-compatible endpoint.
5. **No tool / search / browser permission.** The injected subscription
   executor must run with no tool execution, web search, browser
   access, or filesystem mutation authority. The validator rejects
   `mutation_authorized=true`, `publication_authorized=true`,
   `tool_authority_granted=true`, `browser_authority_granted=true`,
   and `search_authority_granted=true` with code
   `mutation_authority_not_allowed`. The harness writes
   `mutation_performed=false`, `publication_performed=false`, and
   `allowed_actions=advisory_only` into every boundary record.
6. **No mutation request.** The execution row stops on any mutation
   request that arises from the operator, the provider's critique
   output, or any downstream consumer of the DARS critic. The output
   is **advisory only**.
7. **Fresh activation packet per execution.** The activation packet
   that pairs with the policy packet must have a current
   `expires_at` window and must declare
   `endpoint_scope=external_api`,
   `allowed_actions=advisory_only`,
   `human_approved=true`, a matching `approval_ref`, matching
   `backend_id` / `backend_kind`, and a `remote_policy_packet_ref`
   that points at the policy packet path. Expired or mismatched
   packets fail closed (see §4.4).
8. **Fresh policy packet per execution.** The remote subscription
   policy packet must have a current `expires_at` window, match
   `approval_ref` with the activation packet and the CLI/runtime
   request, declare `access_mode=subscription`, declare
   `audit_required=true`, and declare an adapter class that matches
   `provider_id` (`codex_subscription` for `codex`,
   `claude_subscription` for `claude`).
9. **Deterministic runtime-boundary record.** Each successful
   execution writes a JSON + Markdown pair under the partition
   declared in Section 6. The record fields are advisory-only and
   must satisfy the M-DARS-BE-6 record contract
   (`external_call_made=true`, `model_boundary_crossed=true`,
   `local_model_call_made=false`, `mutation_performed=false`,
   `publication_performed=false`, `allowed_actions=advisory_only`,
   `transport_kind=injected_subscription_executor`).
10. **Bounded repair.** If the execution row's focused gates fail,
    repair under the existing Ralph bounded-repair rule (≤ 5 focused
    repair loops) before re-asking the operator. Failures that
    require credential surface, account configuration, allowlist
    expansion, raw-secret handling, arbitrary endpoint configuration,
    mutation authority, browser / search / tool permission, or any
    non-subscription transport are non-delegable; stop and ask the
    user.
11. **No automatic completion-claim upgrade.** Even after a successful
    execution row, the DARS completion claim remains
    `local_fixture_localhost_controlled_advisory_complete` until the
    Ralph loop authors and reviews a GREEN/GATE row that records the
    runtime-boundary evidence and re-classifies the queue.

## 4. Exact execution packet contract

The execution row that follows this PREP must use the following inputs
and only the following inputs. Field names match
`src/hisys/agents/dars_remote_subscription_policy.py`,
`src/hisys/agents/dars_remote_subscription_dispatch.py`, and
`src/hisys/agents/dars_backend_activation.py`.

### 4.1 Operator-supplied subscription policy packet

A JSON file matching the `hisys.dars.remote_subscription_policy`
schema (validated by
`validate_dars_remote_subscription_policy_packet(...)`). Schema id is
`hisys.dars.remote_subscription_policy`; schema version
(`DARS_REMOTE_SUBSCRIPTION_POLICY_SCHEMA_VERSION`) is `0.1.0`.

```json
{
  "policy_id":                "DARS-REMOTE-SUB-POLICY-<YYYYMMDD>-<seq>",
  "approval_ref":             "APPROVAL-DARS-REMOTE-SUB-<YYYYMMDD>-<seq>",
  "operator_id":              "<operator identity slug>",
  "provider_id":              "codex | claude",
  "access_mode":              "subscription",
  "subscription_account_ref": "vault://<operator-controlled-ref>",
  "adapter_class":            "codex_subscription | claude_subscription",
  "redaction_policy_ref":     "<operator-controlled redaction policy ref>",
  "egress_scope":             "<operator-controlled egress scope label>",
  "expires_at":               "<ISO-8601 UTC future>",
  "revocation_ref":           "<operator-controlled revocation ref>",
  "audit_required":           true
}
```

Field rules:

- `policy_id`, `approval_ref`, `operator_id`, `provider_id`,
  `access_mode`, `subscription_account_ref`, `adapter_class`,
  `redaction_policy_ref`, `egress_scope`, `expires_at`, and
  `revocation_ref` must be non-empty strings; missing or empty values
  fail with `missing_required_field` (or
  `missing_subscription_account_ref` for the subscription account
  reference).
- `provider_id` must be `codex` or `claude`; any other value fails with
  `provider_not_allowlisted`.
- `access_mode` must equal `subscription`; any other value fails with
  `invalid_access_mode`.
- `adapter_class` must equal `codex_subscription` when
  `provider_id="codex"` and `claude_subscription` when
  `provider_id="claude"`; any other pairing fails with
  `adapter_class_mismatch`.
- `audit_required` must be the boolean `true`; any other value fails
  with `audit_required_must_be_true`.
- `expires_at` must be ISO-8601 and must be **strictly in the future**
  per the injected `now` value used by the validator; expired or
  non-ISO-8601 values fail with `policy_expired` or
  `invalid_expires_at` respectively.
- No raw secret-like field name (`api_key`, `apikey`, `auth_token`,
  `access_token`, `secret`, `password`, `credential`, `token`) and no
  raw secret-looking value (prefixes `sk-`, `sk_`, `ghp_`, `xoxb-`,
  `xoxp-`, `hf_`) may appear in the packet; matches fail with
  `raw_secret_value_not_allowed`.
- No `endpoint`, `endpoint_url`, `base_url`, `api_url`, or `api_base`
  field may appear; matches fail with
  `endpoint_url_not_allowed_for_subscription`.
- No `mutation_authorized`, `publication_authorized`,
  `tool_authority_granted`, `browser_authority_granted`, or
  `search_authority_granted` flag may be `true`; `true` values fail
  with `mutation_authority_not_allowed`.
- The validator emits a deterministic
  `remote_dispatch_not_implemented` **warning** on every valid packet
  so schema validity is **not** authority to dispatch.

### 4.2 Operator-supplied activation packet (paired with the policy packet)

A JSON file matching the `hisys.dars.backend.activation` schema
(validated by `validate_dars_backend_activation_packet(...)`).

```json
{
  "activation_id":             "DARS-BE-ACT-<YYYYMMDD>-REMOTE-SUB-<seq>",
  "backend_id":                "<configured remote subscription backend id>",
  "backend_kind":              "<configured backend kind>",
  "endpoint_scope":            "external_api",
  "allowed_actions":           "advisory_only",
  "human_approved":            true,
  "approval_ref":              "APPROVAL-DARS-REMOTE-SUB-<YYYYMMDD>-<seq>",
  "expires_at":                "<ISO-8601 UTC future>",
  "remote_policy_packet_ref":  "<path to subscription policy packet JSON>"
}
```

Field rules:

- `endpoint_scope` must equal `external_api` (M-DARS-BE-6 enforces this
  pairing for remote subscription dispatch; `localhost_only` is the
  local DARS path and is out of scope here).
- `allowed_actions` must equal `advisory_only`; any other value fails
  with `invalid_allowed_actions`.
- `human_approved` must equal `true`; any other value fails with
  `human_approval_required`.
- `approval_ref` must match the policy packet's `approval_ref` and the
  CLI/runtime request's `approval_ref`. Mismatches fail closed at
  dispatch with `activation_approval_ref_mismatch` or
  `remote_policy_approval_ref_mismatch`.
- `backend_id` and `backend_kind` must match the configured remote
  subscription backend that the operator has registered. Mismatches
  fail closed with `activation_backend_id_mismatch` /
  `activation_backend_kind_mismatch`.
- `remote_policy_packet_ref` must point to the policy packet JSON file
  used in the same dispatch; mismatched refs fail closed with
  `activation_remote_policy_ref_mismatch`.
- `expires_at` must be ISO-8601 and in the future; expired packets
  fail closed with `activation_expired`.
- No raw secret-like field name or value may appear (same allowlist as
  §4.1); matches fail with `raw_secret_value_not_allowed`.
- External-backend activation packets that omit
  `remote_policy_packet_ref` fail with
  `external_backend_requires_remote_policy_packet`.

### 4.3 Operator-supplied subscription executor

The execution row must call
`run_dars_remote_subscription_dispatch(instance, request,
executor=<operator-supplied subscription executor>)` and must supply
the `executor=` argument explicitly. The signature is:

```python
RemoteSubscriptionExecutor = Callable[[dict[str, Any]], str]
```

Required executor invariants (operator-owned):

- runs **outside Hisys**; Hisys passes only the executor payload
  defined by `run_dars_remote_subscription_dispatch(...)`;
- resolves credentials externally through the operator's vault and
  never returns raw credentials to Hisys;
- holds no tool / search / browser / mutation authority;
- returns a non-empty string critique; an empty/whitespace return
  fails closed with `remote_subscription_executor_empty_output`;
- raises on any provider error; the harness fails closed at the
  dispatch chokepoint instead of recovering silently.

If `executor=None` (or absent), the harness raises
`ValueError("remote_subscription_executor_required")`. Merely
importing or wiring the module cannot perform a live provider call.

### 4.4 Validator and runtime issue codes

Codes emitted by
`validate_dars_remote_subscription_policy_packet(...)`
(M-DARS-BE-5):

```text
missing_required_field
missing_subscription_account_ref
provider_not_allowlisted
invalid_access_mode
adapter_class_mismatch
audit_required_must_be_true
endpoint_url_not_allowed_for_subscription
raw_secret_value_not_allowed
mutation_authority_not_allowed
policy_expired
invalid_expires_at
```

Deterministic warning emitted on every valid policy packet:

```text
remote_dispatch_not_implemented
```

Codes emitted by `validate_dars_backend_activation_packet(...)`
(M-DARS-BE-1) that may surface during the execution row:

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

Codes raised by
`run_dars_remote_subscription_dispatch(...)` (M-DARS-BE-6) and
`run_dars_remote_subscription_panel_dispatch(...)` (M24 panel
dispatch) that may surface during the execution row:

```text
invalid_date_partition
invalid_request_id
invalid_backend_id
invalid_source_execution_id
missing_backend_kind
missing_approval_ref
missing_activation_packet_ref
missing_policy_packet_ref
missing_prompt
backend_activation_packet_required
remote_policy_packet_required
remote_policy_packet_invalid
activation_approval_ref_mismatch
activation_backend_id_mismatch
activation_backend_kind_mismatch
activation_endpoint_scope_mismatch
activation_remote_policy_ref_mismatch
invalid_allowed_actions
remote_policy_approval_ref_mismatch
invalid_access_mode
audit_required_must_be_true
remote_subscription_executor_required
remote_subscription_executor_empty_output
multi_critic_panel_requires_at_least_two_requests
panel_date_partition_mismatch
panel_request_id_mismatch
duplicate_panel_source_execution_id
```

Any of these codes is a **fail-closed** signal: do not call the
operator-supplied subscription executor, do not write a boundary
record, do not retry, and surface the code to the operator with the
exact field/path that triggered it. The execution row records the
issue, reports it to the operator, and waits for a corrected packet.

## 5. Exact execution row shape (operator-driven)

The execution row that follows this PREP shall use exactly this shape
and shall not invent additional flags, alternate code paths, or
provider SDK calls. Ralph/Hermes drives steps 1, 2, 5, and 6; the
operator drives steps 0, 3, and 4.

```text
Step 0 (operator): out of band, register the operator subscription
                   account, the vault entry behind
                   subscription_account_ref, the redaction policy, the
                   egress scope, and the revocation reference.
                   confirm the subscription executor function exists
                   outside Hisys and has no tool/search/browser/mutation
                   authority. supply HISYS_INSTANCE to the operator
                   session out of band.

Step 1: confirm imports and harness symbols (no provider call):

  PYTHONPATH=src:. python3 -c "from hisys.agents.dars_remote_subscription_dispatch import \
      RemoteSubscriptionDispatchRequest, run_dars_remote_subscription_dispatch; \
      print('ok')"

Step 2: rehearse the validator and harness against fixture-only inputs
        (no provider call). This step uses the existing
        tests/unit/test_dars_remote_subscription_policy.py and
        tests/unit/test_dars_remote_subscription_dispatch.py focused
        cohorts to confirm that the fail-closed signals in §4.4 still
        surface on the operator's working tree:

  PYTHONPATH=src:. pytest tests/unit/test_dars_remote_subscription_policy.py \
                          tests/unit/test_dars_remote_subscription_dispatch.py -q

Step 3 (operator gate): visually confirm every Section 7 precondition
                        is green before authorizing Step 5. specifically
                        confirm the subscription executor exists outside
                        Hisys, the vault entry behind
                        subscription_account_ref resolves credentials
                        outside Hisys, the redaction policy is applied
                        before the provider call, and the egress scope
                        matches the operator audit/network policy.

Step 4 (operator): build the policy packet JSON (§4.1) and activation
                   packet JSON (§4.2) on local disk. confirm the
                   expires_at windows are current. confirm approval_ref
                   matches across packet, activation, and request.

Step 5: cross the provider boundary through the injected executor
        (operator drives the executor parameter):

  PYTHONPATH=src:. python3 - <<'PY'
  from pathlib import Path
  from hisys.config.instance import resolve_instance_root
  from hisys.agents.dars_remote_subscription_dispatch import (
      RemoteSubscriptionDispatchRequest,
      run_dars_remote_subscription_dispatch,
  )
  # operator supplies subscription_executor outside Hisys; see Section 4.3
  from operator_local.dars_subscription import subscription_executor
  instance = resolve_instance_root(Path("<HISYS_INSTANCE>"))
  request = RemoteSubscriptionDispatchRequest(
      yyyymmdd="<YYYYMMDD>",
      request_id="REQ-DARS-REMOTE-SUB-<seq>",
      backend_id="<configured backend id>",
      backend_kind="<configured backend kind>",
      source_execution_id="EXEC-DARS-REMOTE-SUB-<seq>",
      approval_ref="APPROVAL-DARS-REMOTE-SUB-<YYYYMMDD>-<seq>",
      activation_packet_ref="<path to activation packet json>",
      policy_packet_ref="<path to policy packet json>",
      prompt="<operator-supplied advisory critique prompt>",
  )
  result = run_dars_remote_subscription_dispatch(
      instance,
      request,
      executor=subscription_executor,
  )
  print(result)
  PY

Step 6: re-run the focused subscription cohort + traceability + secret
        scan + diff check, and inspect the runtime-boundary record
        written under the partition declared in Section 6.
```

The dispatch harness is the enforcement boundary. No CLI surface is
provided in this PREP; adding `request-dars-critique --backend
configured` with `endpoint_scope=external_api` and
`--remote-policy-packet` flags is **deferred** to a future row and is
out of scope here.

## 6. Runtime-boundary record path

Each successful execution row writes a JSON + Markdown pair under the
following partition (the existing M-DARS-BE-6 convention; see
`_write_remote_subscription_boundary(...)` in
`src/hisys/agents/dars_remote_subscription_dispatch.py`):

```text
$HISYS_INSTANCE/runtime-boundary/dars-remote-subscriptions/<YYYYMMDD>/<REQUEST_ID>/<BACKEND_ID>-<SOURCE_EXECUTION_ID>.json
$HISYS_INSTANCE/runtime-boundary/dars-remote-subscriptions/<YYYYMMDD>/<REQUEST_ID>/<BACKEND_ID>-<SOURCE_EXECUTION_ID>.md
```

When the execution row composes multiple critic requests through
`run_dars_remote_subscription_panel_dispatch(...)`, the panel boundary
record is written under (same M-DARS-BE-6 / M24 panel convention):

```text
$HISYS_INSTANCE/runtime-boundary/dars-remote-subscription-panels/<YYYYMMDD>/<REQUEST_ID>/<PANEL_ID>.json
$HISYS_INSTANCE/runtime-boundary/dars-remote-subscription-panels/<YYYYMMDD>/<REQUEST_ID>/<PANEL_ID>.md
```

Required record fields (carried by the M-DARS-BE-6 writer):

```text
schema_id              = hisys.dars.remote_subscription_dispatch
schema_version         = 0.1.0
request_id             = <request id>
source_execution_id    = <source execution id>
backend_id             = <configured backend id>
backend_kind           = <configured backend kind>
provider_id            = codex | claude
adapter_class          = codex_subscription | claude_subscription
endpoint_scope         = external_api
approval_ref           = <approval ref>
activation_ref         = <activation packet ref>
policy_ref             = <policy packet ref>
external_call_made     = true
model_boundary_crossed = true
local_model_call_made  = false
mutation_performed     = false
publication_performed  = false
allowed_actions        = advisory_only
requires_human_review  = true
transport_kind         = injected_subscription_executor
critique_text_preview  = <first 500 chars of executor return>
policy_refs            = [HISYS-FR-AGT-001, HISYS-FR-AGT-003,
                          HISYS-CON-010, HISYS-CON-012, M-DARS-BE-6]
```

For panel records the `transport_kind` is
`injected_subscription_executor_panel` and the writer adds
`critic_count`, `completed_critic_count`, `provider_ids`,
`adapter_classes`, and `boundary_refs` per the M-DARS-BE-6 / M24
contract.

No raw API key, raw token, raw `Authorization` header, raw credential
value, raw operator PII, full critique body (beyond the 500-char
preview), raw operator IP/MAC/host metadata, or provider-account
identifier may appear in the boundary record beyond what the existing
`dars_remote_subscription_dispatch.py` writer already supports.

## 7. Stop-condition matrix (apply before and during the execution row)

The execution row stops, the operator is notified, and no further
command runs on any of these signals. Each condition maps to the
M-DARS-BE-5 contract in
`docs/contracts/dars-remote-subscription-backend-policy.md`, the
M-DARS-BE-6 dispatch source, and the M-DARS-BE-1 / M-DARS-BE-2 codes.

| Signal | Effect | Existing surface |
|---|---|---|
| Missing or unreadable policy packet | Stop before any executor call | dispatch raises `remote_policy_packet_required` |
| Invalid policy packet (any §4.4 policy code) | Stop before any executor call | validator returns `ConfigValidationReport(valid=false)`; dispatch raises `remote_policy_packet_invalid` |
| Expired policy packet | Stop before any executor call | validator returns `policy_expired` |
| `provider_id` outside `codex` / `claude` | Stop before any executor call | validator returns `provider_not_allowlisted` |
| `adapter_class` not matching `provider_id` | Stop before any executor call | validator returns `adapter_class_mismatch` |
| `access_mode` ≠ `subscription` | Stop before any executor call | validator returns `invalid_access_mode`; dispatch raises `invalid_access_mode` |
| `audit_required` ≠ `true` | Stop before any executor call | validator returns `audit_required_must_be_true`; dispatch raises `audit_required_must_be_true` |
| Missing or unreadable activation packet | Stop before any executor call | dispatch raises `backend_activation_packet_required` |
| Invalid activation packet (any §4.4 activation code) | Stop before any executor call | validator returns `ConfigValidationReport(valid=false)`; dispatch raises the first error code |
| Expired activation packet | Stop before any executor call | validator returns `activation_expired` |
| External-backend activation packet without `remote_policy_packet_ref` | Stop before any executor call | validator returns `external_backend_requires_remote_policy_packet` |
| Mismatched `approval_ref` between policy / activation / request | Stop before any executor call | dispatch raises `activation_approval_ref_mismatch` / `remote_policy_approval_ref_mismatch` |
| Mismatched `backend_id` / `backend_kind` / `endpoint_scope` between activation and request | Stop before any executor call | dispatch raises `activation_backend_id_mismatch` / `activation_backend_kind_mismatch` / `activation_endpoint_scope_mismatch` |
| Mismatched `remote_policy_packet_ref` between activation and request | Stop before any executor call | dispatch raises `activation_remote_policy_ref_mismatch` |
| Raw secret-like field or value anywhere in policy or activation packet | Stop before any executor call | validator returns `raw_secret_value_not_allowed` |
| Arbitrary endpoint field (`endpoint`, `endpoint_url`, `base_url`, `api_url`, `api_base`) | Stop before any executor call | validator returns `endpoint_url_not_allowed_for_subscription` |
| Mutation / publication / tool / browser / search authority flag set | Stop before any executor call | validator returns `mutation_authority_not_allowed` |
| Executor missing or `None` | Stop before any executor call | dispatch raises `remote_subscription_executor_required` |
| Executor returns empty/whitespace critique | Stop before writing boundary record | dispatch raises `remote_subscription_executor_empty_output` |
| Panel request with fewer than 2 critic requests | Stop before any executor call | panel dispatch raises `multi_critic_panel_requires_at_least_two_requests` |
| Panel request with mismatched date / request_id, or duplicate `source_execution_id` | Stop before any executor call | panel dispatch raises `panel_date_partition_mismatch` / `panel_request_id_mismatch` / `duplicate_panel_source_execution_id` |
| Operator endpoint or executor demands raw credential / Authorization header / API key from Hisys | Stop before any executor call | contract §boundary invariants |
| Tool / search / browser permission requested by subscription executor | Stop before any executor call | contract §boundary invariants |
| Mutation request from operator or executor output | Stop before any further critique | contract §boundary invariants |
| Secret scan failure (`python3 scripts/scan_secrets.py` → `hit_count > 0`) | Stop before any further critique | Ralph §2.2 |
| Operator uncertainty about any precondition | Stop before any further critique | Ralph §2 |
| Working tree dirty in a non-execution surface | Stop before commit/push | Ralph §10.3 |
| Branch / upstream is not `dars` / `origin/dars` | Stop before push | Ralph §10.3 |
| Any focused gate red after 5 bounded repair loops | Stop and ask | Ralph bounded-repair rule |
| Request to expand provider allowlist beyond `codex` / `claude` or adapter-class allowlist beyond `codex_subscription` / `claude_subscription` | Stop and ask | contract §stop conditions |
| Request to add raw-API-key / arbitrary-endpoint / Gemini / Grok / local-proxy / pay-per-call surface | Stop and ask | contract §scope and §stop conditions |
| Request to upgrade DARS completion claim before a GREEN/GATE row | Stop and ask | Ralph §16 |

## 8. Validation commands for this PREP row

This PREP authors no behavior change, so the focused gates are
governance and traceability only. The execution row that follows this
PREP will additionally run the focused subscription cohort.

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

The execution row that follows shall additionally run, post-Step 6,
the focused subscription cohort and the broader DARS regression:

```bash
PYTHONPATH=src:. pytest \
  tests/unit/test_dars_remote_subscription_policy.py \
  tests/unit/test_dars_remote_subscription_dispatch.py \
  tests/unit/test_dars_runtime.py \
  tests/unit/test_dars_backend_activation.py \
  tests/unit/test_dars_backend_boundary.py \
  tests/unit/test_dars_config.py \
  tests/unit/test_dars_dispatch.py \
  tests/unit/test_dars_critic_panel_cli.py \
  tests/unit/test_dars_critic_panel_adapters.py \
  tests/unit/test_dars_critic_panel_runtime.py \
  tests/unit/test_dars_critic_panel_tool_execution_runtime.py \
  tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

## 9. Files this PREP row touches

This PREP row touches docs/control surfaces only:

- `docs/plans/dars-remote-subscription-auth-prep-tasks.md` (this file;
  new).
- `docs/milestone-bootstrap/profile.yaml` — version bump and
  `next_safe_task` advance.
- `tests/unit/test_governance_docs_current_state.py` — assertion
  update to match the new profile state.
- `docs/traceability/README.md` — prepend a
  `DARS-REMOTE-SUBSCRIPTION-AUTH-PREP` row.
- `ralph.md` — Section 16 next-row update and Reflection Log entry.

No file under `src/`, `tests/unit/test_dars_*.py`, fixture trees,
`docs/runbooks/`, `docs/examples/dars/`, `docs/contracts/`, or
runtime-boundary partitions is modified by this PREP row.

## 10. Next safe Ralph row after this PREP commits

```text
DARS-REMOTE-SUBSCRIPTION-AUTH-EXECUTE-OPERATOR-PREREQUISITES
```

This next row is **non-delegable**. It can advance only when the
operator has supplied:

- `provider_id` choice (`codex` or `claude`);
- operator identity and approval reference;
- a vault-style `subscription_account_ref` whose credentials resolve
  outside Hisys;
- a redaction policy reference;
- an egress scope label that matches the operator audit/network
  policy;
- a current `expires_at` window and revocation reference;
- a fresh policy packet JSON path (matching §4.1);
- a fresh activation packet JSON path (matching §4.2) whose
  `remote_policy_packet_ref` points to the policy packet path;
- a separately governed subscription executor function (matching
  §4.3) supplied at dispatch time;
- explicit confirmation that the subscription executor has no tool /
  search / browser / mutation authority;
- explicit confirmation that the operator is decisive about every
  Section 7 precondition;
- `HISYS_INSTANCE` (Hisys instance root) for the runtime-boundary
  record partition.

Until these prerequisites land, the Ralph loop must stop at this PREP
and wait. The `next_safe_task` field in `profile.yaml` advances to
`DARS-REMOTE-SUBSCRIPTION-AUTH-EXECUTE-OPERATOR-PREREQUISITES`, which
is a documented stop-and-ask gate, not an action Ralph can
self-supply.

## 11. Resume checkpoint convention

Append a Resume checkpoint after this PREP commits and after every
subsequent execution-row attempt, matching the format in `ralph.md`
§5.1.1. Required fields:

```text
Current HEAD:        <git rev-parse --short HEAD with subject>
Working tree:        <clean or exact file list>
Last completed task: DARS-REMOTE-SUBSCRIPTION-AUTH-PREP
Next safe target:    DARS-REMOTE-SUBSCRIPTION-AUTH-EXECUTE-OPERATOR-PREREQUISITES
Stop condition:      operator must supply provider/operator/account
                     ref/redaction/egress/expiry/revocation/policy
                     packet/activation packet/subscription executor/
                     no-tool-no-mutation confirmations.
```
