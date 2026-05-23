# DARS Live Operations Status Runbook

Traceability: HISYS-FR-DARS-CP-014 / HISYS-T-DARS-CP-016 / DARS-LIVE-RELEASE-R6-STATUS-ROLLBACK.

This runbook defines the local DARS live/unattended operations status surface. It does not authorize live provider calls, credential lookup, standing approval activation, rollback execution, publication, deployment, external notification, or removal of human review.

## Status command

Use the local status surface to write JSON and Markdown reports under the selected Hisys instance root:

```bash
hisys dars-live-status \
  --instance "$HISYS_INSTANCE" \
  --date YYYYMMDD \
  --policy-ref docs/examples/dars/live-provider-panel-smoke.policy.example.json \
  --standing-approval-ref docs/examples/dars/unattended-standing-approval.example.json \
  --kill-switch-ref ops/dars-live-kill-switch.json \
  --budget-state-ref ops/dars-live-budget-state.json \
  --rollback-runbook-ref docs/runbooks/dars-live-rollback.md \
  --release-ref unreleased/dars-r6-local-safe \
  --format json
```

The command reports refs and bounded state only. It reads local JSON state files under the selected instance root, scans latest boundary refs under `runtime-boundary/dars-unattended-advisory/<YYYYMMDD>/`, and writes:

- `reports/run-summaries/<YYYYMMDD>/dars-live-status.json`
- `reports/run-summaries/<YYYYMMDD>/dars-live-status.md`

## Required fields

The status report must include:

- policy refs;
- standing approval ref and `standing_approval_activated=false`;
- kill-switch state;
- budget/circuit-breaker state;
- failed-run count;
- latest boundary refs;
- rollback runbook ref;
- release/version ref;
- boundary flags showing no external call, no credential lookup, no mutation, no publication, no live action authorization, and no standing approval activation.

## Kill-switch state

The kill-switch state file is local instance data. A typical file is:

```json
{
  "kill_switch_engaged": true,
  "reason": "operator pause"
}
```

If the file is missing or unreadable, the status surface treats the kill switch as engaged and reports `reason=kill_switch_file_missing`.

## Latest boundary refs

The status surface reports latest boundary refs, not raw boundary payloads. This preserves privacy and avoids copying provider output, prompts, debug fields, or secret-like values into the status report.

## evidence-retention and privacy

Keep status reports, audit ledgers, and boundary records under the controlled Hisys instance root. Retain them according to the standing approval policy's `audit_retention_ref`. Do not paste raw provider outputs, credentials, Authorization headers, tokens, key material, or unredacted prompt payloads into the runbook, status report, traceability matrix, or release notes.

## troubleshooting

| Symptom | Local check | Required action |
|---|---|---|
| Kill switch reports engaged | Inspect the local kill-switch state file | Keep live/unattended runs stopped until a human clears the condition |
| Latest boundary refs missing | Check the selected `--date` and instance root | Do not infer a successful live/unattended run without boundary evidence |
| Failed-run count is nonzero | Review referenced boundary records in the instance root | Perform human review before any further live/unattended action |
| Budget state unavailable | Check `--budget-state-ref` | Stop canary/release claims until budget/circuit-breaker state is available |
| Rollback runbook ref missing | Use `docs/runbooks/dars-live-rollback.md` | Do not claim release candidate readiness |

## Boundary

This R6 surface is local-safe. It can support later human review, rollback readiness, and release-candidate checks, but it does not itself make `bounded_unattended_advisory_operation_ready`, `release_candidate_ready`, or `released_for_controlled_advisory_use` true.
