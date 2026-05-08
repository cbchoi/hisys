# Hisys Traceability Summary

This summary links product-code modules and tests in this repository to the
controlled Hisys documentation at
`/home/cbchoi/workspaces/sysailab/pre-develop/Hisys/`.

The controlled docs (and especially `INDEX.md` there) are authoritative.
This file is a working pointer; if it drifts, fix it here, not in the docs.

## Implemented increments

| Increment | Source doc | Status here |
|---|---|---|
| I0 Repository skeleton | HISYS-IMP-001 (implementation-plan.md) Section 3 | Complete |
| I1 Schemas and IDs | HISYS-IMP-001 Section 3; HISYS-SCHEMA-001 (schema-definitions.md) | Initial Pydantic v2 models for all named records |
| I2 Source governance | HISYS-IMP-001 Section 3; HISYS-SRC-REG-INIT-001; HISYS-CHECK-WEB-001 | Initial in-memory registry, fixture registry, and web compliance gate |
| I3 Adapter framework | HISYS-IMP-001 Section 3; HISYS-IDD-001 HISYS-IF-003/HISYS-IF-015; HISYS-FIXTURE-001 | Common DataSource contract, fixture adapters, registry-gated runtime, health report, and failure isolation |
| I4 Investigator foundation | HISYS-INST-INV-001; HISYS-RUNTIME-DIR-001; HISYS-HARNESS-GUIDE-001; HISYS-D-015; HISYS-D-016 | Runtime instance paths, YAML config loader, audit/observation persistence, Hermes boundary writer, Investigator collection skeleton, example instance, and CI smoke gate |
| I4 CLI glue | HISYS-INST-INV-001; HISYS-RUNTIME-DIR-001; HISYS-D-015; HISYS-D-016 | `hisys validate-config`, fixture-backed `hisys collect`, Hermes Markdown boundary record persistence, and JSON/Markdown run summary persistence |

I4 is present as a fixture-backed foundation/skeleton with CLI glue for local
runtime execution. Full Investigator workflow coverage remains pending; later
increments (I5 extraction, I6 editorial, I7 chief editor, I8 DARS loop, I9
hardening) are not implemented yet.

## Module to controlled-doc map

| Module | Controlled doc / SRS area | Test |
|---|---|---|
| `hisys.core.ids` | HISYS-DATA-001 (stable IDs) | `tests/unit/test_core.py` |
| `hisys.core.time` | HISYS-IDD-001 Section 2 (ISO timestamps) | `tests/unit/test_core.py` |
| `hisys.core.errors` | HISYS-SDD-001 Section 8 (failure handling) | `tests/unit/test_core.py` |
| `hisys.core.result` | HISYS-IDD-001 Section 2 (error status) | `tests/unit/test_core.py` |
| `hisys.schemas.source` | HISYS-FR-SRC-001..005, HISYS-SCHEMA-001 Section 3 | `tests/unit/test_schemas.py` |
| `hisys.schemas.compliance` | HISYS-CHECK-WEB-001, HISYS-NFR-SEC-003, HISYS-NFR-SEC-005, HISYS-CON-022..023 | `tests/unit/test_registry.py` |
| `hisys.registry.source_registry` | HISYS-SRC-REG-INIT-001, HISYS-FR-SRC-001..005, HISYS-T-001..002 | `tests/unit/test_registry.py` |
| `hisys.adapters.base` | HISYS-IDD-001 Section 4, HISYS-FR-DS-001..006, normalize/provenance/error contract | `tests/unit/test_adapters.py` |
| `hisys.adapters.runtime` | HISYS-FR-DS-005, HISYS-NFR-REL-001, HISYS-CON-014, HISYS-T-006 | `tests/unit/test_adapters.py` |
| `hisys.schemas.observation` | HISYS-FR-INV-002..005, HISYS-DATA-002, HISYS-SCHEMA-001 Section 4 | `tests/unit/test_schemas.py` |
| `hisys.schemas.signal` | HISYS-FR-EXT-001..004, HISYS-SCHEMA-001 Section 5 | `tests/unit/test_schemas.py` |
| `hisys.schemas.perspective` | HISYS-FR-PER-001..004, HISYS-SCHEMA-001 Section 6 | `tests/unit/test_schemas.py` |
| `hisys.schemas.memo` | HISYS-FR-MEM-001..005, HISYS-SCHEMA-001 Section 7 | `tests/unit/test_schemas.py` |
| `hisys.schemas.alert` | HISYS-FR-CE-002..006, HISYS-SCHEMA-001 Section 8 | `tests/unit/test_schemas.py` |
| `hisys.schemas.handoff` | HISYS-FR-AGT-001..005, HISYS-SCHEMA-001 Section 9, HISYS-DARS-CONTRACT-001 | `tests/unit/test_schemas.py` |
| `hisys.schemas.hermes_trace` | HISYS-FR-DS-006, HISYS-FR-INV-006, HISYS-FR-AGT-005, HISYS-DATA-005, HISYS-SCHEMA-001 Section 10 | `tests/unit/test_schemas.py` |
| `hisys.schemas.audit` | HISYS-FR-ADM-002, HISYS-SCHEMA-001 Section 11 | `tests/unit/test_schemas.py` |
| `hisys.adapters.hardware_mock` | HISYS-FIXTURE-001 hardware-mock-temperature, HISYS-T-003 | `tests/unit/test_adapters.py` |
| `hisys.adapters.web_news_mock` | HISYS-FIXTURE-001 web-news-rss-permitted, HISYS-T-004 | `tests/unit/test_adapters.py` |
| `hisys.adapters.agent_system_mock` | HISYS-FIXTURE-001 agent-dars-critique, HISYS-T-005 | `tests/unit/test_adapters.py` |
| `hisys.adapters.hermes_tool_mock` | HISYS-FIXTURE-001 hermes-tool-hierarchy, HISYS-T-005A | `tests/unit/test_adapters.py`, `tests/integration/test_trace_path.py` |
| `hisys.config.instance` | HISYS-RUNTIME-DIR-001, HISYS-D-015, HISYS-D-016 | `tests/unit/test_instance_config.py` |
| `hisys.config.loader` | HISYS-FR-SRC-001..005, HISYS-T-001..002 | `tests/unit/test_instance_config.py`, `tests/unit/test_example_instance.py` |
| `hisys.audit.writer` | HISYS-FR-ADM-002, HISYS-D-015, secret redaction guard | `tests/unit/test_runtime_writers.py` |
| `hisys.integrations.hermes_boundary` | HISYS-FR-DS-006, HISYS-FR-INV-006, HISYS-DATA-005 | `tests/unit/test_runtime_writers.py` |
| `hisys.investigator.runtime` | HISYS-INST-INV-001, HISYS-FR-INV-001..006, HISYS-T-007..008 | `tests/unit/test_investigator_runtime.py` |
| `hisys.cli.main` | HISYS-PKG-ARCH-001 Section 3, HISYS-RUNTIME-DIR-001, HISYS-INST-INV-001, HISYS-T-001, HISYS-T-005A, HISYS-T-007..008 | `tests/unit/test_cli_runtime.py` |
| `examples/instance` | HISYS-RUNTIME-DIR-001, HISYS-HARNESS-GUIDE-001, HISYS-D-015, HISYS-D-016 | `tests/unit/test_example_instance.py` |

## End-to-end trace path tests

`tests/integration/test_trace_path.py` exercises the path required by
`HISYS-IMP-001` Section 4 and `HISYS-T-024`:

    SourceRegistryEntry
      -> HermesCollectionTrace + RawObservation
      -> ExtractedSignal
      -> ZettelMemo
      -> AlertDecisionRecord
      -> AuditEvent

For each step the test asserts:

- evidence and interpretation records are linked but distinct;
- Hermes hierarchical fields (campaign_id, hermes_parent_run_id, user_input_ref,
  delegated_task_id, tool_invocation_id, prompt_or_query_ref, tool_output_ref,
  boundary_record_ref, scope_policy_ref, approval_state) are populated;
- the boundary record path matches the controlled convention
  `hisys/runtime-boundary/hermes/<YYYYMMDD>/<campaign_id>/<record_kind>-<stable_id>.md`.

## Constraints honored here

- HISYS-CON-022..023: no live web/network calls in this code; only fixtures.
- HISYS-T-001..002: source registry entries require governance metadata;
  web/news collection is blocked without compliance checklist evidence.
- HISYS-T-003..006: adapter contract covers initialization, health,
  collection, normalization, provenance capture, bounded error records, and
  source failure isolation.
- HISYS-T-007..008: Investigator foundation and CLI glue collect from
  registered fixture sources, write RawObservation JSON records, skip
  unregistered sources, append audit JSONL records, persist Hermes Markdown
  boundary records for Hermes sources, and persist JSON/Markdown run summaries
  in the local runtime instance.
- HISYS-D-015: I4 persistence baseline is local JSON/JSONL, not a live database
  or external service.
- HISYS-D-016: Hermes foundation is collection-only and scoped to preapproved
  registered sources and Markdown boundary records.
- HISYS-CON-021: Python 3.11+ runtime baseline.
- HISYS-NFR-SEC-001..002: only fake non-secret tokens in fixtures.
- HISYS-DATA-005: Hermes provenance fields are non-optional in the trace
  record schema and validated at construction time.
