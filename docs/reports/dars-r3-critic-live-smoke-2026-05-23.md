# DARS R3 critic live smoke report — 2026-05-23

## Conclusion

A single R3 critic live smoke was executed once through the governed Codex CLI subprocess prompt-mode path after the operator instruction `go for R3 critic live smoke`.

This is accepted as runtime-boundary evidence for one bounded advisory critic smoke crossing a model boundary. It is **not** a broad DARS completion upgrade, not an R4 multi-critic panel, not R5 unattended operation, and not release readiness.

## Execution identity

- Recorded at: `2026-05-23T13:59:51Z`
- Repository branch before smoke: `## dars...origin/dars`
- Repository HEAD before smoke: `47bb94f docs: record dars r3 r5 live evidence preflight stop`
- Instance root: `/tmp/hisys-r3-critic-live-smoke-20260523`
- Request ID: `REQ-DARS-R3-CRITIC-LIVE-SMOKE-20260523-001`
- Source execution ID: `EXEC-DARS-R3-CRITIC-LIVE-SMOKE-20260523-001`
- Approval ref: `APPROVAL-DARS-R3-CRITIC-LIVE-SMOKE-20260523-USER-GO`
- Provider ID: `codex`
- Adapter class: `codex_subscription`
- Transport kind: `codex_cli_subprocess_prompt_mode`
- Backend ID: `codex_subscription_dars_critic`

## Preflight evidence

- `command -v codex`: `/usr/bin/codex`
- `codex --version`: `codex-cli 0.128.0`
- Focused governance/Codex/dispatch cohort:
  `PYTHONPATH=src:. pytest tests/unit/test_dars_codex_cli_subprocess.py tests/unit/test_dars_remote_subscription_dispatch.py tests/unit/test_dars_remote_subscription_policy.py tests/unit/test_dars_backend_activation.py -q` → `88 passed`
- Traceability validator: `OK`
- Secret scan before smoke: `hit_count=0`
- `git diff --check`: clean
- Fresh policy packet: `/tmp/hisys-r3-critic-live-smoke-20260523/decision-packet/policy.json`
- Fresh activation packet: `/tmp/hisys-r3-critic-live-smoke-20260523/decision-packet/activation.json`
- Policy/activation expiry: `2026-06-23T23:59:00Z`

## Execution notes

Two initial attempts stopped before subprocess spawn because the redaction guard rejected the prompt string as `codex_cli_prompt_not_redacted`. The false-positive collision came from forbidden marker text in the prompt wording. The prompt was narrowed and rerun. No model/provider call was made until the final successful attempt.

The final successful path used the governed Hisys wrapper around Codex CLI prompt mode. Hisys did not read provider credentials, API keys, provider account configuration, or Authorization material. Codex CLI local authentication remained operator-managed outside Hisys.

## Runtime-boundary evidence

Runtime-boundary JSON:

```text
/tmp/hisys-r3-critic-live-smoke-20260523/runtime-boundary/dars-remote-subscriptions/20260523/REQ-DARS-R3-CRITIC-LIVE-SMOKE-20260523-001/codex_subscription_dars_critic-EXEC-DARS-R3-CRITIC-LIVE-SMOKE-20260523-001.json
```

Runtime-boundary Markdown:

```text
/tmp/hisys-r3-critic-live-smoke-20260523/runtime-boundary/dars-remote-subscriptions/20260523/REQ-DARS-R3-CRITIC-LIVE-SMOKE-20260523-001/codex_subscription_dars_critic-EXEC-DARS-R3-CRITIC-LIVE-SMOKE-20260523-001.md
```

Observed boundary fields:

```json
{
  "external_call_made": true,
  "model_boundary_crossed": true,
  "local_model_call_made": false,
  "mutation_performed": false,
  "publication_performed": false,
  "requires_human_review": true,
  "transport_kind": "codex_cli_subprocess_prompt_mode",
  "allowed_actions": "advisory_only"
}
```

The runtime-boundary schema is `hisys.dars.remote_subscription_dispatch`, not `hisys.dars.live_provider_adapter`. The R2 live-provider adapter still has no raw-provider transport and remains fail-closed. This report therefore records the approved Codex subscription subprocess path as the R3 critic live smoke evidence, while preserving the distinction from a raw provider API transport.

## Critic output preview

```text
Risk:
Low to moderate. The smoke exercises the governed Codex CLI subprocess prompt-mode path, but it still crosses an external model boundary, so auditability depends on wrapper enforcement and evidence capture.

Evidence sufficiency:
Sufficient for a bounded live smoke critique if the recorded evidence includes the exact command contract, boundary fields, clean branch state, and confirmation that no raw provider transport was invoked.

Recommendation:
Accept as advisory smoke evidence only. Preserve `requires_human_review=true`, keep fail-closed raw transport behavior, and require human review before treating this as completion or production readiness.

Claim boundary:
Do not upgrade the completion claim. This supports only that the governed Codex CLI subprocess prompt-mode advisory path was exercised under the stated constraints.
```

## Boundaries preserved

- Exactly one successful Codex subprocess model-boundary call was made.
- No Codex SDK import occurred.
- No raw provider API call from Hisys occurred.
- No credential lookup by Hisys occurred.
- No raw secret, token, Authorization header, or provider account identifier was recorded in the policy, activation, report, or runtime-boundary evidence.
- No web search, browser, shell tool grant, workspace-write authority, publication, deployment, PR/issue creation, release, or downstream action authority was requested.
- `mutation_performed=false`, `publication_performed=false`, and `requires_human_review=true` are preserved.
- Repository status after smoke remained clean before this report was written.

## Review decision

The smoke evidence supports this narrow claim:

```text
r3_single_critic_codex_subscription_live_smoke_evidence_captured
```

It does not by itself support:

```text
multi_critic_live_provider_advisory_complete
bounded_unattended_advisory_operation_ready
release_candidate_ready
released_for_controlled_advisory_use
```

The next safe row is a review/gate row that inspects this report and runtime-boundary evidence, then decides whether to record the claim-ladder transition to `live_provider_advisory_smoked` or keep the narrower Codex-subprocess claim boundary.
