# M21 Advanced Codebase-Analysis Roadmap Implementation Plan

> **For Hermes:** Execute one M21 increment at a time with strict Plan -> RED -> GREEN -> validate -> commit discipline. Use the `test-driven-development` skill for code-bearing tasks and the `milestone-bootstrap` follow-on pattern for Prepare/document-RED checkpoints.

**Goal:** Convert the M21 advanced codebase-analysis backlog into a sequenced, local-only, advisory-only implementation roadmap after M21.1 and M21.2 are complete.

**Architecture:** M21 remains a chain of bounded analyzers and reporters over existing local artifacts. Each increment reads controlled repo files or runtime-boundary artifact refs, emits JSON/Markdown under `runtime-boundary/<surface>/<YYYYMMDD>/`, and exposes a thin CLI only after a Prepare/doc-RED checkpoint. The roadmap prioritizes artifacts that improve governance observability before any live connector, credential, subagent, LSP, or external comparison surface.

**Tech Stack:** Python 3, pytest, argparse CLI in `src/hisys/cli/main.py`, operation modules under `src/hisys/operations/`, runtime-boundary writers using existing path/ref conventions, docs under `docs/traceability/`, `docs/plans/`, and `ralph.md`.

**Context Packet:** Current HEAD at planning time is `fa54acd feat: add traceability coverage CLI wrapper`; branch `dars` is ahead of origin and no remote push is authorized. Completed M21 anchors are `docs/plans/m21-1-traceability-coverage-report-implementation-tasks.md`, `docs/plans/m21-2-traceability-coverage-cli-wrapper-implementation-tasks.md`, `src/hisys/operations/traceability_coverage.py`, `scripts/report_traceability_coverage.py`, `src/hisys/cli/main.py`, `tests/unit/test_traceability_coverage.py`, and `tests/unit/test_domain_cli.py`. Source backlog anchor is `ralph.md` Milestone M21 lines describing change-impact analyzer, traceability coverage checker, runtime-boundary consistency checker, code-analysis pass-contract loop, architecture candidate generator, approved OSS comparison adapter, optional local LSP adapter, subagent evidence collector protocol, regression benchmark fixture repositories, and codebase map freshness/drift review.

**Boundary Record:** Local file writes and local Git commits are allowed after validation. Remote push, publication, live external access, credential resolution, raw source archival, process-spawning adapters, subagent execution protocols, LSP servers, and external OSS comparison calls remain unauthorized until separately planned and approved.

---

## Roadmap principles

1. **Evidence before automation.** Build reports and consistency checks before generators or analyzers that depend on those reports.
2. **Local-only/advisory-only.** Every M21 increment must record `external_call_made=false`, `allowed_actions=advisory_only`, and human-review-required semantics where applicable.
3. **Refs and counts over raw content.** Runtime reports may store IDs, relative refs, digests, status flags, counts, and issue summaries. They must not store raw source snapshots or secrets.
4. **Prepare before implementation.** For each new M21.x behavior, create a document-RED plan first, then implement through a focused failing test.
5. **One coherent commit per increment.** Do not batch multiple M21 behaviors into one commit.

## Candidate sequencing

| Order | Increment | Decision | Rationale | Gate before implementation |
|---:|---|---|---|---|
| Done | M21.1 Traceability coverage report | Complete | Produced local coverage JSON/Markdown and coverage data for later candidates. | Already committed at `6e5a1ce`. |
| Done | M21.2 Traceability coverage CLI wrapper | Complete | Exposed the coverage reporter through a thin CLI without changing advisory semantics. | Already committed at `fa54acd`. |
| 1 | M21.3 Runtime-boundary consistency checker | Start next | Pure local read-only over runtime-boundary refs; detects missing files, unsafe `..`, absolute refs, malformed JSON, and missing advisory flags. This gives later analyzers a trustworthy artifact substrate. | Prepare/doc-RED plan, then RED unit test expecting missing module/CLI. |
| 2 | M21.4 Codebase map freshness/drift review | Start after M21.3 | Uses existing codebase-analysis refs and git metadata to report stale or missing map artifacts without reading or archiving raw source. | Requires M21.3 consistency report shape or explicit waiver. |
| 3 | M21.5 Regression benchmark fixture repositories | Start after M21.4 | Adds deterministic fixture repositories and expected reports so future analyzers can be benchmarked without live repos. | Requires fixture scope doc and no external clone/download. |
| 4 | M21.6 Change-impact analyzer Prepare + local MVP | Start after benchmark fixtures | Uses M21.1 coverage data plus local git diff/file refs to produce advisory impacted requirement/test/design IDs. | Requires M21.1/M21.2 stable coverage and M21.5 fixtures. |
| 5 | M21.7 Architecture candidate generator Prepare + local MVP | Defer until M21.6 | Generator should consume trusted coverage/impact/freshness facts rather than infer from raw source. | Requires human gate before any recommendation wording beyond advisory candidates. |
| 6 | M21.8 Code-analysis pass-contract loop | Defer | Cross-cutting; should follow stable reports and fixtures. | Requires explicit pass/fail schema and rollback plan. |
| Later | Approved OSS comparison adapter | Human gate | External comparison surface; even if fixture-only first, it changes evidence provenance. | Requires approved-source/fixture contract and no live calls. |
| Later | Optional local LSP adapter | Human gate | Process-spawning surface and local tool dependency. | Requires process boundary record and opt-in runtime config. |
| Later | Subagent evidence collector protocol | Human gate | Agent execution/provenance surface; higher governance risk. | Requires protocol schema, sandbox boundary, and explicit approval. |

## M21.3 detailed implementation plan — runtime-boundary consistency checker

### Task M21.3-PREP: Prepare/document-RED runtime-boundary consistency checker

**Objective:** Create the implementation plan and bootstrap artifacts for a local-only checker before production code.

**Files:**
- Create: `docs/plans/m21-3-runtime-boundary-consistency-checker-implementation-tasks.md`
- Update: `docs/milestone-bootstrap/*v0.0.10*`
- Update: `ralph.md`

**Steps:**
1. Inspect current writer/ref conventions in `src/hisys/operations/codebase_analysis.py`, `src/hisys/operations/traceability_coverage.py`, and runtime-writing CLI tests.
2. Write a plan defining a pure operation `src/hisys/operations/runtime_boundary_consistency.py` and optional later CLI `hisys runtime-boundary-check`.
3. Define RED test `tests/unit/test_runtime_boundary_consistency.py::test_runtime_boundary_consistency_flags_missing_and_unsafe_refs`.
4. Validate docs/YAML/JSON, run focused existing gates, and commit `docs: prepare runtime-boundary consistency checker`.

**Expected first RED:**
```bash
PYTHONPATH=src pytest tests/unit/test_runtime_boundary_consistency.py::test_runtime_boundary_consistency_flags_missing_and_unsafe_refs -q
```
Expected failure: `ModuleNotFoundError: No module named 'hisys.operations.runtime_boundary_consistency'`.

### Task M21.3-RED/GREEN: Implement pure consistency report

**Objective:** Add a bounded pure checker and runtime writer with no CLI yet.

**Files:**
- Create: `tests/unit/test_runtime_boundary_consistency.py`
- Create: `src/hisys/operations/runtime_boundary_consistency.py`
- Update: `docs/traceability/README.md`
- Update: `ralph.md`

**Behavior:**
- Input is a caller-provided list of runtime refs and/or a bounded local root scan under `runtime-boundary/`.
- Reject or flag refs that are absolute, contain `..`, do not start with `runtime-boundary/`, or point outside the instance root.
- Report missing files, malformed JSON files, mismatched JSON/Markdown pairs when the writer convention expects both, and missing advisory boundary flags where applicable.
- Persist report under `runtime-boundary/runtime-boundary-consistency/<YYYYMMDD>/consistency-report.{json,md}`.

**Validation:**
```bash
PYTHONPATH=src pytest tests/unit/test_runtime_boundary_consistency.py -q
PYTHONPATH=src pytest tests/unit/test_traceability_coverage.py tests/unit/test_domain_cli.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

### Task M21.3-CLI: Add thin CLI wrapper only after pure checker is stable

**Objective:** Expose `hisys runtime-boundary-check --instance <root> --date <YYYYMMDD>` as a thin dispatcher.

**Files:**
- Modify: `tests/unit/test_domain_cli.py`
- Modify: `src/hisys/cli/main.py`
- Update: `docs/traceability/README.md`
- Update: `ralph.md`

**First RED:** add CLI smoke test and expect argparse rejection of `runtime-boundary-check`.

**Non-goals:** no live probes, no deletion/repair, no external filesystem outside the instance root, no credential resolution.

## M21.4 detailed plan — codebase map freshness/drift review

### Task M21.4-PREP

Create `docs/plans/m21-4-codebase-map-freshness-drift-review-implementation-tasks.md`. Define tests around local codebase-analysis bundle refs and git metadata only.

### Task M21.4-RED/GREEN

Add `src/hisys/operations/codebase_map_freshness.py` and `tests/unit/test_codebase_map_freshness.py`.

Expected report path:
```text
runtime-boundary/codebase-map-freshness/<YYYYMMDD>/freshness-report.{json,md}
```

Report fields should include bundle refs, observed/generated dates, current HEAD short hash if provided by caller, stale/missing/ref-unsafe counts, `external_call_made=false`, and advisory-only status. Do not read or persist raw code content.

## M21.5 detailed plan — regression benchmark fixture repositories

### Task M21.5-PREP

Create a fixture design doc describing small synthetic repo shapes: empty repo, single Python module with tests, multi-language docs/code mix, missing test anchors, and malformed runtime refs.

### Task M21.5-RED/GREEN

Add fixture directories under a controlled fixture path such as `tests/fixtures/codebase_repos/` and expected JSON reports. Tests should run analyzers against local fixture paths only. No `git clone`, no network, no external package install.

## M21.6 detailed plan — change-impact analyzer

### Task M21.6-PREP

Define a local diff/ref input schema. It may accept a caller-provided changed-file list or a local git diff summary, but no remote branch fetch.

### Task M21.6-RED/GREEN

Add `src/hisys/operations/change_impact.py` and tests. The MVP maps changed files to advisory impacted requirement/test/design IDs using existing coverage anchors and fixture maps.

Expected report path:
```text
runtime-boundary/change-impact/<YYYYMMDD>/impact-report.{json,md}
```

## M21.7+ deferred candidates

- **Architecture candidate generator:** consume M21.1/M21.4/M21.6 facts; produce candidate sets and rationale only. No implementation authority.
- **Code-analysis pass-contract loop:** define pass contracts only after fixture benchmark reports stabilize.
- **Approved OSS comparison adapter:** requires approved fixture/source contract and human gate before live use.
- **Optional local LSP adapter:** requires process boundary, opt-in config, and timeout/kill semantics.
- **Subagent evidence collector protocol:** requires provenance schema and explicit sandbox/approval boundary.

## Quality gates for every M21 increment

Run focused tests first, then the current Hisys safety gates:

```bash
PYTHONPATH=src pytest tests/unit/test_traceability_coverage.py tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_cli.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

Add new focused tests to the first command as M21.3+ files are created.

## Stop conditions

Stop and ask for a new decision if any next step would require:

- remote push or changed remote configuration;
- live external network, browser, connector, model, or LSP process use;
- credential lookup, mutation, or persistence;
- raw source archival or broad source-content embedding in reports;
- deletion/repair of runtime artifacts rather than advisory reporting;
- subagent execution protocol or cross-agent provenance claims;
- schema/data migration with compatibility risk.

## Next executable action

The next safe task is **M21.3-PREP — runtime-boundary consistency checker Prepare/document-RED**. It should be committed as a docs/control increment before any `runtime_boundary_consistency.py` production module is created.
