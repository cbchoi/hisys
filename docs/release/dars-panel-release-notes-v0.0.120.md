---
title: DARS Panel Release Notes v0.0.120
version: v0.0.120
date: 2026-05-28
---

# DARS Panel Release Notes v0.0.120

## Repository-record recommendation recorded

The repository-record recommendation is recorded for the single-operator DARS panel. The accepted claim is `repository_record_recommendation_recorded_for_human_review`.

The active controlled record set recommends `docs/reports/dars-r4c-codex-subprocess-panel-smoke-success-2026-05-28.md` as the current R4C transport-evidence record. The historical-only record set recommends `docs/reports/dars-r4-codex-subprocess-panel-smoke-auth-stop-2026-05-24.md` as historical blocker evidence.

The R4C claim remains narrow: `r4c_codex_subscription_multi_critic_panel_smoke_completed_with_findings` is recorded, while `dars_completion_upgrade_claimed=false`, `bounded_unattended_advisory_operation_ready=false`, and `human_review_removal_authorized=false` remain explicit boundaries.

Safety boundaries remain closed: `package_upload_scope_retired=true`, `credential_lookup_by_hisys=false`, `live_external_action_authorized=false`, `live_model_call_authorized=false`, `raw_provider_api_call_by_hisys=false`, and `requires_human_review=true`.

Next safe task: `DARS-LIVE-RELEASE-POST-INVENTORY-REVIEW-GATE`.
