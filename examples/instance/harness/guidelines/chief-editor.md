# Chief Editor Harness Guideline

Traceability: HISYS-HARNESS-GUIDE-001, HISYS-FR-CE-001..006,
HISYS-CE-POLICY-001, HISYS-T-014, HISYS-T-015, HISYS-T-016, HISYS-T-017,
HISYS-T-018.

## Purpose

Validate that Chief Editor behavior can transform runtime-local memo review
outputs into auditable alert decisions without sending live alerts, writing to a
live Obsidian vault, or invoking external connectors.

## Inputs

- `data/memo-drafts/<YYYYMMDD>/*.json`
- `reports/run-summaries/<YYYYMMDD>/memo-review-report.json`

The harness stage uses reviewed `ZettelMemo` records only. It must not inspect
raw observation payloads directly.

## Procedure

1. Load runtime-local memo drafts for the run date.
2. Load the memo review report for the same run date.
3. Apply the fixture Chief Editor policy version
   `HISYS-CE-POLICY-001.fixture-v0`.
4. Convert `flagged_conflict` memos into pending `AlertDecisionRecord` records.
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
11. Do not send Discord messages, direct messages, software triggers, handoffs,
    or other live external actions in this harness stage.

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
- JSON and Markdown outputs are deterministic enough for regression tests.
- The CLI command `hisys decide-alerts --instance <root> --date <YYYYMMDD>`
  succeeds only when memo drafts and a memo review report are present.

## Non-goals

- Live alert delivery.
- Live Obsidian vault writes.
- Suppression windows across historical runs.
- Configurable suppression duration beyond the same-date fixture window.
- Human approval transition workflow beyond creating approval-request records.
- Discord/software connector execution.
- DARS handoff execution.
