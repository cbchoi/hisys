# Milestone Plan v0.0.1 — Hisys DARS Critic Panel Runtime

## Decision context

Target workspace: `/home/cbchoi/workspaces/develop/repos/hisys`.

Selected profile: `develop`.

Current branch at bootstrap start: `dars` tracking `origin/dars`, HEAD `a39f922 test: add DARS critic panel RED anchors`.

Existing milestone-bootstrap artifacts were absent. This is an initial `v0.0.1` bootstrap package created from existing design outputs, source/tests, and Ralph control content.

## Evidence seed

| Evidence | Status | Notes |
|---|---|---|
| Git repo | present | `git status --short --branch` reported `## dars...origin/dars` before bootstrap edits. |
| `ralph.md` | present | Existing control plan is large and preserved; bootstrap adds an overlay instead of overwriting it. |
| Requirements | present | `docs/requirements/dars-critic-panel-runtime-requirements.md` defines `HISYS-FR-DARS-CP-001..008` and `HISYS-NFR-DARS-CP-001..002`. |
| SDD | present | `docs/design/dars-critic-panel-runtime-sdd.md` defines `hisys.agents.dars_panel` contracts. |
| STD | present | `docs/test/dars-critic-panel-runtime-std.md` defines `HISYS-T-DARS-CP-001..010`. |
| RTM | present | `docs/traceability/dars-critic-panel-runtime-traceability.md` maps requirements to tests. |
| RED tests | present | `tests/unit/test_dars_critic_panel_runtime.py` currently expects missing `hisys.agents.dars_panel`. |
| Production implementation | missing | `src/hisys/agents/dars_panel.py` is the next implementation target. |

## Milestones

### MB-DARS-CP-M1 — GREEN the fixture-local critic panel runtime

Objective: implement the minimum `hisys.agents.dars_panel` production surface required by `tests/unit/test_dars_critic_panel_runtime.py` while preserving advisory-only, no external call, no mutation authority boundaries.

Exit criteria:

- `PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_runtime.py -q` passes.
- Critique, synthesis, and trace artifacts preserve `advisory_only=true`, `requires_human_review=true`, `action_authorized=false`, `external_call_made=false`, and `mutation_performed=false` where applicable.
- Failed critic isolation produces partial evidence and `needs_more_evidence` synthesis.

### MB-DARS-CP-M2 — Integrate panel runtime with existing DARS governance docs and traceability

Objective: update traceability and operational docs after the GREEN implementation so the new panel runtime is visible in the existing Hisys traceability summary and DARS integration design.

Exit criteria:

- Relevant traceability summary rows mention the DARS critic panel implementation.
- Existing DARS tests continue to pass or documented blockers are recorded.
- Secret scan and whitespace checks pass.

### MB-DARS-CP-M3 — Prepare platform-kernel extension path

Objective: prepare the next design increment for `CriticAdapterRegistry`, `ToolExecutionRuntime`, and execution graph/process-boundary records without enabling live dispatch.

Exit criteria:

- A plan or RED tests describe adapter/runtime boundaries.
- No live external backend is enabled.
- Human gate remains required for remote push, live DARS dispatch, publication, or credential changes.

## First Ralph task

Start with `MB-DARS-CP-T001`: inspect the RED test and implement `src/hisys/agents/dars_panel.py` minimally until the focused DARS critic panel test passes.
