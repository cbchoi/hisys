---
doc_id: HISYS-DARS-PANEL-RELEASE-NOTES-V0-0-127
title: DARS Panel Release Notes v0.0.127
version: v0.0.127
status: role-separation-recorded
created: 2026-05-28
---

# DARS Panel Release Notes v0.0.127

## Accepted claim

```text
accepted_claim=hisys_altas_dars_judge_role_separation_recorded
next_safe_task=HISYS-ALTAS-DARS-JUDGE-MODULE-SKELETON
```

## Change

This increment records the Hisys subsystem role separation:

```text
Hisys = Altas + DARS + Judge
Altas finds and projects.
DARS challenges and improves.
Judge decides and bounds.
```

The architecture is recorded in `docs/design/hisys-subsystem-architecture.md`. The increment prepares the next module-skeleton refactor without moving implementation or changing runtime authority.

## Boundary

The DARS subsystem remains complete only as a bounded advisory productized baseline. This release note does not claim DARS completion upgrade, raw provider API readiness, adapter-native readiness, bounded unattended advisory operation readiness, live external action authority, release action authority, credential lookup authority, or human-review removal.
