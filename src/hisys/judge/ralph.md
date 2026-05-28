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

Continue from the subsystem-local readiness command in `src/hisys/judge/rloo.py` and the bounded advisory decision packet schema in `src/hisys/judge/decision_packet.py`. Judge is now individually executable through `PYTHONPATH=src:. python3 -m hisys.judge.rloo --check --format json` without depending on the root-level RLOO controller, and `validate_judge_decision_packet` deterministically validates an already-prepared local decision packet mapping while pinning the Judge authority locks. Next safe candidate: add a gate-result renderer that consumes a validated `JudgeAdvisoryDecisionPacket` (or an already-prepared local packet mapping) and emits a deterministic, human-readable advisory gate result without granting any execution authority. Keep all Judge code read-only, deterministic, and compatibility-preserving. Do not introduce any live provider/model call, raw provider API call, credential lookup, network access, remote push, vault/evidence mutation, publication, deployment, human-review removal, or cross-subsystem call.

## Reflection log

- 2026-05-29 — `JUDGE-SUBSYSTEM-DECISION-PACKET-SCHEMA`: Added the Judge-only bounded advisory decision packet schema in `src/hisys/judge/decision_packet.py` and exported it through the package seam. `validate_judge_decision_packet` is a pure, deterministic, side-effect-free validator that consumes an already-prepared local packet mapping (operator/Altas/DARS prepared) and returns a frozen `JudgeDecisionPacketValidation` with `valid`, ordered `failures`, `warnings`, and an optional frozen `JudgeAdvisoryDecisionPacket`. It checks required string fields (`packet_id`, `decision_subject_ref`, `verdict`, `rationale`), the bounded verdict set (`pass`, `fail`, `block`, `needs_human_review`), at least one `evidence_refs` handle, list-typed `evidence_refs`/`opposition_refs` of strings, and refuses any authority escalation in the input — emitting deterministic failure codes if `advisory_only`/`requires_human_review` are not true or if `live_external_action_authorized`/`mutation_authorized`/`publication_authorized`/`human_review_removal_authorized` are set true. Valid packets pin all authority locks to advisory-only, human-review-required values and emit `SCHEMA_VALIDITY_WARNING` to record that schema validity does not authorize action. 28 focused tests GREEN (`tests/unit/test_judge_decision_packet_schema.py`); combined Judge suite 44 GREEN; `validate_traceability.py` OK; `scan_secrets.py` hit_count=0; `git diff --check` clean. Boundary preserved: no live provider/model call, raw provider API call, credential lookup, network access, remote push, release, publication, deployment, vault/evidence mutation, cross-subsystem call, or human-review removal. The validator does no I/O and does not mutate its input.
- 2026-05-29 — `JUDGE-SUBSYSTEM-INDIVIDUAL-EXECUTION-COMMAND`: Added the Judge subsystem-local public seam and RLOO readiness command. The command `PYTHONPATH=src:. python3 -m hisys.judge.rloo --check --format json` reads `src/hisys/judge/ralph.md`, parses controller metadata, authority locks, and the current next safe task, composes the `get_judge_subsystem_manifest` and `get_judge_subsystem_invocation_modes` seams, and emits a deterministic JSON readiness packet. The packet pins the Judge authority locks (`advisory_only=true`, `requires_human_review=true`, `live_external_action_authorized=false`, `mutation_authorized=false`, `publication_authorized=false`, `remote_push_authorized=false`, `human_review_removal_authorized=false`) and explicitly records `independence.depends_on_root_rloo=false`, `independence.depends_on_altas=false`, `independence.depends_on_dars=false`, and `independence.subsystem_locally_invocable=true`. Boundary preserved: no live provider/model call, raw provider API call, credential lookup, network access, remote push, release, publication, deployment, vault/evidence mutation, cross-subsystem call, or human-review removal.
