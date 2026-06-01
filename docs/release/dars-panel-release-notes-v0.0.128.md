---
doc_id: HISYS-DARS-PANEL-RELEASE-NOTES-V0-0-128
title: DARS Panel Release Notes v0.0.128
version: v0.0.128
status: released-for-controlled-advisory-use
created: 2026-06-02
---

# DARS Panel Release Notes v0.0.128

## Accepted claim

```text
accepted_claim=dars_released_for_controlled_advisory_use
operator_instruction=dars release로 승격
next_safe_task=JUDGE-SUBSYSTEM-READINESS-PACKET-CONTINUATION
```

## Change

This increment promotes the existing DARS panel baseline to release status for controlled advisory use:

```text
dars_release_promoted=true
released_for_controlled_advisory_use=true
dars_bounded_advisory_productized_baseline=true
single_operator_dars_panel_usable=true
requires_human_review=true
```

The promotion is a local controlled-document release record. It uses the accepted productization closure, current-state review, Hermes smoke, and Hisys subsystem role-separation records as its evidence scope.

## Boundary

This release note does not authorize tag creation, tag push, package upload, deployment, publication, external notification, live provider/model calls, raw provider API calls, credential lookup, standing unattended approval activation, branch rewrite, force push, or removal of human review.
