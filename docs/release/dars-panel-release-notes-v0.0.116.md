---
title: DARS Panel Release Notes v0.0.116
version: v0.0.116
date: 2026-05-25
---

# DARS Panel Release Notes v0.0.116

## Package-upload registry/artifact policy details partial

The artifact/version policy details were received, but registry policy details are still missing. The accepted claim is limited to `release_package_upload_registry_artifact_policy_details_partial`.

Recorded details include the controlled artifact build command `python -m build --outdir dist/package-upload-v0.0.113`, controlled output directory `dist/package-upload-v0.0.113/`, SHA-256 recording method, version-alignment basis distinguishing DARS release/control version `v0.0.113` from Python package distribution version `0.1.0`, and the explicit boundary that upload execution remains separately gated.

The packet remains incomplete because it does not include target registry policy, registry URL policy, production-PyPI exclusion, or credential-reference handling. Therefore `registry_policy_details_received=false`, `composite_approval_packet_complete=false`, `registry_human_approval_recorded=false`, `artifact_build_human_approval_recorded=false`, `version_alignment_human_approval_recorded=false`, `distribution_artifact_built=false`, `build_command_executed=false`, `upload_command_executed=false`, `package_upload_performed=false`, `package_registry_interaction_performed=false`, and `credential_lookup_by_hisys=false` remain locked.

Next safe task: `DARS-LIVE-RELEASE-PACKAGE-UPLOAD-REGISTRY-ARTIFACT-EXACT-APPROVAL`.
