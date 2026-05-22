# DARS Codex CLI subprocess smoke review gate — 2026-05-22

## Review conclusion

The single-smoke evidence is accepted for a narrow claim:

```text
codex_cli_subprocess_single_smoke_review_accepted
```

The evidence shows that Hisys crossed the model boundary once through the
governed Codex CLI subprocess prompt-mode path and wrote runtime-boundary
evidence with advisory-only, no-mutation, and no-publication fields preserved.

This review does not upgrade the broader DARS completion claim and does not
approve repeated provider calls, multi-critic panels, web search, workspace-write,
publication, deployment, or provider-account actions.

## Evidence reviewed

- Review time: `2026-05-22T13:59:04Z`
- Repository HEAD reviewed: `9e28704 feat: capture codex cli subprocess smoke evidence`
- Smoke report: `docs/reports/dars-codex-cli-subprocess-single-smoke-2026-05-22.md`
- Smoke decision: `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.54.md`
- Runtime-boundary JSON:
  `/tmp/hisys-dars-codex-subscription/runtime-boundary/dars-remote-subscriptions/20260522/REQ-DARS-CODEX-SMOKE-20260522-001/codex_subscription_dars_critic-EXEC-DARS-CODEX-SMOKE-20260522-001.json`
- Runtime-boundary Markdown:
  `/tmp/hisys-dars-codex-subscription/runtime-boundary/dars-remote-subscriptions/20260522/REQ-DARS-CODEX-SMOKE-20260522-001/codex_subscription_dars_critic-EXEC-DARS-CODEX-SMOKE-20260522-001.md`

## Boundary fields accepted

The runtime-boundary JSON records:

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

The `provider_id`, `adapter_class`, and `backend` fields match the governed
subscription packet path:

```text
provider_id = codex
adapter_class = codex_subscription
backend_id = codex_subscription_dars_critic
backend_kind = codex_subscription
allowed_actions = advisory_only
```

## Evidence sufficiency assessment

Accepted for:

- proving one governed Codex CLI subprocess prompt-mode boundary crossing;
- proving the dispatch harness can write runtime-boundary JSON/Markdown for the
  Codex subscription path;
- proving the reviewed smoke preserved no-mutation and no-publication boundary
  fields;
- proving the corrected Codex CLI 0.128.0 command contract is the active path:
  `codex --ask-for-approval never exec --sandbox read-only --cd <dir> -- <prompt>`.

Not accepted for:

- broad DARS completion;
- repeated provider execution;
- multi-critic panel execution;
- live web search;
- workspace-write or broader sandbox modes;
- provider-account or credential management;
- publication, deployment, PR/issue creation, or release;
- treating advisory output as an automatically accepted decision.

## Observed advisory content

The smoke advisory itself identified remaining execution robustness risk:

```text
Risk: Prompt-mode behavior may still diverge under real subprocess edge cases such as timeout, partial output, or malformed advisory metadata.
Recommendation: Run a human-reviewed dry-run fixture that simulates timeout and malformed-output cases while confirming `requires_human_review` stays true.
```

The review accepts this as a relevant next engineering direction. It is a local
fixture/failure-mode follow-up and does not require another live Codex call.

## Claim boundary after review

The narrow reviewed claim is:

```text
Hisys has one accepted runtime-boundary evidence record for a governed Codex CLI
subprocess prompt-mode DARS critic smoke, with advisory-only/no-mutation/no-
publication fields preserved and human review required.
```

The broader completion claim remains below full live DARS/panel completion:

```text
local_fixture_localhost_controlled_advisory_complete
+
codex_cli_subprocess_single_smoke_review_accepted
```

## Next safe row

```text
DARS-CODEX-CLI-SUBPROCESS-FAILURE-MODE-FIXTURE-PREP
```

This row should prepare local fake-runner/failure-mode tests for timeout,
non-zero exit, blank output, malformed advisory metadata, and secret-like output
rejection. It must not run Codex again.
