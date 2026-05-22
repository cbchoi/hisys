# DARS Codex CLI subprocess multi-critic evidence-packet smoke — 2026-05-22

A bounded two-critic Codex CLI subprocess prompt-mode panel was executed through the prepared evidence-bearing packet after explicit operator approval. The run used only `docs/examples/dars/codex-cli-subprocess-multi-critic-panel.evidence-prep.json` as the evidence-prep packet and preserved the advisory-only/no-mutation/no-publication/no-tool/search/browser boundary.

## Execution identity

- Row: `DARS-CODEX-CLI-SUBPROCESS-MULTI-CRITIC-EVIDENCE-PACKET-SMOKE-GATE`
- Request ID: `REQ-DARS-CODEX-PANEL-EVIDENCE-20260522-001`
- Panel ID: `PANEL-DARS-CODEX-SUBPROCESS-EVIDENCE-20260522-001`
- Provider: `codex`
- Adapter class: `codex_subscription`
- Per-critic transport: `codex_cli_subprocess_prompt_mode`
- Panel transport: `injected_subscription_executor_panel`
- Instance root: `/tmp/hisys-dars-codex-evidence-panel-smoke`

## Runtime-boundary evidence

- Aggregate: `/tmp/hisys-dars-codex-evidence-panel-smoke/runtime-boundary/dars-remote-subscription-panels/20260522/REQ-DARS-CODEX-PANEL-EVIDENCE-20260522-001/PANEL-DARS-CODEX-SUBPROCESS-EVIDENCE-20260522-001.json`
- Logical critic: `/tmp/hisys-dars-codex-evidence-panel-smoke/runtime-boundary/dars-remote-subscriptions/20260522/REQ-DARS-CODEX-PANEL-EVIDENCE-20260522-001/codex_subscription_dars_critic-EXEC-DARS-CODEX-PANEL-EVIDENCE-LOGICAL-20260522-001.json`
- Evidence-governance critic: `/tmp/hisys-dars-codex-evidence-panel-smoke/runtime-boundary/dars-remote-subscriptions/20260522/REQ-DARS-CODEX-PANEL-EVIDENCE-20260522-001/codex_subscription_dars_critic-EXEC-DARS-CODEX-PANEL-EVIDENCE-GOVERNANCE-20260522-001.json`

The aggregate record contains:

```text
critic_count=2
completed_critic_count=2
external_call_made=true
model_boundary_crossed=true
local_model_call_made=false
mutation_performed=false
publication_performed=false
requires_human_review=true
allowed_actions=advisory_only
```

## Critic previews

Logical-consistency critic preview:

```text
Advisory findings:

1. Claim mostly follows from the evidence summary.
   The evidence states `critic_count: 2` and `completed_critic_count: 2`, which supports the claim that a bounded two-critic panel completed.

2. “Produced findings” is supported.
   The `known_findings` field lists findings from both critics, including one logical-consistency finding and one evidence-governance finding.

3. “Not a no-issue continuation” is supported.
```

Evidence-governance critic preview:

```text
Advisory findings:

1. Boundary preservation appears intact for the bounded claim.
   The packet keeps the claim scoped to panel completion with findings, not system completion or no-issue continuation.

2. Human review remains correctly required.
   `requires_human_review: true` is present in both the bounded claim and evidence summary, and no completion-claim upgrade is requested.

3. Mutation and publication boundaries appear preserved.
```

## Boundary statement

No Codex SDK import, raw provider API call from Hisys, credential lookup, vault resolution, raw token/key/header handling, provider account configuration, web search flag, browser/tool authority, workspace-write by Codex, publication, deployment, PR/issue/release, or DARS completion-claim upgrade occurred. The subprocess call was bounded to Codex CLI prompt mode with read-only sandbox and advisory prompt text.

## Review outcome

The evidence supports only the bounded smoke result:

```text
codex_cli_subprocess_multi_critic_evidence_packet_smoke_completed
```

The result remains advisory and human-review-required. It is not a DARS completion-claim upgrade.
