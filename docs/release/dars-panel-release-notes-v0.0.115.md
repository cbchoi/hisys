---
title: DARS Panel Release Notes v0.0.115
version: v0.0.115
date: 2026-05-25
---

# DARS Panel Release Notes v0.0.115

## Package-upload registry/artifact approval packet incomplete

The approval tokens were received, but required policy details were not included. The accepted claim is limited to `release_package_upload_registry_artifact_approval_packet_incomplete`.

The received tokens are `APPROVE-PACKAGE-UPLOAD-REGISTRY-v0.0.113`, `APPROVE-PACKAGE-UPLOAD-ARTIFACT-BUILD-v0.0.113`, and `APPROVE-PACKAGE-UPLOAD-VERSION-ALIGNMENT-v0.0.113`. The packet remains incomplete because it does not include the target registry policy, artifact build command/output directory, artifact hash recording method, version-alignment basis, credential-reference handling, and the boundary that upload execution remains separately gated.

The lock state remains `approval_tokens_received=true`, `approval_policy_details_received=false`, `composite_approval_packet_complete=false`, `registry_human_approval_recorded=false`, `artifact_build_human_approval_recorded=false`, `version_alignment_human_approval_recorded=false`, `registry_target_selected=false`, `distribution_artifact_built=false`, `package_version_alignment_verified=false`, `build_command_executed=false`, `upload_command_executed=false`, `package_upload_authorized=false`, `package_upload_performed=false`, `package_registry_interaction_performed=false`, and `credential_lookup_by_hisys=false`.

Next safe task: `DARS-LIVE-RELEASE-PACKAGE-UPLOAD-REGISTRY-ARTIFACT-EXACT-APPROVAL`.
