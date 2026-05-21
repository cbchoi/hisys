# DARS Live Backend Implementation Plan

> **For Hermes/Ralph:** This is a controlled Prepare/document-RED artifact for the next DARS backend line after `origin/dars` was synchronized at `ee90674`. Use `test-driven-development` before production code. This plan starts live-backend implementation planning only; it does not authorize a live model call, remote API call, credential lookup, publication, deployment, vault mutation, or additional remote push.

**Goal:** make DARS backend execution operational through a governed backend boundary while preserving advisory-only semantics and fail-closed behavior.

**Architecture:** separate backend activation policy, credential-reference policy, adapter execution, runtime-boundary records, and smoke/runbook evidence. The first executable target remains localhost-only `openai_compatible` backend hardening and fake/local rehearsal; remote external providers are deferred to a separate high-impact approval packet.

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
- External/remote DARS backend requires a later decision packet with explicit approval, egress scope, credential-ref policy, redaction policy, operator identity, expiry, and rollback/disable controls.

---

## Current-state finding

The previous live-panel line has already implemented the safe localhost class: activation packet validation, fake-server local-model adapter, CLI activation rehearsal, and localhost smoke runbook. The remaining backend question is not "can a local model be called by the panel?" but "how should DARS backend activation be represented, audited, and later extended without weakening the advisory boundary?"

Therefore this plan treats **live backend** as a two-level roadmap:

1. **Local live backend hardening:** make the existing `openai_compatible` localhost backend easier to validate, rehearse, and audit without real model access in CI.
2. **External provider backend preparation:** define a separate policy packet and fail-closed schemas for remote providers, without implementing remote dispatch yet.

## Design candidates

| Candidate | Description | Benefit | Risk | Decision |
|---|---|---|---|---|
| A. Extend current local OpenAI-compatible backend only | Harden config/reporting around `DarsRuntime.run_configured_critique` and localhost fake-server smoke. | Lowest risk; reuses existing code; aligns with current tests. | Does not satisfy future remote-provider needs alone. | **Accepted for first implementation line.** |
| B. Add remote provider backend now | Implement external OpenAI/Anthropic/etc. DARS adapter. | Directly enables remote DARS. | Credential, egress, privacy, cost, and governance risk; requires high-impact approval. | **Rejected for this plan.** Defer to M-DARS-BE-5. |
| C. Create provider-neutral backend policy packet first | Define schema and fail-closed validator before adapter code. | Creates safe path for future remote providers. | More planning overhead before execution. | **Accepted as preparation after local hardening.** |

## Implementation sequence

### Task M-DARS-BE-1: Backend activation policy packet validator

**Objective:** define a backend-level activation packet distinct from panel activation so backend dispatch can state what boundary is authorized.

**Files:**
- Create: `src/hisys/agents/dars_backend_activation.py`
- Create: `tests/unit/test_dars_backend_activation.py`
- Modify: `docs/traceability/README.md`

**Step 1: Write failing test**

```python
def test_backend_activation_rejects_external_provider_without_policy_packet():
    report = validate_dars_backend_activation_packet({
        "activation_id": "DARS-BE-ACT-20260521-001",
        "backend_id": "external-openai",
        "backend_kind": "openai_compatible",
        "endpoint_scope": "external_api",
        "allowed_actions": "advisory_only",
        "human_approved": True,
        "approval_ref": "APPROVAL-DARS-BE-20260521-001",
    }, config_ref="inline://external")
    assert report.valid is False
    assert any(issue.code == "external_backend_requires_remote_policy_packet" for issue in report.issues)
```

**Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_backend_activation.py::test_backend_activation_rejects_external_provider_without_policy_packet -q
```

Expected: fail because `hisys.agents.dars_backend_activation` does not exist.

**Step 3: Minimal implementation**

Add a Pydantic model and validator with these fields:

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

Reject:

- any raw secret-like field or value;
- `allowed_actions != advisory_only`;
- `endpoint_scope=external_api` without `remote_policy_packet_ref`;
- missing `approval_ref`;
- `human_approved != true`.

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

**Objective:** require the backend activation packet for local live backend rehearsal while keeping existing fixture/loopback behavior unchanged.

**Files:**
- Modify: `src/hisys/agents/dars.py`
- Modify: `src/hisys/cli/main.py`
- Modify: `tests/unit/test_dars_runtime.py`
- Modify: `tests/unit/test_dars_critic_panel_cli.py` if the panel CLI is used as the surface.

**Step 1: Write failing tests**

Add tests that prove:

- `openai_compatible` local backend rejects missing backend activation packet before endpoint contact;
- loopback and fixture-local paths remain unchanged;
- approved localhost activation records `model_boundary_crossed=true`, `local_model_call_made=true`, `external_call_made=false`.

**Step 2: Verify RED**

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_runtime.py::test_configured_local_backend_requires_backend_activation_packet -q
```

Expected: fail because current configured critique only accepts `approval_ref`.

**Step 3: Minimal implementation**

- Add optional backend activation packet loading to the configured DARS runtime or CLI wrapper.
- Validate the packet before dispatching any `openai_compatible` backend.
- Keep dispatch gate appraiser separation unchanged.
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

### Task M-DARS-BE-5: Remote provider policy packet, fail-closed only

**Objective:** define the schema and default-blocking tests for future external DARS providers without implementing remote dispatch.

**Files:**
- Create: `src/hisys/agents/dars_remote_backend_policy.py`
- Create: `tests/unit/test_dars_remote_backend_policy.py`
- Create: `docs/contracts/dars-remote-backend-policy.md`

**Acceptance:**

The policy packet must include:

- `approval_ref`, `operator_id`, `provider_id`, `endpoint_allowlist`, `credential_ref_policy`, `redaction_policy_ref`, `egress_scope`, `max_cost_or_token_budget`, `expires_at`, `revocation_ref`, and `audit_required=true`;
- no raw token/API-key/password fields;
- no mutation/publication/tool/browser/search authority;
- remote dispatch remains blocked unless a later separately approved implementation consumes this policy.

**Validation:**

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_remote_backend_policy.py -q
python3 scripts/scan_secrets.py
```

**Commit:**

```bash
git add src/hisys/agents/dars_remote_backend_policy.py tests/unit/test_dars_remote_backend_policy.py docs/contracts/dars-remote-backend-policy.md docs/traceability/README.md ralph.md
git commit -m "feat: add remote dars backend policy packet"
```

## Quality gate for each implementation increment

Run focused tests first, then the DARS cohort, then repository gates:

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
- any remote provider/API call;
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
