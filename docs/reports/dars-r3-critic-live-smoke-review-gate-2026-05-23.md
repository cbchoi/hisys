# DARS R3 critic live smoke review gate — 2026-05-23

## Review conclusion

The R3 critic live-smoke evidence is accepted only for the narrow reviewed claim:

```text
r3_codex_subscription_single_critic_smoke_review_accepted
```

The evidence shows exactly one governed Codex CLI subprocess prompt-mode advisory critic boundary crossing through the remote-subscription dispatch path, with advisory-only, no-mutation, no-publication, and human-review-required fields preserved.

This review does **not** upgrade the claim to `live_provider_advisory_smoked`, because the recorded schema is `hisys.dars.remote_subscription_dispatch` and the adapter class is `codex_subscription`, not the R2 `hisys.dars.live_provider_adapter` raw-provider path. The R2 live-provider adapter remains fail-closed for unapproved real-provider transport.

This review also does not approve repeated provider calls, R4 multi-critic execution, R5 unattended ACTION, release-candidate readiness, workspace-write authority, web/search authority, deployment, publication, PR/issue creation, release, provider-account action, credential lookup, or automatic acceptance of advisory output.

## Evidence reviewed

- Review time: `2026-05-23T14:15:31Z`
- Repository HEAD reviewed: `8f50b55 docs: capture dars r3 critic live smoke`
- Smoke report: `docs/reports/dars-r3-critic-live-smoke-2026-05-23.md`
- Runtime-boundary JSON:
  `/tmp/hisys-r3-critic-live-smoke-20260523/runtime-boundary/dars-remote-subscriptions/20260523/REQ-DARS-R3-CRITIC-LIVE-SMOKE-20260523-001/codex_subscription_dars_critic-EXEC-DARS-R3-CRITIC-LIVE-SMOKE-20260523-001.json`
- Runtime-boundary Markdown:
  `/tmp/hisys-r3-critic-live-smoke-20260523/runtime-boundary/dars-remote-subscriptions/20260523/REQ-DARS-R3-CRITIC-LIVE-SMOKE-20260523-001/codex_subscription_dars_critic-EXEC-DARS-R3-CRITIC-LIVE-SMOKE-20260523-001.md`
- Policy packet: `/tmp/hisys-r3-critic-live-smoke-20260523/decision-packet/policy.json`
- Activation packet: `/tmp/hisys-r3-critic-live-smoke-20260523/decision-packet/activation.json`

## Boundary fields accepted

The runtime-boundary JSON and Markdown record these accepted fields:

```json
{
  "external_call_made": true,
  "model_boundary_crossed": true,
  "local_model_call_made": false,
  "mutation_performed": false,
  "publication_performed": false,
  "requires_human_review": true,
  "transport_kind": "codex_cli_subprocess_prompt_mode",
  "provider_id": "codex",
  "adapter_class": "codex_subscription",
  "backend_id": "codex_subscription_dars_critic",
  "allowed_actions": "advisory_only",
  "schema_id": "hisys.dars.remote_subscription_dispatch"
}
```

A local review script checked these values against the expected review-gate criteria and returned `boundary_review=PASS`. The same check found no secret/token/authorization/API-key/password-shaped top-level JSON keys.

## Evidence sufficiency assessment

Accepted for:

- confirming one operator-authorized Codex subscription subprocess advisory smoke crossed the model boundary;
- confirming the runtime-boundary record preserved `external_call_made=true` and `model_boundary_crossed=true` for that one dispatch;
- confirming advisory-only/no-mutation/no-publication/human-review-required boundary fields;
- confirming the smoke evidence is sufficient for a reviewed Codex-subprocess R3 evidence checkpoint.

Not accepted for:

- `live_provider_advisory_smoked` as a raw-provider/live-provider-adapter claim;
- broad DARS completion;
- R4 multi-critic panel completion;
- R5 unattended ACTION readiness;
- release-candidate readiness or release completion;
- repeated provider execution;
- workspace-write, browser/search/tool grants, publication, deployment, PR/issue creation, or release;
- credential lookup, provider-account management, vault resolution, or raw secret handling;
- treating the critic text as an automatically accepted decision.

## Claim boundary after review

The narrow reviewed claim is:

```text
Hisys has one accepted runtime-boundary evidence record for an R3 governed Codex subscription single-critic advisory smoke, with advisory-only/no-mutation/no-publication fields preserved and human review required.
```

The broader current claim remains:

```text
local_fixture_localhost_controlled_advisory_complete
+
r3_codex_subscription_single_critic_smoke_review_accepted
```

This is intentionally below `live_provider_advisory_smoked` until a separate governed path either implements an approved R3 live-provider adapter transport or formally maps the Codex subscription subprocess path into the controlled live-provider claim ladder with explicit human approval.

## Next safe row

```text
DARS-LIVE-RELEASE-R3-ACTION-TRANSPORT-PREP
```

This row should remain preparation-only unless a later explicit approval authorizes a specific live action. It should define how R3 evidence can satisfy the live-provider claim ladder without confusing the Codex subscription subprocess path with a raw provider API transport. It must not invoke Codex, raw provider APIs, credential lookup, R4, R5 ACTION, or release work.
