# Readiness Decision Record v0.0.4

## Decision

`RALPH_START_READY_WITH_CONTROLS`

## Formal Hisys result

`not_run_in_this_bootstrap`

No formal Hisys readiness run was executed in this current-session bootstrap. This record is a local advisory readiness decision only.

## Hermes/local advisory result

The workspace is ready to start the next local Ralph/TDD increment under controls. The only allowed first task is `MB-DARS-CP-EXT9-T001`: write and observe the RED test for persisted per-task `duration_ms`.

## Evidence scope

- Target workspace: `/home/cbchoi/workspaces/develop/repos/hisys`.
- Branch: `dars`.
- Baseline HEAD: `aa707ca feat: record per-task DARS boundary timing`.
- M-CP-EXT-8 added distinct per-task `started_at` and `completed_at` fields.
- M-CP-EXT-9 implementation plan: `docs/plans/dars-critic-panel-mcp-ext-9-implementation-tasks.md`.

## Allowed next action

Write the RED test in `tests/unit/test_dars_critic_panel_tool_execution_runtime.py` and verify it fails because persisted boundary records do not contain `duration_ms`.

## Blocked scopes

- Production schema/runtime implementation before RED is observed.
- Live external dispatch or connector activation.
- CLI argument/config schema change.
- Credential mutation or credential value persistence.
- Remote push.
- Destructive Git/history operations.
- Publication, deployment, or downstream decision/action approval.
- tmux/background agent spawning in this bootstrap.

## Version decision

Patch bump from `v0.0.3` to `v0.0.4` because this is a follow-on implementation-readiness bootstrap and no formal readiness pass was run.
