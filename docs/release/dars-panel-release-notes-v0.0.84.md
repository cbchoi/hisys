---
doc_id: HISYS-DARS-R7-RC-NOTES-001
title: DARS Panel Release Notes v0.0.84
version: v0.0.84
status: scope-decision-draft
created: 2026-05-24
---

# DARS Panel Release Notes v0.0.84

Scope decision only. These notes describe the candidate package scope prepared for human review after R4H harness closure. No release artifact is produced by this note.

## Candidate scope

- Local fixture and localhost-controlled DARS advisory evidence remain part of the package.
- R3 is represented only by the reviewed mapped-subscription Codex subprocess single-smoke claim.
- R4H is represented by Hermes-mediated advisory and local fixture-injected request/response harness closure.
- R4C Codex subprocess panel completion remains deferred.
- R5 is represented by PREP/dry-run policy and runner evidence only unless a later human-gated canary is accepted.
- R6 is represented by local status and rollback readiness.

## Claim boundary

`release_candidate_ready=false` for this scope-decision increment. A later RC decision packet must accept residual risks and evidence completeness before the candidate is ready for human release approval.
