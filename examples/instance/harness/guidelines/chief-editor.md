# Chief Editor Harness Guideline

Traceability: HISYS-HARNESS-GUIDE-001, HISYS-FR-CE-001..006,
HISYS-CE-POLICY-001, HISYS-T-014, HISYS-T-015, HISYS-T-016.

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
6. Persist alert decisions under `data/alert-decisions/<YYYYMMDD>/` as JSON and
   Markdown.
7. Persist the run summary under
   `reports/run-summaries/<YYYYMMDD>/alert-decision-report.{json,md}`.
8. Do not send Discord messages, direct messages, software triggers, handoffs,
   or other live external actions in this harness stage.

## Pass Criteria

- Every persisted alert decision is a valid `AlertDecisionRecord`.
- Conflict-triggered decisions preserve `memo_refs`, `signal_refs`, policy
  version, severity, confidence, suppression key, and follow-up guidance.
- Duplicate memo decisions are recorded as non-escalation decisions with
  `status=suppressed` and `action_taken=none`.
- High/critical sent or triggered actions are impossible without approval per
  the schema gate, even though I7-A does not yet perform live sends.
- JSON and Markdown outputs are deterministic enough for regression tests.
- The CLI command `hisys decide-alerts --instance <root> --date <YYYYMMDD>`
  succeeds only when memo drafts and a memo review report are present.

## Non-goals

- Live alert delivery.
- Live Obsidian vault writes.
- Suppression windows across historical runs.
- Human approval transition workflow.
- Discord/software connector execution.
- DARS handoff execution.
