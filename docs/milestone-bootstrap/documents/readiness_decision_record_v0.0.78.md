# Readiness decision record v0.0.78 — DARS R4 Codex subprocess panel smoke retry auth stop

## Request context

- Operator asked: `지금 다시 해볼래?`
- Retry time: `2026-05-24T02:47:55Z`
- Baseline before retry: `809fbff docs: clarify codex token refresh stop`

## Result

The R4 Codex subprocess panel smoke was retried under the same bounded scope and stopped again by Codex CLI authentication refresh-state failure before any critique output or runtime-boundary panel evidence was produced.

Accepted bounded result:

```text
r4_codex_subscription_multi_critic_panel_smoke_retry_attempted_auth_blocked
```

Rejected completion claim:

```text
r4_codex_subscription_multi_critic_panel_smoke_completed_with_findings
```

## Retry preflight evidence

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

## Stop evidence

Temporary retry instance:

```text
/tmp/hisys-r4-codex-panel-smoke-retry-20260524-002
```

Only secret-free control packet files were written. No panel runtime-boundary record exists.

Codex CLI returned nonzero before critique output:

```text
codex_cli_subprocess_failed: returncode=1
Failed to refresh token: 401 Unauthorized
code=refresh_token_reused
message=Your refresh token has already been used to generate a new access token. Please try signing in again.
```

## Boundary

No credential lookup by Hisys, raw provider API call by Hisys, mutation, publication, deployment, release, external notification, R5/R7/R8 action, or human-review removal was performed. Codex CLI used its own existing subscription-auth state and failed while refreshing it.

## Next safe task

```text
DARS-LIVE-RELEASE-R4-CODEX-REFRESH-STATE-RECONCILIATION-OUTSIDE-HISYS
```
