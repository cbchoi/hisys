# DARS Codex CLI subprocess failure-mode fixture PREP

Date: 2026-05-22
Baseline: `a986edc docs: review codex cli subprocess smoke evidence`
Related authorization records and anchors:

- `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.55.md` (smoke review gate; named this PREP as the next safe local-only row)
- `docs/reports/dars-codex-cli-subprocess-single-smoke-2026-05-22.md` (smoke advisory recommending fixture coverage for timeout and malformed-output cases)
- `docs/runbooks/dars-codex-subscription-executor-runbook.md` (transport_kind contract; stop-condition matrix §6)
- `src/hisys/agents/dars_codex_cli_subprocess.py` (existing PREP executor)
- `tests/unit/test_dars_codex_cli_subprocess.py` (existing fake-runner cohort)

## Scope

This PREP extends the local-only fake-runner cohort for the governed Codex CLI
subprocess prompt-mode executor with five focused failure modes named by the
smoke advisory and Section 16 next-row entry:

1. **Subprocess timeout** — runner raises `subprocess.TimeoutExpired`; the
   executor fails closed with `codex_cli_subprocess_timeout` and reports the
   configured `timeout_seconds` instead of leaking the exception.
2. **Non-zero exit with secret-like stderr** — runner returns `returncode != 0`
   with stderr containing a secret-shaped substring; the executor fails closed
   with `codex_cli_subprocess_failed` but the raised message redacts the stderr
   payload so the focused error message cannot leak the secret-shaped substring.
3. **Blank output variants** — runner returns whitespace-only stdout (spaces,
   tabs, newlines); the executor fails closed with
   `codex_cli_subprocess_empty_output` consistently across the variants.
4. **Malformed advisory metadata** — runner returns stdout that either (a)
   exceeds `_MAX_CRITIQUE_CHARS`, (b) contains forbidden control characters, or
   (c) claims unauthorized authority such as `workspace_write: true`,
   `web_search: true`, `sandbox bypass`, `danger-full-access`,
   `mutation_performed: true`, `publication_performed: true`,
   `requires_human_review: false`, or pseudo tool-call markers; each fails
   closed with `codex_cli_subprocess_output_too_long`,
   `codex_cli_subprocess_output_contains_control_chars`, or
   `codex_cli_subprocess_output_claims_unauthorized_authority`.
5. **Secret-like output rejection** — runner returns stdout containing a
   secret-shaped substring (`sk-`, `sk_`, `ghp_`, `xoxb-`, `xoxp-`, `hf_`,
   `Authorization:`, `api_key`, `refresh_token`, `access_token`
   assignment-style prefixes); the executor fails closed with
   `codex_cli_output_not_redacted` and the raised message does not echo the
   secret payload.

## Boundary

This PREP is local-only. It does **not** invoke `/usr/bin/codex`, import a
Codex SDK, call a raw provider API, inspect credentials, read API keys, send
Authorization headers, configure provider accounts, hold raw secrets,
write a runtime-boundary record, mutate files outside this PREP's docs/control
artifacts, publish, deploy, create PRs/issues, run repeated Codex smokes,
authorize a multi-critic panel, expand the provider/adapter/transport
allowlist, or upgrade the DARS completion claim. All failure modes are
exercised via injected fake runners that match the existing
`SubprocessRunner` protocol; the default `subprocess.run` is never called.

The DARS completion claim remains
`local_fixture_localhost_controlled_advisory_complete` plus the previously
accepted narrow `codex_cli_subprocess_single_smoke_review_accepted` claim. No
upgrade is implied by this PREP.

## Deterministic issue-code catalog after this PREP

| Failure mode | Deterministic ValueError code |
|---|---|
| Subprocess timed out | `codex_cli_subprocess_timeout` |
| Non-zero exit | `codex_cli_subprocess_failed` (stderr preview is redacted when secret-shaped) |
| Empty / whitespace-only stdout | `codex_cli_subprocess_empty_output` |
| stdout exceeds `_MAX_CRITIQUE_CHARS` (32_000) | `codex_cli_subprocess_output_too_long` |
| stdout contains forbidden control characters | `codex_cli_subprocess_output_contains_control_chars` |
| stdout claims unauthorized authority (tool / shell / search / mutation / publication / `requires_human_review=false`) | `codex_cli_subprocess_output_claims_unauthorized_authority` |
| stdout contains raw-secret-shaped substring | `codex_cli_output_not_redacted` |

These codes are exercised by the extended cohort in
`tests/unit/test_dars_codex_cli_subprocess.py` only. They are emitted by
`src/hisys/agents/dars_codex_cli_subprocess.py` and propagate through the
remote-subscription dispatch harness as `ValueError` so callers can stop and
record the blocked request without producing a runtime-boundary record.

## Stderr redaction rule for `codex_cli_subprocess_failed`

When the subprocess returncode is non-zero and the captured stderr contains a
match for the raw-secret-marker regex `_RAW_SECRET_MARKERS`, the executor must
not echo the stderr substring in the raised error message. Instead it replaces
the bounded stderr preview with a redaction sentinel
(`<stderr-redacted-secret-detected len=N>`) before raising. Non-secret stderr
text is still surfaced verbatim up to `_MAX_STDERR_PREVIEW_CHARS` so operators
can diagnose ordinary failures.

## Required outputs

- Extend `src/hisys/agents/dars_codex_cli_subprocess.py` with:
  - `_MAX_CRITIQUE_CHARS = 32_000`;
  - `_CONTROL_CHAR_RE` for forbidden control characters
    (`\x00-\x08`, `\x0b`, `\x0c`, `\x0e-\x1f`);
  - `_FORBIDDEN_AUTHORITY_MARKERS` for claimed tool/shell/search/mutation/
    publication authority and the explicit `requires_human_review=false`
    marker;
  - `subprocess.TimeoutExpired` handling that raises
    `codex_cli_subprocess_timeout: timeout_seconds=<n>`;
  - secret-aware stderr redaction in the `codex_cli_subprocess_failed`
    message.
- Extend `tests/unit/test_dars_codex_cli_subprocess.py` with focused fake-runner
  coverage for each failure mode and for stderr redaction.
- Update `docs/runbooks/dars-codex-subscription-executor-runbook.md` so §6
  cites the deterministic issue codes for timeout, output-too-long,
  control-character, claimed-authority, and stderr-redaction cases.
- Record readiness decision v0.0.56; bump `docs/milestone-bootstrap/profile.yaml`
  to `v0.0.56`; update `tests/unit/test_governance_docs_current_state.py`
  expectation; prepend a `DARS-CODEX-CLI-SUBPROCESS-FAILURE-MODE-FIXTURE-PREP`
  row to `docs/traceability/README.md`; update Section 16 queue status and add
  this PREP entry to the Reflection Log.

## Verification gates

```bash
PYTHONPATH=src pytest tests/unit/test_dars_codex_cli_subprocess.py -q
PYTHONPATH=src pytest tests/unit/test_dars_codex_cli_subprocess.py tests/unit/test_dars_remote_subscription_dispatch.py tests/unit/test_governance_docs_current_state.py -q
PYTHONPATH=src:. pytest -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
git status --short --branch
```

## Stop-condition matrix

| Signal | Required action |
|---|---|
| Focused failure-mode tests do not fail before implementation | Re-author RED tests; do not commit a non-RED increment |
| Governance current-state test does not match the new `profile_version` | Update profile.yaml + assertion together; do not commit drift |
| Secret scan hit_count > 0 | Stop; rework strings or use literal-splitting like the existing tests |
| `git diff --check` fails | Stop and fix whitespace before commit |
| Branch is not `dars` or upstream is not `origin/dars` | Stop and report; do not push |
| Operator asks for repeated Codex smoke, multi-critic panel, LSP allowlist expansion, or new product-scope milestone | Stop and ask; this PREP does not authorize those |
| Operator asks for completion-claim upgrade past `local_fixture_localhost_controlled_advisory_complete + codex_cli_subprocess_single_smoke_review_accepted` | Stop and ask; this PREP does not upgrade the claim |

## Next safe Ralph row after this PREP

After this PREP commits and pushes the local fixture coverage, the next safe
row is documented as a stop-and-ask gate:

```text
QUEUE-REFILL-PREP-STOP — every remaining post-PREP candidate (repeated Codex
smoke, multi-critic panel, live LSP execution / executable allowlist
expansion, M25 / new product-scope milestone, Section 10.3 branch alignment,
real OSS comparison / license adjudication live execution) requires fresh
explicit operator authorization.
```
