# Readiness Decision Record v0.0.74 — DARS R3 mapped subscription bridge decision

## Decision

`r3_mapped_subscription_transport_live_smoke_ready_for_human_review`

## Request context

최창범 교수 instructed: `mapped로 가자`. This selects the `mapped_subscription` bridge path from the R3 action transport prep. The decision maps the already reviewed Codex subscription subprocess prompt-mode smoke into the live-release claim ladder with a bounded subscription-transport claim.

## Evidence scope

Reviewed and updated:

- `docs/reports/dars-r3-critic-live-smoke-2026-05-23.md`
- `docs/reports/dars-r3-critic-live-smoke-review-gate-2026-05-23.md`
- `docs/reports/dars-r3-action-transport-prep-2026-05-23.md`
- `docs/reports/dars-r3-action-decision-packet-mapped-subscription-2026-05-23.md`
- runtime-boundary JSON under `/tmp/hisys-r3-critic-live-smoke-20260523/runtime-boundary/dars-remote-subscriptions/20260523/REQ-DARS-R3-CRITIC-LIVE-SMOKE-20260523-001/`
- `docs/milestone-bootstrap/profile.yaml`
- `ralph.md`
- `docs/traceability/dars-critic-panel-runtime-traceability.md`
- `tests/unit/test_governance_docs_current_state.py`

## Validation status

This record is valid only after the commit containing it passes:

```bash
PYTHONPATH=src:. pytest tests/unit/test_governance_docs_current_state.py -q
PYTHONPATH=src:. pytest tests/unit -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

## Claim boundary

Accepted:

```text
r3_mapped_subscription_transport_live_smoke_ready_for_human_review
```

Mapped ladder claim, with explicit scope:

```text
live_provider_advisory_smoked
scope=codex_subscription_subprocess_transport_only
raw_provider_api_readiness=false
adapter_native_readiness=false
human_review_required=true
advisory_only=true
```

The accepted evidence records:

```text
schema_id=hisys.dars.remote_subscription_dispatch
adapter_class=codex_subscription
transport_kind=codex_cli_subprocess_prompt_mode
```

It does not record:

```text
schema_id=hisys.dars.live_provider_adapter
adapter_native_real_provider_transport=true
```

## Blockers preserved

No new live model/provider call, Codex subprocess call, raw provider API call, credential lookup, standing unattended approval activation, R4 multi-critic action, R5 ACTION, release-candidate transition, deployment, publication, external notification, destructive Git action, or human-review removal is authorized or performed by this decision packet.

## Next action

Run `DARS-LIVE-RELEASE-R4-PANEL-MAPPED-SUBSCRIPTION-PREP` to prepare the mapped-subscription panel path. Stop before any additional provider/model execution unless exact scoped approval is recorded for those calls.
