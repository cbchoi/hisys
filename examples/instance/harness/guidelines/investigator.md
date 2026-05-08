# Investigator Harness Guideline

Traceability: HISYS-INST-INV-001, HISYS-T-006, HISYS-T-007, HISYS-T-008,
HISYS-T-026, HISYS-TPL-RESEARCH-SEARCH-001.

## Purpose

Validate that the Investigator collects only from registered collectable sources,
normalizes adapter results into RawObservation records, preserves provenance, and
records audit events. Validate that `investigate-memo` can turn a research
topic/goal into a template-based Investigator memo artifact before Chief Editor
orchestration.

## Procedure

1. Load `config/source-registry.yaml` and `config/web-compliance/*.yaml`.
2. Refuse unregistered, blocked, suspended, retired, or X-class sources.
3. Execute adapters through the registry-gated adapter runtime.
4. Write RawObservation JSON files under `data/raw-observations/<YYYYMMDD>/`.
5. Append AuditEvent JSONL records under `data/audit/<YYYYMMDD>/`.
6. Continue collecting registered sources even if one source fails.
7. For direct memo runs, execute `hisys investigate-memo` with a research topic,
   goal, perspective, and one or more registered sources.
8. Verify the memo body follows `HISYS-TPL-RESEARCH-SEARCH-001` sections:
   research question, query set, accepted source records, skipped/rejected
   records, investigation findings, evidence trace, interpretation, and open
   questions.

## Pass Criteria

- Registered fixture source produces a RawObservation.
- Unregistered source is skipped and audited.
- Adapter failure is bounded and does not stop other sources.
- No live network or credential access is required.
- `investigate-memo` writes `data/investigation-memos/<YYYYMMDD>/*.json/.md`
  and `reports/run-summaries/<YYYYMMDD>/investigation-memo-report.{json,md}`.
- Investigation memos reference `source_refs`, `observation_refs`, and
  `signal_refs` but do not copy raw payload content into the memo body.
