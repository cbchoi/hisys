# Live LSP diagnostic triage/fix report — 2026-05-23

## Request

After the live LSP smoke refresh was pushed, 최창범 교수 requested `push and rloi`. This pass treats `rloi` as RLOO continuation and addresses the bounded advisory diagnostics using local-safe source edits and governed LSP evidence.

## Pre-fix diagnostics

- `ruff check --output-format=concise src tests/unit/test_lsp_adapter.py` reported 14 diagnostics: unused imports, one placeholder-free f-string, and one unused local variable.
- `pyright src/hisys/operations/lsp_adapter.py` reported 2 `reportArgumentType` diagnostics for non-concrete diagnostic line/column values in the LSP adapter parser.

## Minimal fixes

- Removed unused imports in the local DARS panel adapter, CLI, backup, and codebase benchmark modules while preserving DARS dispatch's public guard-constant reexports.
- Removed the unused `head_label` local variable in governance docs.
- Replaced the placeholder-free f-string in the evidence-store CLI status text with a plain string.
- Normalized parsed ruff and pyright line/column values to concrete `int` values before constructing `LspAdapterDiagnostic` records.

## After-fix runtime evidence

| Tool command id | Output format | Diagnostics | Errors | Warnings | Info | Exit | Timed out | Truncated | Runtime report |
|---|---|---:|---:|---:|---:|---:|---|---|---|
| ruff-check-live-after-fix | ruff_json | 0 | 0 | 0 | 0 | 0 | False | False | `runtime-boundary/lsp-adapter/20260523/ruff-check-live-after-fix/lsp-report.json` |
| pyright-check-live-after-fix | pyright_json | 0 | 0 | 0 | 0 | 0 | False | False | `runtime-boundary/lsp-adapter/20260523/pyright-check-live-after-fix/lsp-report.json` |

## Boundary

Execution stayed inside local source edits and governed local LSP/lint subprocess checks. No package installation, command allowlist expansion, credential lookup, network fetch/clone/search, provider/model call, mutation/fix tool command, publication/deployment/release, or destructive Git action occurred.

The generated reports preserve advisory-only flags and require human review. This report does not declare DARS completion, production readiness, release readiness, compliance, or removal of human review.
