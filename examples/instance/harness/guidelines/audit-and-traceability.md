# Audit and Traceability Harness Guideline

Traceability: HISYS-FR-ADM-002, HISYS-T-008, HISYS-T-023, HISYS-T-024.

## Procedure

1. Every collection success, skip, and failure emits an AuditEvent.
2. Every RawObservation has source, collection run, payload, provenance, quality,
   usage constraint, and retention metadata.
3. Hermes records link user input, prompt/query, tool output, boundary record,
   RawObservation, and AuditEvent refs.
4. Secret-like strings must be redacted before audit persistence.

## Pass Criteria

- Audit JSONL can reconstruct collection outcomes.
- RawObservation refs in reports resolve to JSON files.
- Hermes boundary refs resolve to Markdown files when Hermes is involved.
- No raw secret values appear in audit summaries.
