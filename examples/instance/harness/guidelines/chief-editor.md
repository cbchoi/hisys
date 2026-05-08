# Chief Editor Harness Guideline

Traceability: HISYS-HARNESS-GUIDE-001, HISYS-FR-CE-001..006,
HISYS-CE-POLICY-001, HISYS-T-014, HISYS-T-015, HISYS-T-016, HISYS-T-017,
HISYS-T-018, HISYS-T-019, HISYS-T-020, HISYS-T-021, HISYS-T-022,
HISYS-T-025.

## Purpose

Validate that Chief Editor behavior can transform runtime-local memo review
outputs into auditable alert decisions without sending live alerts, writing to a
live Obsidian vault, or invoking external connectors.

## Inputs

Decision stage inputs:

- `data/memo-drafts/<YYYYMMDD>/*.json`
- `reports/run-summaries/<YYYYMMDD>/memo-review-report.json`

Action-plan and approval stage inputs:

- `data/alert-decisions/<YYYYMMDD>/*.json`

The harness stage uses reviewed `ZettelMemo` records only. It must not inspect
raw observation payloads directly.

## Procedure

1. Load runtime-local memo drafts for the run date.
2. Load the memo review report for the same run date.
3. Select the configured Chief Editor product from `config/chief-editor.yaml` or
   the CLI override:
   - `analysis_only`: record judgment only; no alert target/send candidate.
   - `alert_delivery_dry_run`: preserve alert-delivery dry-run candidate path.
4. Apply the fixture Chief Editor policy version
   `HISYS-CE-POLICY-001.fixture-v0`.
5. Convert `flagged_conflict` memos into pending `AlertDecisionRecord` records.
5. Convert `flagged_duplicate` memos into suppressed non-escalation decision
   records so suppression is auditable.
6. Before persisting a new escalation candidate, compare its `suppression_key`
   against same-date non-suppressed alert decisions already under
   `data/alert-decisions/<YYYYMMDD>/`.
7. Convert repeated same-date alert candidates into suppressed non-escalation
   decision records with `trigger_reason=suppression_window_duplicate_alert`.
8. For high/critical or non-local target alert candidates, set
   `approval_status=requested`, `status=needs_approval`, and `action_taken=none`.
9. Persist alert decisions under `data/alert-decisions/<YYYYMMDD>/` as JSON and
   Markdown.
10. Persist the run summary under
   `reports/run-summaries/<YYYYMMDD>/alert-decision-report.{json,md}`.
11. Read persisted alert decisions and write dry-run alert action plans under
    `data/alert-action-plans/<YYYYMMDD>/`.
12. For each action plan, record `live_delivery_permitted=false`,
    `action_taken=none`, and a blocked reason such as `approval_required`,
    `suppressed`, `no_target_channel`, or `live_delivery_disabled`.
13. Mark approved pending decisions with target channels as dry-run send
    candidates using `would_send=true`, but keep `live_delivery_permitted=false`
    and `blocked_reason=live_delivery_disabled`.
14. Persist the action-plan run summary under
    `reports/run-summaries/<YYYYMMDD>/alert-action-plan-report.{json,md}`.
15. For fixture approval review, accept only requested decisions with
    `approval_status=requested` and `status=needs_approval`.
16. Apply `approved` by changing `approval_status=approved`, `status=pending`,
    and preserving `action_taken=none`; apply `rejected` by changing
    `approval_status=rejected`, `status=closed`, and preserving
    `action_taken=none`.
17. Persist the approval transition summary under
    `reports/run-summaries/<YYYYMMDD>/alert-approval-transition-report.{json,md}`.
18. Read dry-run action plans through the disabled fixture connector harness and
    persist connector execution records under
    `data/alert-connector-executions/<YYYYMMDD>/` plus
    `reports/run-summaries/<YYYYMMDD>/alert-connector-execution-report.{json,md}`.
19. Connector execution records must keep `execution_status=blocked`,
    `live_delivery_permitted=false`, and `action_taken=none` even when
    `would_send=true`.
20. Do not send Discord messages, direct messages, software triggers, handoffs,
    or other live external actions in this harness stage.
21. For explicit live connector requests, write a runtime-boundary decision under
    `runtime-boundary/live-connectors/<YYYYMMDD>/` and keep the request blocked
    unless the connector is enabled, the requested action is allow-listed, and an
    approval reference is present; this baseline still performs no external call.

## Pass Criteria

- Every persisted alert decision is a valid `AlertDecisionRecord`.
- Conflict-triggered decisions preserve `memo_refs`, `signal_refs`, policy
  version, severity, confidence, suppression key, and follow-up guidance.
- Duplicate memo decisions are recorded as non-escalation decisions with
  `status=suppressed` and `action_taken=none`.
- Repeated same-date alert candidates with a previously persisted non-suppressed
  `suppression_key` are recorded as non-escalation decisions with
  `trigger_reason=suppression_window_duplicate_alert`, `status=suppressed`, and
  `action_taken=none`.
- High/critical sent or triggered actions are impossible without approval per
  the schema gate, and high/critical or non-local target candidates are persisted
  as approval requests with `approval_status=requested`, `status=needs_approval`,
  and `action_taken=none`.
- `analysis_only` product decisions keep `action_taken=none`, set
  `target_channel=null`, `approval_status=not_required`, and `status=closed` so
  downstream action planning records `would_send=false`/`no_target_channel`.
- `alert_delivery_dry_run` product decisions may enter approval/action-plan
  flow, but still cannot send because live delivery remains disabled.
- Dry-run action plans are valid JSON/Markdown artifacts, keep
  `live_delivery_permitted=false` and `action_taken=none`, and record an explicit
  blocked reason; approved pending target-channel candidates may set
  `would_send=true` but remain blocked by `live_delivery_disabled`.
- Approval transitions only mutate runtime-local alert decision artifacts and
  reports: approved decisions become `approval_status=approved`, `status=pending`,
  `action_taken=none`; rejected decisions become `approval_status=rejected`,
  `status=closed`, `action_taken=none`.
- Disabled connector execution records are valid JSON/Markdown artifacts,
  preserve `would_send` from the action plan, and keep `execution_status=blocked`,
  `live_delivery_permitted=false`, and `action_taken=none`.
- Live connector decisions are valid runtime-boundary Markdown artifacts and keep
  `execution_status=blocked`, `live_execution_permitted=false`,
  `external_call_made=false`, and `action_taken=none` unless connector/action/
  approval gates are explicitly satisfied in a future approved adapter increment.
- JSON and Markdown outputs are deterministic enough for regression tests.
- The CLI command `hisys decide-alerts --instance <root> --date <YYYYMMDD>`
  succeeds only when memo drafts and a memo review report are present.
- The CLI command `hisys plan-alert-actions --instance <root> --date <YYYYMMDD>`
  succeeds only when alert decisions are present.
- The CLI command `hisys review-alert-approval --instance <root> --date <YYYYMMDD>`
  succeeds only for requested approval decisions and never triggers delivery.

- The CLI command `hisys execute-alert-actions --instance <root> --date <YYYYMMDD>`
  succeeds only as a disabled connector harness and never sends live alerts.

## Non-goals

- Live alert delivery.
- Live Obsidian vault writes.
- Suppression windows across historical runs.
- Configurable suppression duration beyond the same-date fixture window.
- Human approval transition workflows beyond the fixture approve/reject stub.
- Discord/software connector execution.
- DARS handoff execution.
