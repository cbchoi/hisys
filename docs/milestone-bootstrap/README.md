# Hisys Milestone Bootstrap

This package bootstraps the current Hisys `dars` branch as a governed develop-profile milestone-readiness package.

Current package version: `v0.0.4`.

Primary focus: keep the DARS critic panel runtime line Ralph/TDD-ready without spawning tmux, background agents, live connectors, credential mutation, publication, deployment, or remote synchronization.

The package records a local advisory readiness result only. It does not claim a formal Hisys readiness pass unless a formal Hisys run is explicitly executed and recorded.

## Current package — v0.0.4

Patch bootstrap after `aa707ca feat: record per-task DARS boundary timing`.

First safe task: `MB-DARS-CP-EXT9-T001`, implement no production code until the RED test for `duration_ms` persistence is written and observed failing.

Required current artifacts:

- `profile.yaml`
- `reports/milestone_plan_v0.0.4.md`
- `tasks/milestone_tasks_v0.0.4.yaml`
- `testcases/milestone_testcases_v0.0.4.yaml`
- `gates/quality_gate_v0.0.4.md`
- `documents/readiness_decision_record_v0.0.4.md`
- `hisys/request_v0.0.4.json`
- `hisys/result_v0.0.4.md`
- `evidence/validation_log_v0.0.4.md`

## v0.0.3 — M-CP-EXT-6 implementation readiness

Patch bootstrap for the read-only `hisys run-dars-panel` CLI.

## v0.0.2 — M-CP-EXT-3 Prepare

Patch bootstrap after M-CP-EXT-2 completion.

## v0.0.1 — Initial DARS critic panel runtime bootstrap

Initial develop-profile bootstrap for fixture-local DARS critic panel runtime readiness.
