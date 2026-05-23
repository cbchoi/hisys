# DARS R3 action transport prep — 2026-05-23

## Prep conclusion

The latest operator instruction, `go for live release`, is treated as a release-intent signal, not as sufficient evidence to skip the claim ladder. The current governed state remains below `live_provider_advisory_smoked` because the accepted R3 evidence is a Codex subscription subprocess prompt-mode dispatch, not an R2 live-provider adapter raw-provider transport record.

This prep row defines the bridge condition for a future R3 ACTION claim and stops before any additional live provider/model call, credential lookup, R4/R5 action, release-candidate transition, deployment, package publication, tag push, or release publication.

## Current accepted evidence

Accepted narrow claim:

```text
r3_codex_subscription_single_critic_smoke_review_accepted
```

Evidence refs:

- `docs/reports/dars-r3-critic-live-smoke-2026-05-23.md`
- `docs/reports/dars-r3-critic-live-smoke-review-gate-2026-05-23.md`
- `/tmp/hisys-r3-critic-live-smoke-20260523/runtime-boundary/dars-remote-subscriptions/20260523/REQ-DARS-R3-CRITIC-LIVE-SMOKE-20260523-001/codex_subscription_dars_critic-EXEC-DARS-R3-CRITIC-LIVE-SMOKE-20260523-001.json`

Accepted boundary fields from the review gate:

```text
schema_id=hisys.dars.remote_subscription_dispatch
adapter_class=codex_subscription
provider_id=codex
transport_kind=codex_cli_subprocess_prompt_mode
external_call_made=true
model_boundary_crossed=true
mutation_performed=false
publication_performed=false
requires_human_review=true
allowed_actions=advisory_only
```

## Bridge rule

`live_provider_advisory_smoked` may be accepted only if a future decision packet chooses exactly one of these governed paths and records it explicitly:

1. **Adapter-native R3 ACTION path** — implement or configure an approved real-provider transport behind `hisys.dars.live_provider_adapter`, with credential-reference-only policy, activation-packet approval, redaction, budget/rate bounds, env gate, and a runtime-boundary record whose schema is `hisys.dars.live_provider_adapter` and whose transport is not fixture/fake.
2. **Explicit mapped-subscription path** — formally map the already reviewed Codex subscription subprocess transport into the R3 claim ladder through a controlled decision packet that names the schema mismatch, accepts that `codex_subscription` is the live boundary for this release line, and preserves the claim as subscription-transport live smoke rather than raw-provider API readiness.

Without one of these packeted choices, the system must not upgrade the claim from `r3_codex_subscription_single_critic_smoke_review_accepted` to `live_provider_advisory_smoked`.

## Required future decision packet fields

A future R3 ACTION decision packet must state:

- request context and exact operator approval phrase;
- chosen bridge path: `adapter_native` or `mapped_subscription`;
- provider, model/backend, transport kind, and schema id;
- credential reference scheme without resolving or storing secrets;
- policy packet ref, activation packet ref, and approval ref coherence;
- prompt class, redaction policy, max prompt/output bytes, rate limit, and cost budget ref;
- controlled instance root and boundary artifact destination;
- expected boundary fields: `external_call_made`, `model_boundary_crossed`, `mutation_performed=false`, `publication_performed=false`, `requires_human_review=true`, `allowed_actions=advisory_only`;
- review checklist and stop conditions;
- explicit non-goals: no R4, no R5 ACTION, no release candidate, no publication, no deployment, no removal of human review.

## Release gate effect

The release claim ladder is not skipped. The current state remains:

```text
local_fixture_localhost_controlled_advisory_complete
+
r3_codex_subscription_single_critic_smoke_review_accepted
```

The next claim remains blocked:

```text
live_provider_advisory_smoked = BLOCKED_PENDING_DECISION_PACKET_AND_BRIDGE_CHOICE
```

R4 multi-critic, R5 unattended canary, R7 release candidate, and R8 controlled release remain blocked until the R3 bridge is accepted and the corresponding reviewed evidence exists.

## Boundary preserved by this prep row

This prep row performed no live provider/model call, no Codex subprocess call, no raw provider API call, no credential lookup, no standing unattended approval activation, no R4/R5 action, no release-candidate transition, no tag/package/deploy/publication action, no external notification, no mutation outside repository docs/control/test files, and no removal of human review.

## Next safe row

```text
DARS-LIVE-RELEASE-R3-ACTION-DECISION-PACKET
```

That row should draft the packet selecting `adapter_native` or `mapped_subscription`. It must still stop before executing another provider/model call unless the packet records exact scoped human approval for that call.
