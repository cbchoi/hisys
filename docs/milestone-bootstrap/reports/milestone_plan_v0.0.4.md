# Milestone Plan v0.0.4 — M-CP-EXT-9 Per-task duration_ms

## Scope

Target workspace: `/home/cbchoi/workspaces/develop/repos/hisys`.

Selected profile: `develop`.

This patch bootstrap prepares the next implementation increment after `aa707ca feat: record per-task DARS boundary timing`. The increment is limited to adding a derived integer `duration_ms` field to persisted DARS `ExecutionBoundaryRecord` JSON.

## Evidence baseline

- Branch: `dars`.
- Baseline HEAD: `aa707ca feat: record per-task DARS boundary timing`.
- Focused DARS panel/CLI regression: `46 passed` before this Prepare write.
- M-CP-EXT-8 introduced distinct per-task `started_at` and `completed_at` values.
- M-CP-EXT-8 explicitly deferred per-task `duration_ms` because it requires a schema field and traceability update.

## Milestone MB-DARS-CP-EXT9-M1 — duration_ms RED and minimal GREEN

Goal: add a failing tool-execution test that expects `duration_ms` in persisted boundary JSON, then implement the minimal dataclass/runtime derivation.

First safe task: `MB-DARS-CP-EXT9-T001`.

Non-goals:

- no CLI argument/config change;
- no live DARS dispatch;
- no external adapter activation;
- no browser/network/process-spawn dependency;
- no credential resolution;
- no publication or downstream action approval;
- no parallel execution activation.

## Milestone MB-DARS-CP-EXT9-M2 — non-negative duration characterization

Goal: pin a backward-clock safety characterization so `duration_ms` remains non-negative.

## Milestone MB-DARS-CP-EXT9-M3 — Traceability and gate

Goal: update traceability docs and Ralph reflection, run focused plus safety gates, then commit locally. Remote push remains out of scope.

## Readiness decision

Local advisory readiness: `RALPH_START_READY_WITH_CONTROLS`.

Formal Hisys result: `not_run_in_this_bootstrap`.

The next task is ready only as a RED-test task. Production code remains gated by observing the RED failure first.
