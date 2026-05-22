# DARS Codex CLI subprocess multi-critic panel PREP tasks

## Purpose

Prepare a controlled multi-critic panel row after queue refill authorization.
The row starts from the existing single-smoke evidence, reviewed smoke gate, and
local failure-mode fixture coverage. It does not run Codex by itself.

## Controlled anchors

- `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.57.md`
- `docs/reports/dars-codex-cli-subprocess-smoke-review-2026-05-22.md`
- `docs/plans/dars-codex-cli-subprocess-failure-mode-fixture-prep-tasks.md`
- `docs/runbooks/dars-codex-subscription-executor-runbook.md`
- `src/hisys/agents/dars_codex_cli_subprocess.py`
- `src/hisys/agents/dars_remote_subscription_dispatch.py`
- `tests/unit/test_dars_codex_cli_subprocess.py`
- `tests/unit/test_dars_remote_subscription_dispatch.py`

## Existing readiness baseline

The repository already contains:

- `build_codex_cli_prompt_mode_executor(...)` for a bounded single-critic Codex
  CLI subprocess prompt-mode executor;
- fake-runner coverage for timeout, non-zero exit, blank output, overlong output,
  forbidden control characters, unauthorized authority claims, and secret-like
  output rejection;
- `run_dars_remote_subscription_panel_dispatch(...)` for an injected-executor
  multi-critic panel that writes per-critic and aggregate runtime-boundary
  records;
- fail-closed panel-shape checks for invalid date/request/panel identifiers,
  fewer than two critic requests, mismatched request IDs, and duplicate source
  execution IDs.

## PREP checklist

Before any live multi-critic panel smoke, complete these local checks:

1. Define the exact panel request packet:
   - one `request_id`;
   - one slug-safe `panel_id`;
   - at least two unique `source_execution_id` values;
   - one controlled instance root;
   - declared `yyyymmdd` partition;
   - per-critic prompt packets with distinct bounded advisory roles.
2. Verify every critic request uses:
   - `provider_id=codex`;
   - `adapter_class=codex_subscription`;
   - `transport_kind=codex_cli_subprocess_prompt_mode`;
   - `allowed_actions=advisory_only`;
   - `mutation_performed=false`;
   - `publication_performed=false`.
3. Verify the aggregate panel boundary record must use:
   - `schema_id=hisys.dars.remote_subscription_panel_dispatch`;
   - `transport_kind=injected_subscription_executor_panel`;
   - `requires_human_review=true`;
   - no completion-claim upgrade.
4. Re-run focused local tests before any later live smoke.
5. Confirm secret scan is clean before any prompt crosses the Codex CLI boundary.
6. Stop if Codex CLI is unavailable, policy/activation packets are expired or
   invalid, prompt text contains raw-secret markers, or any requested authority
   exceeds advisory-only read-only critique.

## Future live panel row boundary

A later live row may be named:

```text
DARS-CODEX-CLI-SUBPROCESS-MULTI-CRITIC-PANEL-SMOKE-GATE
```

That row may run at most the explicitly prepared bounded panel. It must not add
web search, browser tools, shell/tool delegation, workspace-write, publication,
deployment, PR/issue creation, credential lookup, provider account configuration,
or automatic DARS completion-claim upgrade.

## Validation commands for this PREP row

```bash
PYTHONPATH=src:. pytest tests/unit/test_governance_docs_current_state.py tests/unit/test_dars_codex_cli_subprocess.py tests/unit/test_dars_remote_subscription_dispatch.py -q
PYTHONPATH=src:. pytest -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```
