# Readiness Decision Record v0.0.3

## Decision

`RALPH_START_READY_WITH_CONTROLS`

## Formal Hisys result

`not_run_in_this_bootstrap`

No formal Hisys readiness run was executed in this current-session bootstrap. This record is a local advisory readiness decision only.

## Hermes/local advisory result

The workspace is ready to start the next local Ralph/TDD increment under controls. The only allowed first task is `MB-DARS-CP-EXT6-T001`: write and observe the RED CLI acceptance test for `hisys run-dars-panel`.

## Evidence scope

- Target workspace: `/home/cbchoi/workspaces/develop/repos/hisys`.
- Branch: `dars`.
- Baseline HEAD: `4fe086e docs: prepare read-only DARS panel CLI increment`.
- Existing M-CP extension commits through M-CP-EXT-7 are local on branch `dars`.
- M-CP-EXT-6 implementation plan: `docs/plans/dars-critic-panel-mcp-ext-6-implementation-tasks.md`.

## Allowed next action

Write the RED test in `tests/unit/test_dars_critic_panel_cli.py` and verify it fails because the `run-dars-panel` subcommand does not exist.

## Blocked scopes

- Production CLI implementation before RED is observed.
- Live external dispatch or connector activation.
- Credential mutation or credential value persistence.
- Remote push.
- Destructive Git/history operations.
- Publication, deployment, or downstream decision/action approval.
- tmux/background agent spawning in this bootstrap.

## Version decision

Patch bump from `v0.0.2` to `v0.0.3` because this is a follow-on implementation-readiness bootstrap and no formal readiness pass was run.
