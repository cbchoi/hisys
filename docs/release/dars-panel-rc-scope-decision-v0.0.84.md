---
doc_id: HISYS-DARS-R7-RC-SCOPE-DECISION-001
title: DARS Panel R7 Release Candidate Scope Decision
version: v0.0.84
status: scope-decision-for-human-review
created: 2026-05-24
---

# DARS Panel R7 Release Candidate Scope Decision

## Request context

The operator instructed `go` after R4H request/response harness closure. This record executes only `DARS-LIVE-RELEASE-R7-RC-SCOPE-DECISION`: it decides the release-candidate scope and records blockers before any release-candidate readiness claim, release artifact, tag, package upload, deployment, publication, or external notification.

accepted_claim=r7_rc_scope_decision_recorded_for_human_review

## Scope decision

The only acceptable RC scope at this point is a **human-review package scope** for the controlled DARS advisory product line. The scope may include local fixture evidence, R3 mapped-subscription single-smoke evidence, R4H Hermes-mediated advisory/request-response harness evidence, R5 PREP dry-run evidence, and R6 local status/rollback readiness evidence.

It must not be presented as a completed release candidate until the remaining human-gated evidence rows are accepted.

```text
release_candidate_ready=false
released_for_controlled_advisory_use=false
bounded_unattended_advisory_operation_ready=false
r5_action_canary_evidence=missing
r4c_codex_subprocess_completion=deferred
raw_provider_api_readiness=false
adapter_native_readiness=false
requires_human_review=true
```

## Evidence allowed in the RC package

- R0-R2 local policy, transport, adapter, and fail-closed evidence.
- R3 mapped-subscription single-critic subprocess smoke review evidence, bounded to Codex subscription subprocess transport only.
- R4H Hermes-mediated advisory and request/response harness evidence, bounded to human review and not equivalent to R4C Codex subprocess completion.
- R5 PREP bounded unattended dry-run policy/runner evidence.
- R6 local status and rollback readiness runbooks.
- Full unit, traceability, secret scan, and diff-check validation evidence.

## Explicit blockers before `release_candidate_ready`

1. Human-reviewed acceptance of the scoped RC package.
2. Explicit residual-risk acceptance for using R4H as the scoped substitute while R4C remains deferred, or a later R4C reconciliation packet.
3. R5 bounded unattended live canary evidence remains missing unless a separate human-gated action packet authorizes and reviews it.
4. Release notes and checklist must preserve the claim ladder and all non-goals.
5. No raw secrets may be persisted; provider credentials remain outside Hisys.

## Boundary

This decision performs no live provider/model call, Codex subprocess retry, raw provider API call, credential lookup, standing unattended approval activation, mutation outside repository docs/tests/control files, rollback execution, release action, publication, or human-review removal. It performs no release tag, package upload, deployment, publication, or external notification.

Next safe task: `DARS-LIVE-RELEASE-R7-RC-PACKET-PREP`.
