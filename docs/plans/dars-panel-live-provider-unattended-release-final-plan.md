# DARS Panel Live-Provider, Unattended Operation, and Release Completion Final Plan

> **For Ralph/Hermes:** Use `ralph-loop-control`, `writing-plans`, and `test-driven-development` before executing this plan. Execute one RED--GREEN--validate--commit unit at a time. This plan is a controlled final roadmap; it does not by itself authorize live provider calls, credential access, unattended execution, release, deployment, publication, force push, or external mutation.

**Goal:** Advance DARS panel from `local_fixture_localhost_controlled_advisory_complete` to a controlled, live-provider-capable, bounded-unattended, releasable product line with explicit evidence for each claim.

**Architecture:** Keep the existing DARS panel runtime, trace writers, advisory semantics, and failure isolation. Add a layered live-provider stack: provider policy and credential-reference validation, injected transport harness, real provider adapter with bounded prompts and redaction, provider smoke gates, standing approval policy for unattended advisory-only runs, runtime monitor/kill-switch surfaces, and final release readiness evidence. Live provider execution and unattended operation remain claim-specific gates, not implicit side effects of configuration.

**Tech Stack:** Python package under `src/hisys`, pytest, existing DARS panel modules, existing remote subscription dispatch harness, controlled Markdown/YAML/JSON docs, runtime-boundary artifacts, secret scanner, traceability validator, normal Git commit/push on branch `dars` after validation.

**Context Packet:**

Required source handles:

- `docs/traceability/dars-critic-panel-runtime-traceability.md` — current DARS panel RTM and local completion boundary.
- `docs/reports/dars-panel-local-completion-audit.md` — current local completion audit and four-boundary evidence.
- `docs/runbooks/dars-panel-fixture-operator-run.md` — current fixture-local operator boundary.
- `docs/runbooks/dars-codex-subscription-executor-runbook.md` — current remote subscription executor boundary.
- `src/hisys/agents/dars_panel.py` — current panel runtime and fixture adapters.
- `src/hisys/agents/dars_panel_live_config.py` — localhost-only activation packet.
- `src/hisys/agents/dars_panel_live_adapter.py` — localhost-only OpenAI-compatible bridge.
- `src/hisys/agents/dars_remote_subscription_dispatch.py` — injected remote subscription dispatch seam.
- `src/hisys/agents/dars_codex_cli_subprocess.py` — governed Codex CLI subprocess wrapper and failure-mode contract.
- `src/hisys/agents/dars_remote_subscription_policy.py` and `src/hisys/agents/dars_backend_activation.py` — policy/activation validators.
- `tests/unit/test_dars_critic_panel_*.py`, `tests/unit/test_dars_panel_readiness.py`, `tests/unit/test_dars_remote_subscription_dispatch.py`, `tests/unit/test_dars_codex_cli_subprocess.py` — current DARS panel/regression anchors.

Omitted context until retrieved just-in-time: raw runtime-boundary evidence payloads, provider-specific account settings, credentials, and any live provider outputs. Do not store raw secrets in repo or plans.

**Boundary Record:**

This plan may be committed as documentation. Execution must stop for a decision packet before any of the following: real provider/model call, credential reference activation, standing unattended approval, release artifact publication, deployment, external notification, package upload, removal of `requires_human_review`, or any mutation outside a controlled Hisys runtime root. Normal local commits and `git push origin dars` are allowed after docs/control validation because the repository/branch/remote are explicit and already configured.

---

## 1. Current State and Claim Gap

Current accepted claim:

```text
local_fixture_localhost_controlled_advisory_complete
```

Current evidence shows:

- fixture-local DARS panel productization is closed;
- localhost model rehearsal exists but remains human-gated;
- remote subscription dispatch exists through injected/fake executors and bounded Codex subprocess smoke evidence;
- live external provider execution remains unimplemented/unproven for DARS panel productization;
- production/release readiness and unattended operation are not yet claimed;
- `requires_human_review=true` remains part of the safety contract.

Final target claims must be separated:

| Claim ID | Claim | Meaning | Required before claim can be true |
|---|---|---|---|
| `live_provider_advisory_smoked` | DARS panel can call a real provider under explicit approval | At least one real provider/model boundary crossed through a governed adapter, with runtime-boundary evidence and no mutation/publication | Decision packet, credential reference, allowlist, redaction, quota/rate limits, single-critic smoke, review |
| `multi_critic_live_provider_advisory_complete` | Multi-critic panel can run against live provider(s) | Two or more critic tasks complete or fail-isolate under a panel-level live boundary record | Multi-critic smoke, partial failure test, cost/latency envelope evidence |
| `bounded_unattended_advisory_operation_ready` | Operator can grant standing approval for bounded advisory-only runs | No per-run approval needed within a finite policy envelope; kill switch and monitoring exist | Standing approval policy, scheduler/runner, budget caps, circuit breakers, audit ledger, alerting, rollback |
| `release_candidate_ready` | A human can review a release candidate | Tests, docs, traceability, runbooks, security scan, release notes, migration/rollback evidence pass | CI/local full gates, release checklist, packaging dry run, operator acceptance |
| `released_for_controlled_advisory_use` | Controlled release is published/available | Release artifact exists and is tagged/published according to approved process | Human approval, final decision packet, tag/package/upload/deploy run, post-release smoke |

Non-goal unless separately approved: fully autonomous authority to mutate user data, publish externally, deploy code, approve decisions, trade/place orders, bypass human review for substantive recommendations, or remove audit records.

## 2. DOE-Informed Architecture Choice

| Candidate | Description | Strength | Risk | Verdict |
|---|---|---|---|---|
| A. Direct provider SDK in panel runtime | Add provider SDK calls inside `dars_panel.py` | Short path | Entangles runtime scheduling with credentials, policy, and provider failures | Reject |
| B. Extend existing injected remote subscription dispatch seam | Use policy/activation packets plus executor abstraction; add real executor only after fixture gates | Preserves boundaries, testability, and evidence records | Needs more control docs and transport validation | Recommended |
| C. Delegate all live calls to external CLI agents only | Keep Hisys as prompt/boundary generator and use Codex/Claude CLI wrappers | Low credential handling in Hisys | Harder to standardize provider telemetry and unattended operation | Use as one provider transport option, not the only path |
| D. Release localhost-only as final | Avoid external provider work | Safe | Does not satisfy user target | Reject for final target |

Recommended final architecture: **B with C as a supported transport class**. The DARS panel should call a provider executor through an explicit transport interface that can be fake/injected in tests, Codex CLI subprocess in governed subscription mode, or a real provider adapter only after policy/approval/credential-reference gates pass.

## 3. Release Milestones

### Milestone R0 — Final controlled requirement update

**Objective:** Convert the desired final state into controlled requirements, design, tests, and traceability before code.

**Files:**

- Modify: `docs/requirements/dars-critic-panel-runtime-requirements.md`
- Modify: `docs/design/dars-critic-panel-runtime-sdd.md`
- Modify: `docs/test/dars-critic-panel-runtime-std.md`
- Modify: `docs/traceability/dars-critic-panel-runtime-traceability.md`
- Create: `docs/milestone-bootstrap/documents/readiness_decision_record_<next>.md`

**Tasks:**

1. Add explicit final claims and non-goals from Section 1.
2. Add V&V rows for live-provider smoke, multi-critic live-provider smoke, bounded unattended operation, release candidate readiness, and controlled release.
3. Add traceability rows that preserve `requires_human_review=true` unless a future human-approved policy explicitly changes the claim.
4. Validate docs and commit.

**Validation:**

```bash
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit:** `docs: define dars panel live release claims`

### Milestone R1 — Provider policy, credential-reference, and transport contract

**Objective:** Specify and test a live-provider transport contract without reading credentials or calling providers.

**Files:**

- Create: `src/hisys/agents/dars_live_provider_policy.py`
- Create: `src/hisys/agents/dars_live_provider_transport.py`
- Create: `tests/unit/test_dars_live_provider_policy.py`
- Create: `tests/unit/test_dars_live_provider_transport.py`
- Modify: `docs/runbooks/dars-codex-subscription-executor-runbook.md`
- Modify: `docs/traceability/dars-critic-panel-runtime-traceability.md`

**Task R1.1 — RED: policy rejects raw secrets**

Write a failing test that a policy packet containing `api_key`, `token`, `password`, `sk-*`, `hf_*`, or `Authorization` is invalid.

Run:

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_live_provider_policy.py::test_live_provider_policy_rejects_raw_secret_fields -q
```

Expected RED: module or validator missing.

**Task R1.2 — GREEN: policy accepts credential references only**

Implement a schema with fields such as:

```text
provider_id
provider_kind
model_id
credential_ref
credential_ref_kind
endpoint_ref
allowed_actions=advisory_only
external_call_allowed=true
mutation_allowed=false
publication_allowed=false
requires_human_review=true
max_prompt_bytes
max_output_bytes
rate_limit_per_minute
cost_budget_ref
approval_ref
expires_at
```

Do not resolve `credential_ref`. Store only refs such as `env://HISYS_DARS_PROVIDER_TOKEN` or `secret-manager-ref://...`.

**Task R1.3 — Transport interface and fake executor**

Add a transport request/result object that carries redacted prompt metadata, boundary flags, provider refs, cost/token placeholders, and failure codes. Unit tests use a fake transport only.

**Validation:**

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_live_provider_policy.py tests/unit/test_dars_live_provider_transport.py -q
python3 scripts/scan_secrets.py
git diff --check
```

**Commit:** `feat: add dars live provider policy contract`

### Milestone R2 — Provider adapter fail-closed implementation

**Objective:** Add the real-provider adapter seam but keep live execution disabled unless an activation packet, provider policy, env gate, and explicit approval are present.

**Files:**

- Create/modify: `src/hisys/agents/dars_live_provider_adapter.py`
- Modify: `src/hisys/agents/dars_remote_subscription_dispatch.py`
- Create: `tests/unit/test_dars_live_provider_adapter.py`
- Modify: `src/hisys/cli/main.py` only if a CLI wrapper is needed for smoke preparation.

**Tasks:**

1. RED: adapter refuses missing executor/credential reference.
2. RED: adapter refuses missing approval/env gate.
3. RED: adapter refuses mutation/publication/tool/browser/search authority.
4. GREEN: implement a dry-run/fake transport path that writes boundary records with `external_call_made=false`.
5. GREEN: implement live transport entry point behind all gates; tests still use monkeypatched fake HTTP/CLI runner, not real provider.
6. Add output redaction and max-output enforcement.
7. Add deterministic failure codes: timeout, non-2xx, malformed JSON, empty output, output too long, raw secret in output, unauthorized authority claim, quota exceeded.

**Validation:**

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_live_provider_adapter.py tests/unit/test_dars_remote_subscription_dispatch.py tests/unit/test_dars_codex_cli_subprocess.py -q
python3 scripts/scan_secrets.py
git diff --check
```

**Commit:** `feat: add fail-closed dars live provider adapter`

### Milestone R3 — Single-critic live-provider smoke gate

**Objective:** Cross one real provider/model boundary under a human-approved decision packet and record bounded evidence.

**Files:**

- Create: `docs/runbooks/dars-live-provider-single-smoke.md`
- Create: `docs/examples/dars/live-provider-single-smoke.policy.example.json`
- Create: `docs/reports/dars-live-provider-single-smoke-<date>.md` after run
- Runtime output: `runtime-boundary/dars-live-provider/<yyyymmdd>/<request_id>/...`

**Preconditions:**

- Human-approved decision packet exists.
- Credential is available only through the chosen credential reference mechanism.
- Provider/model/endpoint are allowlisted by policy.
- Budget/rate limit are finite.
- Prompt and output redaction tests pass.
- Operator confirms this smoke is allowed.

**Execution pattern:**

1. Run preflight with no live call.
2. Run exactly one single-critic live call.
3. Persist boundary record with:
   - `external_call_made=true`
   - `model_boundary_crossed=true`
   - `mutation_performed=false`
   - `publication_performed=false`
   - `allowed_actions=advisory_only`
   - `requires_human_review=true`
   - provider/model refs, not raw credentials
   - token/cost/latency fields if available
4. Human review accepts or rejects the evidence.

**Stop conditions:** any missing decision packet, secret scan hit, unexpected authority claim, output redaction failure, budget violation, failed provider call, or operator uncertainty.

**Commit after review:** `docs: record dars live provider single smoke`

### Milestone R4 — Multi-critic live-provider panel smoke gate

**Objective:** Prove DARS panel can run two or more live provider critics with panel-level boundary evidence and failure isolation.

**Files:**

- Create: `docs/runbooks/dars-live-provider-panel-smoke.md`
- Create: `docs/examples/dars/live-provider-panel-smoke.policy.example.json`
- Modify: `src/hisys/agents/dars_remote_subscription_dispatch.py` if panel-level live evidence needs new fields
- Create/modify: `tests/unit/test_dars_live_provider_panel_dispatch.py`
- Create: `docs/reports/dars-live-provider-panel-smoke-<date>.md` after run

**Tasks:**

1. RED: panel smoke refuses duplicate source execution ids and nonmatching request ids.
2. RED: panel smoke refuses policy mismatch across critics unless explicitly allowed.
3. GREEN: panel-level live boundary record summarizes all per-critic boundary refs, statuses, cost/latency, and safety flags.
4. GREEN: failure isolation test where one critic fails and synthesis remains advisory/partial.
5. Live smoke: run two critics under one decision packet and one finite budget envelope.
6. Human review: accept only the bounded claim `multi_critic_live_provider_advisory_complete` if evidence matches.

**Validation:**

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_live_provider_panel_dispatch.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_remote_subscription_dispatch.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit after review:** `docs: record dars live provider panel smoke`

### Milestone R5 — Bounded unattended advisory operation

**Objective:** Permit unattended advisory-only DARS panel runs inside a finite standing approval policy, without granting mutation/publication/decision authority.

**Files:**

- Create: `src/hisys/agents/dars_unattended_policy.py`
- Create: `src/hisys/operations/dars_unattended_runner.py`
- Create: `tests/unit/test_dars_unattended_policy.py`
- Create: `tests/unit/test_dars_unattended_runner.py`
- Create: `docs/runbooks/dars-unattended-advisory-operation.md`
- Create: `docs/examples/dars/unattended-standing-approval.example.json`

**Policy fields:**

```text
standing_approval_id
approved_by
approval_ref
valid_from
expires_at
provider_policy_refs
allowed_request_classes
allowed_panel_ids
max_runs_per_day
max_critics_per_run
max_cost_per_run_ref
max_cost_per_day_ref
rate_limit_per_minute
kill_switch_ref
audit_retention_policy_ref
alert_on_failure_ref
requires_post_run_human_review=true
mutation_allowed=false
publication_allowed=false
external_action_allowed=false
```

**Tasks:**

1. RED: standing policy expires and blocks runner.
2. RED: runner refuses missing kill switch.
3. RED: runner refuses budget/rate limit absence.
4. RED: runner refuses any mutation/publication/action authority.
5. GREEN: runner executes fake transport runs and writes an audit ledger.
6. GREEN: runner stops on circuit breaker: repeated failures, cost threshold, secret scan hit, policy mismatch, output redaction failure.
7. Add CLI preflight only if needed, with dry-run default.
8. Run a dry-run unattended rehearsal with fake transport.
9. After human approval, run a limited unattended live canary: one scheduled or batch run, one request class, finite budget, no mutation, post-run review required.

**Validation:**

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_unattended_policy.py tests/unit/test_dars_unattended_runner.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit:** `feat: add bounded dars unattended advisory runner`

**Claim boundary:** This milestone may support `bounded_unattended_advisory_operation_ready`. It must not claim autonomous decision authority or release readiness.

### Milestone R6 — Observability, operations, and rollback readiness

**Objective:** Make live/unattended operation inspectable, stoppable, and recoverable.

**Files:**

- Create: `src/hisys/operations/dars_live_status.py`
- Create: `tests/unit/test_dars_live_status.py`
- Create: `docs/runbooks/dars-live-operations.md`
- Create: `docs/runbooks/dars-live-rollback.md`
- Modify: existing readiness/status surface if appropriate.

**Tasks:**

1. Add status report: last runs, current policy refs, kill-switch state, budget use refs, failed-run counts, latest boundary refs, release/version refs.
2. Add local-only rollback/run-disable procedure: revoke standing approval, disable provider policy, rotate credential outside Hisys, stop scheduler outside Hisys, verify no further runs.
3. Add evidence-retention and privacy notes.
4. Add operator troubleshooting table.

**Validation:**

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_live_status.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit:** `feat: add dars live operations status surface`

### Milestone R7 — Release candidate gate

**Objective:** Produce a release candidate package and decision packet without publishing.

**Files:**

- Create: `docs/release/dars-panel-release-candidate-checklist.md`
- Create: `docs/release/dars-panel-release-notes-<version>.md`
- Create: `docs/release/dars-panel-release-decision-packet-<version>.md`
- Modify: `README.md` or relevant docs index if release docs need discoverability.

**Gate commands:**

```bash
PYTHONPATH=src:. pytest tests/unit -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

Add any existing package/build checks if the repo defines them. Do not invent a release build command until the repo confirms it.

**Release candidate checklist must confirm:**

- all target claims and non-goals are listed;
- fixture/local/live/unattended evidence refs are present;
- live provider smoke evidence has human review;
- unattended canary evidence has human review;
- kill switch and rollback runbooks are present;
- no raw secrets are persisted;
- all tests pass;
- release risk assessment is recorded;
- unresolved blockers are either closed or explicitly accepted by human approval.

**Commit:** `docs: prepare dars panel release candidate packet`

### Milestone R8 — Controlled release execution

**Objective:** Publish or deploy only after explicit human approval of the release decision packet.

**Preconditions:**

- Release candidate gate passed.
- Human release approval is recorded.
- Remote/tag/package/deployment target is explicit.
- Rollback procedure is verified.
- Credentials for publishing/deployment are user-managed and not read into repo artifacts.

**Actions:**

1. Create final release tag or package only if user approves exact command.
2. Publish/deploy only through the approved channel.
3. Run post-release smoke with no mutation/publication beyond the release itself.
4. Record release artifact refs, tag/version, post-release smoke results, and rollback pointer.
5. Commit or tag release docs as required by repo policy.

**Claim after successful gate:** `released_for_controlled_advisory_use`.

## 4. Required Decision Packets

Create or update a decision packet before these gates:

| Gate | Decision packet required | Minimum human decision |
|---|---|---|
| R3 single live provider smoke | Yes | approve one provider/model call, provider policy, credential-ref, budget, prompt class |
| R4 multi-critic live provider smoke | Yes | approve multi-call envelope and failure/cost boundary |
| R5 unattended live canary | Yes | approve standing approval policy, scheduler/runner envelope, kill switch, post-run review |
| R7 release candidate acceptance | Yes | accept residual risks and release candidate scope |
| R8 release execution | Yes | approve exact release/publish/deploy command and target |

Decision packets should state request context, evidence scope, validation status, claim boundary, blockers, next actions, and approval state.

## 5. Final Claim Ladder and Stop Rules

Do not skip claim levels. Each claim requires the previous level to be accepted and linked in traceability.

```text
local_fixture_localhost_controlled_advisory_complete
  -> live_provider_advisory_smoked
  -> multi_critic_live_provider_advisory_complete
  -> bounded_unattended_advisory_operation_ready
  -> release_candidate_ready
  -> released_for_controlled_advisory_use
```

Stop and report if any of these occur:

- live provider policy or activation packet contains raw secrets;
- credential reference cannot be validated without reading a secret;
- provider output includes raw secret-looking values or unauthorized authority claims;
- cost/rate/budget/circuit breaker cannot be enforced;
- kill switch is missing or cannot be checked;
- tests, traceability, or secret scan fail;
- user asks to remove human review for substantive outcomes without a new controlled requirement and risk decision;
- release target, remote, tag, package destination, or approval state is unclear.

## 6. Ralph Queue Seed

After this plan is accepted, replace the current short live-LSP-focused `ralph.md` with a DARS release-focused controller or append a new active queue if preserving the current file. Seed queue:

1. `DARS-LIVE-RELEASE-R0-PREP` — requirements/design/test/traceability update.
2. `DARS-LIVE-RELEASE-R1-POLICY` — policy/credential-ref/transport contract.
3. `DARS-LIVE-RELEASE-R2-ADAPTER` — fail-closed live-provider adapter.
4. `DARS-LIVE-RELEASE-R3-SINGLE-SMOKE-PREP` — single live smoke runbook and decision packet template.
5. **Human gate:** approve one live provider smoke.
6. `DARS-LIVE-RELEASE-R3-SINGLE-SMOKE-ACTION` — run and review one live call.
7. `DARS-LIVE-RELEASE-R4-PANEL-SMOKE-PREP` — multi-critic panel smoke prep.
8. **Human gate:** approve multi-critic live smoke.
9. `DARS-LIVE-RELEASE-R4-PANEL-SMOKE-ACTION` — run and review multi-critic live panel.
10. `DARS-LIVE-RELEASE-R5-UNATTENDED-PREP` — standing approval policy and fake/dry-run unattended runner.
11. **Human gate:** approve bounded unattended canary.
12. `DARS-LIVE-RELEASE-R5-UNATTENDED-CANARY` — limited live unattended canary and review.
13. `DARS-LIVE-RELEASE-R6-OPS` — status/monitor/rollback/runbook surfaces.
14. `DARS-LIVE-RELEASE-R7-RC` — release candidate decision packet.
15. **Human gate:** accept release candidate and approve exact release action.
16. `DARS-LIVE-RELEASE-R8-RELEASE` — controlled release execution and post-release evidence.

Each queue item must end with validation, local commit, and normal `git push origin dars` when the branch is clean and synchronized.

## 7. Minimum Final Validation Set

Before declaring final release completion:

```bash
PYTHONPATH=src:. pytest tests/unit -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
git status --short --branch
```

Plus live/release-specific evidence checks:

- runtime-boundary records exist for single and multi-critic live provider runs;
- unattended canary ledger exists and is reviewed;
- release candidate decision packet accepted;
- release artifact/tag/deploy ref recorded;
- post-release smoke report exists;
- rollback/kill-switch path verified.

## 8. Reporting Language

Use this wording only after each claim is proven:

- After R3: “DARS panel has a reviewed single live-provider advisory smoke.”
- After R4: “DARS panel has reviewed multi-critic live-provider advisory evidence.”
- After R5: “DARS panel is ready for bounded unattended advisory operation under a finite standing approval policy.”
- After R7: “DARS panel release candidate is ready for human release approval.”
- After R8: “DARS panel is released for controlled advisory use under the approved release scope.”

Do not say “fully autonomous,” “production complete,” “human review removed,” or “unrestricted live provider operation” unless a future controlled requirement and decision packet explicitly authorize those claims.
