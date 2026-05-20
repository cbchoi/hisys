# Milestone M21.1 — Traceability Coverage Report Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for every code-bearing task. This plan is the QUEUE-REFILL-PREP / document-RED artifact authored after the M20 milestone closed (`cae708d docs: document codebase domain artifact bridge`). It activates the safest M21 backlog candidate as a spec-first task.

**Goal:** Implement a deterministic, fixture-local traceability coverage report under `scripts/` that consumes the existing controlled traceability anchors (SRS/SDD/IDD/STD references plus `docs/traceability/README.md` rows) and emits a bounded coverage summary (counts of requirements with at least one referenced design/interface/test anchor, gaps where a requirement is unreferenced, and orphaned tests with no requirement reference). The reporter must remain advisory — never approving deployment, never modifying source, never authorizing live action.

**Architecture:** Add a new pure-Python module — for example `scripts/report_traceability_coverage.py` or `src/hisys/operations/traceability_coverage.py` — that loads anchor IDs from the existing controlled-document references (re-using parsers from `scripts/validate_traceability.py` where possible) and emits a deterministic Markdown + JSON pair under `runtime-boundary/traceability-coverage/<YYYYMMDD>/`. Reuse the existing slug validators and `resolve_instance_runtime_ref` chokepoint. No new dependency, no network call, no model invocation, no credential resolution, no destructive Git, no remote push, and no raw source archival.

**Tech Stack:** Python 3.11, regex, pathlib, Pydantic v2 for the report records, pytest. No new dependency.

**Context Packet:** Required source handles: `scripts/validate_traceability.py` (existing anchor parser), `docs/traceability/README.md` (implemented-increments table), `src/hisys/schemas/` (record-class `REQUIREMENTS` tuples), `/home/cbchoi/workspaces/sysailab/pre-develop/Hisys/requirements-record.md` (SRS — anchor source-of-truth), `/home/cbchoi/workspaces/sysailab/pre-develop/Hisys/software-test-description.md` (STD anchors), `tests/integration/test_trace_path.py` (existing trace test). Retrieve exact module structure before implementation.

**Boundary Record:** Local fixture-only tests/docs/code mutation and local commit are allowed after validation. Remote push is not authorized. No live external read, raw source archival, credential resolution, browser/network/model call, destructive Git, publication, or action authorization. The coverage report is advisory only and never implies approval.

---

## Accepted decisions

1. **Pure local read-only:** The reporter reads only files already inside the repository (`docs/`, `src/hisys/schemas/`, `tests/`) and the controlled-document anchors under the existing SRS/SDD/IDD/STD paths. It must not open any path outside the configured roots and must not follow symlinks that escape them.
2. **Bounded report shape:** The output Pydantic record is small: per-requirement coverage counts, lists of unreferenced requirement IDs, lists of orphan test IDs, and a top-level `coverage_ratio`. No raw source text, no design-document content, and no test source bodies are embedded.
3. **Safe write location:** The reporter writes through `resolve_instance_runtime_ref` under `runtime-boundary/traceability-coverage/<YYYYMMDD>/coverage-report.{json,md}`. Slug validators reuse the existing `_DATE_PATTERN` and `_REQUEST_ID_PATTERN` from `src/hisys/operations/codebase_analysis.py` for any per-run identifiers.
4. **Advisory only:** The report explicitly states it is advisory and requires human review. It must not be treated as a quality-gate pass for any other Hisys flow.
5. **No CLI argument expansion in M21.1:** A `hisys traceability-coverage` subcommand may be added later. M21.1 ships as a standalone `python3 scripts/...` invocation.

---

## Task 0: Reconstruct baseline before editing

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_cli.py -q
python3 scripts/validate_traceability.py
```

**Expected:** branch `dars`, HEAD at or after `cae708d docs: document codebase domain artifact bridge`; combined domain + CLI gate passes; traceability validator passes.

---

## Task 1: RED — coverage report rejects missing required anchors

Add a failing pytest under `tests/unit/test_traceability_coverage.py` that constructs a fixture anchor universe with one requirement that is referenced by no design/test anchor and asserts the coverage report's `unreferenced_requirements` list contains exactly that ID and `coverage_ratio` is below 1.0. The test should fail before any production module exists.

```bash
PYTHONPATH=src pytest tests/unit/test_traceability_coverage.py -q
```

**Expected RED:** `ImportError` or `ModuleNotFoundError` because the coverage module is not yet implemented.

---

## Task 2: GREEN — implement minimal coverage reporter

Add `src/hisys/operations/traceability_coverage.py` exposing a pure function `build_traceability_coverage_report(anchors: TraceabilityAnchors) -> TraceabilityCoverageReport` plus a writer `write_traceability_coverage_report(instance_root, date, report)` that persists JSON + Markdown under `runtime-boundary/traceability-coverage/<YYYYMMDD>/`. The reporter must compute deterministic, sorted output. Add a thin `scripts/report_traceability_coverage.py` wrapper that wires the anchor loader and writer for command-line use.

```bash
PYTHONPATH=src pytest tests/unit/test_traceability_coverage.py -q
PYTHONPATH=src pytest tests/unit/test_traceability_coverage.py tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py -q
```

---

## Task 3: Documentation, gate, and commit

- Modify: `docs/traceability/README.md` — append an `M21.1` row referencing the new module/script and the verified governance invariants.
- Modify: `ralph.md` — add a Reflection Log entry following the existing M20 format with Resume checkpoint.

**Validation:**

```bash
PYTHONPATH=src pytest tests/unit/test_traceability_coverage.py tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_cli.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit (after RED/GREEN):**

```bash
git add tests/unit/test_traceability_coverage.py src/hisys/operations/traceability_coverage.py scripts/report_traceability_coverage.py docs/traceability/README.md ralph.md
git commit -m "feat: add traceability coverage report"
```

---

## Stop conditions

Stop and report if implementation requires reading paths outside the repository, opening symlinks that escape the configured roots, embedding raw source text into the report, adding live external reads, requesting credentials, destructive Git, publication, or remote push. Stop and prepare a narrower plan if the SRS/SDD/IDD/STD anchor parsers materially diverge from what `scripts/validate_traceability.py` already exposes.

## Follow-on increments

- **M21.2 (backlog):** add a `hisys traceability-coverage` subcommand wrapping the new module.
- **M21.3 (backlog):** evaluate the next safest M21 candidate via QUEUE-REFILL-PREP.
