# Readiness Decision Record v0.0.56 — Codex CLI subprocess failure-mode fixture PREP

- **Decision ID:** `DARS-CODEX-CLI-SUBPROCESS-FAILURE-MODE-FIXTURE-PREP-20260522`
- **Recorded at:** `2026-05-22T15:30:00Z`
- **Triggering signal:** smoke-review advisory in
  `docs/reports/dars-codex-cli-subprocess-single-smoke-2026-05-22.md` and
  follow-up direction in
  `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.55.md` that
  named `DARS-CODEX-CLI-SUBPROCESS-FAILURE-MODE-FIXTURE-PREP` as the next safe
  local-only row.
- **Reviewed HEAD before this PREP:** `a986edc docs: review codex cli subprocess smoke evidence`
- **PREP plan:** `docs/plans/dars-codex-cli-subprocess-failure-mode-fixture-prep-tasks.md`

## Decision

Authorize the local-only fixture/failure-mode prep for the governed Codex CLI
subprocess prompt-mode executor. The PREP extends the existing fake-runner
cohort with five focused failure modes:

1. subprocess timeout (`codex_cli_subprocess_timeout`),
2. non-zero exit with secret-aware stderr redaction
   (`codex_cli_subprocess_failed` with `<stderr-redacted-secret-detected>`),
3. blank / whitespace-only output (`codex_cli_subprocess_empty_output`),
4. malformed advisory metadata — output too long
   (`codex_cli_subprocess_output_too_long`), control characters
   (`codex_cli_subprocess_output_contains_control_chars`), and claimed
   unauthorized authority
   (`codex_cli_subprocess_output_claims_unauthorized_authority`),
5. secret-like output rejection (`codex_cli_output_not_redacted`).

All five are exercised through injected `SubprocessRunner` fakes. No real
`/usr/bin/codex` subprocess is launched by this PREP.

## Claim boundary

This PREP does not upgrade the broader DARS completion claim. The claim
remains:

```text
local_fixture_localhost_controlled_advisory_complete
+
codex_cli_subprocess_single_smoke_review_accepted
```

The narrow single-smoke review claim is unchanged. The PREP adds local-only
test coverage and deterministic issue codes; it does not write a new
runtime-boundary record, does not call Codex, and does not authorize repeated
provider calls or a multi-critic panel.

## Boundary conditions preserved

- No Codex subprocess was launched (fake runners only).
- No Codex SDK import occurred.
- No raw provider API call from Hisys occurred.
- No credential lookup, vault resolution, raw token/key/header handling,
  Authorization header storage, or provider account configuration occurred.
- No web search flag, workspace-write, danger-full-access, sandbox bypass,
  publication, deployment, PR/issue creation, release, or multi-critic panel
  was authorized.
- No allowlist expansion beyond `codex` / `claude` (`codex_subscription` /
  `claude_subscription`) and no transport-kind expansion beyond
  `injected_subscription_executor` / `codex_cli_subprocess_prompt_mode`.
- No DARS completion-claim upgrade beyond the existing combined claim.

## Required follow-up

After this PREP commits, the next safe row is documented as a stop-and-ask
gate:

```text
QUEUE-REFILL-PREP-STOP — every remaining post-PREP candidate (repeated Codex
smoke, multi-critic panel, live LSP execution / executable allowlist
expansion, M25 / new product-scope milestone, Section 10.3 branch alignment,
real OSS comparison / license adjudication live execution) requires fresh
explicit operator authorization.
```

The smoke advisory's recommendation has been satisfied: a human-reviewed
dry-run fixture now simulates timeout and malformed-output cases while
confirming `requires_human_review` remains true (the fail-closed paths raise
before the dispatch boundary writer, so no boundary record claims
`requires_human_review=false`).
