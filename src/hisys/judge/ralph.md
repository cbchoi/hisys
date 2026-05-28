# Judge RLOO Control

```yaml
subsystem: judge
scope: Judge only
architecture_ref: docs/design/hisys-subsystem-architecture.md
branch: dars
package_root: src/hisys/judge
root_controller: ../../../ralph.md
```

## Purpose

This file is the subsystem-local RLOO controller for Judge. Use it when running Judge-only Ralph/RLOO cycles so bounded advisory judgment work can proceed independently from Altas and DARS while preserving the root Hisys architecture boundary.

Judge decides and bounds. It issues bounded advisory judgments, gate outcomes, readiness reviews, and decision packets from already prepared evidence, Altas retrieval packets, and DARS opposition packets.

## Authority locks

```yaml
advisory_only: true
requires_human_review: true
live_external_action_authorized: false
mutation_authorized: false
publication_authorized: false
remote_push_authorized: false
human_review_removal_authorized: false
```

## RLOO cycle

```text
prfl -> action -> pofl
```

- `prfl`: verify branch/worktree, local scope, clean tree, and Judge-only task boundary.
- `action`: implement one Judge-only RED/GREEN increment without granting execution authority or collapsing Judge into Altas/DARS.
- `pofl`: record reflection in this file and update the root `ralph.md` only when a root-level Hisys queue pointer must change.

## Current next safe task

```text
JUDGE-SUBSYSTEM-READINESS-PACKET-CONTINUATION
```

Continue from the subsystem-local readiness command in `src/hisys/judge/rloo.py`. Judge is now individually executable through `PYTHONPATH=src:. python3 -m hisys.judge.rloo --check --format json` without depending on the root-level RLOO controller. Next safe candidates: add a bounded advisory decision packet schema or gate-result renderer that consumes already prepared local packets. Keep the command read-only, deterministic, and compatibility-preserving. Do not introduce any live provider/model call, raw provider API call, credential lookup, network access, remote push, vault/evidence mutation, publication, deployment, human-review removal, or cross-subsystem call.

## Reflection log

- 2026-05-29 — `JUDGE-SUBSYSTEM-INDIVIDUAL-EXECUTION-COMMAND`: Added the Judge subsystem-local public seam and RLOO readiness command. The command `PYTHONPATH=src:. python3 -m hisys.judge.rloo --check --format json` reads `src/hisys/judge/ralph.md`, parses controller metadata, authority locks, and the current next safe task, composes the `get_judge_subsystem_manifest` and `get_judge_subsystem_invocation_modes` seams, and emits a deterministic JSON readiness packet. The packet pins the Judge authority locks (`advisory_only=true`, `requires_human_review=true`, `live_external_action_authorized=false`, `mutation_authorized=false`, `publication_authorized=false`, `remote_push_authorized=false`, `human_review_removal_authorized=false`) and explicitly records `independence.depends_on_root_rloo=false`, `independence.depends_on_altas=false`, `independence.depends_on_dars=false`, and `independence.subsystem_locally_invocable=true`. Boundary preserved: no live provider/model call, raw provider API call, credential lookup, network access, remote push, release, publication, deployment, vault/evidence mutation, cross-subsystem call, or human-review removal.
