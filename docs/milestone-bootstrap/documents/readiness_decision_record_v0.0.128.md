# Readiness Decision Record v0.0.128

Date: 2026-06-02
Task: `DARS-RELEASE-PROMOTION-GATE`

## Decision

The operator instruction `dars release로 승격` is accepted as authorization to record a local DARS release promotion for controlled advisory use. This is a governance/status promotion only. It does not authorize any concrete external release action.

## Accepted claim

```text
task_id=DARS-RELEASE-PROMOTION-GATE
accepted_claim=dars_released_for_controlled_advisory_use
operator_instruction=dars release로 승격
dars_release_promoted=true
released_for_controlled_advisory_use=true
dars_bounded_advisory_productized_baseline=true
single_operator_dars_panel_usable=true
requires_human_review=true
next_safe_task=JUDGE-SUBSYSTEM-READINESS-PACKET-CONTINUATION
```

## Boundary flags

```text
tag_creation_authorized=false
tag_creation_performed=false
tag_push_authorized=false
tag_push_performed=false
package_upload_authorized=false
package_upload_performed=false
deployment_authorized=false
deployment_performed=false
publication_authorized=false
publication_performed=false
external_notification_authorized=false
external_notification_performed=false
live_external_action_authorized=false
live_model_call_authorized=false
raw_provider_api_call_by_hisys=false
credential_lookup_by_hisys=false
standing_unattended_approval_activated=false
human_review_removal_authorized=false
force_push_authorized=false
branch_rewrite_authorized=false
requires_human_review=true
```

## Evidence scope

- `docs/release/dars-release-promotion-v0.0.128.md`
- `docs/release/dars-panel-release-notes-v0.0.128.md`
- `docs/release/dars-panel-release-candidate-checklist.md`
- `docs/traceability/dars-critic-panel-runtime-traceability.md`
- `docs/milestone-bootstrap/profile.yaml`
- `ralph.md`
- `tests/unit/test_dars_release_promotion_gate.py`
- `tests/unit/test_governance_docs_current_state.py`

## Next safe task

```text
next_safe_task=JUDGE-SUBSYSTEM-READINESS-PACKET-CONTINUATION
```
