# Readiness Decision Record v0.0.33

## Decision

`RALPH_START_READY_WITH_CONTROLS` for the M23 adapter portfolio integration follow-up and local LSP server smoke continuation.

## User authorization

On 2026-05-22 KST, 최창범 교수 requested candidate 1 and candidate 2: `1번은 진행하고 2번, LSP 서버 설치 및 실행해. ruff, pyright, eslint면 될 것 같아.`

## Authorized scope

- Proceed with `M23-ADAPTER-PORTFOLIO-INTEGRATION` so the M22 codebase evidence portfolio can include `M23_OSS_ADAPTER` and `M23_LSP_ADAPTER` lines by refs, counts, schema ids, and quality-gate refs.
- Install and run local LSP/lint executables `ruff`, `pyright`, and `eslint` through the governed Hisys LSP adapter boundary.
- Persist advisory runtime/report evidence that preserves `raw_source_content_persisted=false` and message-digest-only diagnostic content.

## Evidence already captured

- `docs/reports/m23-live-lsp-server-smoke.md` records installation and first execution evidence.
- Repo-scoped runtime reports were written for `ruff-check-live` and `pyright-check-live` under `runtime-boundary/lsp-adapter/20260522/`.
- ESLint was installed and run against a local fixture because this Hisys repo has no JavaScript/TypeScript project configuration.

## Non-claims and remaining gates

This record does not authorize credential lookup or mutation, secret capture, arbitrary network search/clone/fetch, real OSS repository clone, license-text capture, license adjudication, new or changed remote configuration, publication/deployment/release, destructive Git/history operations, force push, mutation of non-fixture user/live data, unbounded live external provider execution, or a live-provider DARS completion claim.

## Next safe task

`M23-ADAPTER-PORTFOLIO-INTEGRATION-PREP`.
