# Quality Gate v0.0.9 — M21 Roadmap

## Required checks

- Roadmap states completed M21.1/M21.2 baseline and next M21.3-PREP task.
- Roadmap preserves local-only/advisory-only/no-live/no-credential/no-raw-source boundaries.
- Machine-readable bootstrap YAML/JSON parses.
- Existing focused traceability/domain/CLI regression passes.
- DARS focused regression passes.
- `scripts/validate_traceability.py` passes.
- `scripts/scan_secrets.py` reports `hit_count=0`.
- `git diff --check` is clean.

## Authorization result

Local docs/control commit is allowed after all checks pass. Remote push is not authorized.
