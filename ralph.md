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
| Active task | `DARS-LIVE-RELEASE-R3-SINGLE-SMOKE-PREP` (R1+R2 GREEN; R3 prepares the single-critic live smoke runbook and decision packet template before any human-gated live call) |
| User authorization | 최창범 교수 requested: `ralph.md를 ralph.history.md로 이동하고 요구사항/설계/시험/추적성 문서를 업데이트` |

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

R1 and R2 are GREEN. The next executable task is R3 PREP: author the single-critic live-provider smoke runbook and decision packet template that documents the human conditions required before any single live-provider call. R3 PREP is documentation/control only and remains within the local-safe authorization envelope; the actual single live call is a separately approved HUMAN-GATED action.

## 2. Continuous local-safe authorization envelope

The current request authorizes local repository edits, docs/control updates, fixture-local tests, fake/injected transport tests, validation, local commit, and normal `git push origin dars` after validation. It does **not** authorize live provider/model calls, credential lookup, standing unattended approval, release artifact publication, deployment, package upload, external notification, mutation outside a controlled Hisys runtime root, or removal of `requires_human_review=true`.

## 3. Stop conditions

Stop before action if the next step would require any of these boundaries:

1. real provider/model call or remote API dispatch;
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

### Next: `DARS-LIVE-RELEASE-R3-SINGLE-SMOKE-PREP`

Objective: author the single-critic live-provider smoke runbook and decision packet template so a human can later approve exactly one real provider call under R3 ACTION. This row is documentation/control only; no live call is performed, no credential is read, and no boundary record beyond template/example files is produced by this row.

Expected files (PREP scope):

- `docs/runbooks/dars-live-provider-single-smoke.md` (new) — preflight, single-call procedure, evidence requirements, stop conditions.
- `docs/examples/dars/live-provider-single-smoke.policy.example.json` (new) — sample policy packet that passes the R1 validator (credential reference only, no raw secrets).
- `docs/examples/dars/live-provider-single-smoke.activation.example.json` (new) — sample activation packet that matches the example policy and a sample approval_ref.
- `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.69.md` (new) — readiness decision recording the R3 PREP scope and the boundary that no live call is authorized by this row.
- updates to `docs/traceability/dars-critic-panel-runtime-traceability.md` and the runbook anchor table.

RED commands (planned for R3 ACTION, not PREP):

```bash
# Human-gated. PREP row does not run this.
PYTHONPATH=src:. pytest tests/unit/test_dars_live_provider_single_smoke_runbook.py -q
```

GREEN requirements for R3 PREP:

- runbook explicitly lists the human decision-packet, allowlist, redaction, budget/rate, and post-run review preconditions;
- example policy/activation packets pass `validate_live_provider_policy_packet` and `validate_dars_backend_activation_packet` with `live_provider_dispatch_not_authorized_by_policy_alone` warning and zero errors;
- secret scan over the new examples returns zero hits;
- traceability validator continues to pass;
- ralph.md and RTM reflect R3 PREP GREEN and explicitly leave R3 ACTION as a separate HUMAN-GATED row.

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
- 2026-05-23 — `DARS-LIVE-RELEASE-R2-ADAPTER`: GREEN. RED-first added `tests/unit/test_dars_live_provider_adapter.py` (17 tests); failed at import with `ModuleNotFoundError` before implementation. GREEN added `src/hisys/agents/dars_live_provider_adapter.py` exposing `DarsLiveProviderAdapterRequest`/`Result`, `run_dars_live_provider_adapter`, and the `DARS_LIVE_PROVIDER_LIVE_TRANSPORT_ENV_VAR` env-gate constant. Adapter composes the R1 policy validator, the existing backend activation validator, and the R1 fake transport seam into a single fail-closed entry point. Cross-checks: approval_ref (request vs policy vs activation), backend_id (request vs activation), activation `endpoint_scope=external_api`, activation `remote_policy_packet_ref` equals request `policy_packet_ref`. Env gate `HISYS_DARS_LIVE_PROVIDER_LIVE_TRANSPORT_ENABLED=true` required in live mode. Boundary records persisted under `<instance>/runtime-boundary/dars-live-provider-adapter/<YYYYMMDD>/<request_id>/<backend_id>-<source_execution_id>.{json,md}` for both completed and failed runs, always with `external_call_made=false`, `model_boundary_crossed=false`, `mutation_performed=false`, `publication_performed=false`, `advisory_only=true`, `requires_human_review=true`, and no credential/token material. Focused R1+R2 gate `pytest test_dars_live_provider_policy.py test_dars_live_provider_transport.py test_dars_live_provider_adapter.py -q` → 46 passed. Regression gate `pytest tests/unit -q -k dars` → 321 passed, 836 deselected. Traceability validator → OK. Secret scan → `hit_count=0` (794 scanned files). `git diff --check` clean. RTM HISYS-FR-DARS-CP-010 → GREEN for the policy+transport+adapter scope; only the real-provider transport remains PLANNED. Boundary preserved: identical to R1. Success likelihood: 95% because all changes remain local Python + tests + docs and every R2 plan requirement is satisfied. Next safe task: `DARS-LIVE-RELEASE-R3-SINGLE-SMOKE-PREP` (documentation/control only; the actual single live call is a separately approved HUMAN-GATED action).
- Current HEAD: 5e25844 (pre-R2-commit)
