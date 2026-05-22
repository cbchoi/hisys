# Readiness Decision Record v0.0.58 — Codex CLI subprocess multi-critic panel PREP

- **Decision ID:** `DARS-CODEX-CLI-SUBPROCESS-MULTI-CRITIC-PANEL-PREP-20260522`
- **Recorded at:** `2026-05-22T14:44:00Z`
- **Operator instruction:** `DARS-CODEX-CLI-SUBPROCESS-MULTI-CRITIC-PANEL-PREP`
- **Baseline HEAD:** `2cc946a docs: authorize codex multi-critic panel prep`
- **Previous profile:** `v0.0.57`
- **Previous next row:** `DARS-CODEX-CLI-SUBPROCESS-MULTI-CRITIC-PANEL-PREP`

## Decision

The PREP row is completed as a controlled local specification and fixture-backed
contract for a later bounded multi-critic panel smoke.

The prepared panel packet is:

```text
docs/examples/dars/codex-cli-subprocess-multi-critic-panel.prepared.json
```

The packet defines:

- `request_id=REQ-DARS-CODEX-PANEL-SMOKE-20260522-001`;
- `panel_id=PANEL-DARS-CODEX-SUBPROCESS-20260522-001`;
- `yyyymmdd=20260522`;
- two unique critic `source_execution_id` values;
- per-critic `transport_kind=codex_cli_subprocess_prompt_mode`;
- per-critic `allowed_actions=advisory_only`;
- `mutation_performed=false`;
- `publication_performed=false`;
- `requires_human_review=true`;
- an aggregate panel boundary path under
  `runtime-boundary/dars-remote-subscription-panels/20260522/REQ-DARS-CODEX-PANEL-SMOKE-20260522-001`.

## RED/GREEN evidence

A contract test was added before the packet existed:

```text
tests/unit/test_dars_remote_subscription_dispatch.py::test_codex_cli_subprocess_multi_critic_panel_prep_packet_matches_dispatch_contract
```

RED observed:

```text
FileNotFoundError: docs/examples/dars/codex-cli-subprocess-multi-critic-panel.prepared.json
```

GREEN observed after adding the packet:

```text
1 passed
```

The test runs the prepared packet through the existing
`run_dars_remote_subscription_panel_dispatch(...)` harness with a fake Codex CLI
executor and verifies the per-critic and aggregate boundary contract without
launching `/usr/bin/codex`.

## Claim boundary

Accepted claim:

```text
codex_cli_subprocess_multi_critic_panel_prep_complete
```

Not accepted or claimed:

- live multi-critic panel execution;
- repeated Codex subprocess calls;
- broad DARS completion;
- web access, shell/tool delegation, workspace-write, mutation, publication,
  deployment, PR/issue creation, release, provider-account setup, or automatic
  claim upgrade.

## Next safe task

```text
DARS-CODEX-CLI-SUBPROCESS-MULTI-CRITIC-PANEL-SMOKE-GATE
```

The smoke gate may run only the explicitly prepared bounded panel after immediate
preflight confirms a clean repository state, valid policy/activation packet
status, clean secret scan, Codex CLI availability, read-only sandbox command
shape, and no requested authority beyond advisory critique.
