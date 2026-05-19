---
doc_id: HISYS-DARS-CP-SRS-001
title: DARS Critic Panel Runtime Requirements
version: 0.1.0
document_status: draft-for-tdd
created: 2026-05-19
updated: 2026-05-19
source_packet: /tmp/hisys-dars-critic-panel-instance/runtime-boundary/agent-workflows/20260519/SPEC-DARS-CRITIC-PANEL-001.json
parent_requirements: [HISYS-FR-AGT-001, HISYS-FR-AGT-002, HISYS-FR-AGT-003, HISYS-FR-AGT-004, HISYS-FR-DOM-003, HISYS-FR-DOM-004, HISYS-NFR-REL-001, HISYS-NFR-SEC-001, HISYS-NFR-SEC-004]
---

# DARS Critic Panel Runtime Requirements

## 1. Purpose

This document defines TDD-ready requirements for extending DARS from a single advisory critique path into a governed critic panel runtime. Hisys remains the system of record. DARS critics are advisory-only agent roles that produce schema-validated critique artifacts and may be executed serially or in bounded parallel under a runtime boundary record.

## 2. Scope

In scope:

- critic panel configuration and role selection;
- execution-plan tasks for logical, evidence, safety, process, and domain critics;
- local fixture/loopback critic execution only for the first increment;
- structured critique, round trace, and synthesis artifacts;
- governance invariants for advisory-only behavior, no mutation, no external call by default, and human reviewability;
- TDD anchors and traceability to SDD/STD/pytest skeletons.

Out of scope for this increment:

- live external DARS service calls;
- agent file edits or repository mutation;
- publication, alert delivery, autonomous approval, or software trigger execution;
- production worker queues beyond serial/bounded-parallel contracts.

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
| HISYS-NFR-DARS-CP-001 | The runtime shall isolate individual critic failures so unrelated critics can complete and the synthesis can report partial evidence when policy allows. | One failing fixture critic yields a failed task result while another completes; synthesis reports `needs_more_evidence`. | HISYS-T-DARS-CP-009 |
| HISYS-NFR-DARS-CP-002 | Panel artifacts shall not contain credentials, token values, or unrestricted raw prompt text. | Secret scan over new docs/tests and artifact fixtures finds no credential patterns. | HISYS-T-DARS-CP-010 |

## 4. TDD Readiness

A developer can begin with failing tests before production code because each requirement has a stable ID, an observable artifact contract, a corresponding STD testcase, and a pytest skeleton in `tests/unit/test_dars_critic_panel_runtime.py`.
