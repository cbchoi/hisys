# Validation Log v0.0.11 — M21.5 Prepare

## Baseline

- Date: 2026-05-20
- Target: `/home/cbchoi/workspaces/develop/repos/hisys`
- Branch: `dars`
- Baseline HEAD: `d992905 feat: add codebase-map-freshness-review cli wrapper`
- Scope: M21.5 regression benchmark fixture repositories Prepare/document-RED

## Artifact validation

- Structural parse: pass for required v0.0.11 files, `profile.yaml`, `tasks/milestone_tasks_v0.0.11.yaml`, `testcases/milestone_testcases_v0.0.11.yaml`, and `hisys/request_v0.0.11.json`.
- Profile check: `version=v0.0.11`, `selected_profile=develop`.
- Task check: first task is `MB-M21-5-RED`.
- Plan ref check: `docs/plans/m21-5-regression-benchmark-fixture-repositories-implementation-tasks.md` exists.
- Extended focused gate: `PYTHONPATH=src pytest tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_cli.py -q` -> 44 passed.
- DARS focused regression: `PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q` -> 48 passed.
- Traceability validator: `python3 scripts/validate_traceability.py` -> OK.
- Secret scan: `python3 scripts/scan_secrets.py` -> `scanned_files=596 skipped_files=0 hit_count=0`.
- Whitespace check: `git diff --check` -> clean.
