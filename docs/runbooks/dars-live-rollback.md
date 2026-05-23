# DARS Live Rollback Runbook

Traceability: HISYS-FR-DARS-CP-014 / HISYS-T-DARS-CP-016 / DARS-LIVE-RELEASE-R6-STATUS-ROLLBACK.

This runbook defines rollback readiness for DARS live/unattended advisory operation. It is a local operations guide and does not authorize credential access, provider calls, scheduler mutation by Hermes, release publication, deployment, external notification, or destructive Git actions.

## Preconditions

Rollback requires human review and an operator who controls the live runtime environment. Hermes/Hisys may report local state and generate refs, but the operator performs any live disablement, credential rotation, scheduler stop, or provider-console action outside Hisys.

## Rollback readiness sequence

1. **revoke standing approval**
   - Mark the standing approval policy revoked in the governed approval system or remove it from the scheduler's approved policy set.
   - Preserve a decision/ref that states who revoked it and when.

2. **disable provider policy**
   - Disable the provider policy or remove it from the allowlisted policy refs used by the live runner.
   - Do not delete audit ledgers or boundary records.

3. **rotate credential outside Hisys**
   - If credential exposure or misuse is suspected, rotate the provider credential in the external secret manager or provider console.
   - Do not paste old or new credential values into Hisys docs, status reports, tickets, prompts, or boundary records.

4. **stop scheduler outside Hisys**
   - Stop the external scheduler, cron job, CI workflow, or service that launches unattended DARS runs.
   - The exact command depends on the deployment target and must be approved by the operator who owns that runtime.

5. **verify no further runs**
   - Run `hisys dars-live-status` for the current date and inspect `latest_boundary_refs` and `failed_run_count`.
   - Confirm no new boundary records appear after the rollback timestamp.
   - Confirm `standing_approval_activated=false` in status reports generated after rollback.

## Local status command after rollback

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
  --format markdown
```

## Evidence to retain

Retain:

- the rollback decision/ref;
- the status report generated before rollback if available;
- the status report generated after rollback;
- latest boundary refs reviewed by the operator;
- the kill-switch state ref;
- budget/circuit-breaker state refs;
- any provider-console or scheduler evidence kept outside Hisys.

## Stop conditions

Stop and request human review if any of these occur:

- rollback authority is unclear;
- standing approval cannot be revoked;
- provider policy cannot be disabled;
- credential rotation would require exposing credential values to Hisys;
- scheduler ownership is unclear;
- new boundary records continue after rollback;
- status or secret-scan validation fails.

## Claim boundary

Rollback readiness means the procedure and local status surface exist and can be reviewed. It does not mean a live rollback was executed. A live rollback execution requires a separate human-approved action record.
