# Editorial Harness Guideline

Traceability: HISYS-HARNESS-GUIDE-001, HISYS-FR-PER-001..004,
HISYS-FR-MEM-001..005, HISYS-DATA-002, HISYS-T-011, HISYS-T-012,
HISYS-T-013.

## Purpose

Validate that Associate Editor behavior turns extracted interpretation signals
into atomic Zettelkasten memo drafts while preserving evidence links and keeping
runtime tests isolated from a live Obsidian vault.

## Procedure

1. Start from fixture-collected `RawObservation` records and extracted
   `ExtractedSignal` records.
2. Apply an active `PerspectiveProfile`, currently fixture `PERSP-OPS-001`.
3. Create one atomic `ZettelMemo` draft per signal.
4. Persist draft JSON and Markdown under
   `data/memo-drafts/<YYYYMMDD>/` inside the runtime instance.
5. Persist a memo draft report under
   `reports/run-summaries/<YYYYMMDD>/memo-draft-report.{json,md}`.
6. Do not write to the user's live Obsidian vault in this harness stage.

## Pass Criteria

- Retired/non-active perspectives are rejected or produce no drafts.
- Memo drafts include stable memo IDs, source refs, signal refs, perspective ID,
  confidence, tags, links, revision, and draft review status.
- Memo bodies include trace references but do not copy raw payload fields or
  secret-like fixture values.
- JSON and Markdown outputs are deterministic enough for regression tests.

## Non-goals

- Live Obsidian vault writes.
- Duplicate/conflict adjudication beyond future stub coverage.
- Chief Editor alert policy or DARS handoff execution.
