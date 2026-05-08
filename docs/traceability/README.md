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

Later increments (I2 source governance, I3 adapter framework, I4 investigator,
I5 extraction, I6 editorial, I7 chief editor, I8 DARS loop, I9 hardening) are
**not** implemented; only minimal mocks exist to exercise the end-to-end trace
path required by `HISYS-IMP-001` Section 4 ("Definition of Done for Phase-3").

## Module to controlled-doc map

| Module | Controlled doc / SRS area | Test |
|---|---|---|
| `hisys.core.ids` | HISYS-DATA-001 (stable IDs) | `tests/unit/test_core.py` |
| `hisys.core.time` | HISYS-IDD-001 Section 2 (ISO timestamps) | `tests/unit/test_core.py` |
| `hisys.core.errors` | HISYS-SDD-001 Section 8 (failure handling) | `tests/unit/test_core.py` |
| `hisys.core.result` | HISYS-IDD-001 Section 2 (error status) | `tests/unit/test_core.py` |
| `hisys.schemas.source` | HISYS-FR-SRC-001..005, HISYS-SCHEMA-001 Section 3 | `tests/unit/test_schemas.py` |
| `hisys.schemas.observation` | HISYS-FR-INV-002..005, HISYS-DATA-002, HISYS-SCHEMA-001 Section 4 | `tests/unit/test_schemas.py` |
| `hisys.schemas.signal` | HISYS-FR-EXT-001..004, HISYS-SCHEMA-001 Section 5 | `tests/unit/test_schemas.py` |
| `hisys.schemas.perspective` | HISYS-FR-PER-001..004, HISYS-SCHEMA-001 Section 6 | `tests/unit/test_schemas.py` |
| `hisys.schemas.memo` | HISYS-FR-MEM-001..005, HISYS-SCHEMA-001 Section 7 | `tests/unit/test_schemas.py` |
| `hisys.schemas.alert` | HISYS-FR-CE-002..006, HISYS-SCHEMA-001 Section 8 | `tests/unit/test_schemas.py` |
| `hisys.schemas.handoff` | HISYS-FR-AGT-001..005, HISYS-SCHEMA-001 Section 9, HISYS-DARS-CONTRACT-001 | `tests/unit/test_schemas.py` |
| `hisys.schemas.hermes_trace` | HISYS-FR-DS-006, HISYS-FR-INV-006, HISYS-FR-AGT-005, HISYS-DATA-005, HISYS-SCHEMA-001 Section 10 | `tests/unit/test_schemas.py` |
| `hisys.schemas.audit` | HISYS-FR-ADM-002, HISYS-SCHEMA-001 Section 11 | `tests/unit/test_schemas.py` |
| `hisys.adapters.base` | HISYS-IDD-001 Section 4, HISYS-FR-DS-001..002 | `tests/unit/test_adapters.py` |
| `hisys.adapters.hardware_mock` | HISYS-FIXTURE-001 hardware-mock-temperature, HISYS-T-003 | `tests/unit/test_adapters.py` |
| `hisys.adapters.web_news_mock` | HISYS-FIXTURE-001 web-news-rss-permitted, HISYS-T-004 | `tests/unit/test_adapters.py` |
| `hisys.adapters.agent_system_mock` | HISYS-FIXTURE-001 agent-dars-critique, HISYS-T-005 | `tests/unit/test_adapters.py` |
| `hisys.adapters.hermes_tool_mock` | HISYS-FIXTURE-001 hermes-tool-hierarchy, HISYS-T-005A | `tests/unit/test_adapters.py`, `tests/integration/test_trace_path.py` |

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
- HISYS-CON-021: Python 3.11+ runtime baseline.
- HISYS-NFR-SEC-001..002: only fake non-secret tokens in fixtures.
- HISYS-DATA-005: Hermes provenance fields are non-optional in the trace
  record schema and validated at construction time.
