# DARS R4 Codex subprocess panel smoke attempt — token refresh-state stop — 2026-05-24

## Result

The approved R4 Codex subprocess panel smoke was attempted using the existing Codex subscription-auth path and stopped before any completed critic boundary record was written.

```text
r4_codex_subscription_multi_critic_panel_smoke_blocked_by_codex_refresh_token_reuse
```

## Request context

- Operator challenged the previous conservative stop: `codex subprocess실행까지 해야하지 않나??`
- Explicit approval selected in the clarification gate: `승인: R4 Codex subprocess panel smoke 실행`
- Attempt time: `2026-05-24T02:14:55Z`
- Repository branch: `dars`
- Baseline before attempt: `2679c60 docs: record dars r4 mapped panel action packet`

## Approved scope

- Transport scope: `codex_subscription_subprocess_transport_only`
- Critics: 2
- Allowed actions: `advisory_only`
- Mutation: false
- Publication: false
- Raw provider API call from Hisys: false
- Credential lookup by Hisys: false
- Human review required: true

## Preflight evidence

```bash
PYTHONPATH=src:. pytest \
  tests/unit/test_dars_codex_cli_subprocess.py \
  tests/unit/test_dars_remote_subscription_dispatch.py::test_remote_subscription_multi_critic_panel_dispatch_writes_aggregate_boundary \
  tests/unit/test_dars_remote_subscription_dispatch.py::test_remote_subscription_multi_critic_panel_rejects_mixed_request_ids_before_executor \
  tests/unit/test_dars_remote_subscription_dispatch.py::test_codex_cli_subprocess_multi_critic_panel_prep_packet_matches_dispatch_contract \
  tests/unit/test_dars_remote_subscription_dispatch.py::test_codex_cli_subprocess_multi_critic_evidence_packet_prep_includes_claim_and_evidence \
  -q
# 49 passed

python3 scripts/validate_traceability.py
# OK
python3 scripts/scan_secrets.py
# hit_count=0
git diff --check
# clean
command -v codex
# /usr/bin/codex
codex --version
# codex-cli 0.128.0
```

## Attempt command

The local runner created a temporary governed instance under:

```text
/tmp/hisys-r4-codex-panel-smoke-20260524
```

It wrote only secret-free control packet refs:

```text
/tmp/hisys-r4-codex-panel-smoke-20260524/control-packets/r4-codex-panel-remote-policy.json
/tmp/hisys-r4-codex-panel-smoke-20260524/control-packets/r4-codex-panel-activation.json
```

It then invoked `run_dars_remote_subscription_panel_dispatch(...)` with `build_codex_cli_prompt_mode_executor(...)`, using `codex exec --sandbox read-only --ask-for-approval never` through the governed executor seam.

## Stop evidence

The first Codex subprocess found/used the existing Codex subscription-auth state, then returned nonzero before a critique was produced because the CLI-side refresh token was rejected as already used:

```text
codex_cli_subprocess_failed: returncode=1
Failed to refresh token: 400 Bad Request
code=refresh_token_reused
message=Your refresh token has already been used to generate a new access token. Please try signing in again.
```

No panel boundary record was produced:

```text
/tmp/hisys-r4-codex-panel-smoke-20260524/runtime-boundary/...
# absent
```

Only the local control packet files exist in the temporary instance.

## Claim boundary

Accepted claim:

```text
r4_codex_subscription_multi_critic_panel_smoke_attempted_auth_blocked
```

Rejected or not accepted:

- `r4_codex_subscription_multi_critic_panel_smoke_completed_with_findings`
- `live_provider_panel_advisory_smoked`
- raw provider API readiness
- adapter-native readiness
- R5 unattended readiness
- release-candidate readiness
- release execution readiness

## Boundary assessment

- Hisys did not inspect, resolve, print, store, or request credential material.
- Hisys did not call a raw provider API.
- Codex CLI used its own existing subscription-auth state, attempted refresh, and failed with `refresh_token_reused`.
- No advisory critique text was returned.
- No per-critic or aggregate runtime-boundary record was written by the dispatch harness because the executor failed before returning output.
- No mutation, publication, deployment, release, external notification, R5 action, R7 action, or R8 action was performed.
- `requires_human_review=true` remains in force.

## Next safe task

```text
DARS-LIVE-RELEASE-R4-CODEX-REFRESH-STATE-RECONCILIATION-OUTSIDE-HISYS
```

The operator should reconcile the Codex CLI subscription-auth refresh state outside Hisys, without exposing token material to Hisys, then provide a new exact scoped approval before retrying the R4 Codex subprocess panel smoke.

## Retry attempt 002 — 2026-05-24T02:47:55Z

The operator asked `지금 다시 해볼래?`; Hisys retried the same bounded R4 Codex subprocess panel smoke scope.

Retry preflight evidence:

```bash
PYTHONPATH=src:. pytest \
  tests/unit/test_dars_codex_cli_subprocess.py \
  tests/unit/test_dars_remote_subscription_dispatch.py::test_remote_subscription_multi_critic_panel_dispatch_writes_aggregate_boundary \
  tests/unit/test_dars_remote_subscription_dispatch.py::test_codex_cli_subprocess_multi_critic_panel_prep_packet_matches_dispatch_contract \
  tests/unit/test_governance_docs_current_state.py \
  -q
# 48 passed

command -v codex
# /usr/bin/codex
codex --version
# codex-cli 0.128.0
```

Retry instance:

```text
/tmp/hisys-r4-codex-panel-smoke-retry-20260524-002
```

Only secret-free control packet files were written. No per-critic or aggregate runtime-boundary panel record exists.

Retry stop evidence:

```text
codex_cli_subprocess_failed: returncode=1
Failed to refresh token: 401 Unauthorized
code=refresh_token_reused
message=Your refresh token has already been used to generate a new access token. Please try signing in again.
```

Accepted retry claim:

```text
r4_codex_subscription_multi_critic_panel_smoke_retry_attempted_auth_blocked
```

The completion claim remains rejected. Boundary preserved: Hisys did not inspect credentials, call raw provider APIs, mutate, publish, deploy, release, execute R5/R7/R8, or remove human review.
