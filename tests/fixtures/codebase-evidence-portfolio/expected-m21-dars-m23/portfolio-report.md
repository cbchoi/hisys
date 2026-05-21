# Codebase Evidence Portfolio (advisory)

- schema_id: hisys.codebase_evidence_portfolio.v1
- date: 20260522
- current_head_short: c7fb9af
- implemented_surface_count: 23
- human_gated_surface_count: 7
- advisory_only: true
- requires_human_review: true
- external_call_made: false
- mutation_performed: false
- raw_source_content_persisted: false
- allowed_actions: advisory_only

## Source lines

- DARS_PANEL_LOCAL_COMPLETION
- M21
- M23_LSP_ADAPTER
- M23_OSS_ADAPTER

## Schema IDs

- `hisys.architecture_candidates.v1`
- `hisys.change_impact.v1`
- `hisys.dars_panel_readiness.v1`
- `hisys.lsp_adapter.v1`
- `hisys.oss_comparison_adapter.v1`
- `hisys.traceability.coverage.v1`

## Artifact refs

- `docs/plans/dars-panel-completion-before-codebase-return.md`
- `docs/plans/m21-1-traceability-coverage-report-implementation-tasks.md`
- `docs/plans/m21-6-change-impact-analyzer-implementation-tasks.md`
- `docs/plans/m21-7-architecture-candidate-generator-implementation-tasks.md`
- `docs/plans/m23-advanced-codebase-adapter-integration-plan.md`
- `docs/plans/m23-cli-lsp-adapter-implementation-tasks.md`
- `docs/plans/m23-cli-oss-comparison-adapter-implementation-tasks.md`
- `docs/plans/m23-golden-lsp-adapter-implementation-tasks.md`
- `docs/plans/m23-golden-oss-comparison-adapter-implementation-tasks.md`
- `docs/plans/m23-lsp-adapter-implementation-tasks.md`
- `docs/plans/m23-oss-comparison-adapter-implementation-tasks.md`
- `docs/reports/dars-panel-local-completion-audit.md`
- `docs/reports/m23-live-lsp-server-smoke.md`
- `runtime-boundary/lsp-adapter/20260522/pyright-check-live/lsp-report.json`
- `runtime-boundary/lsp-adapter/20260522/ruff-check-live/lsp-report.json`

## Quality gate refs

- `tests/unit/test_architecture_candidates.py`
- `tests/unit/test_change_impact.py`
- `tests/unit/test_dars_critic_panel_cli.py`
- `tests/unit/test_dars_critic_panel_runtime.py`
- `tests/unit/test_lsp_adapter.py`
- `tests/unit/test_oss_comparison_adapter.py`
- `tests/unit/test_traceability_coverage.py`

## Unsafe refs (rejected)

- (none)

## Unsafe line labels (rejected)

- (none)
