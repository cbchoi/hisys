# Hisys DARS Live-Provider Release RLOO Control Plan

> Active control file for `/rloo` in this repository. Historical control logs are preserved in `ralph.history.md`; do not append new active-loop reflections to the historical file. This controller starts after the final roadmap in `docs/plans/dars-panel-live-provider-unattended-release-final-plan.md` and after the R0 controlled-document update requested on 2026-05-23.

## 0. Control Metadata

| Field | Value |
|---|---|
| Plan ID | `RALPH-HISYS-DARS-LIVE-RELEASE-2026-05-23` |
| Repository | `/home/cbchoi/workspaces/develop/repos/hisys` |
| Branch | `dars` |
| Baseline at plan creation | `7b40649` |
| Previous active control file | archived into `ralph.history.md` on 2026-05-23 |
| Runtime | one coherent RED--GREEN--validate--commit unit per run; maximum 5 hours |
| Active task | R3 critic live smoke evidence captured once through the governed Codex CLI subprocess prompt-mode path; next safe task is the R3 smoke review/gate, not R4/R5/R7. |
| User authorization | 최창범 교수 requested R3-R5 live evidence execution on 2026-05-23, then explicitly instructed `go for R3 critic live smoke`; exactly one Codex subprocess model-boundary call was made for R3 advisory evidence. |

## 1. Objective and bounded target outcome

Advance DARS panel from the accepted `local_fixture_localhost_controlled_advisory_complete` state toward controlled live-provider, bounded unattended advisory operation, and release readiness. The active controller follows the claim ladder in `docs/plans/dars-panel-live-provider-unattended-release-final-plan.md`:

```text
local_fixture_localhost_controlled_advisory_complete
  -> live_provider_advisory_smoked
  -> multi_critic_live_provider_advisory_complete
  -> bounded_unattended_advisory_operation_ready
  -> release_candidate_ready
  -> released_for_controlled_advisory_use
```

R1, R2, R3 PREP, R4 PREP, R5 PREP, and R6 are GREEN. R6 implemented the local live/unattended status surface, latest-boundary ref reporting, kill-switch/budget/circuit-breaker status refs, and rollback-readiness runbooks. On 2026-05-23, a R3-R5 live evidence request was first preflighted and stopped before live action because the current R2 adapter has no raw-provider transport, R4 lacked accepted R3 ACTION evidence, and R5 remained PREP-only dry-run. After the later explicit `go for R3 critic live smoke` instruction, one bounded R3 advisory smoke crossed the model boundary through the governed Codex CLI subprocess prompt-mode path and wrote runtime-boundary evidence. The next safe task is a R3 smoke review/gate; R4, R5 ACTION, and R7 must not proceed until this R3 evidence is reviewed and the claim boundary is accepted.

## 2. Continuous local-safe authorization envelope

The current request authorizes local repository edits, docs/control updates, fixture-local tests, fake/injected transport tests, validation, one already-completed R3 Codex subprocess prompt-mode advisory smoke, local commit, and normal `git push origin dars` after validation. It does **not** authorize any further live provider/model calls, credential lookup, standing unattended approval, release artifact publication, deployment, package upload, external notification, mutation outside a controlled Hisys runtime root, or removal of `requires_human_review=true`.

## 3. Stop conditions

Stop before action if the next step would require any of these boundaries:

1. any additional real provider/model call or remote API dispatch beyond the already-completed single R3 Codex subprocess smoke;
2. credential, token, keychain, or secret lookup;
3. activation of a standing unattended approval policy;
4. release tag/package/upload/deploy/publication;
5. browser/search/tool authority for a critic;
6. mutation, approval, external notification, or downstream action authority;
7. destructive Git/history operation, force push, remote reconfiguration, or unclear branch/remote;
8. validation failure that cannot be fixed with local docs/control or fixture-safe code edits.

## 4. Controlled anchors to read first

- `docs/plans/dars-panel-live-provider-unattended-release-final-plan.md`
- `docs/requirements/dars-critic-panel-runtime-requirements.md`
- `docs/design/dars-critic-panel-runtime-sdd.md`
- `docs/test/dars-critic-panel-runtime-std.md`
- `docs/traceability/dars-critic-panel-runtime-traceability.md`
- `docs/reports/dars-panel-local-completion-audit.md`
- `src/hisys/agents/dars_remote_subscription_dispatch.py`
- `src/hisys/agents/dars_remote_subscription_policy.py`
- `src/hisys/agents/dars_backend_activation.py`
- `tests/unit/test_dars_remote_subscription_dispatch.py`
- `tests/unit/test_dars_codex_cli_subprocess.py`

## 5. Task queue

### Completed setup — archive previous active file and update controlled docs

The previous active `ralph.md` was archived into `ralph.history.md`. Requirements, design, test, traceability, and a readiness decision record were updated to define final claims and verification gates for live-provider, unattended advisory operation, release-candidate readiness, and controlled release.

### Completed: `DARS-LIVE-RELEASE-R1-POLICY` (2026-05-23)

Implemented the R1 live-provider policy validator and the fake/injected transport contract:

- `src/hisys/agents/dars_live_provider_policy.py` — credential-reference-only policy validator with deterministic `live_provider_dispatch_not_authorized_by_policy_alone` warning.
- `src/hisys/agents/dars_live_provider_transport.py` — `LiveProviderTransportRequest`/`Result`, `FakeLiveProviderTransport`, `LiveProviderTransportFailure`, `run_live_provider_transport`. Executor payload carries no credential or token; safety envelope locks `advisory_only=true`, `requires_human_review=true`, `mutation_performed=false`, `publication_performed=false`, `external_call_made=false`.
- `tests/unit/test_dars_live_provider_policy.py` (13 tests) and `tests/unit/test_dars_live_provider_transport.py` (16 tests) — 29 focused tests GREEN.
- `docs/traceability/dars-critic-panel-runtime-traceability.md` flips HISYS-FR-DARS-CP-009 to GREEN and HISYS-FR-DARS-CP-010 to PARTIAL-GREEN (transport contract GREEN; fail-closed adapter PLANNED for R2). Version bumped to 0.17.0.
- `docs/runbooks/dars-codex-subscription-executor-runbook.md` controlled anchors now reference the R1 modules.

Validation (all GREEN):

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_live_provider_policy.py tests/unit/test_dars_live_provider_transport.py -q   # 29 passed
PYTHONPATH=src:. pytest tests/unit -q -k dars                                                                            # 304 passed, 836 deselected
python3 scripts/validate_traceability.py                                                                                 # OK
python3 scripts/scan_secrets.py                                                                                          # hit_count=0
git diff --check                                                                                                         # clean
```

### Completed: `DARS-LIVE-RELEASE-R2-ADAPTER` (2026-05-23)

Implemented the fail-closed live-provider adapter:

- `src/hisys/agents/dars_live_provider_adapter.py` — composes the R1 policy validator, the existing backend activation validator, and the R1 fake transport seam. Validates policy + activation + approval/backend/policy-ref coherence; the env gate `HISYS_DARS_LIVE_PROVIDER_LIVE_TRANSPORT_ENABLED=true` is required before the live mode can be reached. Both modes currently route through `FakeLiveProviderTransport`; a real-provider transport requires a separately approved later increment.
- Boundary records persisted under `<instance>/runtime-boundary/dars-live-provider-adapter/<YYYYMMDD>/<request_id>/<backend_id>-<source_execution_id>.{json,md}` carry `external_call_made=false`, `model_boundary_crossed=false`, `mutation_performed=false`, `publication_performed=false`, `advisory_only=true`, `requires_human_review=true`, and never contain `credential_ref` or other secret material. Records are written for completed and failed runs.
- Deterministic failure codes: `live_provider_transport_required`, `live_provider_policy_packet_unreadable`, `live_provider_activation_packet_unreadable`, `live_provider_policy_invalid`, `live_provider_activation_invalid`, `live_provider_approval_ref_mismatch`, `live_provider_backend_id_mismatch`, `live_provider_activation_scope_mismatch`, `live_provider_activation_policy_ref_mismatch`, `live_provider_env_gate_missing`, plus transport-level codes propagated through.
- `tests/unit/test_dars_live_provider_adapter.py` (17 tests) GREEN. Combined R1+R2 focused gate (46 tests) GREEN; full DARS regression (321 tests) GREEN.
- `docs/traceability/dars-critic-panel-runtime-traceability.md` (v0.18.0) records the R2 reflection and flips HISYS-FR-DARS-CP-010 to GREEN for the policy+transport+adapter scope; only the real-provider transport remains PLANNED.

Validation (all GREEN):

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_live_provider_policy.py tests/unit/test_dars_live_provider_transport.py tests/unit/test_dars_live_provider_adapter.py -q   # 46 passed
PYTHONPATH=src:. pytest tests/unit -q -k dars                                                                                                                          # 321 passed
python3 scripts/validate_traceability.py                                                                                                                              # OK
python3 scripts/scan_secrets.py                                                                                                                                       # hit_count=0
git diff --check                                                                                                                                                      # clean
```

### Completed: `DARS-LIVE-RELEASE-R3-SINGLE-SMOKE-PREP` (2026-05-23)

Authored the single-critic live-provider smoke PREP artifacts:

- `docs/runbooks/dars-live-provider-single-smoke.md` — preconditions (decision packet, R1 policy validation, activation packet, approval/backend/policy-ref coherence, credential reference scheme, bounded prompt/output/rate limits, `cost_budget_ref`, redaction policy, R2 env gate, controlled instance root, operator certainty), single-call procedure, boundary-record requirements, post-run human review, exhaustive stop-condition list. The runbook explicitly does not by itself authorize the live call.
- `docs/examples/dars/live-provider-single-smoke.policy.example.json` — credential-reference-only sample policy that passes the R1 validator (with the deterministic dispatch warning).
- `docs/examples/dars/live-provider-single-smoke.activation.example.json` — matching activation packet (`endpoint_scope=external_api`, `human_approved=true`).
- `tests/unit/test_dars_live_provider_single_smoke_runbook.py` (9 tests) — runbook existence + required phrase + stop-condition + R1/R2 anchor + non-authorization + example-packet R1 validator + credential-reference-only + activation validator + activation/policy match coverage. GREEN.
- `docs/traceability/dars-critic-panel-runtime-traceability.md` (v0.19.0) flips HISYS-FR-DARS-CP-011 to PREP-GREEN + HUMAN-GATED ACTION PLANNED and adds the DARS-LIVE-RELEASE-R3-SINGLE-SMOKE-PREP reflection section.

Validation (all GREEN):

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_live_provider_policy.py tests/unit/test_dars_live_provider_transport.py tests/unit/test_dars_live_provider_adapter.py tests/unit/test_dars_live_provider_single_smoke_runbook.py -q   # 55 passed
PYTHONPATH=src:. pytest tests/unit -q -k dars                                                                                                                                                                              # 330 passed
python3 scripts/validate_traceability.py                                                                                                                                                                                  # OK
python3 scripts/scan_secrets.py                                                                                                                                                                                           # hit_count=0
git diff --check                                                                                                                                                                                                          # clean
```

### Completed: `DARS-LIVE-RELEASE-R4-PANEL-SMOKE-PREP` (2026-05-23)

Authored the multi-critic live-provider panel smoke PREP artifacts:

- `docs/runbooks/dars-live-provider-panel-smoke.md` — preconditions (reviewed R3 single smoke as a hard precondition, decision packet, R1 policy validation, activation packet, approval/backend/policy-ref coherence, per-critic redaction, per-critic `max_prompt_bytes`/`max_output_bytes`/`rate_limit_per_minute`, panel-level `cost_budget_ref`, R2 env gate, controlled instance root, operator certainty), multi-critic procedure (two or more critics under one decision packet, unique `source_execution_id` per critic, shared `request_id`/`panel_id`), per-critic + panel-level boundary record requirements with explicit failure-isolation expectations and advisory synthesis (`needs_more_evidence`), post-run human review steps, and exhaustive stop-condition list including duplicate `source_execution_id`, mismatched `request_id`, and cross-critic policy mismatches.
- `docs/examples/dars/live-provider-panel-smoke.policy.example.json` and `live-provider-panel-smoke.activation.example.json` — credential-reference-only sample packets that pass the R1 + activation validators.
- `tests/unit/test_dars_live_provider_panel_smoke_runbook.py` (10 tests) GREEN. Combined R1+R2+R3+R4 PREP focused gate (65 tests) GREEN; full DARS regression (340 tests) GREEN.
- `docs/traceability/dars-critic-panel-runtime-traceability.md` (v0.20.0) flips HISYS-FR-DARS-CP-012 to PREP-GREEN + HUMAN-GATED ACTION PLANNED and adds the DARS-LIVE-RELEASE-R4-PANEL-SMOKE-PREP reflection section.

Validation (all GREEN):

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_live_provider_policy.py tests/unit/test_dars_live_provider_transport.py tests/unit/test_dars_live_provider_adapter.py tests/unit/test_dars_live_provider_single_smoke_runbook.py tests/unit/test_dars_live_provider_panel_smoke_runbook.py -q   # 65 passed
PYTHONPATH=src:. pytest tests/unit -q -k dars                                                                                                                                                                                                                                       # 340 passed
python3 scripts/validate_traceability.py                                                                                                                                                                                                                                          # OK
python3 scripts/scan_secrets.py                                                                                                                                                                                                                                                   # hit_count=0
git diff --check                                                                                                                                                                                                                                                                  # clean
```

### R5 documentation checkpoint: `DARS-LIVE-RELEASE-R5-UNATTENDED-PREP-DOCS` (2026-05-23)

Authored the bounded unattended advisory operation documentation artifacts:

- `docs/runbooks/dars-unattended-advisory-operation.md` — standing approval policy contract, unattended runner contract, dry-run/fake-transport rehearsal procedure, audit ledger requirements, circuit breaker matrix, post-run human review, validation commands, and stop conditions.
- `docs/examples/dars/unattended-standing-approval.example.json` — reference-only standing approval example with finite validity, request-class allowlist, budget/rate caps, kill-switch ref, audit retention ref, post-run human review, and no mutation/publication/external-action authority.
- `tests/unit/test_dars_unattended_docs.py` — documentation and example-packet content checks for R5 docs PREP.
- `docs/traceability/dars-critic-panel-runtime-traceability.md` (v0.21.0) records HISYS-FR-DARS-CP-013 as DOCS-PREP + IMPLEMENTATION PLANNED + HUMAN-GATED ACTION PLANNED.

Boundary preserved: no live provider/model call, no credential lookup, no standing unattended approval activation, no mutation, no publication, no deployment, no release, no external notification, and no human-review removal.

### Completed: `DARS-LIVE-RELEASE-R5-UNATTENDED-PREP` (2026-05-23)

Implemented the bounded unattended advisory PREP runtime:

- `src/hisys/agents/dars_unattended_policy.py` — `validate_standing_approval_policy` enforces finite validity, request-class allowlists, budget/rate/prompt/output caps, kill-switch and audit-retention refs, `requires_post_run_human_review=true`, advisory-only authority, and raw-secret rejection. Valid policies emit a deterministic warning that schema validity does not authorize live action by itself.
- `src/hisys/operations/dars_unattended_runner.py` — `DarsUnattendedAdvisoryRunner` validates the standing approval policy, checks dry-run request class, kill-switch state, policy/activation refs, authority flags, and circuit breakers, routes only through the R2 fail-closed adapter with `FakeLiveProviderTransport`, and writes one audit ledger entry per completed, blocked, failed, or circuit-broken run.
- `tests/unit/test_dars_unattended_policy.py` (10 tests) and `tests/unit/test_dars_unattended_runner.py` (9 tests) — RED-first coverage for validity windows, missing request classes, R5 PREP live-canary rejection, budget/rate/kill-switch/audit requirements, authority rejection, raw-secret rejection, dry-run fake-transport execution, audit ledger writing, and circuit breakers.
- `src/hisys/agents/dars_live_provider_adapter.py` — R2 adapter policy-ref coherence accepts equivalent filesystem refs while preserving URI mismatch and distinct-path fail-closed behavior.
- `docs/runbooks/dars-unattended-advisory-operation.md` and `docs/traceability/dars-critic-panel-runtime-traceability.md` (v0.22.0) reflect R5 PREP GREEN and leave R5 ACTION as HUMAN-GATED.

Validation (all GREEN):

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_unattended_policy.py tests/unit/test_dars_unattended_runner.py tests/unit/test_dars_unattended_docs.py tests/unit/test_dars_live_provider_adapter.py -q   # 43 passed
PYTHONPATH=src:. pytest tests/unit -q -k dars                                                                                                                                  # 366 passed, 836 deselected
python3 scripts/validate_traceability.py                                                                                                                                      # OK
python3 scripts/scan_secrets.py                                                                                                                                               # hit_count=0
git diff --check                                                                                                                                                              # clean
```

Boundary preserved: no live provider/model call, credential lookup, standing unattended approval activation, mutation, publication, deployment, release, external notification, or human-review removal. R5 ACTION remains separately HUMAN-GATED.

### Completed: `DARS-LIVE-RELEASE-R6-STATUS-ROLLBACK` (2026-05-23)

Implemented local live/unattended operations status and rollback readiness:

- `src/hisys/operations/dars_live_status.py` — builds a refs-only status packet with policy refs, standing approval ref, kill-switch state, budget/circuit-breaker state, failed-run count, latest boundary refs, rollback runbook ref, release/version ref, and explicit no-live-action boundary flags.
- `hisys dars-live-status` — writes JSON/Markdown reports under `reports/run-summaries/<YYYYMMDD>/` and prints text/JSON/Markdown without external calls.
- `docs/runbooks/dars-live-operations.md` and `docs/runbooks/dars-live-rollback.md` — document status operation, evidence retention/privacy, troubleshooting, and rollback readiness steps: revoke standing approval, disable provider policy, rotate credential outside Hisys, stop scheduler outside Hisys, and verify no further runs.
- `tests/unit/test_dars_live_status.py` — RED-first coverage for kill-switch/latest-boundary refs without secrets, report writing, CLI output/artifacts, and operations/rollback runbook content.
- `docs/traceability/dars-critic-panel-runtime-traceability.md` (v0.23.0) records HISYS-FR-DARS-CP-014 / HISYS-T-DARS-CP-016 as GREEN for local status/rollback readiness.

Validation (all GREEN):

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_live_status.py tests/unit/test_governance_docs_current_state.py -q   # 5 passed
PYTHONPATH=src:. pytest tests/unit -q -k dars                                                          # 370 passed, 836 deselected
PYTHONPATH=src:. pytest tests/unit -q                                                                  # 1206 passed
python3 scripts/validate_traceability.py                                                              # OK
python3 scripts/scan_secrets.py                                                                       # hit_count=0
git diff --check                                                                                      # clean
```

Boundary preserved: no live provider/model call, credential lookup, standing unattended approval activation, rollback execution, mutation, publication, deployment, release, external notification, or human-review removal.

Next safe task: `DARS-LIVE-RELEASE-R3-SMOKE-REVIEW-GATE` — inspect `docs/reports/dars-r3-critic-live-smoke-2026-05-23.md` and the runtime-boundary evidence under `/tmp/hisys-r3-critic-live-smoke-20260523`, then decide whether the claim can advance to `live_provider_advisory_smoked` or must remain the narrower Codex-subprocess smoke claim. Do not start R4, R5 ACTION, or R7 release-candidate readiness until accepted R3 ACTION evidence exists.

## 6. Quality gates

Run after each coherent task:

```bash
PYTHONPATH=src:. pytest <focused tests> -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
git status --short --branch
```

Before release-candidate or live-gated work, also run the full local unit gate:

```bash
PYTHONPATH=src:. pytest tests/unit -q
```

## 7. Commit and push rule

Commit each coherent increment after gates pass. Normal `git push origin dars` is allowed when the repository is on branch `dars`, upstream is `origin/dars`, validation passes, and no force/credential/security/release action is required.

## 8. Human reporting format

Report:

- completed task ID and claim boundary;
- files changed;
- validation commands and results;
- commit hash and push result if pushed;
- next safe task or exact stop condition.

## 9. Reflection Log

- 2026-05-23 — `DARS-LIVE-RELEASE-R0-PREP`: active `ralph.md` archived into `ralph.history.md`; new DARS live-provider release controller prepared; R0 controlled-document update in progress. Success likelihood: 85% because all current work is docs/control-local and no live provider or credential boundary is crossed.
- 2026-05-23 — `DARS-LIVE-RELEASE-R1-POLICY`: GREEN. RED-first added `tests/unit/test_dars_live_provider_policy.py` (13 tests) and `tests/unit/test_dars_live_provider_transport.py` (16 tests); both failed at import with `ModuleNotFoundError` before implementation. GREEN added `src/hisys/agents/dars_live_provider_policy.py` and `src/hisys/agents/dars_live_provider_transport.py`. Focused gate `pytest test_dars_live_provider_policy.py test_dars_live_provider_transport.py -q` → 29 passed. Regression gate `pytest tests/unit -q -k dars` → 304 passed, 836 deselected. Traceability validator → OK. Secret scan over full repository → `hit_count=0` (fake secret-rejection inputs use the `FAKE_`/`sk-fake_*`/`hf_fake_*` prefixes recognised by `hisys.security.secret_scan.SAFE_VALUE_PREFIXES`). `git diff --check` clean. RTM HISYS-FR-DARS-CP-009 → GREEN; HISYS-FR-DARS-CP-010 → PARTIAL-GREEN (transport contract GREEN; R2 fail-closed adapter PLANNED). Boundary preserved: no live provider/model call, credential lookup, standing unattended approval, release artifact publication, deployment, package upload, external notification, mutation outside the repository, destructive Git operation, or human-review removal. Success likelihood: 95% because all changes are local Python contract + tests + docs and every R1 RED command in the plan is now GREEN. Committed as `5e25844`. Pushed to `origin/dars`. Next safe task: `DARS-LIVE-RELEASE-R2-ADAPTER`.
- 2026-05-23 — `DARS-LIVE-RELEASE-R2-ADAPTER`: GREEN. RED-first added `tests/unit/test_dars_live_provider_adapter.py` (17 tests); failed at import with `ModuleNotFoundError` before implementation. GREEN added `src/hisys/agents/dars_live_provider_adapter.py` exposing `DarsLiveProviderAdapterRequest`/`Result`, `run_dars_live_provider_adapter`, and the `DARS_LIVE_PROVIDER_LIVE_TRANSPORT_ENV_VAR` env-gate constant. Adapter composes the R1 policy validator, the existing backend activation validator, and the R1 fake transport seam into a single fail-closed entry point. Cross-checks: approval_ref (request vs policy vs activation), backend_id (request vs activation), activation `endpoint_scope=external_api`, activation `remote_policy_packet_ref` equals request `policy_packet_ref`. Env gate `HISYS_DARS_LIVE_PROVIDER_LIVE_TRANSPORT_ENABLED=true` required in live mode. Boundary records persisted under `<instance>/runtime-boundary/dars-live-provider-adapter/<YYYYMMDD>/<request_id>/<backend_id>-<source_execution_id>.{json,md}` for both completed and failed runs, always with `external_call_made=false`, `model_boundary_crossed=false`, `mutation_performed=false`, `publication_performed=false`, `advisory_only=true`, `requires_human_review=true`, and no credential/token material. Focused R1+R2 gate `pytest test_dars_live_provider_policy.py test_dars_live_provider_transport.py test_dars_live_provider_adapter.py -q` → 46 passed. Regression gate `pytest tests/unit -q -k dars` → 321 passed, 836 deselected. Traceability validator → OK. Secret scan → `hit_count=0` (794 scanned files). `git diff --check` clean. RTM HISYS-FR-DARS-CP-010 → GREEN for the policy+transport+adapter scope; only the real-provider transport remains PLANNED. Boundary preserved: identical to R1. Success likelihood: 95% because all changes remain local Python + tests + docs and every R2 plan requirement is satisfied. Committed as `278ae23`. Pushed to `origin/dars`. Next safe task: `DARS-LIVE-RELEASE-R3-SINGLE-SMOKE-PREP` (documentation/control only; the actual single live call is a separately approved HUMAN-GATED action).
- 2026-05-23 — `DARS-LIVE-RELEASE-R3-SINGLE-SMOKE-PREP`: GREEN. RED-first added `tests/unit/test_dars_live_provider_single_smoke_runbook.py` (9 tests) covering runbook existence, required-phrase coverage (decision packet, approval/credential refs, redaction policy, bounded prompt/output/rate-limit fields, `cost_budget_ref`, env gate, boundary record flags, post-run human review), stop-condition coverage (missing decision packet, raw secret, credential lookup, mutation/publication/tool/browser/search authority, budget/rate violation, secret-scan hit, output redaction failure, operator uncertainty), R1+R2 module/anchor anchoring, the explicit "does not by itself authorize" assertion, R1 policy validator acceptance of the example policy (with the deterministic warning), the credential-reference-only invariant in the example policy, the activation validator acceptance of the example activation, and the cross-packet matching between the example policy and activation. Tests initially failed at runbook/file existence and content-anchor mismatches. GREEN added `docs/runbooks/dars-live-provider-single-smoke.md`, `docs/examples/dars/live-provider-single-smoke.policy.example.json`, and `docs/examples/dars/live-provider-single-smoke.activation.example.json`. Two minor adjustments unstuck content-anchor mismatches: removed a line-wrap inside the "does not by itself authorize" phrase and added an explicit "Prior controlled increments" section listing `DARS-LIVE-RELEASE-R1-POLICY` and `DARS-LIVE-RELEASE-R2-ADAPTER`. Focused R1+R2+R3 gate `pytest test_dars_live_provider_policy.py test_dars_live_provider_transport.py test_dars_live_provider_adapter.py test_dars_live_provider_single_smoke_runbook.py -q` → 55 passed. Regression gate `pytest tests/unit -q -k dars` → 330 passed, 836 deselected. Traceability validator → OK. Secret scan → `hit_count=0` (798 scanned files). `git diff --check` clean. RTM HISYS-FR-DARS-CP-011 → PREP-GREEN + HUMAN-GATED ACTION PLANNED. Boundary preserved: no live provider/model call, credential lookup, network request, mutation, publication, deployment, package upload, external notification, or human-review removal; only docs/control files added; R3 ACTION explicitly remains separately approved HUMAN-GATED action. Success likelihood: 95% because PREP work is local docs/tests only and the runbook is paired with passing validator coverage. Committed as `88036cd`. Pushed to `origin/dars`. Next safe task: `DARS-LIVE-RELEASE-R4-PANEL-SMOKE-PREP`.
- 2026-05-23 — `DARS-LIVE-RELEASE-R4-PANEL-SMOKE-PREP`: GREEN. RED-first added `tests/unit/test_dars_live_provider_panel_smoke_runbook.py` (10 tests) covering runbook existence, required-phrase coverage for the multi-critic governance contract (multi-critic, two or more critics, panel_id, per-critic + panel-level boundary record, failure isolation, advisory synthesis, decision packet, approval/credential refs, redaction policy, `max_prompt_bytes`/`max_output_bytes`/`rate_limit_per_minute`, `cost_budget_ref`, env gate, boundary record flags, post-run human review), stop-condition coverage including duplicate `source_execution_id` and cross-critic policy mismatch, R1+R2+R3 module/anchor anchoring, the explicit "does not by itself authorize" assertion, the R3 reviewed single-smoke + `live_provider_advisory_smoked` precondition assertion, R1 policy validator acceptance of the example policy (with the deterministic warning), the credential-reference-only invariant in the example policy, the activation validator acceptance of the example activation, and the cross-packet matching between the example policy and activation. Tests initially failed at runbook/file existence and three content-anchor mismatches. GREEN added `docs/runbooks/dars-live-provider-panel-smoke.md`, `docs/examples/dars/live-provider-panel-smoke.policy.example.json`, and `docs/examples/dars/live-provider-panel-smoke.activation.example.json`. Three minor content-anchor adjustments unstuck content-anchor mismatches: (a) recast "exactly two or more advisory critic calls" to a wording that contains the literal "two or more critics" substring, (b) collapsed a line-wrap inside "rate-limit violation", (c) lowercased the leading "Synthesis" so the test substring "synthesis remains advisory" matches, and (d) added an explicit per-critic bounded-prompt/output/rate-limit field list in the preconditions section. Focused R1+R2+R3+R4 gate `pytest test_dars_live_provider_policy.py test_dars_live_provider_transport.py test_dars_live_provider_adapter.py test_dars_live_provider_single_smoke_runbook.py test_dars_live_provider_panel_smoke_runbook.py -q` → 65 passed. Regression gate `pytest tests/unit -q -k dars` → 340 passed, 836 deselected. Traceability validator → OK. Secret scan → `hit_count=0` (802 scanned files). `git diff --check` clean. RTM HISYS-FR-DARS-CP-012 → PREP-GREEN + HUMAN-GATED ACTION PLANNED. Boundary preserved: identical to R3 PREP; only docs/control files added; R4 ACTION explicitly remains separately approved HUMAN-GATED action and additionally requires a reviewed R3 ACTION smoke as a precondition. Success likelihood: 95% because PREP work is local docs/tests only and the runbook is paired with passing validator coverage. Next safe task: `DARS-LIVE-RELEASE-R5-UNATTENDED-PREP` (local Python + tests + docs; the bounded unattended live canary R5 ACTION is HUMAN-GATED).
- 2026-05-23 — `DARS-LIVE-RELEASE-R5-UNATTENDED-PREP-DOCS`: DOCS-PREP. Authored `docs/runbooks/dars-unattended-advisory-operation.md`, `docs/examples/dars/unattended-standing-approval.example.json`, and `tests/unit/test_dars_unattended_docs.py`. Updated RTM to v0.21.0 and recorded HISYS-FR-DARS-CP-013 as DOCS-PREP + IMPLEMENTATION PLANNED + HUMAN-GATED ACTION PLANNED. Boundary preserved: no live provider/model call, credential lookup, standing unattended approval activation, mutation, publication, deployment, release, external notification, or human-review removal. Next safe implementation task remains R5 standing approval policy + unattended runner RED→GREEN.
- 2026-05-23 — `DARS-LIVE-RELEASE-R5-UNATTENDED-PREP`: GREEN. RED-first added `tests/unit/test_dars_unattended_policy.py` (10 tests) and `tests/unit/test_dars_unattended_runner.py` (9 tests); both failed at import with `ModuleNotFoundError` before implementation. GREEN added `src/hisys/agents/dars_unattended_policy.py` and `src/hisys/operations/dars_unattended_runner.py`, with a small R2 adapter path-equivalence fix for activation policy refs. Focused R5+adapter gate `pytest test_dars_unattended_policy.py test_dars_unattended_runner.py test_dars_unattended_docs.py test_dars_live_provider_adapter.py -q` → 43 passed. Regression gate `pytest tests/unit -q -k dars` → 366 passed, 836 deselected. Traceability validator → OK. Secret scan → `hit_count=0` (809 scanned files). `git diff --check` clean. RTM HISYS-FR-DARS-CP-013 → PREP-GREEN + HUMAN-GATED ACTION PLANNED. Boundary preserved: no live provider/model call, credential lookup, standing unattended approval activation, mutation, publication, deployment, release, external notification, or human-review removal. Next safe task: `DARS-LIVE-RELEASE-R6-STATUS-ROLLBACK`.
- 2026-05-23 — `DARS-LIVE-RELEASE-R6-STATUS-ROLLBACK`: GREEN. RED-first added `tests/unit/test_dars_live_status.py` (4 tests); initial focused run failed with missing `hisys.operations.dars_live_status`, missing `hisys dars-live-status`, and missing operations/rollback runbooks. GREEN added the local refs-only status module, CLI surface, operations runbook, rollback runbook, and RTM v0.23.0 update. Focused R6+governance gate `pytest tests/unit/test_dars_live_status.py tests/unit/test_governance_docs_current_state.py -q` → 5 passed. DARS regression `pytest tests/unit -q -k dars` → 370 passed, 836 deselected. Full unit gate `pytest tests/unit -q` → 1206 passed. Traceability validator → OK. Secret scan → `hit_count=0` (813 scanned files). `git diff --check` clean. Boundary preserved: no live provider/model call, credential lookup, standing unattended approval activation, rollback execution, mutation, publication, deployment, release, external notification, or human-review removal. Next safe task: `DARS-LIVE-RELEASE-R7-RC`.
- 2026-05-23 — `DARS-LIVE-RELEASE-R3-R5-LIVE-EVIDENCE-PREFLIGHT`: STOPPED before live action. User requested R3-R5 live evidence. Inspected R3/R4/R5 runbooks, `dars_live_provider_adapter`, and `dars_unattended_runner`; current R2 adapter still has no approved real-provider transport and always records `external_call_made=false`/`model_boundary_crossed=false`, R4 requires accepted R3 ACTION evidence, and R5 remains PREP-only dry-run. Packet validators accepted the example templates with only the expected non-authorization warnings. Focused gate `pytest tests/unit/test_dars_live_provider_policy.py tests/unit/test_dars_live_provider_transport.py tests/unit/test_dars_live_provider_adapter.py tests/unit/test_dars_live_provider_single_smoke_runbook.py tests/unit/test_dars_live_provider_panel_smoke_runbook.py tests/unit/test_dars_unattended_policy.py tests/unit/test_dars_unattended_runner.py tests/unit/test_dars_unattended_docs.py tests/unit/test_dars_live_status.py -q` → 95 passed. Generated local stop record `docs/reports/dars-r3-r5-live-evidence-preflight-2026-05-23.md`, a temporary fail-closed R3 boundary under `/tmp/hisys-r3-r5-live-evidence-20260523`, and a temporary R5 PREP dry-run ledger under the same instance. Boundary preserved: no live provider/model call, no Codex subprocess invocation, no credential lookup, no standing unattended approval activation, no mutation/publication/deployment/release/external notification. Next safe task: `DARS-LIVE-RELEASE-R3-ACTION-TRANSPORT-PREP`.
- 2026-05-23 — `DARS-LIVE-RELEASE-R3-CRITIC-LIVE-SMOKE`: EVIDENCE CAPTURED. After explicit operator instruction `go for R3 critic live smoke`, ran one governed Codex CLI subprocess prompt-mode advisory critic through `run_dars_remote_subscription_dispatch` and `build_codex_cli_prompt_mode_executor`. Preflight gate `pytest tests/unit/test_dars_codex_cli_subprocess.py tests/unit/test_dars_remote_subscription_dispatch.py tests/unit/test_dars_remote_subscription_policy.py tests/unit/test_dars_backend_activation.py -q` → 88 passed; traceability validator → OK; secret scan → `hit_count=0`; `git diff --check` clean; `/usr/bin/codex` → `codex-cli 0.128.0`. Two initial attempts stopped before subprocess spawn with `codex_cli_prompt_not_redacted`; the final narrowed prompt produced runtime-boundary evidence at `/tmp/hisys-r3-critic-live-smoke-20260523/runtime-boundary/dars-remote-subscriptions/20260523/REQ-DARS-R3-CRITIC-LIVE-SMOKE-20260523-001/codex_subscription_dars_critic-EXEC-DARS-R3-CRITIC-LIVE-SMOKE-20260523-001.json` with `external_call_made=true`, `model_boundary_crossed=true`, `mutation_performed=false`, `publication_performed=false`, `requires_human_review=true`, and `transport_kind=codex_cli_subprocess_prompt_mode`. Report written at `docs/reports/dars-r3-critic-live-smoke-2026-05-23.md`. Boundary preserved: exactly one Codex subprocess model-boundary call; no raw provider API call from Hisys, no credential lookup by Hisys, no standing unattended approval activation, no mutation/publication/deployment/release/external notification, and no human-review removal. Next safe task: `DARS-LIVE-RELEASE-R3-SMOKE-REVIEW-GATE`.
- Current HEAD: 47bb94f
