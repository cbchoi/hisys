# Live LSP smoke refresh report — 2026-05-23

## Request

최창범 교수 requested a live LSP RLOO control plan that can run without further user approval and finish in one stepwise pass.

## Runtime evidence

| Tool command id | Output format | Diagnostics | Errors | Warnings | Info | Exit | Timed out | Truncated | Runtime report |
|---|---|---:|---:|---:|---:|---:|---|---|---|
| ruff-check-live-refresh | ruff_json | 14 | 14 | 0 | 0 | 1 | False | False | `runtime-boundary/lsp-adapter/20260523/ruff-check-live-refresh/lsp-report.json` |
| pyright-check-live-refresh | pyright_json | 2 | 2 | 0 | 0 | 1 | False | False | `runtime-boundary/lsp-adapter/20260523/pyright-check-live-refresh/lsp-report.json` |

## Boundary

Execution used only the existing governed `hisys lsp-adapter` boundary with caller-authored bundles, existing `ruff` and `pyright` executables, no package installation, no credential lookup, no network fetch/clone/search, no provider/model call, no mutation/fix command, no publication/deployment/release, and no command allowlist expansion.

The generated reports preserve `advisory_only=true`, `requires_human_review=true`, `external_call_made=false`, `mutation_performed=false`, `raw_source_content_persisted=false`, `live_external_action_authorized=false`, and `allowed_actions=advisory_only`.

This report is an advisory local evidence refresh only. It does not declare DARS completion, production readiness, release readiness, compliance, or removal of human review.
