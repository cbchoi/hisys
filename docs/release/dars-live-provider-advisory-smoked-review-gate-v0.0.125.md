---
doc_id: HISYS-DARS-LIVE-PROVIDER-ADVISORY-SMOKED-REVIEW-GATE-V0-0-125
title: DARS Live-Provider Advisory Smoked Review Gate
version: v0.0.125
status: current-state-reviewed
created: 2026-05-28
---

# DARS Live-Provider Advisory Smoked Review Gate

```text
task_id=DARS-LIVE-PROVIDER-ADVISORY-SMOKED-REVIEW-GATE
accepted_claim=live_provider_advisory_smoked_current_state_reviewed
live_provider_advisory_smoked: usable_with_scoped_human_review
scope=codex_subscription_subprocess_transport_only
single_operator_dars_panel_usable=true
active_transport_evidence_ref=docs/reports/dars-r4c-codex-subprocess-panel-smoke-success-2026-05-28.md
next_safe_task=MB-CODEBASE-M21-6-PREP
```

## Evidence scope

This review answers the operator's current-state question about `live_provider_advisory_smoked`. The accepted repository record set already preserves the R3 mapped-subscription bridge and the later R4C Codex subprocess panel success report as active controlled evidence for the single-operator DARS panel.

The usable claim is deliberately scoped: `live_provider_advisory_smoked` is usable only under scoped human review, for the Codex subscription subprocess transport path. It does not mean raw provider API readiness, adapter-native real-provider readiness, unattended operation readiness, DARS completion, or release execution.

## Boundary flags

```text
raw_provider_api_readiness=false
adapter_native_readiness=false
dars_completion_upgrade_claimed=false
bounded_unattended_advisory_operation_ready=false
released_for_controlled_advisory_use=false
release_action_authorized=false
credential_lookup_by_hisys=false
live_external_action_authorized=false
live_model_call_authorized=false
raw_provider_api_call_by_hisys=false
standing_unattended_approval_activated=false
human_review_removal_authorized=false
requires_human_review=true
```

## Decision

The DARS panel can be treated as usable for local, single-operator, human-reviewed advisory work through the accepted scoped Codex-subprocess evidence. Hisys must still keep every live external action, raw provider API, credential lookup, unattended activation, completion-upgrade, release, deployment, publication, notification, and human-review-removal boundary closed until a separate exact approval and evidence packet authorizes that boundary.
