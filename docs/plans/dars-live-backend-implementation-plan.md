# DARS Live Backend Implementation Plan

> **For Hermes/Ralph:** This is a controlled Prepare/document-RED artifact for the next DARS backend line after `origin/dars` was synchronized at `ee90674`. Use `test-driven-development` before production code. This plan starts live-backend implementation planning only; it does not authorize a live model call, remote API call, credential lookup, publication, deployment, vault mutation, or additional remote push.

**Goal:** make DARS backend execution operational through a governed backend boundary while preserving advisory-only semantics and fail-closed behavior.

**Architecture:** separate backend activation policy, subscription-access policy, adapter execution, runtime-boundary records, and smoke/runbook evidence. Backend activation is enforced in `DarsRuntime.run_configured_critique()` after `DarsDispatchGate.evaluate()` allows dispatch and immediately before any model-boundary adapter call; the dispatch gate stays focused on appraiser/dispatch policy and must not absorb packet validation. The first executable target remains localhost-only `openai_compatible` backend hardening and fake/local rehearsal; remote subscription providers are deferred to a separate high-impact approval packet and are limited to Codex and Claude only.

**Tech Stack:** Python, Pydantic schemas, existing Hisys DARS modules (`dars.py`, `dars_config.py`, `dars_dispatch.py`, `dars_panel_live_config.py`, `dars_panel_live_adapter.py`), pytest, runtime-boundary JSON/Markdown artifacts.

**Context Packet:**
- Repo: `/home/cbchoi/workspaces/develop/repos/hisys`
- Branch: `dars`
- Synced baseline: `ee90674 feat: bridge codebase current artifacts to source inspection`
- Existing local/live surfaces:
  - `src/hisys/agents/dars.py` — `DarsRuntime.run_configured_critique`, loopback/openai-compatible local boundary path.
  - `src/hisys/agents/dars_config.py` — backend schema, loopback endpoint validation, backend metadata.
  - `src/hisys/agents/dars_dispatch.py` — advisory-only appraiser/dispatch gate.
  - `src/hisys/agents/dars_panel_live_config.py` — local-model activation packet validation.
  - `src/hisys/agents/dars_panel_live_adapter.py` — fake-server-backed local model panel adapter.
  - `docs/runbooks/dars-live-panel-localhost-smoke.md` — human-gated localhost smoke runbook.
  - `docs/plans/dars-live-panel-configuration-implementation-tasks.md` — earlier panel-level implementation plan, now partly implemented.
- Omitted until retrieved just-in-time: full runtime artifact examples, complete milestone-bootstrap package history, and full test logs.

**Boundary Record:**
- Allowed in this plan increment: local docs, tests, validators, runtime-boundary schemas, fake-server tests, local commit after validation.
- Not authorized: real model call, remote API call, credential lookup/resolution, provider account use, browser/search/tool execution by DARS, deployment, publication, vault write, tag/release, or another remote push.
- External/remote DARS backend requires a later decision packet with explicit approval, egress scope, subscription-access policy, redaction policy, operator identity, expiry, and rollback/disable controls.
- Remote provider scope is restricted to subscription-style access for Codex and Claude only. Raw API-key/provider-token integration, pay-per-call provider APIs, arbitrary OpenAI/Anthropic-compatible endpoints, and additional vendors are out of scope unless a later human decision explicitly changes this provider allowlist.

---

## Current-state finding

The previous live-panel line has already implemented the safe localhost class: activation packet validation, fake-server local-model adapter, CLI activation rehearsal, and localhost smoke runbook. The remaining backend question is not "can a local model be called by the panel?" but "how should DARS backend activation be represented, audited, and later extended without weakening the advisory boundary?"

Therefore this plan treats **live backend** as a two-level roadmap:

1. **Local live backend hardening:** make the existing `openai_compatible` localhost backend easier to validate, rehearse, and audit without real model access in CI.
2. **Remote subscription backend preparation:** define a separate policy packet and fail-closed schemas for Codex/Claude subscription access, without implementing remote dispatch yet.

## Design candidates

| Candidate | Description | Benefit | Risk | Decision |
|---|---|---|---|---|
| A. Extend current local OpenAI-compatible backend only | Harden config/reporting around `DarsRuntime.run_configured_critique` and localhost fake-server smoke. | Lowest risk; reuses existing code; aligns with current tests. | Does not satisfy future remote-provider needs alone. | **Accepted for first implementation line.** |
| B. Add remote provider backend now | Implement direct remote API adapters. | Directly enables remote DARS. | Credential, egress, privacy, cost, and governance risk; violates subscription-only scope. | **Rejected for this plan.** Defer to M-DARS-BE-5 as fail-closed policy only. |
| C. Create Codex/Claude subscription policy packet first | Define schema and fail-closed validator before adapter code, with provider allowlist limited to `codex` and `claude`. | Creates a safe path for future remote subscription access while excluding raw API-key and arbitrary provider paths. | More planning overhead before execution. | **Accepted as preparation after local hardening.** |
| D. Enforce activation inside `DarsRuntime.run_configured_critique()` | Validate backend activation after `DarsDispatchGate.evaluate()` returns `allowed` and before any adapter that crosses a model/backend boundary is called. Keep `DarsDispatchGate` responsible only for dispatch/appraiser policy and decision-record emission. | Prevents CLI/Python API bypass, preserves separation between dispatch decisions and runtime activation, and gives one side-effect chokepoint. | Requires small runtime signature and CLI pass-through change. | **Accepted for M-DARS-BE-2.** |

## Backend activation enforcement decision

Activation packet enforcement belongs in `DarsRuntime.run_configured_critique()`, not only in the CLI and not inside `DarsDispatchGate`. The enforcement order is:

```text
load_dars_config()
select default backend
DarsDispatchGate.evaluate(... intent="advisory_critique" ...)
if dispatch.decision != "allowed": block before any adapter call
if selected backend crosses a model/backend boundary: load and validate backend activation packet
if activation/config/approval metadata do not match: block before any adapter call
call the selected backend adapter only after both gates pass
```

`DarsDispatchGate` remains the appraiser/dispatch policy gate: backend declared/enabled, advisory intent, external-call approval reference where applicable, and dispatch decision artifact. It must not become the activation-packet schema validator or remote subscription policy validator. `dars_backend_activation.py` owns packet validation; `dars_remote_subscription_policy.py` owns future Codex/Claude subscription policy validation; `DarsRuntime` is the runtime chokepoint that composes these gates immediately before side effects.

Activation applicability rules:

```text
loopback backend
  backend activation packet not required

fixture_text / run_fixture_critique
  backend activation packet not required

fixture-local paths that do not cross a model boundary
  backend activation packet not required

openai_compatible + local_network_only
  backend activation packet required
  endpoint_scope must be localhost_only
  approval_ref must match activation.approval_ref
  external_call_made=false
  local_model_call_made=true
  model_boundary_crossed=true after successful call

external_api / remote subscription candidate
  backend activation packet required
  remote_policy_packet_ref required
  policy provider allowlist remains Codex/Claude subscription-only
  actual remote dispatch remains blocked until a later explicit implementation approval
```

Initial integration should preserve existing callers by adding an optional `backend_activation_packet_ref` argument beside `approval_ref`, then making the packet authoritative for model-boundary execution. If both are supplied, mismatched approval references must fail closed with `activation_approval_ref_mismatch`.

## Validator and integration blocker controls

M-DARS-BE-1 must keep the activation packet narrow and deterministic so M-DARS-BE-2 can enforce it without ambiguity. The validator may define both `localhost_only` and `external_api` endpoint scopes, but remote/external scope remains fail-closed preparation only: an `external_api` packet is valid only as a policy description when `remote_policy_packet_ref` is present; it still does not authorize remote dispatch.

Validator output should follow the existing Hisys validation-report pattern with deterministic issue codes. Reuse `ConfigValidationIssue` / `ConfigValidationReport` if that fits cleanly; otherwise define a small DARS-specific report with the same `valid`, `issues`, `path`, `code`, `message`, and `severity` shape. Tests must assert issue codes rather than free-form message strings.

Required M-DARS-BE-1 issue codes:

```text
external_backend_requires_remote_policy_packet
raw_secret_value_not_allowed
invalid_allowed_actions
missing_approval_ref
human_approval_required
activation_expired
invalid_endpoint_scope
```

Recommended additional M-DARS-BE-2/runtime mismatch codes:

```text
backend_activation_packet_required
activation_approval_ref_mismatch
activation_backend_id_mismatch
activation_backend_kind_mismatch
activation_endpoint_scope_mismatch
remote_dispatch_not_implemented
```

`expires_at` handling must be deterministic. The validator should accept an optional injected `now` value for tests and runtime callers. Tests must not depend on wall-clock time. If an implementation cannot add `now` cleanly in the first increment, it may validate ISO format in M-DARS-BE-1 and defer expiry comparison to the runtime integration task, but the deferral must be explicit and covered by a failing test before runtime enforcement.

Secret rejection must be bounded and explainable. Reject secret-like field names such as `api_key`, `token`, `secret`, `password`, and `credential` except the controlled reference field `approval_ref`. Also reject obvious raw secret-like string values with a small deterministic matcher. Do not add high-recall secret scanning that creates unstable false positives in ordinary approval or policy refs.

M-DARS-BE-2 must preserve the existing `approval_ref` argument while adding `backend_activation_packet_ref`. The activation packet becomes authoritative for model-boundary execution. If both references are supplied, mismatches fail closed with `activation_approval_ref_mismatch`. Missing packet must be proven to block before endpoint contact by a test that monkeypatches or spies on `_run_openai_compatible_backend` and asserts it is not called.

## Implementation sequence

### Task M-DARS-BE-1: Backend activation policy packet validator

**Objective:** define a backend-level activation packet distinct from panel activation so backend dispatch can state what boundary is authorized.

**Files:**
- Create: `src/hisys/agents/dars_backend_activation.py`
- Create: `tests/unit/test_dars_backend_activation.py`
- Modify: `docs/traceability/README.md`

**Step 1: Write failing tests**

```python
def _issue_codes(report):
    return {issue.code for issue in report.issues}


def test_backend_activation_rejects_external_provider_without_policy_packet():
    report = validate_dars_backend_activation_packet({
        "activation_id": "DARS-BE-ACT-20260521-001",
        "backend_id": "external-openai",
        "backend_kind": "openai_compatible",
        "endpoint_scope": "external_api",
        "allowed_actions": "advisory_only",
        "human_approved": True,
        "approval_ref": "APPROVAL-DARS-BE-20260521-001",
        "expires_at": "2026-05-22T00:00:00Z",
    }, config_ref="inline://external", now="2026-05-21T00:00:00Z")
    assert report.valid is False
    assert "external_backend_requires_remote_policy_packet" in _issue_codes(report)


def test_backend_activation_rejects_expired_packet_deterministically():
    report = validate_dars_backend_activation_packet({
        "activation_id": "DARS-BE-ACT-20260521-002",
        "backend_id": "local-llm",
        "backend_kind": "openai_compatible",
        "endpoint_scope": "localhost_only",
        "allowed_actions": "advisory_only",
        "human_approved": True,
        "approval_ref": "APPROVAL-DARS-BE-20260521-002",
        "expires_at": "2026-05-20T00:00:00Z",
    }, config_ref="inline://expired", now="2026-05-21T00:00:00Z")
    assert report.valid is False
    assert "activation_expired" in _issue_codes(report)


def test_backend_activation_rejects_secret_like_fields_and_values():
    report = validate_dars_backend_activation_packet({
        "activation_id": "DARS-BE-ACT-20260521-003",
        "backend_id": "local-llm",
        "backend_kind": "openai_compatible",
        "endpoint_scope": "localhost_only",
        "allowed_actions": "advisory_only",
        "human_approved": True,
        "approval_ref": "APPROVAL-DARS-BE-20260521-003",
        "expires_at": "2026-05-22T00:00:00Z",
        "api_key": "sk-test-not-allowed",
    }, config_ref="inline://secret", now="2026-05-21T00:00:00Z")
    assert report.valid is False
    assert "raw_secret_value_not_allowed" in _issue_codes(report)
```

**Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_backend_activation.py::test_backend_activation_rejects_external_provider_without_policy_packet -q
```

Expected: fail because `hisys.agents.dars_backend_activation` does not exist. After creating the test file, the full RED set for this task is:

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_backend_activation.py -q
```

**Step 3: Minimal implementation**

Add a Pydantic model and validator with deterministic validation-report output. Prefer the existing `ConfigValidationIssue` / `ConfigValidationReport` shape if clean; otherwise mirror its fields in a small DARS-specific report. Add a `now` parameter to `validate_dars_backend_activation_packet(..., now: str | datetime | None = None)` so expiry tests do not depend on wall-clock time.

Fields:

- `activation_id`
- `backend_id`
- `backend_kind`
- `endpoint_scope`: `localhost_only | external_api`
- `allowed_actions="advisory_only"`
- `human_approved=True`
- `approval_ref`
- `expires_at`
- `remote_policy_packet_ref: str | None`
- derived flags:
  - `mutation_authorized=false`
  - `publication_authorized=false`
  - `requires_human_review=true`

Reject with deterministic issue codes:

- any raw secret-like field or bounded raw secret-like value -> `raw_secret_value_not_allowed`;
- `allowed_actions != advisory_only` -> `invalid_allowed_actions`;
- `endpoint_scope` outside `localhost_only | external_api` -> `invalid_endpoint_scope`;
- `endpoint_scope=external_api` without `remote_policy_packet_ref` -> `external_backend_requires_remote_policy_packet`;
- missing `approval_ref` -> `missing_approval_ref`;
- `human_approved != true` -> `human_approval_required`;
- `expires_at` before injected `now` -> `activation_expired`.

**Step 4: Verify GREEN**

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_backend_activation.py -q
```

**Step 5: Commit**

```bash
git add src/hisys/agents/dars_backend_activation.py tests/unit/test_dars_backend_activation.py docs/traceability/README.md ralph.md
git commit -m "feat: add dars backend activation validator"
```

### Task M-DARS-BE-2: Local backend activation integration

**Objective:** require the backend activation packet in `DarsRuntime.run_configured_critique()` for local live backend rehearsal while keeping existing fixture/loopback behavior unchanged and keeping packet validation out of `DarsDispatchGate`.

**Files:**
- Modify: `src/hisys/agents/dars.py`
- Modify: `src/hisys/cli/main.py`
- Modify: `tests/unit/test_dars_runtime.py`
- Modify: `tests/unit/test_dars_critic_panel_cli.py` if the panel CLI is used as the surface.

**Step 1: Write failing tests**

Add tests that prove:

- `openai_compatible` + `local_network_only` rejects missing `backend_activation_packet_ref` before endpoint contact;
- `DarsDispatchGate` is still called before activation validation and remains a dispatch/appraiser gate, not a packet validator;
- loopback, fixture text, and fixture-local paths that do not cross a model boundary remain unchanged and do not require activation;
- approved localhost activation requires `endpoint_scope=localhost_only`, matching `approval_ref`, `allowed_actions=advisory_only`, `human_approved=true`, and records `model_boundary_crossed=true`, `local_model_call_made=true`, `external_call_made=false`;
- mismatched CLI/runtime `approval_ref` and activation packet `approval_ref` fails closed with `activation_approval_ref_mismatch`;
- missing activation blocks before endpoint contact by monkeypatching or spying on `_run_openai_compatible_backend` and asserting it is not called;
- direct Python calls to `DarsRuntime.run_configured_critique()` cannot bypass activation even if the CLI would normally pass the packet path;
- the CLI only passes `--backend-activation-packet` / `backend_activation_packet_ref` through and is not the enforcement boundary.

**Step 2: Verify RED**

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_runtime.py::test_configured_local_backend_requires_backend_activation_packet -q
```

Expected: fail because current configured critique only accepts `approval_ref` and does not require/load `backend_activation_packet_ref` before the local model adapter path.

**Step 3: Minimal implementation**

- Add optional `backend_activation_packet_ref` pass-through to the CLI surface, but make `DarsRuntime.run_configured_critique()` the enforcement boundary.
- In `DarsRuntime.run_configured_critique()`, run `DarsDispatchGate.evaluate()` first, then validate the activation packet immediately before dispatching any backend that crosses a model/backend boundary.
- Keep `DarsDispatchGate` appraiser/dispatch separation unchanged; do not move packet schema validation or remote subscription policy validation into the gate.
- For `openai_compatible` + `local_network_only`, require `endpoint_scope=localhost_only`, `activation.backend_id == backend_id`, `activation.backend_kind == backend.kind`, and `activation.approval_ref == approval_ref` when both are supplied. Use deterministic runtime error codes `backend_activation_packet_required`, `activation_approval_ref_mismatch`, `activation_backend_id_mismatch`, `activation_backend_kind_mismatch`, and `activation_endpoint_scope_mismatch`.
- Preserve no Authorization header and no credential lookup for localhost-only mode.

**Step 4: Verify GREEN**

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_runtime.py tests/unit/test_dars_config.py tests/unit/test_dars_dispatch.py -q
```

**Step 5: Commit**

```bash
git add src/hisys/agents/dars.py src/hisys/cli/main.py tests/unit/test_dars_runtime.py tests/unit/test_dars_critic_panel_cli.py docs/traceability/README.md ralph.md
git commit -m "feat: gate local dars backend with activation packets"
```

### Task M-DARS-BE-3: Runtime-boundary backend decision records

**Objective:** persist a backend-level decision record separate from panel task records and dispatch decisions.

**Files:**
- Create or modify: `src/hisys/agents/dars_backend_boundary.py`
- Modify: `src/hisys/agents/dars.py`
- Create: `tests/unit/test_dars_backend_boundary.py`

**Acceptance:**

Each local live backend run writes a JSON/Markdown pair under:

```text
runtime-boundary/dars-backends/<YYYYMMDD>/<REQUEST_ID>/<BACKEND_ID>.json
runtime-boundary/dars-backends/<YYYYMMDD>/<REQUEST_ID>/<BACKEND_ID>.md
```

Required fields:

```text
schema_id=hisys.dars.backend_boundary
backend_id=<id>
backend_kind=openai_compatible
endpoint_scope=localhost_only
approval_ref=<ref>
activation_ref=<ref>
model_boundary_crossed=true
local_model_call_made=true
external_call_made=false
mutation_performed=false
publication_performed=false
allowed_actions=advisory_only
requires_human_review=true
```

**Validation:**

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_backend_boundary.py tests/unit/test_dars_runtime.py -q
```

**Commit:**

```bash
git add src/hisys/agents/dars_backend_boundary.py src/hisys/agents/dars.py tests/unit/test_dars_backend_boundary.py tests/unit/test_dars_runtime.py docs/traceability/README.md ralph.md
git commit -m "feat: record dars backend boundary decisions"
```

### Task M-DARS-BE-4: Operator-facing local backend smoke packet

**Objective:** provide a copy-editable, secret-free local backend activation example and a no-network/fake-server rehearsal command.

**Files:**
- Create: `docs/examples/dars/backend-activation-localhost.example.json`
- Create or modify: `docs/runbooks/dars-live-backend-localhost-smoke.md`
- Create: `tests/unit/test_dars_live_backend_runbook.py`

**Acceptance:**

The runbook must state:

- the endpoint is supplied by the operator and must be loopback-only;
- Hisys does not install/start/download/select a model runner;
- no credentials or Authorization header are used for localhost mode;
- smoke stops on non-loopback endpoint, credential demand, missing activation, mutation/publication/tool/search/browser request, failed secret scan, or operator uncertainty;
- remote providers are not covered.

**Validation:**

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_live_backend_runbook.py -q
python3 scripts/scan_secrets.py
```

**Commit:**

```bash
git add docs/examples/dars/backend-activation-localhost.example.json docs/runbooks/dars-live-backend-localhost-smoke.md tests/unit/test_dars_live_backend_runbook.py docs/traceability/README.md ralph.md
git commit -m "docs: add local dars backend smoke packet"
```

### Task M-DARS-BE-5: Remote subscription provider policy packet, fail-closed only

**Objective:** define the schema and default-blocking tests for future Codex/Claude subscription-backed DARS providers without implementing remote dispatch.

**Files:**
- Create: `src/hisys/agents/dars_remote_subscription_policy.py`
- Create: `tests/unit/test_dars_remote_subscription_policy.py`
- Create: `docs/contracts/dars-remote-subscription-backend-policy.md`

**Acceptance:**

The policy packet must include:

- `approval_ref`, `operator_id`, `provider_id`, `access_mode="subscription"`, `subscription_account_ref`, `adapter_class`, `redaction_policy_ref`, `egress_scope`, `max_session_or_token_budget`, `expires_at`, `revocation_ref`, and `audit_required=true`;
- `provider_id` is restricted to `codex` or `claude`;
- `adapter_class` is restricted to the matching subscription adapter class, e.g. `codex_subscription` or `claude_subscription`;
- no raw token/API-key/password fields and no endpoint URL fields that would convert subscription access into an arbitrary API/backend path;
- no provider outside Codex/Claude, including generic OpenAI-compatible, generic Anthropic-compatible, Gemini, Grok, local proxy, custom HTTP, or arbitrary URL providers;
- no mutation/publication/tool/browser/search authority;
- remote dispatch remains blocked unless a later separately approved implementation consumes this policy.

**Validation:**

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_remote_subscription_policy.py -q
python3 scripts/scan_secrets.py
```

**Commit:**

```bash
git add src/hisys/agents/dars_remote_subscription_policy.py tests/unit/test_dars_remote_subscription_policy.py docs/contracts/dars-remote-subscription-backend-policy.md docs/traceability/README.md ralph.md
git commit -m "feat: add remote dars subscription policy packet"
```

## Quality gate for each implementation increment

Run focused tests first, then the DARS cohort, then repository gates. For M-DARS-BE-2, include tests proving the CLI cannot bypass runtime enforcement and direct Python calls cannot bypass CLI checks:

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_runtime.py tests/unit/test_dars_config.py tests/unit/test_dars_dispatch.py tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_live_config.py tests/unit/test_dars_critic_panel_live_adapter.py tests/unit/test_dars_critic_panel_live_runbook.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
git status --short --branch
```

For implementation changes that touch common CLI/runtime paths, also run:

```bash
PYTHONPATH=src:. pytest -q
```

## Stop conditions

Stop and request a new explicit decision before any of these:

- real local model call against an operator endpoint;
- any remote provider/API/subscription call;
- credential reference resolution or environment-variable secret lookup;
- provider account configuration;
- deployment, release, tag, publication, or runtime operation beyond fixture/fake-server tests;
- additional remote push after commits created by this plan;
- boundary semantics change from advisory-only to action/execution authority.

## Next executable RED

After this Prepare plan is committed, the next safe command is:

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_backend_activation.py::test_backend_activation_rejects_external_provider_without_policy_packet -q
```

Expected first failure: `ModuleNotFoundError: No module named 'hisys.agents.dars_backend_activation'`.
