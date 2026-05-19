# Quality Gate v0.0.4 — M-CP-EXT-9 duration_ms Readiness

## Gate scope

This gate covers follow-on implementation readiness for adding `duration_ms` to persisted DARS `ExecutionBoundaryRecord` JSON. The bootstrap itself is planning/readiness work only; it does not implement the schema field.

## Required pre-implementation gate

Before editing production code, run the RED test from `MB-DARS-CP-EXT9-T001` and confirm the failure is caused by the missing `duration_ms` field.

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_tool_execution_runtime.py::test_panel_runtime_records_duration_ms_per_task -q
```

## Required implementation gate

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

## Safety gates

- No live DARS dispatch.
- No external adapter activation flag.
- No credential resolution or raw secret persistence.
- No browser/network/process-spawn dependency.
- No CLI argument/config schema change.
- No publication, deployment, or downstream action approval.
- No remote push in this bootstrap.
- No tmux or background agent spawned.

## Bootstrap validation result

Pass. See `evidence/validation_log_v0.0.4.md`.
