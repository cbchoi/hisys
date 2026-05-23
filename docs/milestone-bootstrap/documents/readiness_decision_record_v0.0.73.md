# Readiness Decision Record v0.0.73 — DARS R3 action transport prep

## Decision

`r3_action_transport_prep_complete`

## Request context

최창범 교수 instructed: `go for live release`. The instruction is recorded as release intent, but the controlled claim ladder still requires R3 bridge evidence before `live_provider_advisory_smoked`, R4, R5 ACTION, R7 release-candidate readiness, or R8 controlled release can proceed.

## Evidence scope

Reviewed and updated:

- `docs/reports/dars-r3-critic-live-smoke-2026-05-23.md`
- `docs/reports/dars-r3-critic-live-smoke-review-gate-2026-05-23.md`
- `docs/reports/dars-r3-action-transport-prep-2026-05-23.md`
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

This decision accepts only the preparation claim:

```text
r3_action_transport_prep_complete
```

It defines the two permissible bridge choices for future R3 ACTION evidence:

1. `adapter_native` — an approved real-provider transport behind `hisys.dars.live_provider_adapter` with live-provider-adapter boundary evidence.
2. `mapped_subscription` — an explicit decision-packet mapping of the reviewed Codex subscription subprocess transport into the claim ladder without claiming raw-provider API readiness.

The current accepted runtime evidence remains the narrower Codex subscription subprocess smoke review claim. It is not yet `live_provider_advisory_smoked`.

## Blockers preserved

No live model/provider call, Codex subprocess call, raw provider API call, credential lookup, standing unattended approval activation, R4 multi-critic action, R5 ACTION, release-candidate transition, deployment, publication, external notification, destructive Git action, or human-review removal is authorized or performed by this prep row.

## Next action

Run `DARS-LIVE-RELEASE-R3-ACTION-DECISION-PACKET` to draft the exact bridge-selection decision packet. Stop again before any new provider/model execution unless that packet records exact scoped human approval for the call.
