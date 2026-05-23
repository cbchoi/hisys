---
doc_id: HISYS-DARS-CP-SRS-001
title: DARS Critic Panel Runtime Requirements
version: 0.2.0
document_status: draft-for-tdd
created: 2026-05-19
updated: 2026-05-23
source_packet: /tmp/hisys-dars-critic-panel-instance/runtime-boundary/agent-workflows/20260519/SPEC-DARS-CRITIC-PANEL-001.json
release_plan: docs/plans/dars-panel-live-provider-unattended-release-final-plan.md
parent_requirements: [HISYS-FR-AGT-001, HISYS-FR-AGT-002, HISYS-FR-AGT-003, HISYS-FR-AGT-004, HISYS-FR-DOM-003, HISYS-FR-DOM-004, HISYS-NFR-REL-001, HISYS-NFR-SEC-001, HISYS-NFR-SEC-004]
---

# DARS Critic Panel Runtime Requirements

## 1. Purpose

This document defines TDD-ready requirements for extending DARS from a single advisory critique path into a governed critic panel runtime. Hisys remains the system of record. DARS critics are advisory-only agent roles that produce schema-validated critique artifacts and may be executed serially or in bounded parallel under runtime boundary records.

The current accepted completion claim is `local_fixture_localhost_controlled_advisory_complete`. The next product line is live-provider and release completion. That line is claim-gated: live provider execution, bounded unattended advisory operation, release-candidate readiness, and controlled release are separate claims with separate evidence and human decision packets.

## 2. Scope

In scope:

- critic panel configuration and role selection;
- execution-plan tasks for logical, evidence, safety, process, and domain critics;
- local fixture/loopback critic execution and localhost-only rehearsal;
- structured critique, round trace, synthesis, and operator-facing advisory reports;
- governed live-provider policy and transport contracts using credential references, not raw secrets;
- single-critic and multi-critic live-provider smoke gates under explicit human approval;
- bounded unattended advisory operation under finite standing approval, budget/rate limits, kill switch, audit ledger, and post-run human review;
- release-candidate and controlled-release evidence gates;
- governance invariants for advisory-only behavior, no mutation, no publication, no autonomous approval, and human reviewability;
- TDD anchors and traceability to SDD/STD/pytest skeletons.

Out of scope unless a future controlled requirement and decision packet explicitly authorize it:

- unrestricted live external DARS service calls;
- raw credential storage, credential lookup by tests, or secret persistence;
- agent file edits or repository mutation by critics;
- publication, alert delivery, autonomous approval, software trigger execution, deployment, package upload, or release execution without an explicit release decision packet;
- removing `requires_human_review=true` from substantive DARS outputs;
- production worker queues that exceed the bounded unattended advisory policy.

## 3. Requirements

| ID | Requirement | Acceptance direction | Verification |
|---|---|---|---|
| HISYS-FR-DARS-CP-001 | The system shall represent a DARS review as a `DarsCriticPanelConfig` containing one or more named critic roles, each with role ID, backend ID, rubric ref, critique dimensions, output contract, and governance flags. | A fixture config with two critic roles validates; duplicate role IDs or non-`DarsCritiqueRecord` output contracts are rejected. | HISYS-T-DARS-CP-001 |
| HISYS-FR-DARS-CP-002 | The system shall convert a panel config and candidate artifact ref into a `DarsRoundPlan` containing independent critic tasks and explicit synthesis dependency edges. | Two independent critic tasks are created before one synthesis task; each task carries candidate/evidence/rubric refs. | HISYS-T-DARS-CP-002 |
| HISYS-FR-DARS-CP-003 | The system shall execute local fixture/loopback critic tasks as advisory-only tasks that produce `DarsCritiqueRecord` artifacts. | Each fixture critic writes a critique artifact with `allowed_actions=advisory_only`, `action_taken=none`, `mutation_performed=false`, and `external_call_made=false`. | HISYS-T-DARS-CP-003 |
| HISYS-FR-DARS-CP-004 | The system shall persist one `DarsRoundTrace` per panel round, linking candidate ref, critic task refs, critique refs, synthesis ref, unresolved findings, and stop-condition status. | Round trace exists and reconstructs candidate-to-critique-to-synthesis lineage. | HISYS-T-DARS-CP-004 |
| HISYS-FR-DARS-CP-005 | The system shall synthesize multiple critic outputs into a deterministic `DarsCritiqueSynthesis` artifact without granting decision authority. | Synthesis deduplicates finding IDs, preserves critic role provenance, and returns an advisory disposition such as `revise_candidate` or `needs_more_evidence`. | HISYS-T-DARS-CP-005 |
| HISYS-FR-DARS-CP-006 | The runtime shall support serial execution first and a bounded-parallel policy interface for independent critic tasks without changing artifact contracts. | The same round plan is executable under serial mode; max-parallel and dependency semantics are represented in the plan. | HISYS-T-DARS-CP-006 |
| HISYS-FR-DARS-CP-007 | Disabled or external critic backends shall be blocked by default unless explicit approval and policy allow dispatch. | A configured external backend without approval returns a blocked task result and no critique artifact from that backend. | HISYS-T-DARS-CP-007 |
| HISYS-FR-DARS-CP-008 | The system shall distinguish advisory critic output from human-approved decisions in every panel artifact. | Critique, round trace, and synthesis artifacts set `advisory_only=true` or equivalent, `requires_human_review=true`, and never set approval fields. | HISYS-T-DARS-CP-008 |
| HISYS-FR-DARS-CP-009 | The system shall define a live-provider policy packet that permits real provider dispatch only through provider/model allowlists, credential references, explicit approval refs, bounded prompt/output sizes, rate limits, budget refs, and advisory-only action flags. | Policy validation accepts credential references and rejects raw credential fields, secret-looking values, mutation/publication authority, missing approval refs, and unbounded prompt/output or rate settings. | HISYS-T-DARS-CP-011 |
| HISYS-FR-DARS-CP-010 | The system shall provide a live-provider transport contract that can run through fake/injected transports in tests and a gated real provider adapter only after policy, approval, and credential-reference gates pass. | Fake transport tests produce boundary records with no external call; real transport entry points fail closed until every precondition is present. | HISYS-T-DARS-CP-012 |
| HISYS-FR-DARS-CP-011 | The system shall support a reviewed single-critic live-provider advisory smoke claim. | A human-approved smoke crosses one provider/model boundary, records provider/model refs and bounded cost/latency metadata, and preserves no-mutation/no-publication flags. | HISYS-T-DARS-CP-013 |
| HISYS-FR-DARS-CP-012 | The system shall support a reviewed multi-critic live-provider panel smoke claim with failure isolation. | At least two live-provider critic tasks produce per-critic and panel-level boundary records; one failed critic does not erase completed critic evidence. | HISYS-T-DARS-CP-014 |
| HISYS-FR-DARS-CP-013 | The system shall support bounded unattended advisory operation under a finite standing approval policy. | The unattended runner requires expiry, request-class allowlists, budget/rate caps, kill switch, audit ledger, circuit breakers, and post-run human review; it refuses mutation/publication/action authority. | HISYS-T-DARS-CP-015 |
| HISYS-FR-DARS-CP-014 | The system shall expose live/unattended operation status and rollback readiness. | A status surface reports policy refs, kill-switch state, latest run refs, budget/circuit-breaker state, and rollback instructions without exposing secrets. | HISYS-T-DARS-CP-016 |
| HISYS-FR-DARS-CP-015 | The system shall gate release-candidate readiness and controlled release as explicit human-approved claims. | Release candidate evidence includes tests, traceability, secret scan, smoke evidence, unattended canary evidence, rollback docs, release notes, and accepted residual risk; release execution records tag/package/deploy refs only after approval. | HISYS-T-DARS-CP-017 |
| HISYS-NFR-DARS-CP-001 | The runtime shall isolate individual critic failures so unrelated critics can complete and the synthesis can report partial evidence when policy allows. | One failing fixture or live-provider critic yields a failed task result while another completes; synthesis reports `needs_more_evidence`. | HISYS-T-DARS-CP-009, HISYS-T-DARS-CP-014 |
| HISYS-NFR-DARS-CP-002 | Panel artifacts shall not contain credentials, token values, or unrestricted raw prompt text. | Secret scan over new docs/tests and artifact fixtures finds no credential patterns; live-provider policy and activation packets reject raw secret fields. | HISYS-T-DARS-CP-010, HISYS-T-DARS-CP-011 |
| HISYS-NFR-DARS-CP-003 | Live-provider, unattended, and release claims shall preserve auditability and decision-packet boundaries. | Each claim has a boundary record or decision packet before it is reported as achieved; stronger claims are not inferred from weaker evidence. | HISYS-T-DARS-CP-017 |

## 4. Claim ladder

DARS panel completion claims shall be reported only after the corresponding evidence gate passes:

```text
local_fixture_localhost_controlled_advisory_complete
  -> live_provider_advisory_smoked
  -> multi_critic_live_provider_advisory_complete
  -> bounded_unattended_advisory_operation_ready
  -> release_candidate_ready
  -> released_for_controlled_advisory_use
```

## 5. TDD Readiness

A developer can begin with failing tests before production code because each requirement has a stable ID, an observable artifact contract, a corresponding STD testcase, and a pytest anchor. For R1 and later live-provider work, RED tests must use fake/injected transports first and must not read credentials or call live providers.
