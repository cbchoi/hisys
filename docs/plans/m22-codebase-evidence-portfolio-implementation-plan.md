# M22 Codebase Evidence Portfolio Implementation Plan

> **For Hermes/Ralph:** Execute M22 one checkpoint at a time with Plan -> RED -> GREEN -> validate -> commit discipline. M22 is a local-safe continuation after M21 and DARS panel local completion. It does not authorize live provider execution, credential lookup, external repository access, local LSP process spawning, subagent execution, publication, deployment, or raw source archival.

**Goal:** Convert the completed M21 local codebase-analysis surfaces into an operator-readable evidence portfolio that can answer what evidence exists, which local reports are available, which quality gates are reproducible, and which future adapters remain human-gated.

**Architecture:** M22 aggregates existing local M21/DARS artifacts by reference, count, schema id, and advisory boundary flags. It should not copy raw source content into reports. It should prefer manifest/index artifacts and fixture-local tests before adding any new analyzer or adapter. The first increment is a documentation/control PREP checkpoint that defines the portfolio schema and RED tests.

**Context Packet:**
- Current branch/head at planning: `dars` / `f5b63fb docs: queue-refill-prep verifies m21-6 roll-forward and stops on human-gated backlog`.
- Completed local lines: DARS panel local completion audit (`docs/reports/dars-panel-local-completion-audit.md`) and M21.1..M21.9 codebase-analysis surfaces.
- Existing M21 anchors: `docs/plans/m21-roadmap-implementation-plan.md`, `docs/plans/m21-*-implementation-tasks.md`, `docs/traceability/README.md`, M21 operation modules under `src/hisys/operations/`, and unit tests under `tests/unit/`.
- Human-gated surfaces remain out of scope: approved OSS comparison adapter, optional local LSP adapter, and separately governed live-provider DARS execution.

**Boundary Record:**
- Authorized: local docs/control planning, local fixture/test data, local pytest execution, local runtime report artifacts under explicit temp/fixture instance roots, traceability updates, local commits, normal push to existing `origin/dars` after validation.
- Not authorized: live external provider calls, network clone/fetch/search, credential lookup or mutation, local LSP subprocess spawning, subagent execution, publication/deployment, force push, new remote configuration, destructive Git/history operations, schema/data migrations against non-fixture data, raw source-content archival beyond bounded refs/counts/digests.

---

## M22 task queue

| Row | Task | Type | Status |
|---|---|---|---|
| M22-PORTFOLIO-PREP | Define the M22 codebase evidence portfolio schema, report paths, RED tests, and quality gates. | docs/control | next |
| M22-PORTFOLIO-RED-GREEN | Implement a pure local portfolio builder/writer over existing M21/DARS refs. | fixture-local implementation | pending after PREP |
| M22-PORTFOLIO-CLI | Add a thin `hisys codebase-evidence-portfolio` CLI wrapper after the pure builder is stable. | fixture-local implementation | pending after builder |
| M22-PORTFOLIO-GOLDEN | Add a golden fixture portfolio run over the checked-in M21 fixture reports and assert stable JSON/Markdown output. | fixture/test | pending after CLI |
| M22-PORTFOLIO-GATE | Record completion evidence, update traceability/Ralph, and decide whether any safe local M22 follow-on remains. | docs/control gate | pending after golden |

## M22-PORTFOLIO-PREP

**Objective:** Create a precise implementation plan for the local codebase evidence portfolio before production code.

**Files:**
- Create: `docs/plans/m22-codebase-evidence-portfolio-implementation-tasks.md`
- Update: `ralph.md`
- Update if needed: `docs/milestone-bootstrap/profile.yaml` and `tests/unit/test_governance_docs_current_state.py`

**Schema sketch:**

```json
{
  "schema_id": "hisys.codebase_evidence_portfolio.v1",
  "date": "20260521",
  "source_lines": ["M21", "DARS_PANEL_LOCAL_COMPLETION"],
  "artifact_refs": [],
  "implemented_surface_count": 0,
  "human_gated_surface_count": 0,
  "quality_gate_refs": [],
  "advisory_only": true,
  "requires_human_review": true,
  "external_call_made": false,
  "mutation_performed": false,
  "raw_source_content_persisted": false,
  "allowed_actions": "advisory_only"
}
```

**RED expectation for the next implementation row:**

```bash
PYTHONPATH=src:. pytest tests/unit/test_codebase_evidence_portfolio.py::test_codebase_evidence_portfolio_indexes_m21_and_dars_refs_without_raw_source -q
```

Expected initial failure after PREP and before implementation:

```text
ModuleNotFoundError: No module named 'hisys.operations.codebase_evidence_portfolio'
```

**Validation for PREP:**

```bash
python3 - <<'PY'
from pathlib import Path
text = Path('docs/plans/m22-codebase-evidence-portfolio-implementation-plan.md').read_text()
assert 'M22-PORTFOLIO-PREP' in text
assert 'raw_source_content_persisted' in text
assert 'live external provider calls' in text
print('m22 plan markers ok')
PY
PYTHONPATH=src:. pytest tests/unit/test_governance_docs_current_state.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

## M22-PORTFOLIO-RED-GREEN

**Objective:** Implement `src/hisys/operations/codebase_evidence_portfolio.py` with a pure builder and writer.

**Required behavior:**
- Accept explicit caller-provided artifact refs and known local line labels only.
- Preserve M21/DARS report refs, schema ids, status flags, and counts.
- Reject unsafe refs (`..`, absolute paths, refs outside allowed docs/runtime roots).
- Persist JSON/Markdown under `runtime-boundary/codebase-evidence-portfolio/<YYYYMMDD>/portfolio-report.{json,md}`.
- Carry advisory-only, human-review-required, no-external-call, no-mutation, no-raw-source flags.
- Do not crawl the repository, read raw source bodies, call Git, spawn processes, execute subagents, open network, or infer live readiness.

## M22-PORTFOLIO-CLI

**Objective:** Expose the pure builder through a thin CLI only after the builder is green.

**Proposed CLI:**

```bash
hisys codebase-evidence-portfolio --instance <root> --date 20260521 --artifact-ref <ref> --line M21 --line DARS_PANEL_LOCAL_COMPLETION
```

The CLI should not infer latest artifacts, run tests, read `.git/`, call `subprocess`, or scan arbitrary source trees.

## M22-PORTFOLIO-GOLDEN

**Objective:** Add a deterministic golden fixture/expected-output test that proves the portfolio can summarize M21 and DARS local evidence without raw source capture.

## M22-PORTFOLIO-GATE

**Objective:** Run focused/full gates, update traceability and `ralph.md`, and perform a queue-end refill preflight. Stop only if no safe local M22 follow-on remains or the next candidate crosses a human-gated boundary.
