# M21.5 Regression Benchmark Fixture Repositories Implementation Plan

> **For Hermes:** Implement this plan one task at a time with strict TDD. Do not create production behavior before the planned RED test has been observed.

**Goal:** Add a local-only regression benchmark fixture surface for codebase-analysis reports so M21 analyzers can be evaluated against deterministic fixture repositories and expected outcomes.

**Architecture:** M21.5 should introduce small synthetic local fixture repositories plus an advisory benchmark report operation. The operation reads only fixture manifests, expected-outcome files, and generated analyzer report refs/counts; it must not clone, fetch, call network services, inspect credentials, or persist raw source snapshots. A CLI wrapper is deferred unless a later Prepare package explicitly authorizes it.

**Tech Stack:** Python 3, pytest, pydantic report models, fixture files under `tests/fixtures/codebase_repos/`, operation module under `src/hisys/operations/`, runtime-boundary JSON/Markdown writer through `resolve_instance_runtime_ref`, traceability docs under `docs/traceability/README.md`.

**Context Packet:** Current HEAD at planning time is `d992905 feat: add codebase-map-freshness-review cli wrapper`; branch `dars` is ahead of origin and no remote push is authorized. Completed M21 anchors include M21.1 traceability coverage, M21.2 traceability coverage CLI, M21.3 runtime-boundary consistency + CLI, and M21.4 codebase map freshness + CLI. Relevant implementation references are `src/hisys/operations/runtime_boundary_consistency.py`, `src/hisys/operations/codebase_map_freshness.py`, `tests/unit/test_runtime_boundary_consistency.py`, `tests/unit/test_codebase_map_freshness.py`, and `tests/unit/test_codebase_symbol_index.py` fixture seeding patterns.

**Boundary Record:** Local fixture files, local tests, local runtime-boundary benchmark reports, docs, and local Git commits are allowed after validation. Remote push, live cloning, package installation, browser/network/model calls, credential lookup, broad source archival, runtime artifact repair/deletion, and any benchmark publication remain unauthorized.

---

## Design decision

Use a small manifest-driven benchmark harness rather than embedding fixture logic directly in analyzer tests.

| Candidate | Decision | Rationale |
|---|---|---|
| Static fixture directories only | Too weak alone | Fixtures help, but no operation records expected outcomes or benchmark status for later M21 consumers. |
| Manifest-driven local benchmark operation | Selected | Gives later M21.6/M21.7 analyzers a stable advisory report surface while preserving local-only/no-live boundaries. |
| Full analyzer replay over live repos | Rejected | Violates no-live-external/no-clone boundary and increases nondeterminism. |

## Expected report path

```text
runtime-boundary/codebase-regression-benchmarks/<YYYYMMDD>/benchmark-report.json
runtime-boundary/codebase-regression-benchmarks/<YYYYMMDD>/benchmark-report.md
```

## Planned fixture set

Create only tiny synthetic repositories under `tests/fixtures/codebase_repos/`:

1. `empty_repo/` — no code and no tests.
2. `single_python_module/` — one module and one test file.
3. `docs_code_mix/` — Markdown docs plus minimal source.
4. `missing_test_anchor/` — source with no matching tests.
5. `malformed_runtime_ref_case/` — manifest entry carrying expected unsafe/malformed runtime refs; do not write unsafe paths.

Each fixture should have a manifest record with:

- fixture ID;
- relative fixture path;
- expected language/file counts or expected analyzer status;
- expected benchmark outcome: `pass`, `warning`, or `expected_issue`;
- rationale and M21 consumer references.

## Task 1: RED — benchmark manifest/report operation is missing

**Objective:** Pin the desired benchmark report behavior before adding fixture repositories or production code.

**Files:**
- Create: `tests/unit/test_codebase_regression_benchmarks.py`
- Future create after RED: `src/hisys/operations/codebase_regression_benchmarks.py`

**Step 1: Write failing test**

Create `tests/unit/test_codebase_regression_benchmarks.py` with `test_codebase_regression_benchmarks_report_expected_outcomes`. The test should import:

```python
from hisys.operations.codebase_regression_benchmarks import (
    BenchmarkFixture,
    build_codebase_regression_benchmark_report,
    write_codebase_regression_benchmark_report,
)
```

The test should create a temporary fixture root with two minimal fixture directories and pass `BenchmarkFixture` objects with expected outcomes. It should assert:

- `schema_id == "hisys.codebase_regression.benchmark.v1"`;
- counts for passed/warning/expected_issue fixtures;
- fixture refs are relative under `tests/fixtures/codebase_repos/` or the supplied local fixture root;
- `external_call_made is False`;
- `mutation_performed is False`;
- `raw_source_content_persisted is False`;
- writer persists JSON/Markdown under `runtime-boundary/codebase-regression-benchmarks/<YYYYMMDD>/`.

**Step 2: Run RED**

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_regression_benchmarks.py::test_codebase_regression_benchmarks_report_expected_outcomes -q
```

Expected failure:

```text
ModuleNotFoundError: No module named 'hisys.operations.codebase_regression_benchmarks'
```

## Task 2: GREEN — minimal advisory benchmark operation

**Objective:** Add the smallest pure operation that classifies fixture outcomes and writes bounded runtime artifacts.

**Files:**
- Create: `src/hisys/operations/codebase_regression_benchmarks.py`
- Modify: `tests/unit/test_codebase_regression_benchmarks.py`

**Implementation shape:**

- `BenchmarkFixture(BaseModel)` with `fixture_id`, `fixture_ref`, `expected_outcome`, and optional `observed_outcome`/`notes`.
- `CodebaseRegressionBenchmarkReport(BaseModel)` with schema ID, sorted fixture partitions, counts, advisory flags, and no raw source content.
- `build_codebase_regression_benchmark_report(*, fixtures: Iterable[BenchmarkFixture])` pure function.
- `write_codebase_regression_benchmark_report(*, instance_root: Path, date: str, report)` writer.

**Constraints:**

- Do not run analyzers over live repos in GREEN.
- Do not read or persist raw fixture file content.
- Do not add CLI in this increment.
- Do not create broad fixture trees; use minimal files only.

**GREEN command:**

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_regression_benchmarks.py -q
```

## Task 3: Fixture repository baseline

**Objective:** Add the minimal fixture directories and manifests needed for deterministic future analyzer replay.

**Files:**
- Create: `tests/fixtures/codebase_repos/empty_repo/README.md`
- Create: `tests/fixtures/codebase_repos/single_python_module/src/example.py`
- Create: `tests/fixtures/codebase_repos/single_python_module/tests/test_example.py`
- Create: `tests/fixtures/codebase_repos/docs_code_mix/README.md`
- Create: `tests/fixtures/codebase_repos/missing_test_anchor/src/untested.py`
- Create: `tests/fixtures/codebase_repos/benchmark_manifest.json`

**Verification:**

Add or extend a test that loads `benchmark_manifest.json`, verifies every fixture path exists, verifies expected outcomes are in the bounded vocabulary, and confirms no fixture path escapes `tests/fixtures/codebase_repos/`.

## Task 4: Documentation and traceability

**Objective:** Record the M21.5 behavior and boundaries.

**Files:**
- Modify: `docs/traceability/README.md`
- Modify: `ralph.md`

Add an implemented-increment row only after GREEN. The row should link the plan, operation module, tests, fixtures, and runtime-boundary path, and state that the benchmark is advisory-only and local-only.

## Validation gates

Focused gate after implementation:

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_regression_benchmarks.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_domain_cli.py -q
```

Project focused gate:

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_regression_benchmarks.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_cli.py -q
```

DARS and safety gates:

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

## Stop conditions

Stop before implementation or ask for a new decision if the next step would require:

- `git clone`, remote fetch, package install, or live repo access;
- credential lookup or secret persistence;
- broad raw source archival in benchmark reports;
- destructive cleanup of fixture/runtime files;
- CLI surface, exit-code policy, or publication beyond this plan;
- changing existing analyzer semantics rather than adding benchmark fixtures.

## Next executable action

After this Prepare plan is committed, run the RED command:

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_regression_benchmarks.py::test_codebase_regression_benchmarks_report_expected_outcomes -q
```
