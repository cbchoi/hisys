# M23 Adapter Portfolio Integration Follow-up Plan

> **For Hermes/Ralph:** The user authorized post-M23 candidate 1: integrate M23 adapter evidence lines into the M22 codebase evidence portfolio. Execute this follow-up locally with PREP -> RED/GREEN -> GATE discipline. The user also authorized installing and running local LSP servers `ruff`, `pyright`, and `eslint`; the first smoke evidence is recorded in `docs/reports/m23-live-lsp-server-smoke.md`.

## Goal

Add M23 adapter evidence-line refs to the codebase evidence portfolio so operators can see OSS comparison adapter and LSP adapter evidence alongside M21 and DARS evidence. The integration must use refs, counts, schema ids, and quality-gate refs only. It must not copy raw source content or raw diagnostic messages.

## Queue

| Row | Task | Type | Status |
|---|---|---|---|
| M23-ADAPTER-PORTFOLIO-INTEGRATION-PREP | Define the exact portfolio bundle lines for `M23_OSS_ADAPTER` and `M23_LSP_ADAPTER`, including live LSP smoke refs. | docs/control | next |
| M23-ADAPTER-PORTFOLIO-INTEGRATION-RED-GREEN | Add/extend fixture or test coverage proving the M22 portfolio accepts M23 adapter evidence lines by refs/counts only. | fixture-local implementation | pending after PREP |
| M23-LIVE-LSP-SMOKE-GATE | Preserve the ruff/pyright/eslint installation+execution evidence and gate boundaries. | docs/control gate | pending after integration |

## Initial portfolio lines

- `M23_OSS_ADAPTER`: refs to OSS comparison adapter module, CLI, tests, golden fixture, and closure/gate record.
- `M23_LSP_ADAPTER`: refs to LSP adapter module, CLI, tests, golden fixture, closure/gate record, and live smoke report refs for ruff/pyright/eslint.

## Boundaries

Allowed: local fixture/test updates, local runtime report refs, docs/traceability/profile/Ralph updates, validation, local commits, normal push to `origin/dars`.

Not allowed: credential lookup or mutation, secret capture, arbitrary network search/clone/fetch, real OSS clone/license capture, new or changed remote configuration, publication/deployment/release, force push, destructive Git/history actions, non-fixture user/live data mutation, raw source-content archival, raw diagnostic-message archival beyond already-redacted adapter reports, or live-provider DARS completion claims.
