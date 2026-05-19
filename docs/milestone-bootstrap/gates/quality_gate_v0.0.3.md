# Quality Gate v0.0.3 — M-CP-EXT-6 CLI Readiness

## Gate scope

This gate covers follow-on implementation readiness for the read-only `hisys run-dars-panel` CLI. The bootstrap itself is planning/readiness work only; it does not implement the CLI.

## Required pre-implementation gate

Before editing production code, run the RED test from `MB-DARS-CP-EXT6-T001` and confirm the failure is caused by the missing `run-dars-panel` subcommand.

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py::test_run_dars_panel_cli_persists_fixture_round_and_prints_json -q
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
- No mutation outside the runtime instance artifact tree and repository files intentionally edited by the increment.
- No publication, deployment, or downstream action approval.
- No remote push in this bootstrap.
- No tmux or background agent spawned.

## Bootstrap validation result

Pass. See `evidence/validation_log_v0.0.3.md`.
