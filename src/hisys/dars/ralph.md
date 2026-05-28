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
DARS-SUBSYSTEM-PUBLIC-SEAM-CONTINUATION
```

Continue from the public seam in `src/hisys/dars/__init__.py`. Keep the subsystem independently invocable and compatibility-preserving.

## Reflection log

- 2026-05-28 — `DARS-SUBSYSTEM-LOCAL-RALPH`: Added subsystem-local RLOO control file so DARS can run independently from Altas/Judge worktrees. Boundary preserved: no live provider/model call, raw provider API call, credential lookup, remote push, release, publication, deployment, vault mutation, or human-review removal.
