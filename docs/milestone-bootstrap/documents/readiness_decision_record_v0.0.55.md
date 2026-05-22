# Readiness Decision Record v0.0.55 — Codex CLI subprocess smoke review gate

- **Decision ID:** `DARS-CODEX-CLI-SUBPROCESS-SMOKE-REVIEW-20260522`
- **Recorded at:** `2026-05-22T13:59:04Z`
- **Operator instruction:** `DARS-CODEX-CLI-SUBPROCESS-SMOKE-REVIEW-GATE에서 이 evidence를 검토`
- **Reviewed HEAD:** `9e28704 feat: capture codex cli subprocess smoke evidence`
- **Review report:** `docs/reports/dars-codex-cli-subprocess-smoke-review-2026-05-22.md`
- **Smoke report:** `docs/reports/dars-codex-cli-subprocess-single-smoke-2026-05-22.md`
- **Runtime-boundary JSON:** `/tmp/hisys-dars-codex-subscription/runtime-boundary/dars-remote-subscriptions/20260522/REQ-DARS-CODEX-SMOKE-20260522-001/codex_subscription_dars_critic-EXEC-DARS-CODEX-SMOKE-20260522-001.json`

## Decision

Accept the single-smoke evidence for a narrow reviewed claim:

```text
codex_cli_subprocess_single_smoke_review_accepted
```

The evidence is sufficient to state that one governed Codex CLI subprocess
prompt-mode DARS critic smoke crossed the model boundary and wrote
runtime-boundary evidence with `external_call_made=true`,
`model_boundary_crossed=true`, `transport_kind=codex_cli_subprocess_prompt_mode`,
`mutation_performed=false`, `publication_performed=false`, and
`requires_human_review=true`.

## Claim boundary

The review does not upgrade the broader DARS completion claim. The current claim
boundary is:

```text
local_fixture_localhost_controlled_advisory_complete
+
codex_cli_subprocess_single_smoke_review_accepted
```

The smoke advisory remains advisory-only and must not be treated as an automatic
DARS decision, publication, release, or product completion result.

## Boundary conditions preserved

- No additional Codex subprocess was executed during this review gate.
- No Codex SDK import occurred.
- No raw provider API call from Hisys occurred.
- No credential lookup, vault resolution, raw token/key/header handling, or
  provider account configuration occurred.
- No web search, workspace-write, danger-full-access, sandbox bypass,
  publication, deployment, PR/issue creation, release, or multi-critic panel was
  authorized by this review.

## Required follow-up

The next safe row is local-only fixture/failure-mode preparation:

```text
DARS-CODEX-CLI-SUBPROCESS-FAILURE-MODE-FIXTURE-PREP
```

It should add or extend fake-runner tests for timeout, non-zero exit, blank
output, malformed advisory metadata, and secret-like output rejection. It must
not run Codex again.
