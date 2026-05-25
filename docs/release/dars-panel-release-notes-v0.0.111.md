---
doc_id: HISYS-DARS-R7-RC-NOTES-020
title: DARS Panel Release Notes v0.0.111
version: v0.0.111
status: package-upload-instruction-override-accepted-for-command-preflight
created: 2026-05-25
---

# DARS Panel Release Notes v0.0.111

Package-upload instruction override accepted for command preflight.

This increment records `DARS-LIVE-RELEASE-PACKAGE-UPLOAD-INSTRUCTION-OVERRIDE` after the operator challenged the exact-token requirement and instructed `override` because the action/version had already been described as `execute package upload v0.0.110`. The accepted claim is `release_package_upload_instruction_override_accepted_for_command_preflight`.

The override accepts the prior natural-language instruction only for advancing to `DARS-LIVE-RELEASE-PACKAGE-UPLOAD-COMMAND-PREFLIGHT`. Actual package upload is still not performed. `package_upload_command_preflight_required=true`, `package_upload_authorized=false`, `package_upload_performed=false`, `package_registry_interaction_performed=false`, `credential_lookup_by_hisys=false`, `deployment_authorized=false`, `publication_authorized=false`, `external_notification_authorized=false`, `live_external_action_authorized=false`, `live_model_call_authorized=false`, `raw_provider_api_call_by_hisys=false`, `standing_unattended_approval_activated=false`, `human_review_removal_authorized=false`, `force_push_authorized=false`, `branch_rewrite_authorized=false`, and `requires_human_review=true` remain in force.
