---
doc_id: HISYS-DARS-R5-CANARY-ACTION-DECISION-NOTES-001
title: DARS Panel Release Notes v0.0.87
version: v0.0.87
status: r5-canary-action-decision-packet-draft
created: 2026-05-24
---

# DARS Panel Release Notes v0.0.87

Packet preparation only. The R5 canary action decision packet has been recorded
as a human-review reference packet that connects the prepared R5 canary packet
to a later HUMAN-GATED canary execution decision.
No release artifact is produced by this note.

Note: the bounded unattended live canary remains a separately HUMAN-GATED action.

## Candidate scope update

- R5 canary action decision packet document is present at
  `docs/release/dars-r5-canary-action-decision-packet-v0.0.87.md` and is now
  the next reviewed evidence row in the release candidate checklist.
- The packet references the existing R5 PREP standing approval validator,
  unattended runner, example policy, R6 live operations and rollback runbooks,
  the prior R5 canary packet preparation, and the prior R5 canary scope
  decision.
- The bounded unattended live canary remains a separately HUMAN-GATED action.
  No canary run has been executed, and no standing unattended approval has
  been activated.
- R4C is excluded from this release scope; R4H remains the scoped
  human-review advisory substitute. Future R4C reactivation requires separate
  explicit operator instruction.
- No live provider/model call, no Codex subprocess call, no raw provider API
  call, and no credential lookup has been performed by Hisys.

## Claim boundary

`release_candidate_ready=false` and `r5_live_canary_executed=false` remain in
force. `bounded_unattended_advisory_operation_ready=false` is preserved. The
R5 canary action decision packet records the boundary the later canary
execution must satisfy and does not itself authorize execution.
