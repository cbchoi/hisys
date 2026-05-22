# DARS Codex CLI subprocess multi-critic panel smoke report — 2026-05-22

## Summary

A bounded two-critic Codex CLI subprocess panel was executed through the prepared
remote-subscription panel dispatch harness after the operator requested bounded
panel execution and continuation only if no issue appears. The panel completed
and wrote runtime-boundary evidence under a governed temporary instance root.
The result is **completed with findings**, not a no-issue continuation.

## Execution identity

- Recorded at: `2026-05-22T14:54:04Z`
- Prior committed HEAD before smoke-gate edits: `680a52a test: prepare codex multi-critic panel packet`
- Instance root: `/tmp/hisys-dars-codex-panel-smoke`
- Request ID: `REQ-DARS-CODEX-PANEL-SMOKE-20260522-001`
- Panel ID: `PANEL-DARS-CODEX-SUBPROCESS-20260522-001`
- Critic source execution IDs:
  - `EXEC-DARS-CODEX-PANEL-LOGICAL-20260522-001`
  - `EXEC-DARS-CODEX-PANEL-EVIDENCE-20260522-001`
- Provider ID: `codex`
- Adapter class: `codex_subscription`
- Per-critic transport kind: `codex_cli_subprocess_prompt_mode`
- Aggregate transport kind: `injected_subscription_executor_panel`

## Preflight evidence

- Branch/upstream before execution: `dars` / `origin/dars`, clean.
- `command -v codex`: `/usr/bin/codex`
- `codex --version`: `codex-cli 0.128.0`
- Focused governance/Codex/dispatch cohort: `65 passed`
- Secret scan before execution: `hit_count=0`
- `git diff --check`: clean before execution.

## Fail-closed issue and local correction

The first panel attempt that reached Codex output failed closed with:

```text
codex_cli_output_not_redacted
```

The executor rejected benign governance vocabulary such as credential/secret/token
boundary language because the raw-secret detector treated generic words as secret
markers. The detector was narrowed to block explicit secret fields or raw-secret
value prefixes while allowing benign boundary statements. A new focused RED/GREEN
test pins this behavior:

```text
tests/unit/test_dars_codex_cli_subprocess.py::test_codex_cli_subprocess_allows_benign_governance_boundary_terms
```

Focused RED before correction: `1 failed` with `codex_cli_output_not_redacted`.
Focused GREEN after correction: `11 passed` for the benign-governance and
secret-like-output cohort.

## Runtime-boundary evidence

Panel runtime-boundary JSON:

```text
/tmp/hisys-dars-codex-panel-smoke/runtime-boundary/dars-remote-subscription-panels/20260522/REQ-DARS-CODEX-PANEL-SMOKE-20260522-001/PANEL-DARS-CODEX-SUBPROCESS-20260522-001.json
```

Per-critic runtime-boundary JSON:

```text
/tmp/hisys-dars-codex-panel-smoke/runtime-boundary/dars-remote-subscriptions/20260522/REQ-DARS-CODEX-PANEL-SMOKE-20260522-001/codex_subscription_dars_critic-EXEC-DARS-CODEX-PANEL-LOGICAL-20260522-001.json
/tmp/hisys-dars-codex-panel-smoke/runtime-boundary/dars-remote-subscriptions/20260522/REQ-DARS-CODEX-PANEL-SMOKE-20260522-001/codex_subscription_dars_critic-EXEC-DARS-CODEX-PANEL-EVIDENCE-20260522-001.json
```

Observed aggregate fields:

```json
{
  "critic_count": 2,
  "completed_critic_count": 2,
  "external_call_made": true,
  "model_boundary_crossed": true,
  "local_model_call_made": false,
  "mutation_performed": false,
  "publication_performed": false,
  "requires_human_review": true,
  "transport_kind": "injected_subscription_executor_panel"
}
```

## Advisory findings

The logical-consistency critic reported that the prepared panel packet did not
include the actual DARS panel claim or runtime-boundary evidence needed to judge
whether the claim follows from evidence. It advised preserving
`requires_human_review=true` and avoiding any completion or success claim upgrade.

The evidence-governance critic found the advisory-only, no-mutation,
no-publication, and no-tool/search/browser boundaries preserved in the packet.

## Review decision

This smoke gate does not authorize automatic continuation into a claim upgrade or
additional live provider execution. The panel completed with useful evidence but
also exposed an evidence-packet completeness issue. The next safe row is local
and bounded:

```text
DARS-CODEX-CLI-SUBPROCESS-MULTI-CRITIC-EVIDENCE-PACKET-PREP
```

That row should prepare a revised panel packet containing the bounded claim and
evidence summary before any further live panel execution. No additional Codex
subprocess, provider call, tool/search/browser authority, mutation, publication,
or DARS completion-claim upgrade is authorized by this report.
