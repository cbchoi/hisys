# Investigator Harness Guideline

Traceability: HISYS-INST-INV-001, HISYS-T-006, HISYS-T-007, HISYS-T-008.

## Purpose

Validate that the Investigator collects only from registered collectable sources,
normalizes adapter results into RawObservation records, preserves provenance, and
records audit events.

## Procedure

1. Load `config/source-registry.yaml` and `config/web-compliance/*.yaml`.
2. Refuse unregistered, blocked, suspended, retired, or X-class sources.
3. Execute adapters through the registry-gated adapter runtime.
4. Write RawObservation JSON files under `data/raw-observations/<YYYYMMDD>/`.
5. Append AuditEvent JSONL records under `data/audit/<YYYYMMDD>/`.
6. Continue collecting registered sources even if one source fails.

## Pass Criteria

- Registered fixture source produces a RawObservation.
- Unregistered source is skipped and audited.
- Adapter failure is bounded and does not stop other sources.
- No live network or credential access is required.
