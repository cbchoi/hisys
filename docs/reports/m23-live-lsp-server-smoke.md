# M23 Live LSP Server Smoke Report

## Request

최창범 교수 requested: `1번은 진행하고 2번, LSP 서버 설치 및 실행해. ruff, pyright, eslint면 될 것 같아.`

## Installation evidence

Installed or verified local LSP/lint executables on 2026-05-22 KST:

- `ruff 0.15.10` already available at `/home/cbchoi/.hermes/hermes-agent/venv/bin/ruff`.
- `pyright 1.1.409` installed under `/home/cbchoi/.hermes/hisys-lsp-tools/node_modules/.bin/pyright`.
- `eslint v10.4.0` installed under `/home/cbchoi/.hermes/hisys-lsp-tools/node_modules/.bin/eslint`.

Install command used for Node tools:

```bash
npm install --prefix /home/cbchoi/.hermes/hisys-lsp-tools pyright eslint
```

## Execution evidence through Hisys LSP adapter

The existing governed `hisys lsp-adapter` boundary was used for execution. The adapter preserves `advisory_only=true`, `requires_human_review=true`, `external_call_made=false`, `mutation_performed=false`, `raw_source_content_persisted=false`, and `live_external_action_authorized=false`.

| Tool | Command id | Scope | Diagnostics | Exit | Runtime report |
|---|---:|---|---:|---:|---|
| ruff | `ruff-check-live` | Hisys repo `src` plus `tests/unit/test_lsp_adapter.py` | 14 errors | 1 | `runtime-boundary/lsp-adapter/20260522/ruff-check-live/lsp-report.json` |
| pyright | `pyright-check-live` | Hisys repo `src/hisys/operations/lsp_adapter.py` | 2 errors | 1 | `runtime-boundary/lsp-adapter/20260522/pyright-check-live/lsp-report.json` |
| eslint | `eslint-check-live` | temporary JavaScript fixture under `/tmp/hisys-lsp-live-smoke/eslint-instance/workspace` | 3 diagnostics | 1 | `/tmp/hisys-lsp-live-smoke/eslint-instance/runtime-boundary/lsp-adapter/20260522/eslint-check-live/lsp-report.json` |

The committed runtime reports for repo-scoped ruff and pyright contain only refs, counts, severities, category refs, line/column positions, subprocess boundary fields, and SHA-256 message digests. They do not persist raw diagnostic messages or raw source bodies.

## Boundary

This smoke did not perform credential lookup, secret capture, network source fetch, remote repository clone, publication/deployment/release, force push, destructive Git/history action, non-fixture user/live data mutation, or live-provider DARS execution. ESLint execution used a local fixture because Hisys currently has no JavaScript/TypeScript source package or ESLint project configuration.
