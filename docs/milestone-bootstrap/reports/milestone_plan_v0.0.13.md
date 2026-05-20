# Milestone Plan v0.0.13 — Current Weakness Analysis Improvement Plan

## Scope

This package records a local advisory weakness analysis over current Hisys code and documents, then selects a safe implementation sequence.

## Baseline

- Target workspace: `/home/cbchoi/workspaces/develop/repos/hisys`
- Branch: `dars`
- Baseline HEAD: `ff89b1b docs: prepare live dars panel configuration`
- Previous package: `v0.0.12` live DARS panel configuration Prepare

## Main findings

1. Live DARS panel activation packet is missing.
2. Panel boundary records cannot yet express local model crossing.
3. Panel-to-local-model adapter bridge is absent.
4. CLI live rehearsal fail-closed path is not pinned.
5. Ralph/bootstrap current-state drift needs synchronization.
6. Plan lifecycle and traceability rows need stronger indexing.
7. M21.5 benchmark fixture surface and M21.6 change-impact analyzer remain absent.
8. Runtime-boundary consistency and codebase-map freshness need hardening tests.

## Next safe task

`MB-DARS-LIVE-GOV-SYNC-RED` — perform a small governance-sync RED/green increment that pins current-state drift before implementing live model panel behavior.

## Boundary

Docs/control planning only. No production code, no test files, no live model call, no external API, no credential lookup, no non-localhost endpoint, no destructive Git, no deployment, no publication, and no remote push are authorized by this package.
