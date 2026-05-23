# DARS R3 ACTION decision packet — mapped subscription bridge — 2026-05-23

## Decision

Chosen bridge path:

```text
mapped_subscription
```

Accepted bounded claim:

```text
r3_mapped_subscription_transport_live_smoke_ready_for_human_review
```

This decision maps the already reviewed Codex subscription subprocess prompt-mode smoke into the R3 live-release claim ladder as **subscription-transport live smoke evidence**. It does not claim raw-provider API readiness and does not claim that the R2 `hisys.dars.live_provider_adapter` has executed an approved real-provider transport.

## Request context

- Prior operator instruction: `go for live release`
- Current operator instruction: `mapped로 가자`
- Decision packet time: `2026-05-23T22:22:51Z`
- Repository branch: `dars`
- Baseline before this packet: `7ced5fa docs: record dars r3 action transport prep`

## Evidence scope

Reviewed evidence refs:

- `docs/reports/dars-r3-critic-live-smoke-2026-05-23.md`
- `docs/reports/dars-r3-critic-live-smoke-review-gate-2026-05-23.md`
- `docs/reports/dars-r3-action-transport-prep-2026-05-23.md`
- `/tmp/hisys-r3-critic-live-smoke-20260523/runtime-boundary/dars-remote-subscriptions/20260523/REQ-DARS-R3-CRITIC-LIVE-SMOKE-20260523-001/codex_subscription_dars_critic-EXEC-DARS-R3-CRITIC-LIVE-SMOKE-20260523-001.json`

Reviewed boundary fields from the accepted R3 smoke:

```text
schema_id=hisys.dars.remote_subscription_dispatch
adapter_class=codex_subscription
provider_id=codex
transport_kind=codex_cli_subprocess_prompt_mode
external_call_made=true
model_boundary_crossed=true
local_model_call_made=false
mutation_performed=false
publication_performed=false
requires_human_review=true
allowed_actions=advisory_only
```

## Schema and claim mapping

This packet explicitly records the schema mismatch:

```text
actual_schema_id=hisys.dars.remote_subscription_dispatch
actual_adapter_class=codex_subscription
actual_transport_kind=codex_cli_subprocess_prompt_mode
not_schema_id=hisys.dars.live_provider_adapter
not_raw_provider_api_transport=true
```

The mapping is accepted only under this claim boundary:

```text
live_provider_advisory_smoked
scope=codex_subscription_subprocess_transport_only
raw_provider_api_readiness=false
adapter_native_readiness=false
human_review_required=true
advisory_only=true
```

For traceability, the preferred narrow claim name is:

```text
r3_mapped_subscription_transport_live_smoke_ready_for_human_review
```

## Non-goals and blocked claims

This packet does not authorize or accept:

- raw provider API transport readiness;
- `adapter_native` readiness;
- another provider/model call;
- Codex subprocess re-execution;
- credential lookup or secret resolution;
- R4 multi-critic action;
- R5 unattended canary/action;
- R7 release-candidate readiness;
- R8 release execution;
- tag/package/deploy/publication/external notification;
- mutation authority;
- removal of `requires_human_review=true`.

## Decision rationale

`mapped_subscription` is selected because the repository already contains reviewed runtime-boundary evidence for a governed Codex subscription subprocess prompt-mode advisory smoke. That evidence crossed a model boundary, preserved advisory-only/no-mutation/no-publication fields, and passed the R3 smoke review gate.

`adapter_native` remains the cleaner long-term architecture for raw-provider/live-provider-adapter readiness, but it would require a new approved real-provider transport, credential-reference configuration, and additional live evidence. That scope is not needed to progress the current controlled advisory release lane if the claim is limited to subscription-transport live smoke.

## Next safe row

```text
DARS-LIVE-RELEASE-R4-PANEL-MAPPED-SUBSCRIPTION-PREP
```

That row should prepare a multi-critic mapped-subscription panel packet and stop before any additional Codex/provider execution unless exact scoped human approval is recorded for the calls.
