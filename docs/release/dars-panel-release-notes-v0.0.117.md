---
title: DARS Panel Release Notes v0.0.117
version: v0.0.117
date: 2026-05-25
---

# DARS Panel Release Notes v0.0.117

## Package registry/upload scope discarded

The package distribution registry/upload scope is discarded. The operator clarified that the DARS panel is for single-operator use and there is no plan to register or publish it through a package distribution registry such as PyPI/TestPyPI.

The accepted claim is `release_package_registry_upload_scope_discarded`. The previous composite upload approval packet is retired instead of completed: `registry_policy_details_required=false`, `composite_upload_approval_packet_retired=true`, `package_upload_path_active=false`, `pypi_registry_use_planned=false`, and `testpypi_registry_use_planned=false`.

The decision concerns package distribution registry/upload scope only. It does not retire Hisys source registries, evidence registries, or fixture registries used by local project mechanics and tests.

All live/external/package actions remain locked: `distribution_artifact_built=false`, `build_command_executed=false`, `upload_command_executed=false`, `package_upload_authorized=false`, `package_upload_performed=false`, `package_registry_interaction_performed=false`, `credential_lookup_by_hisys=false`, `live_external_action_authorized=false`, and `requires_human_review=true`.

Next safe task: `DARS-LIVE-RELEASE-LOCAL-ARTIFACT-RELEASE-SCOPE-REVIEW`.
