# Hisys DRLOO Control Rules

Task ID: `HISYS-DRLOO-ADAPT-1-CONTROL-RULES`

This document applies DRLOO-derived loop-control semantics to the root Hisys RLOO controller without changing Hisys product scope or authority. The increment is docs/control only: it defines how future `/rloo` runs distinguish safe continuation from true stop conditions.

## Objective

Hisys already carries a long RLOO history with completed DARS, codebase-analysis, release, and subsystem-role-separation records. DRLOO adds a stricter operating distinction among:

1. historical/completed candidate surfaces;
2. advisory or backlog-only candidate surfaces;
3. the cleaned active surface that may actually seed the next local-safe row.

The expected outcome is that Hisys can continue local-safe work without repeated approval prompts while avoiding accidental reactivation of completed, historical, live-authority, release, credential, or product-scope rows.

## Local-safe continuation rule

An explicit operator request to continue, run RLOO, or apply DRLOO authorizes only local-safe documentation/control, fixture-only tests, fake/injected transport tests, validation, and coherent local commits. The request does not authorize live or consequential action.

Allowed under this rule:

- local-safe documentation/control edits;
- fixture-only tests and fake/injected transport tests;
- validation commands under the repository;
- local commit of one coherent increment after green gates;
- queue-end refill and stop-preflight bookkeeping.

Locked boundaries remain locked:

- live provider/model call;
- credential lookup;
- standing unattended approval activation;
- release tag/package/upload/deploy/publication;
- external notification;
- raw provider API;
- `requires_human_review=false` or any equivalent removal of human review.

## Preflight-to-implementation continuation rule

When a controlled row is already selected as the next safe task and a local PREP/PREFLIGHT checkpoint passes, the operator's explicit request to run DRLOO, continue, or proceed authorizes a repeated local-safe implementation loop for the same controlled next_safe_task family:

```text
PREP/PREFLIGHT -> RED -> GREEN -> VALIDATE -> COMMIT
```

The loop may repeat without another approval prompt while each iteration stays inside the same controlled family, uses local files only, writes RED tests before GREEN changes when behavior changes, runs focused and repository validation, and records traceability/profile/Ralph reflections after each coherent commit.

This preflight-to-implementation continuation rule is intended to avoid stopping after every local preflight when the next implementation step is still fixture or loopback local. It does not authorize scope expansion. DRLOO must stop before production listener activation, Hermes config mutation, live provider/model calls, credential lookup, raw provider API use, release/deploy/publication, external notification, remote push, branch rewrite/force push, destructive Git, or human-review removal.

## Candidate-state reconciliation

Before seeding a new row, Hisys RLOO must reconcile candidate state. Candidate-state reconciliation classifies each candidate as one of the following:

| Class | Meaning | Action |
|---|---|---|
| completed/historical | Already accepted, closed, or preserved only as evidence/history | Do not seed. Record as historical if relevant. |
| advisory/backlog-only | Useful future direction but not an executable row under current authority | Do not seed unless a safe PREP can be authored from current controlled anchors. |
| local-safe documentation/control | Can be executed from existing anchors without changing product scope or authority | May seed a PREP or docs/control gate row. |
| fixture-only implementation/test | Can be tested through deterministic fixtures or fake/injected transports only | May seed RED/GREEN rows if product scope is already controlled. |
| human-gated/live-authority | Requires live action, credential/security authority, release/publication, external notification, or product-scope expansion | Stop and report exact missing authority. |

No active implementation row may be derived from historical/completed, advisory-only, or human-gated surfaces merely because the text still appears in `ralph.md`, `ralph.history.md`, release notes, traceability files, or historical readiness records.

## Queue-end refill checkpoint

Queue end is not itself a stop condition. Before stopping at queue end, Hisys RLOO must run a queue-end refill checkpoint:

1. read `ralph.md`, the latest reflection/resume checkpoint, milestone bootstrap profile, traceability summaries, release/checklist docs, controlled plans, current tests, and Git state;
2. identify candidate next task families;
3. run candidate-state reconciliation;
4. build the cleaned active surface containing only current local-safe documentation/control or fixture-only rows;
5. if the cleaned active surface contains a safe row, seed the smallest PREP/RED/GREEN/GATE sequence and continue;
6. if the cleaned active surface is empty, record a stop packet naming the inspected anchors and why no local-safe row remains.

The stop packet must not merely say that work is complete. It must state which candidate families were inspected and why each was completed/historical, backlog-only, local-safe, fixture-only, or human-gated/live-authority.

## Application boundary for this increment

This increment changes the controller semantics only. It does not modify Hisys runtime behavior, Hisys DARS/Judge/Altas product claims, MCP sidecar behavior, or release state. It does not execute a model call, raw provider API, credential lookup, standing unattended activation, artifact build, deployment, publication, external notification, remote push, force push, branch rewrite, or human-review removal. The preflight-to-implementation continuation rule permits repeated local-safe implementation loop execution only inside an already selected controlled next_safe_task family and still requires DRLOO to stop before production listener, live, credential, release, external-action, remote, destructive Git, or human-review boundary crossings.

The next safe task remains `JUDGE-SUBSYSTEM-READINESS-PACKET-CONTINUATION` unless a later controlled checkpoint explicitly changes the active queue.
