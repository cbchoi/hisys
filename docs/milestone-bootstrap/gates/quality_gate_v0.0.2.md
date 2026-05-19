# Quality Gate v0.0.2 — M-CP-EXT-3 Prepare

## Scope

This gate applies to the M-CP-EXT-3 Prepare/bootstrap surface only. It authorizes local planning files and Ralph handoff updates. It does not authorize production scheduling code, bounded-parallel activation, a CLI command, live DARS dispatch, remote push, credential changes, publication, or destructive Git operations.

## Required checks

1. Baseline GREEN:
   ```bash
   PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py -q
   ```
2. Document/package checks:
   ```bash
   python3 scripts/validate_traceability.py
   python3 scripts/scan_secrets.py
   git diff --check
   ```
3. Bootstrap artifact checks:
   - `profile.yaml` records `version: v0.0.2` and selected profile `develop`.
   - `milestone_plan_v0.0.2.md`, tasks YAML, testcase YAML, readiness decision, Hisys request/result, and validation log exist.
   - The first safe task is `MB-DARS-CP-EXT3-T001`.

## Stop conditions

Stop before RED tests or production code if:

- package split decision is unresolved;
- the implementation would enable real parallel execution, live external dispatch, or CLI side effects;
- any existing DARS critic panel regression fails;
- secret scan finds a hit;
- working tree contains unrelated user changes.

## Human gates

Human approval is required for remote push, live DARS dispatch, publication, credential changes, destructive Git, or enabling bounded-parallel runtime execution beyond fixture-local primitives.
