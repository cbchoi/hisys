# Milestone Plan v0.0.2 — DARS Critic Panel M-CP-EXT-3 Prepare

## Decision context

Target workspace: `/home/cbchoi/workspaces/develop/repos/hisys`.

Selected profile: `develop`.

Current branch at bootstrap start: `dars` tracking `origin/dars`, HEAD `18fafa9 feat: add DARS execution-boundary record writer`.

This is a patch bootstrap over `v0.0.1`. It does not replace the initial bootstrap package; it records the next safe Prepare surface after M-CP-EXT-1 and M-CP-EXT-2 were completed by Ralph/Claude.

## Evidence seed

| Evidence | Status | Notes |
|---|---|---|
| Git repo | present | `dars` is ahead of `origin/dars` by 7 local commits; remote push remains human-gated. |
| Prior bootstrap `v0.0.1` | present | Initial DARS critic panel readiness package and Ralph overlay exist. |
| M-CP-EXT-1 | complete | `3cc58ed feat: add DARS critic adapter registry`; adapter registry and fixture outcome contract. |
| M-CP-EXT-2 | complete | `18fafa9 feat: add DARS execution-boundary record writer`; per-task boundary records and slug validation. |
| Current focused tests | green | `tests/unit/test_dars_critic_panel_runtime.py`, `test_dars_critic_panel_adapters.py`, and `test_dars_critic_panel_tool_execution_runtime.py` report 28 passed. |
| Current production surface | large | `src/hisys/agents/dars_panel.py` is 784 lines, exceeding the parent plan's package-split consideration threshold. |
| Parent plan | present | `docs/plans/dars-critic-panel-platform-runtime-next.md` defines M-CP-EXT-3 as ExecutionGraphPlan + bounded-parallel scheduling primitive. |

## Milestones

### MB-DARS-CP-EXT3-M1 — Prepare the execution-graph implementation contract

Objective: resolve design decisions for M-CP-EXT-3 before writing RED tests or production code.

Exit criteria:

- A task-generation plan exists for M-CP-EXT-3.
- The plan decides package split vs single-module placement for `ExecutionGraphPlan`.
- The plan pins ready-set semantics, terminal task statuses, bounded chunk ordering, and serial-executor compatibility.
- No CLI, live external dispatch, bounded-parallel activation, credential use, or remote push is authorized.

### MB-DARS-CP-EXT3-M2 — RED-test the execution graph primitive

Objective: define a new focused pytest surface for deterministic graph scheduling behavior.

Exit criteria:

- `tests/unit/test_dars_critic_panel_execution_graph_plan.py` exists.
- Initial RED confirms missing `ExecutionGraphPlan` or missing method behavior.
- Tests cover ready-set determinism, synthesis-after-terminal-critics, bounded chunking, and invalid dependency handling.

### MB-DARS-CP-EXT3-M3 — GREEN the fixture-local graph primitive without activating parallel execution

Objective: implement the minimum graph primitive and wire serial execution to consume the plan without enabling runtime parallelism.

Exit criteria:

- Existing panel, adapter, and tool-execution tests still pass.
- New graph tests pass.
- `DarsCriticPanelRuntime.run_round` remains serial by default; bounded-parallel execution activation is deferred.
- Boundary records and advisory-only invariants remain unchanged.

## First Ralph task

Start with `MB-DARS-CP-EXT3-T001`: author `docs/plans/dars-critic-panel-mcp-ext-3-implementation-tasks.md` as a document-RED/Prepare artifact. Do not write `tests/unit/test_dars_critic_panel_execution_graph_plan.py` or production scheduling code until that task plan is validated.
