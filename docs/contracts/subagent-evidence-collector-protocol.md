# Subagent Evidence Collector Protocol Contract

Traceability: `docs/plans/m21-9-subagent-evidence-collector-protocol-implementation-tasks.md`; `revision_plan_v004.md` Section 7.8.

## Purpose

This contract defines bounded packet shapes for future Hermes subagents that collect codebase-analysis evidence. It is a protocol and validation surface only. It does not authorize subagent execution, process spawning, live network/browser/model calls, credential access, remote synchronization, publication, or raw source archival.

## Task packet

`schema_id`: `hisys.subagent_evidence.task.v1`

Required fields:

- `task_id`: stable task identifier.
- `parent_request_id`: parent Hisys or Hermes request identifier.
- `objective`: bounded objective for the read-only inspection.
- `repo_ref`: safe relative repository reference.
- `include_refs`: safe relative refs the collector may inspect.
- `exclude_refs`: safe relative refs the collector must not inspect.
- `allowed_read_only_tools`: read-only tool names. The initial allowlist is `read_file` and `search_files`.
- `expected_artifact_schema`: expected result schema identifier.
- `what_not_to_do`: explicit prohibitions for the collector.
- `advisory_only`: must be `true`.
- `requires_human_review`: must be `true`.

Validation rejects absolute refs, `..` traversal, empty objective, mutation-capable tools, process/network/browser/model/credential authority, `advisory_only=false`, and missing human-review semantics.

## Result packet

`schema_id`: `hisys.subagent_evidence.result.v1`

Required fields:

- `task_id`: must match the task packet when a parent task is supplied.
- `summary`: bounded natural-language summary.
- `artifact_refs`: safe relative refs to produced artifacts.
- `source_refs`: safe relative refs to evidence sources.
- `validation_suggestions`: commands or checks suggested for the parent.
- `blockers`: unresolved blockers.
- `external_call_made`: must be `false`.
- `mutation_performed`: must be `false`.
- `raw_source_content_persisted`: must be `false`.
- `parent_verification_required`: must be `true`.

A result packet never proves success by itself. The parent must verify returned artifact refs before reporting success or promoting evidence.

## Error-code vocabulary

The initial validator emits deterministic error codes:

- `schema_id_mismatch`
- `required_field_missing`
- `unsafe_ref`
- `read_only_tool_required`
- `mutation_tool_not_allowed`
- `external_call_not_allowed`
- `tool_not_allowed`
- `advisory_only_required`
- `human_review_required`
- `mutation_not_allowed`
- `raw_source_persistence_not_allowed`
- `parent_verification_required_missing`
- `task_id_mismatch`

This vocabulary is local to the subagent evidence protocol. It does not alter pass-contract reason codes.

## Boundary flags

All packets are advisory. M21.9.1 validates packets but does not execute a subagent and does not verify filesystem existence. Parent-side artifact existence checks, runtime-boundary writing, pass-contract integration, and CLI wrapping require separate Prepare/RED increments.
