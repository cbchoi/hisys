# Readiness decision record v0.0.76 — DARS R4 mapped subscription action packet

## Request context

- Operator instruction: `go`
- Time: `2026-05-24T01:59:23Z`
- Repository branch: `dars`
- Baseline before record: `f52b87c feat: configure dars mapped subscription panel`

## Decision

Record the R4 mapped-subscription action decision packet as ready for human review:

```text
r4_mapped_subscription_panel_action_packet_ready_for_human_review
```

The packet selects the R4 `mapped_subscription_panel` path and keeps the live action blocked. It authorizes only local docs/control/test updates and injected-executor harness preflight validation.

## Evidence scope

- `docs/reports/dars-r4-action-decision-packet-mapped-subscription-panel-2026-05-24.md`
- `docs/reports/dars-r3-action-decision-packet-mapped-subscription-2026-05-23.md`
- `examples/instance/config/dars.json`
- Focused remote-subscription panel harness tests: 4 passed

## Boundary

No live provider/model call, Codex subprocess call, raw provider API call, credential lookup, R4 live action, R5 action, release-candidate transition, deployment, publication, release action, external notification, mutation authority, or human-review removal is authorized by this record.

## Next safe task

```text
DARS-LIVE-RELEASE-R4-PANEL-MAPPED-SUBSCRIPTION-HARNESS-PREFLIGHT
```
