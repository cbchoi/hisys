---
doc_id: HISYS-SUBSYSTEM-ROLE-SEPARATION-PREP-V0-0-127
title: Hisys Subsystem Role-Separation Prep
version: v0.0.127
status: role-separation-recorded
created: 2026-05-28
---

# Hisys Subsystem Role-Separation Prep

```text
task_id=HISYS-SUBSYSTEM-ROLE-SEPARATION-PREP
accepted_claim=hisys_altas_dars_judge_role_separation_recorded
architecture_ref=docs/design/hisys-subsystem-architecture.md
next_safe_task=HISYS-ALTAS-DARS-JUDGE-MODULE-SKELETON
```

## Decision

Hisys is now defined as three separable subsystems:

```text
Hisys = Altas + DARS + Judge
Altas finds and projects.
DARS challenges and improves.
Judge decides and bounds.
```

This record is a documentation and test-gate preparation increment. It does not move implementation modules yet and does not change runtime authority.

## Evidence scope

The increment records the subsystem architecture and the intended next implementation increment. It allows later package/module skeleton work to proceed against explicit role boundaries instead of continuing to overload the DARS panel vocabulary.

## Boundary flags

```text
dars_bounded_advisory_productized_baseline=true
dars_completion_upgrade_claimed=false
bounded_unattended_advisory_operation_ready=false
raw_provider_api_readiness=false
adapter_native_readiness=false
live_external_action_authorized=false
release_action_authorized=false
credential_lookup_by_hisys=false
standing_unattended_approval_activated=false
human_review_removal_authorized=false
requires_human_review=true
external_call_made=false
mutation_performed=false
publication_performed=false
```

## Subsystem boundary summary

- Altas is responsible for retrieval, trace, MCP/web/search capture boundaries, and curated note projection workflows. Altas does not accept or reject claims.
- DARS is responsible for developmental opposition and advisory critique. DARS does not approve, mutate, or execute actions.
- Judge is responsible for bounded advisory judgments, gates, readiness reviews, and decision packets. Judge does not remove human review or authorize live/external/destructive actions without a separate scoped approval.

## Next safe task

```text
next_safe_task=HISYS-ALTAS-DARS-JUDGE-MODULE-SKELETON
```

The next increment should add minimal package/module skeletons and public seams for `altas`, `dars`, and `judge` without migrating behavior or expanding live authority.
