# Readiness Decision Record v0.0.54 — Codex CLI subprocess single smoke evidence

- **Decision ID:** `DARS-CODEX-CLI-SUBPROCESS-SINGLE-SMOKE-20260522`
- **Recorded at:** `2026-05-22T13:50:16Z`
- **Operator instruction:** `smoke 진행`
- **Prior HEAD:** `2746ada docs: re-verify stop-preflight at codex cli subprocess single smoke gate`
- **Smoke report:** `docs/reports/dars-codex-cli-subprocess-single-smoke-2026-05-22.md`
- **Runtime-boundary JSON:** `/tmp/hisys-dars-codex-subscription/runtime-boundary/dars-remote-subscriptions/20260522/REQ-DARS-CODEX-SMOKE-20260522-001/codex_subscription_dars_critic-EXEC-DARS-CODEX-SMOKE-20260522-001.json`
- **Runtime-boundary Markdown:** `/tmp/hisys-dars-codex-subscription/runtime-boundary/dars-remote-subscriptions/20260522/REQ-DARS-CODEX-SMOKE-20260522-001/codex_subscription_dars_critic-EXEC-DARS-CODEX-SMOKE-20260522-001.md`

## Decision

The single Codex CLI subprocess smoke gate was executed once through the prepared
Hisys remote-subscription dispatch harness. Runtime-boundary evidence was written
under `/tmp/hisys-dars-codex-subscription` with:

```text
provider_id = codex
adapter_class = codex_subscription
transport_kind = codex_cli_subprocess_prompt_mode
external_call_made = true
model_boundary_crossed = true
mutation_performed = false
publication_performed = false
requires_human_review = true
```

## Command-contract correction

The smoke gate found a CLI-version-specific contract issue before successful
evidence capture. Codex CLI `0.128.0` accepts `--ask-for-approval` as a top-level
option, not as an `exec` subcommand option. The wrapper/runbook/decision record
were corrected from:

```bash
codex exec --sandbox read-only --ask-for-approval never --cd <dir> -- <prompt>
```

to:

```bash
codex --ask-for-approval never exec --sandbox read-only --cd <dir> -- <prompt>
```

The successful smoke used the corrected command shape.

## Boundary interpretation

This decision record does not upgrade the DARS completion claim. It records that
a single governed Codex CLI subprocess prompt-mode smoke produced advisory output
and runtime-boundary evidence. The evidence still requires review before any
claim change.

The following remain forbidden without a separate later decision:

- repeated Codex smoke runs;
- multi-critic Codex/Claude panel execution;
- web search;
- workspace-write or broader sandbox;
- model-requested tool/browser/shell delegation;
- mutation, publication, deployment, PR/issue creation, release, or provider
  account configuration;
- raw credential handling by Hisys/Ralph;
- completion-claim upgrade without a review/gate row.

## Next safe row

```text
DARS-CODEX-CLI-SUBPROCESS-SMOKE-REVIEW-GATE
```

The review gate should inspect the runtime-boundary JSON/Markdown evidence,
confirm repository mutation status and post-smoke validation, and decide whether
to keep the claim unchanged or prepare a narrow claim-update proposal.
