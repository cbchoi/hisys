# Readiness Decision Record v0.0.57 — Queue refill and multi-critic panel authorization

- **Decision ID:** `QUEUE-REFILL-MULTI-CRITIC-PANEL-AUTH-20260522`
- **Recorded at:** `2026-05-22T14:38:28Z`
- **Operator instruction:** `Queue refill planning and multi-critic panel 승인`
- **Baseline HEAD:** `fb54581 feat: add codex cli subprocess failure-mode fixtures`
- **Previous profile:** `v0.0.56`
- **Previous stop row:** `QUEUE-REFILL-PREP-STOP`

## Decision

Open the next controlled DARS queue-refill line and authorize a bounded
multi-critic panel path as the selected queue-refill candidate.

This decision supersedes the `QUEUE-REFILL-PREP-STOP` block only for the
following controlled path:

```text
DARS-CODEX-CLI-SUBPROCESS-MULTI-CRITIC-PANEL-PREP
```

## Allowed next increment

The immediate next increment is PREP/docs-control and local validation for a
Codex CLI subprocess prompt-mode multi-critic panel. It may prepare the exact
panel request shape, critic count, source execution identifiers, prompt packet
boundaries, runtime-boundary output paths, and validation checklist.

The PREP row may use the existing local/injected-executor panel dispatch harness
as an anchor:

```text
run_dars_remote_subscription_panel_dispatch(...)
```

It may also bind the already prepared single-critic Codex CLI subprocess executor
as the future live executor shape, while preserving all fail-closed guards from
`DARS-CODEX-CLI-SUBPROCESS-FAILURE-MODE-FIXTURE-PREP`.

## Not yet claimed

This authorization record does not itself prove or claim:

- a multi-critic panel has run;
- repeated Codex subprocess calls have occurred;
- broad DARS completion;
- provider-account configuration;
- credential lookup or vault resolution;
- web search, browser/tool use, workspace-write, mutation, publication,
  deployment, release, PR/issue creation, or autonomous decision authority.

## Boundary for any later live panel run

A later live panel run must preserve:

- `provider_id=codex`;
- `adapter_class=codex_subscription`;
- `transport_kind=codex_cli_subprocess_prompt_mode` for each critic request;
- panel aggregate `transport_kind=injected_subscription_executor_panel`;
- advisory-only actions;
- read-only Codex CLI sandbox where available;
- no web search, browser, shell/tool delegation, publication, deployment,
  mutation, PR/issue creation, or claim-upgrade authority;
- `requires_human_review=true` in per-critic and aggregate boundary records;
- no credential lookup or raw secret handling by Hisys;
- runtime-boundary JSON/Markdown records under the governed instance root.

## Queue-refill candidate selection

The selected candidate is multi-critic panel preparation because the immediately
prior queue row closed local failure-mode fixture coverage, the single-smoke
evidence has already been reviewed, and the operator explicitly approved the
multi-critic panel line.

Other previously blocked candidates remain blocked unless separately authorized:

- live LSP execution / executable allowlist expansion;
- M25 or new product-scope milestone opening;
- Section 10.3 dormant branch alignment;
- real OSS comparison / license adjudication live execution.

## Next safe task

```text
DARS-CODEX-CLI-SUBPROCESS-MULTI-CRITIC-PANEL-PREP
```
