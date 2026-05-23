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
| Active task | `DARS-LIVE-RELEASE-R2-ADAPTER` (R1 GREEN; R2 prepares the fail-closed live provider adapter) |
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

R1 is GREEN. The next executable task is R2: implement the fail-closed live provider adapter that requires a valid R1 policy packet, an activation packet, a credential reference, and an explicit approval/env gate before any transport entry point is reachable. R2 unit tests still use fake/injected transports only.

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

### Next: `DARS-LIVE-RELEASE-R2-ADAPTER`

Objective: add the fail-closed real-provider adapter seam. Live execution stays disabled unless an activation packet, R1 provider policy, env gate, and explicit approval are all present. Unit tests still use monkeypatched fake HTTP/CLI runners, never a real provider.

Expected files:

- `src/hisys/agents/dars_live_provider_adapter.py`
- `tests/unit/test_dars_live_provider_adapter.py`
- updates to `src/hisys/agents/dars_remote_subscription_dispatch.py` if needed to consume the adapter
- updates to `docs/traceability/dars-critic-panel-runtime-traceability.md` and the runbook

RED commands (planned):

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_live_provider_adapter.py::test_live_provider_adapter_requires_policy_approval_and_credential_ref -q
```

Expected RED: missing module/test surface before implementation.

GREEN requirements:

- adapter refuses missing executor / credential reference / approval / env gate;
- adapter refuses any mutation / publication / tool / browser / search authority;
- dry-run/fake transport path writes boundary records with `external_call_made=false`;
- live transport entry point remains behind all gates and uses monkeypatched fake runner in unit tests;
- output redaction, max-output enforcement, and deterministic failure codes preserved.

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
- 2026-05-23 — `DARS-LIVE-RELEASE-R1-POLICY`: GREEN. RED-first added `tests/unit/test_dars_live_provider_policy.py` (13 tests) and `tests/unit/test_dars_live_provider_transport.py` (16 tests); both failed at import with `ModuleNotFoundError` before implementation. GREEN added `src/hisys/agents/dars_live_provider_policy.py` and `src/hisys/agents/dars_live_provider_transport.py`. Focused gate `pytest test_dars_live_provider_policy.py test_dars_live_provider_transport.py -q` → 29 passed. Regression gate `pytest tests/unit -q -k dars` → 304 passed, 836 deselected. Traceability validator → OK. Secret scan over full repository → `hit_count=0` (fake secret-rejection inputs use the `FAKE_`/`sk-fake_*`/`hf_fake_*` prefixes recognised by `hisys.security.secret_scan.SAFE_VALUE_PREFIXES`). `git diff --check` clean. RTM HISYS-FR-DARS-CP-009 → GREEN; HISYS-FR-DARS-CP-010 → PARTIAL-GREEN (transport contract GREEN; R2 fail-closed adapter PLANNED). Boundary preserved: no live provider/model call, credential lookup, standing unattended approval, release artifact publication, deployment, package upload, external notification, mutation outside the repository, destructive Git operation, or human-review removal. Success likelihood: 95% because all changes are local Python contract + tests + docs and every R1 RED command in the plan is now GREEN. Next safe task: `DARS-LIVE-RELEASE-R2-ADAPTER`.
- Current HEAD: e9c16b0 (pre-commit)
