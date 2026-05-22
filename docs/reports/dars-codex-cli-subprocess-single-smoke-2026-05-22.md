# DARS Codex CLI subprocess single smoke report — 2026-05-22

## Summary

A single governed Codex CLI subprocess smoke was executed through the prepared
remote-subscription dispatch harness after operator instruction `smoke 진행`.
The smoke crossed the model boundary once and wrote runtime-boundary evidence
under the governed temporary instance root.

## Execution identity

- Recorded at: `2026-05-22T13:50:16Z`
- Prior committed HEAD before smoke-gate edits: `2746ada docs: re-verify stop-preflight at codex cli subprocess single smoke gate`
- Instance root: `/tmp/hisys-dars-codex-subscription`
- Request ID: `REQ-DARS-CODEX-SMOKE-20260522-001`
- Source execution ID: `EXEC-DARS-CODEX-SMOKE-20260522-001`
- Backend ID: `codex_subscription_dars_critic`
- Backend kind: `codex_subscription`
- Provider ID: `codex`
- Adapter class: `codex_subscription`
- Transport kind: `codex_cli_subprocess_prompt_mode`

## Preflight evidence

- `git status --short --branch` before smoke: `## dars...origin/dars`
- `command -v codex`: `/usr/bin/codex`
- `codex --version`: `codex-cli 0.128.0`
- Focused governance/Codex/dispatch cohort: `29 passed`
- Traceability validator: `OK`
- Secret scan before smoke: `hit_count=0`
- Policy validation at `2026-05-22T13:30:00Z`: `valid=True` with expected warning `remote_dispatch_not_implemented`
- Activation validation at `2026-05-22T13:30:00Z`: `valid=True`
- Policy/activation expiry: `2026-06-05T06:54:03Z`

## Command-contract correction during smoke gate

The first smoke attempt did not reach the DARS dispatch success boundary because
Codex CLI `0.128.0` rejected the PREP command shape when
`--ask-for-approval never` was placed after `exec`:

```text
codex_cli_subprocess_failed: returncode=2: error: unexpected argument '--ask-for-approval' found
```

`codex exec --help` showed that `--ask-for-approval` is a top-level Codex option,
while `--sandbox` and `--cd` are accepted under `exec`. The wrapper and tests were
therefore corrected to build:

```bash
codex --ask-for-approval never exec \
  --sandbox read-only \
  --cd <controlled-workdir> \
  -- "<redacted bounded DARS critic prompt packet>"
```

Focused wrapper test after the correction: `9 passed`.

## Runtime-boundary evidence

Runtime-boundary JSON:

```text
/tmp/hisys-dars-codex-subscription/runtime-boundary/dars-remote-subscriptions/20260522/REQ-DARS-CODEX-SMOKE-20260522-001/codex_subscription_dars_critic-EXEC-DARS-CODEX-SMOKE-20260522-001.json
```

Runtime-boundary Markdown:

```text
/tmp/hisys-dars-codex-subscription/runtime-boundary/dars-remote-subscriptions/20260522/REQ-DARS-CODEX-SMOKE-20260522-001/codex_subscription_dars_critic-EXEC-DARS-CODEX-SMOKE-20260522-001.md
```

Observed boundary fields:

```json
{
  "external_call_made": true,
  "model_boundary_crossed": true,
  "local_model_call_made": false,
  "mutation_performed": false,
  "publication_performed": false,
  "requires_human_review": true,
  "transport_kind": "codex_cli_subprocess_prompt_mode"
}
```

Critique preview recorded in the runtime-boundary JSON:

```text
- Risk: Prompt-mode behavior may still diverge under real subprocess edge cases such as timeout, partial output, or malformed advisory metadata.
- Recommendation: Run a human-reviewed dry-run fixture that simulates timeout and malformed-output cases while confirming `requires_human_review` stays true.
```

## Boundaries preserved

- No Codex SDK import occurred.
- No raw provider API call from Hisys occurred.
- Hisys did not inspect, copy, store, or print API keys, tokens, refresh tokens,
  Authorization headers, or provider account configuration.
- The existing-auth reference remains `vault://existing-auth/codex-subscription`.
- No web search flag was used.
- No `--full-auto`, `--yolo`, `--sandbox danger-full-access`, or sandbox-bypass
  flag was used.
- No publication, deployment, PR/issue creation, or repository synchronization was
  requested from Codex.
- The runtime-boundary evidence remains advisory and requires human review.
- The DARS completion claim is not upgraded by this report.

## Review decision

This report records a successful single-smoke evidence boundary, not a completion
upgrade. The next safe row is a review/gate row that may decide whether the
single-smoke evidence is sufficient for a narrow claim update or whether more
fixture/failure-mode coverage is required first.
