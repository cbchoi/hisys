---
doc_id: HISYS-DARS-R5-CANARY-PACKET-NOTES-001
title: DARS Panel Release Notes v0.0.86
version: v0.0.86
status: r5-canary-packet-prep-draft
created: 2026-05-24
---

# DARS Panel Release Notes v0.0.86

Packet preparation only. R5 canary packet preparation has been recorded as a
human-review reference packet. No release artifact is produced by this note.

## Candidate scope update

- R5 canary packet preparation document is present at
  `docs/release/dars-r5-canary-packet-prep-v0.0.86.md` and records the prepared
  evidence row in the release candidate checklist.
- The packet references the existing R5 PREP standing approval validator,
  unattended runner, and example policy and the R6 live operations and
  rollback runbooks.
- R5 canary has not been executed in this packet-prep increment; bounded
  unattended live canary evidence remains missing.
- R4C is excluded from this release scope; R4H remains the scoped
  human-review advisory substitute.
- No standing unattended approval has been activated. No live provider/model
  call, no Codex subprocess call, no raw provider API call, and no credential
  lookup has been performed by Hisys.

## Claim boundary

`release_candidate_ready=false` and `r5_live_canary_executed=false` remain in
force. `bounded_unattended_advisory_operation_ready=false` is preserved. The
R5 canary action decision packet (separately HUMAN-GATED) must be authored and
reviewed before any later canary execution.
