# Readiness Decision Record v0.0.52 — Codex CLI subprocess prompt-mode revision

- **Decision ID:** `DARS-CODEX-CLI-SUBPROCESS-PROMPT-MODE-REVISION-20260522`
- **Recorded at:** `2026-05-22T09:30:00Z`
- **Approving operator:** `choi-cb`
- **User instruction:** `subprocess를 만드는 방향으로 전면 수정`
- **Prior HEAD:** `b24a711 docs: re-verify stop-preflight at codex subscription operator gate`
- **Revised runbook:** `docs/runbooks/dars-codex-subscription-executor-runbook.md`

## Decision

The Codex DARS path is revised from a callable-only external subscription
executor model to a governed **Codex CLI subprocess prompt-mode** model.

The intended future transport is:

```text
transport_kind = codex_cli_subprocess_prompt_mode
provider_id = codex
adapter_class = codex_subscription
```

`adapter_class=codex_subscription` is retained for compatibility with the
existing M-DARS-BE-5 allowlist. The runtime-boundary record must use
`transport_kind=codex_cli_subprocess_prompt_mode` so evidence does not imply a
raw SDK/API integration.

## Scope authorized by this revision

This checkpoint authorizes docs/control revision and a future implementation-prep
row for a narrow subprocess wrapper that invokes the installed Codex CLI in
prompt mode under explicit constraints.

Allowed future prep work:

- exact command-line contract for `codex exec` / prompt-mode execution;
- read-only sandbox and `--ask-for-approval never` checks;
- no `--search`, no `--full-auto`, no `--yolo`, no sandbox bypass;
- bounded prompt packet construction and redaction hook;
- timeout, output capture, output sanitization, and empty-output fail-closed
  handling;
- runtime-boundary record fields distinguishing Codex CLI subprocess transport
  from SDK/API transport.

## Boundaries preserved

This revision does not run Codex and does not authorize an immediate smoke.
The following remain forbidden until a later execution row passes its gates:

- Codex SDK import or raw provider API call from Hisys;
- API-key, token, refresh-token, vault, or `Authorization` header lookup by
  Hisys/Ralph;
- provider account configuration;
- web search, browser use, shell/tool execution requested by the model, file
  mutation, git mutation, publication, deployment, release, PR/issue creation,
  or workspace-write execution;
- `--search`, `--full-auto`, `--yolo`, `--sandbox danger-full-access`, or
  `--dangerously-bypass-approvals-and-sandbox` for the DARS smoke;
- multi-critic panel execution;
- completion-claim upgrade beyond
  `local_fixture_localhost_controlled_advisory_complete`.

## Current local tool observation

A prerequisite inspection observed:

```text
codex path = /usr/bin/codex
codex version = codex-cli 0.128.0
```

This is readiness context only. It is not a Codex run and does not imply that
Codex prompt-mode execution has been validated.

## Next safe row

```text
DARS-CODEX-CLI-SUBPROCESS-PROMPT-MODE-PREP
```

The next row may prepare the subprocess wrapper and packet templates, then stop
before any actual Codex subprocess smoke unless the final command, instance root,
redacted prompt packet, no-mutation guard, and runtime-boundary record path are
ready.
