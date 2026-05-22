# Readiness Decision Record v0.0.44 — Live DARS execution authorization

Date: 2026-05-22

## Request context

User approval received in Discord:

```text
live dars execution approve
```

This supersedes the prior `QUEUE-REFILL-PREP-STOP` classification for the specific candidate **Live-provider DARS execution**. It does not reopen OSS comparison/license execution, which remains future-roadmap only.

## Decision

Authorize a controlled DARS live-execution line under Ralph/RLOO governance.

The first executable checkpoint is a docs/control authorization and PREP row. Product/runtime work must still follow the existing DARS backend plan and runbook boundaries before any model boundary is crossed.

## Allowed first increment

- Record this authorization decision.
- Update `ralph.md`, traceability, and bootstrap profile state.
- Seed a bounded DARS live-execution PREP row.
- Reuse the existing DARS live backend plan and localhost smoke runbook as the first governed execution path.

## Execution boundary

A later live DARS execution may proceed only after the PREP row verifies all of these conditions:

- operator-supplied localhost-only model endpoint;
- no credential requirement and no Authorization header;
- backend activation packet present and valid;
- advisory-only action scope;
- no tool/search/browser permission;
- no mutation request;
- secret scan passes;
- runtime-boundary record path is declared before execution.

Remote subscription/provider execution remains bounded by the existing Codex/Claude subscription-policy and dispatch-harness controls. Raw API-key/provider-token integration, arbitrary provider endpoints, credential lookup, publication, deployment, mutation of non-fixture/live user data, and autonomous decision authority remain out of scope unless separately authorized.

## Non-claims

This decision is not evidence that a live DARS execution has already run. Until a later GREEN/GATE row captures successful runtime-boundary evidence, the DARS completion claim remains `local_fixture_localhost_controlled_advisory_complete`.

This decision does not authorize OSS comparison/license execution. OSS remains future-roadmap only.

## Next Ralph row

`DARS-LIVE-EXECUTION-AUTH-PREP` — docs/control PREP for the governed live DARS execution line.
