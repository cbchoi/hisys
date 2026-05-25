---
title: DARS Panel Release Notes v0.0.114
version: v0.0.114
date: 2026-05-25
---

# DARS Panel Release Notes v0.0.114

## Package-upload registry/artifact exact approval missing

Generic 진행 did not provide the composite approval packet required by the registry/artifact exact-approval gate. The gate remains open and the accepted claim is limited to `release_package_upload_registry_artifact_exact_approval_missing`.

The required approval packet still needs all three exact tokens: `APPROVE-PACKAGE-UPLOAD-REGISTRY-v0.0.113`, `APPROVE-PACKAGE-UPLOAD-ARTIFACT-BUILD-v0.0.113`, and `APPROVE-PACKAGE-UPLOAD-VERSION-ALIGNMENT-v0.0.113`, plus the target registry policy, artifact build command/output directory, artifact hash recording method, and version-alignment basis.

The lock state remains `composite_approval_packet_received=false`, `registry_human_approval_recorded=false`, `artifact_build_human_approval_recorded=false`, `version_alignment_human_approval_recorded=false`, `registry_target_selected=false`, `distribution_artifact_built=false`, `package_version_alignment_verified=false`, `build_command_executed=false`, `upload_command_executed=false`, `package_upload_authorized=false`, `package_upload_performed=false`, `package_registry_interaction_performed=false`, and `credential_lookup_by_hisys=false`.

Next safe task: `DARS-LIVE-RELEASE-PACKAGE-UPLOAD-REGISTRY-ARTIFACT-EXACT-APPROVAL`.
