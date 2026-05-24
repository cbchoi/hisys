# DARS R4 ACTION decision packet — mapped subscription panel — 2026-05-24

## Decision

Chosen R4 path:

```text
mapped_subscription_panel
```

Accepted bounded prep claim:

```text
r4_mapped_subscription_panel_action_packet_ready_for_human_review
```

This decision packet records the operator instruction `go` after the named Hisys panel config prep. It authorizes only the local decision-packet and injected-executor harness-preflight scope described below. It does not authorize a new Codex subprocess panel execution, raw provider API call, credential lookup, R5 action, release-candidate transition, or release execution.

## Request context

- Prior operator instruction: `r4로 진행하는데 dars panel에 대한 config를 하드코딩하지 않고 hisys 설정에 추가해봐`
- Current operator instruction: `go`
- Decision packet time: `2026-05-24T01:59:23Z`
- Repository branch: `dars`
- Baseline before this packet: `f52b87c feat: configure dars mapped subscription panel`

## Evidence scope

Reviewed and accepted prerequisite refs:

- `docs/reports/dars-r3-action-decision-packet-mapped-subscription-2026-05-23.md`
- `docs/reports/dars-r3-critic-live-smoke-review-gate-2026-05-23.md`
- `docs/reports/dars-r4-action-decision-packet-mapped-subscription-panel-2026-05-24.md` (this packet)
- `examples/instance/config/dars.json` with `spec.panels.r4_mapped_subscription_panel`
- `docs/runbooks/dars-live-provider-panel-smoke.md`
- `docs/traceability/dars-critic-panel-runtime-traceability.md`

Focused harness preflight already passed in this session:

```bash
PYTHONPATH=src:. pytest \
  tests/unit/test_dars_remote_subscription_dispatch.py::test_remote_subscription_multi_critic_panel_dispatch_writes_aggregate_boundary \
  tests/unit/test_dars_remote_subscription_dispatch.py::test_remote_subscription_multi_critic_panel_rejects_mixed_request_ids_before_executor \
  tests/unit/test_dars_remote_subscription_dispatch.py::test_codex_cli_subprocess_multi_critic_panel_prep_packet_matches_dispatch_contract \
  tests/unit/test_dars_remote_subscription_dispatch.py::test_codex_cli_subprocess_multi_critic_evidence_packet_prep_includes_claim_and_evidence \
  -q
# 4 passed
```

## R4 action boundary

The accepted R3 bridge remains:

```text
live_provider_advisory_smoked
scope=codex_subscription_subprocess_transport_only
raw_provider_api_readiness=false
adapter_native_readiness=false
human_review_required=true
advisory_only=true
```

The R4 mapped-subscription panel path may use only this current safe scope:

```text
panel_config_source=hisys.dars.config:spec.panels.r4_mapped_subscription_panel
panel_transport_mapping=mapped_subscription
safe_execution_mode=injected_executor_harness_preflight_only
actual_live_call_performed=false
codex_subprocess_call=false
raw_provider_api_call=false
credential_lookup_performed=false
mutation_performed=false
publication_performed=false
requires_human_review=true
allowed_actions=advisory_only
```

If a later R4 live panel action is requested, a fresh exact scoped approval must name the panel id, request id, approval ref, credential-reference policy ref, cost-budget ref, redaction policy, prompt/output/rate caps, provider/model boundary, expected critic count, stop conditions, and post-run review owner before any live call is made.

## Non-goals and blocked claims

This packet does not authorize or accept:

- raw provider API transport readiness;
- `adapter_native` readiness;
- another provider/model call;
- Codex subprocess re-execution;
- credential lookup or secret resolution;
- R4 live multi-critic action;
- R5 unattended canary/action;
- R7 release-candidate readiness;
- R8 release execution;
- tag/package/deploy/publication/external notification;
- mutation authority;
- removal of `requires_human_review=true`.

## Decision rationale

The R4 panel can now be represented by a named Hisys config object rather than a sidecar JSON file. The injected-executor harness tests demonstrate that multi-critic panel boundary aggregation, request-id consistency checks, prep packet shape, and evidence packet shape remain coherent without invoking a live provider or Codex subprocess.

The live R4 panel action remains blocked because the current `go` instruction does not include the exact scoped live-call packet fields required for another model-boundary crossing.

## Next safe row

```text
DARS-LIVE-RELEASE-R4-PANEL-MAPPED-SUBSCRIPTION-HARNESS-PREFLIGHT
```

That row may record a local injected-executor harness preflight artifact and stop before any live Codex/provider execution unless a later packet records exact scoped approval for the specific live action.
