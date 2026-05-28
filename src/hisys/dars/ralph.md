# DARS RLOO Control

```yaml
subsystem: dars
scope: DARS only
architecture_ref: docs/design/hisys-subsystem-architecture.md
branch: dars
package_root: src/hisys/dars
root_controller: ../../../ralph.md
```

## Purpose

This file is the subsystem-local RLOO controller for DARS. Use it when running DARS-only Ralph/RLOO cycles so DARS work can proceed independently from Altas and Judge while preserving the root Hisys architecture boundary.

DARS challenges and improves. It produces developmental opposition, advisory critique, risk analysis, missing-evidence pressure, failure-mode analysis, and improvement recommendations.

## Authority locks

```yaml
advisory_only: true
requires_human_review: true
live_external_action_authorized: false
completion_upgrade_claimed: false
raw_provider_api_readiness: false
adapter_native_readiness: false
bounded_unattended_advisory_operation_ready: false
mutation_authorized: false
publication_authorized: false
remote_push_authorized: false
```

## RLOO cycle

```text
prfl -> action -> pofl
```

- `prfl`: verify branch/worktree, local scope, clean tree, and DARS-only task boundary.
- `action`: implement one DARS-only RED/GREEN increment without moving existing legacy `hisys.agents.*` imports unless a migration task explicitly authorizes it.
- `pofl`: record reflection in this file and update the root `ralph.md` only when a root-level Hisys queue pointer must change.

## Current next safe task

```text
DARS-SUBSYSTEM-RLOO-READINESS-PACKET-CONTINUATION
```

Continue from the subsystem-local readiness command in `src/hisys/dars/rloo.py`. DARS is now individually executable through `PYTHONPATH=src:. python3 -m hisys.dars.rloo --check --format json` without depending on the root-level RLOO controller. Next safe candidates: extend the readiness packet with additional bounded advisory structure (e.g., a stable controller-derived DARS-only `task_queue` view or a DARS-only `reflection_log_tail` reflecting the last completed increment) while keeping the command read-only, deterministic, and compatibility-preserving. Do not move existing `hisys.agents.*` implementations and do not introduce any live provider/model call, raw provider API call, credential lookup, network access, remote push, vault mutation, or cross-subsystem call.

## Reflection log

- 2026-05-28 — `DARS-SUBSYSTEM-LOCAL-RALPH`: Added subsystem-local RLOO control file so DARS can run independently from Altas/Judge worktrees. Boundary preserved: no live provider/model call, raw provider API call, credential lookup, remote push, release, publication, deployment, vault mutation, or human-review removal.
- 2026-05-28 — `DARS-SUBSYSTEM-INVOCATION-MODE-SEAM`: Added `DarsSubsystemInvocationMode` and `get_dars_subsystem_invocation_modes` to the public seam in `src/hisys/dars/__init__.py`. Surfaces the documented `dars-only` standalone advisory mode and the `full-loop` composition stage from `docs/design/hisys-subsystem-architecture.md` as a stable, ordered, serializable tuple. RED-first tests (`tests/unit/test_dars_subsystem_public_seam.py`) cover mode identity, advisory/human-review locks, exclusion of `altas-only`/`judge-only`, and packet shape. Additive only — no change to existing exports, no movement of legacy `hisys.agents.*` implementations. Boundary preserved: no live provider/model call, raw provider API call, credential lookup, remote push, release, publication, deployment, vault mutation, or human-review removal.
- 2026-05-28 — `DARS-SUBSYSTEM-INDIVIDUAL-EXECUTION-COMMAND`: Added `src/hisys/dars/rloo.py`, the DARS subsystem-local RLOO entry point. The new command `PYTHONPATH=src:. python3 -m hisys.dars.rloo --check --format json` reads `src/hisys/dars/ralph.md`, parses controller metadata, authority locks, and the current next safe task, composes the existing `get_dars_subsystem_manifest` and `get_dars_subsystem_invocation_modes` seams, and emits a deterministic JSON readiness packet. The packet pins the DARS authority locks (`advisory_only=true`, `requires_human_review=true`, `live_external_action_authorized=false`, `completion_upgrade_claimed=false`, `raw_provider_api_readiness=false`, `adapter_native_readiness=false`, `bounded_unattended_advisory_operation_ready=false`, `mutation_authorized=false`, `publication_authorized=false`, `remote_push_authorized=false`) and explicitly records `independence.depends_on_root_rloo=false`, `independence.depends_on_altas=false`, `independence.depends_on_judge=false`, and `independence.subsystem_locally_invocable=true`. RED-first tests (`tests/unit/test_dars_subsystem_individual_execution.py`, 11 cases) cover module importability, `--check --format json` exit code and shape, controller anchor, manifest and invocation-mode reuse, authority locks, side-effect declarations, independence, controller non-mutation, and `--help` listing. Additive only — no movement of legacy `hisys.agents.*` implementations, no change to existing public seam exports. Boundary preserved: no live provider/model call, raw provider API call, credential lookup, network access, remote push, release, publication, deployment, vault mutation, cross-subsystem call, or human-review removal.
