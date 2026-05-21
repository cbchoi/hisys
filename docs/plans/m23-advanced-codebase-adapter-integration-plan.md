# M23 Advanced Codebase Adapter Integration Plan

> **For Hermes/Ralph:** Execute M23 one checkpoint at a time with PREP -> RED -> GREEN -> GATE discipline. The user authorized the previously human-gated advanced code-analysis line on 2026-05-21 KST. This approval opens governed OSS comparison adapter and local LSP adapter work, but it does not authorize credential lookup, secret capture, publication/deployment/release, destructive Git/history actions, new or changed remote configuration, non-fixture live/user data mutation, or unbounded live external provider execution.

**Goal:** Extend Hisys codebase analysis beyond the completed M21/M22 local evidence portfolio by adding governed adapter surfaces for approved OSS comparison and optional local LSP evidence. The outputs must remain advisory code-analysis evidence that can feed the existing codebase evidence portfolio and gate records.

**Authorization packet:** `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.21.md` records the user approval from Discord: `고급 기능 LSP 외부어댑터 통합까지 모두 승인`.

**Boundary record:**

- Authorized: local docs/control planning, local fixture/test data, local adapter interface code, local subprocess spawning only inside the governed LSP adapter boundary with explicit command allowlist/timeout/workspace-root/kill policy, local OSS comparison adapter fixture integration, runtime-boundary/report artifacts under explicit instance roots, traceability updates, local commits, and normal push to existing `origin/dars` after validation.
- Not authorized: credential lookup or mutation, secret capture, arbitrary network search/clone/fetch, new or changed remote configuration, publication/deployment/release, destructive Git/history operations, force push, mutation of non-fixture user/live data, unbounded live external provider execution, or claiming live-provider DARS completion.

---

## M23 task queue

| Row | Task | Type | Status |
|---|---|---|---|
| M23-OSS-ADAPTER-PREP | Define the approved OSS comparison adapter contract, fixture bundle shape, RED tests, and gate commands. | docs/control | next |
| M23-OSS-ADAPTER-RED-GREEN | Implement fixture/local OSS comparison adapter builder/writer and tests. | fixture-local implementation | pending after PREP |
| M23-LSP-ADAPTER-PREP | Define the local LSP adapter contract: command allowlist, timeout, workspace-root restriction, output schema, kill policy, and RED tests. | docs/control | pending after OSS adapter |
| M23-LSP-ADAPTER-RED-GREEN | Implement the governed local LSP adapter boundary and fixture/local smoke tests. | local subprocess implementation | pending after PREP |
| M23-ADAPTER-PORTFOLIO-INTEGRATION | Integrate OSS/LSP adapter refs into the M22 codebase evidence portfolio without raw source archival. | fixture-local implementation | pending after adapter rows |
| M23-ADVANCED-ADAPTER-GATE | Run focused/full relevant gates, update traceability/Ralph/profile, and decide the next queue. | docs/control gate | pending after integration |

## First executable row: M23-OSS-ADAPTER-PREP

**Objective:** Author `docs/plans/m23-oss-comparison-adapter-implementation-tasks.md` before product code.

**Required PREP content:**

- adapter input schema and allowed fixture refs;
- deterministic comparison output schema;
- explicit no-credential/no-secret/no-network-fetch default;
- how approved OSS references are declared in fixture/config records;
- first RED test command and expected failure;
- focused and regression gate commands;
- traceability and portfolio integration anchors.

**Proposed first RED command after PREP:**

```bash
PYTHONPATH=src:. pytest tests/unit/test_oss_comparison_adapter.py::test_oss_comparison_adapter_builds_advisory_report_from_fixture_refs -q
```

Expected initial failure before implementation:

```text
ModuleNotFoundError: No module named 'hisys.operations.oss_comparison_adapter'
```

## Deferred M23 rows

LSP implementation must not start until `M23-LSP-ADAPTER-PREP` records the subprocess command allowlist, timeout, workspace-root restriction, and kill policy. If those details cannot be derived from existing local anchors, Ralph must author a docs/control blocker rather than spawning an unconstrained process.
