# Milestone M21.9 — Subagent Evidence Collector Protocol Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development`. This plan is the document-RED/Prepare artifact for the human-gated M21 backlog candidate “Subagent evidence collector protocol.” The user authorization phrase for this checkpoint is `m21 go` in the Discord Hisys thread on 2026-05-21. The authorization is interpreted narrowly: local documentation/control and fixture-backed schema work only; it does not authorize live subagent execution, external calls, process spawning, remote push, credential access, or publication.

**Goal:** Define a standard, machine-checkable packet contract for bounded read-only subagent evidence collection over codebase-analysis scopes. The first implementation must validate input/output packet shape, provenance flags, sandbox/tool boundaries, artifact/source refs, and parent-verification requirements without invoking any subagent or reading external sources.

**Architecture:** M21.9 adds a protocol contract layer, not an execution layer.

- Controlled contract document: `docs/contracts/subagent-evidence-collector-protocol.md`.
- Python contract module: `src/hisys/contracts/subagent_evidence_collector.py`.
- Unit tests: `tests/unit/test_subagent_evidence_collector_protocol.py`.
- Optional later CLI wrapper is deferred until the pure validator is stable.

The protocol consumes caller-provided dictionaries or JSON objects and emits validated packet objects or deterministic validation errors. It never launches an agent, never calls `delegate_task`, never spawns a process, never reads `.git/`, never opens artifact paths, never performs live network/browser/model access, never persists raw source content, and never grants approval authority.

**Context Packet:** M21.1..M21.8 are complete. The latest M21 queue-refill checkpoint recorded three remaining human-gated candidates: approved OSS comparison adapter, optional local LSP adapter, and subagent evidence collector protocol. The subagent protocol is selected first because it can begin as a local schema/control surface and because `revision_plan_v004.md` Section 7.8 already defines the minimal input/output packet vocabulary.

**Source anchors:**

- `docs/plans/m21-roadmap-implementation-plan.md` lines 37..39 and 145..151: remaining human-gated M21 candidates and subagent protocol requirement for provenance schema plus explicit sandbox/approval boundary.
- `revision_plan_v004.md` Section 7.8: input fields (`task`, `repo path`, include/exclude paths, allowed read-only tools, expected artifact schema, what not to do) and output fields (`summary`, artifact paths, source refs, validation suggestions, blockers, `external_call_made=false`, `mutation_performed=false`) plus parent artifact verification.
- Existing Hisys boundary vocabulary in M21 reports: `advisory_only=true`, `requires_human_review=true`, `external_call_made=false`, `mutation_performed=false`, `raw_source_content_persisted=false`, `allowed_actions=advisory_only`.

---

## Boundary decisions

1. **Protocol only, no execution.** M21.9 does not call Hermes subagents or any agent CLI. It only validates packets that a future parent/orchestrator may use.
2. **Read-only scope.** Input packets may list read-only tool names and bounded include/exclude refs. They may not authorize mutation, publication, network fetch, model calls, credential lookup, process spawning, LSP servers, or raw source archival.
3. **Relative safe refs only.** Repo paths and artifact/source refs must be relative or explicitly classified as opaque refs. Absolute paths and `..` traversal are rejected unless a field is deliberately named as an external opaque identifier and never treated as a filesystem path.
4. **Parent verification remains mandatory.** A result packet may report artifact refs, but success is not established until the parent verifies those refs in its own boundary. The validator records this as `parent_verification_required=true`.
5. **Boundary flags are fixed false.** Result packets must carry `external_call_made=false`, `mutation_performed=false`, and `raw_source_content_persisted=false`. Any true value is a validation failure.
6. **Human-review semantics stay explicit.** Packets are advisory artifacts and cannot mark implementation readiness, approval, or promotion.
7. **No new pass-contract reason-code taxonomy.** If this protocol later feeds pass contracts, that mapping must be a separate Prepare/RED increment.

---

## Task M21.9-PREP: Prepare/document-RED protocol schema

**Objective:** Create this plan and record the narrow authorization boundary before any schema code.

**Files:**

- Create: `docs/plans/m21-9-subagent-evidence-collector-protocol-implementation-tasks.md`
- Update: `ralph.md`

**Validation:**

```bash
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit:** `docs: prepare subagent evidence collector protocol`

---

## Task M21.9.1: Protocol contract + validator (RED -> GREEN)

**Objective:** Add a pure local validator for task/result packets.

**Files:**

- Create: `docs/contracts/subagent-evidence-collector-protocol.md`
- Create: `tests/unit/test_subagent_evidence_collector_protocol.py`
- Create: `src/hisys/contracts/subagent_evidence_collector.py`
- Update: `docs/traceability/README.md`
- Update: `ralph.md`

**First RED:**

```bash
PYTHONPATH=src pytest tests/unit/test_subagent_evidence_collector_protocol.py::test_subagent_task_packet_accepts_bounded_read_only_scope -q
```

Expected failure: `ModuleNotFoundError: No module named 'hisys.contracts.subagent_evidence_collector'`.

**Minimum behavior:**

- Accept a task packet with `schema_id="hisys.subagent_evidence.task.v1"`, `task_id`, `parent_request_id`, `objective`, `repo_ref`, `include_refs`, `exclude_refs`, `allowed_read_only_tools`, `expected_artifact_schema`, `what_not_to_do`, `advisory_only=true`, and `requires_human_review=true`.
- Reject task packets with absolute refs, `..` traversal, empty objective, mutation-capable tool names, process/network/browser/model/credential authority, or `advisory_only=false`.
- Accept a result packet with `schema_id="hisys.subagent_evidence.result.v1"`, matching `task_id`, `summary`, `artifact_refs`, `source_refs`, `validation_suggestions`, `blockers`, `external_call_made=false`, `mutation_performed=false`, `raw_source_content_persisted=false`, and `parent_verification_required=true`.
- Reject result packets when any boundary flag is true or when artifact/source refs are unsafe filesystem refs.
- Return deterministic error codes such as `unsafe_ref`, `mutation_tool_not_allowed`, `external_call_not_allowed`, `raw_source_persistence_not_allowed`, `parent_verification_required_missing`, and `schema_id_mismatch`.

**Focused validation:**

```bash
PYTHONPATH=src pytest tests/unit/test_subagent_evidence_collector_protocol.py -q
PYTHONPATH=src pytest tests/unit/test_code_analysis_pass_contract.py tests/unit/test_code_analysis_pass_contract_fixtures.py tests/unit/test_domain_cli.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

---

## Task M21.9-CLI: Deferred thin wrapper

A CLI wrapper such as `hisys validate-subagent-evidence-packet --task <json> --result <json>` is out of scope until M21.9.1 is stable. If added later, it must be a separate Prepare/RED increment and must not execute a subagent.

---

## Stop / continue rule

Stop after this M21.9-PREP package is committed if the user has not authorized continuing into M21.9.1. If continuing is authorized, the next safe row is Task M21.9.1 RED: add the failing validator test, observe the expected `ModuleNotFoundError`, then implement the minimal pure validator. Stop immediately if implementing the validator would require live subagent execution, process spawning, external network/browser/model calls, credential access, remote push, raw source archival, or a change to pass-contract promotion semantics.
