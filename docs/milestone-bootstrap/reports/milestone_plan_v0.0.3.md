# Milestone Plan v0.0.3 — M-CP-EXT-6 Read-only DARS Panel CLI

## Scope

Target workspace: `/home/cbchoi/workspaces/develop/repos/hisys`.

Selected profile: `develop`.

This patch bootstrap prepares the next implementation increment after the committed document-RED plan `docs/plans/dars-critic-panel-mcp-ext-6-implementation-tasks.md` at HEAD `4fe086e`. The increment is limited to a read-only `hisys run-dars-panel` CLI wrapper over the existing fixture-local `DarsCriticPanelRuntime.run_round` surface.

## Evidence baseline

- Branch: `dars`.
- Baseline HEAD: `4fe086e docs: prepare read-only DARS panel CLI increment`.
- Existing focused DARS panel regression: 43 tests passed before this bootstrap.
- Current M-CP line already implemented locally: M-CP-EXT-1, 2, 3, 4, 5, and 7.
- Current M-CP-EXT-6 implementation plan exists and defines RED/GREEN tasks.

## Milestone MB-DARS-CP-EXT6-M1 — CLI RED and minimal GREEN

Goal: add the first failing CLI acceptance test for `run-dars-panel`, then implement the minimal argparse/handler/config-loader path required to persist a fixture-local advisory round and print safe JSON/text summaries.

First safe task: `MB-DARS-CP-EXT6-T001`.

Non-goals:

- no live DARS dispatch;
- no external adapter activation flag;
- no browser/network/process-spawn dependency;
- no credential resolution;
- no publication or downstream action approval;
- no actual bounded-parallel execution.

## Milestone MB-DARS-CP-EXT6-M2 — Safety characterization

Goal: verify that external-style backends remain typed blocked outcomes through the CLI and do not activate live dispatch.

## Milestone MB-DARS-CP-EXT6-M3 — Traceability and gate

Goal: update traceability docs and Ralph reflection, run focused plus safety gates, then commit locally. Remote push remains out of scope.

## Readiness decision

Local advisory readiness: `RALPH_START_READY_WITH_CONTROLS`.

Formal Hisys result: `not_run_in_this_bootstrap`.

The next task is ready only as a RED-test task. Production code remains gated by observing the RED failure first.
