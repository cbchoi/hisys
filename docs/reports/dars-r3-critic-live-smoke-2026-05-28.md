# DARS R3 critic live smoke report — 2026-05-28

## Conclusion

A single R3 critic live smoke was executed once through the governed Codex CLI subprocess prompt-mode path after the operator approval `R3 smoke 승인`.

This is runtime-boundary evidence for one bounded advisory critic smoke crossing a model boundary. It is not a raw provider API readiness claim, not a multi-critic panel claim, not bounded unattended operation, not release readiness, and not controlled release.

## Execution identity

- Recorded at: `2026-05-28T18:33:58+0900`
- Repository branch before smoke: `## main...origin/main`
- Repository HEAD before smoke: `6ba9deb docs: record dars panel closure gate`
- Instance root: `/tmp/hisys-r3-critic-live-smoke-20260528-183358`
- Request ID: `REQ-DARS-R3-CRITIC-LIVE-SMOKE-20260528-001`
- Source execution ID: `EXEC-DARS-R3-CRITIC-LIVE-SMOKE-20260528-001`
- Approval ref: `APPROVAL-DARS-R3-SMOKE-20260528-DISCORD-USER-R3-SMOKE-APPROVED`
- Provider ID: `codex`
- Adapter class: `codex_subscription`
- Transport kind: `codex_cli_subprocess_prompt_mode`
- Backend ID: `codex_subscription_dars_critic`

## Preflight evidence

- `command -v codex`: `/usr/bin/codex`
- `codex --version`: `codex-cli 0.134.0`
- Focused governance/Codex/dispatch cohort:
  `PYTHONPATH=src:. pytest tests/unit/test_dars_codex_cli_subprocess.py tests/unit/test_dars_remote_subscription_dispatch.py tests/unit/test_dars_remote_subscription_policy.py tests/unit/test_dars_backend_activation.py -q` → `88 passed`
- Traceability validator: `OK`
- Secret scan before smoke: `hit_count=0`
- `git diff --check`: clean before report write
- Fresh policy packet: `/tmp/hisys-r3-critic-live-smoke-20260528-183358/decision-packet/policy.json`
- Fresh activation packet: `/tmp/hisys-r3-critic-live-smoke-20260528-183358/decision-packet/activation.json`
- Policy/activation expiry: `2026-06-28T23:59:00Z`

## Execution notes

The first attempt stopped before the Codex subprocess could run because Codex CLI rejected an untrusted temporary work directory and required `--skip-git-repo-check`. The governed executor does not use that bypass flag, so the attempt was abandoned without a runtime-boundary record.

The successful attempt used the governed Hisys wrapper around Codex CLI prompt mode with the Hisys repository as the read-only `--cd` workdir. Hisys did not read provider credentials, account material, Authorization headers, or provider SDK/API configuration. Codex CLI local authentication remained operator-managed outside Hisys.

## Runtime-boundary evidence

Runtime-boundary JSON:

```text
/tmp/hisys-r3-critic-live-smoke-20260528-183358/runtime-boundary/dars-remote-subscriptions/20260528/REQ-DARS-R3-CRITIC-LIVE-SMOKE-20260528-001/codex_subscription_dars_critic-EXEC-DARS-R3-CRITIC-LIVE-SMOKE-20260528-001.json
```

Runtime-boundary Markdown:

```text
/tmp/hisys-r3-critic-live-smoke-20260528-183358/runtime-boundary/dars-remote-subscriptions/20260528/REQ-DARS-R3-CRITIC-LIVE-SMOKE-20260528-001/codex_subscription_dars_critic-EXEC-DARS-R3-CRITIC-LIVE-SMOKE-20260528-001.md
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
  "allowed_actions": "advisory_only",
  "transport_kind": "codex_cli_subprocess_prompt_mode",
  "provider_id": "codex",
  "adapter_class": "codex_subscription"
}
```

The runtime-boundary schema is `hisys.dars.remote_subscription_dispatch`, not `hisys.dars.live_provider_adapter`. The R2 live-provider adapter still has no raw-provider transport and remains fail-closed. This report therefore records the approved Codex subscription subprocess path as the R3 critic live smoke evidence while preserving the distinction from a raw provider API transport.

## Critic output preview

```text
Risk

Main risk is overclaiming. The packet is suitable for a narrow live-smoke evidence claim, but not for release, unattended operation, credential handling, raw provider API behavior, or multi-critic orchestration.

Secondary risk is audit ambiguity: the evidence must clearly show that no mutation, publication, deployment, browser, web search, shell, or downstream action occurred.

Evidence Sufficiency

Sufficient for the narrow claim if the runtime-boundary record captures external_call_made=true, model_boundary_crossed=true, mutation_performed=false, publication_performed=false, requires_human_review=true, transport_kind=codex_cli_subprocess_prompt_mode, and request/execution/approval identifiers linking this smoke to the approved boundary.

It is not sufficient for broader DARS readiness claims.

Recommendation

Accept the evidence only as a bounded R3 single-critic Codex subscription live-smoke record. Keep it advisory-only and preserve the human-review boundary.
```

## Boundaries preserved

- Exactly one successful Codex subprocess model-boundary call was made.
- No Codex SDK import occurred.
- No raw provider API call from Hisys occurred.
- No credential lookup by Hisys occurred.
- No raw secret, token value, Authorization header, or provider account identifier was recorded in the policy, activation, report, or runtime-boundary evidence.
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
raw_provider_api_readiness
adapter_native_readiness
```

The next safe row is a review/gate row that inspects this report and runtime-boundary evidence, then decides whether to record the claim-ladder transition to `live_provider_advisory_smoked` or keep the narrower Codex-subprocess claim boundary.
