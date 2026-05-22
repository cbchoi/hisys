# Readiness Decision Record v0.0.51 — Codex subscription live-smoke authorization captured

- **Decision ID:** `DARS-CODEX-SUBSCRIPTION-LIVE-SMOKE-AUTH-CAPTURE-20260522`
- **Recorded at:** `2026-05-22T09:03:15Z`
- **Approving operator:** `choi-cb`
- **User approval sentence:** `허가`
- **Prior gate:** `DARS-REMOTE-SUBSCRIPTION-AUTH-EXECUTE-OPERATOR-PREREQUISITES`
- **Prior HEAD:** `6680f3b docs: record stop-preflight at dars remote subscription operator gate`
- **Related packet drafts:**
  - `docs/examples/dars/codex-subscription-policy.recommended.json`
  - `docs/examples/dars/codex-subscription-activation.recommended.json`
- **Executor runbook:** `docs/runbooks/dars-codex-subscription-executor-runbook.md`

## Decision

The operator's approval is recorded as authorization to open a controlled
single Codex subscription smoke line for DARS, subject to the already documented
remote-subscription policy, activation, executor, redaction, egress, audit, and
runtime-boundary controls.

This record is **not** a provider execution result. It does not by itself supply
the wired external executor function, does not resolve credentials, does not
perform a Codex call, and does not upgrade the DARS completion claim.

## Allowed first increment

The allowed first increment after this authorization is still the prerequisite
consumption gate:

```text
DARS-REMOTE-SUBSCRIPTION-AUTH-EXECUTE-OPERATOR-PREREQUISITES
```

That gate may consume the authorization captured here and may prepare a bounded
single-smoke execution packet only after all remaining operator-owned values are
present:

- wired external `RemoteSubscriptionExecutor` matching
  `docs/runbooks/dars-codex-subscription-executor-runbook.md` §§3–4;
- concrete redaction transform bound to
  `policy://hisys/dars/codex-subscription-redaction-v1`;
- operator egress/audit binding for
  `advisory-dars-critic-prompt-and-bounded-evidence-summary-only`;
- fresh `expires_at` value still in the future near execution time;
- fresh `revocation_ref`;
- fresh policy packet JSON path and fresh activation packet JSON path;
- governed `HISYS_INSTANCE`, recommended as
  `/tmp/hisys-dars-codex-subscription` unless the operator supplies another
  controlled instance root;
- explicit confirmation that the executor has no tool, search, browser,
  mutation, publication, deployment, repository, subprocess, or arbitrary
  endpoint authority.

## Boundaries preserved

The following remain forbidden in this checkpoint:

- no Codex SDK invocation;
- no real provider call;
- no credential lookup, vault unseal, token read, API-key read, refresh-token
  read, or `Authorization` header handling by Hisys/Ralph;
- no raw secret persistence in the repository or runtime-boundary records;
- no provider account configuration;
- no arbitrary OpenAI-compatible, Anthropic-compatible, Gemini, Grok,
  pay-per-call, raw-HTTP, or local-proxy endpoint expansion;
- no browser, web-search, external tool, filesystem mutation, git mutation,
  publication, deployment, release, or destructive history operation authority;
- no multi-critic panel execution until a later single-smoke gate succeeds and a
  separate panel gate is approved;
- no DARS completion-claim upgrade beyond
  `local_fixture_localhost_controlled_advisory_complete`.

## Current authorization interpretation

The approval authorizes a **controlled future single-smoke line**, not an
immediate provider call from this docs/control checkpoint. The live-smoke line
must fail closed unless the full prerequisite packet is available and validators
pass near execution time.

Suggested execution-window default for the next packet, if the operator does not
supply a different bounded value:

```text
expires_at = 2026-05-29T09:03:15Z
revocation_ref = revoke://hisys/dars/codex-subscription/20260522-live-smoke
```
