# Readiness decision record v0.0.77 — DARS R4 Codex subprocess panel smoke token refresh-state stop

## Request context

- Operator asked: `codex subprocess실행까지 해야하지 않나??`
- Clarification gate selected: `승인: R4 Codex subprocess panel smoke 실행`
- Attempt time: `2026-05-24T02:14:55Z`
- Baseline before attempt: `2679c60 docs: record dars r4 mapped panel action packet`

## Result

The R4 Codex subprocess panel smoke was attempted using the existing Codex subscription-auth path and stopped by Codex CLI refresh-token reuse rejection before any critique output or runtime-boundary panel evidence was produced.

Accepted bounded result:

```text
r4_codex_subscription_multi_critic_panel_smoke_attempted_auth_blocked
```

Rejected completion claim:

```text
r4_codex_subscription_multi_critic_panel_smoke_completed_with_findings
```

## Stop evidence

```text
codex_cli_subprocess_failed: returncode=1
Failed to refresh token: 400 Bad Request
code=refresh_token_reused
```

Temporary instance:

```text
/tmp/hisys-r4-codex-panel-smoke-20260524
```

Only control packet files were written; no panel runtime-boundary record exists.

## Boundary

No credential lookup by Hisys, raw provider API call by Hisys, mutation, publication, deployment, release, external notification, R5/R7/R8 action, or human-review removal was performed. Codex CLI found/used its own existing subscription-auth state, attempted refresh, and failed with `refresh_token_reused`.

## Next safe task

```text
DARS-LIVE-RELEASE-R4-CODEX-REFRESH-STATE-RECONCILIATION-OUTSIDE-HISYS
```
