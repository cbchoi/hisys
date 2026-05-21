# Codebase Evidence Portfolio (advisory)

- schema_id: hisys.codebase_evidence_portfolio.v1
- date: 20260521
- current_head_short: ec192e3
- implemented_surface_count: 14
- human_gated_surface_count: 2
- advisory_only: true
- requires_human_review: true
- external_call_made: false
- mutation_performed: false
- raw_source_content_persisted: false
- allowed_actions: advisory_only

## Source lines

- DARS_PANEL_LOCAL_COMPLETION
- M21

## Schema IDs

- `hisys.architecture_candidates.v1`
- `hisys.change_impact.v1`
- `hisys.dars_panel_readiness.v1`
- `hisys.traceability.coverage.v1`

## Artifact refs

- `docs/plans/dars-panel-completion-before-codebase-return.md`
- `docs/plans/m21-1-traceability-coverage-report-implementation-tasks.md`
- `docs/plans/m21-6-change-impact-analyzer-implementation-tasks.md`
- `docs/plans/m21-7-architecture-candidate-generator-implementation-tasks.md`
- `docs/reports/dars-panel-local-completion-audit.md`

## Quality gate refs

- `tests/unit/test_architecture_candidates.py`
- `tests/unit/test_change_impact.py`
- `tests/unit/test_dars_critic_panel_cli.py`
- `tests/unit/test_dars_critic_panel_runtime.py`
- `tests/unit/test_traceability_coverage.py`

## Unsafe refs (rejected)

- (none)

## Unsafe line labels (rejected)

- (none)
