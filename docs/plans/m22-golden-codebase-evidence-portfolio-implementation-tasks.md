# Milestone M22 — Codebase Evidence Portfolio Golden Fixture Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for every code-bearing task. This file is the document-RED/Prepare artifact for Milestone M22 Task `M22-PORTFOLIO-GOLDEN` — a deterministic byte-equality round-trip fixture over the pure `src/hisys/operations/codebase_evidence_portfolio.py` builder/writer landed by `M22-PORTFOLIO-RED-GREEN` (commit `86684f4`) and the `hisys codebase-evidence-portfolio` CLI landed by `M22-PORTFOLIO-CLI` (commit `ec192e3`). The golden test is fixture-local; it never crosses live-provider, credential, subagent, LSP, network, or raw-source boundaries.

**Goal:** Pin a canonical M21 + DARS line-ref bundle so that any future change to `EvidenceLineRef`, `CodebaseEvidencePortfolioRequest`, `CodebaseEvidencePortfolioReport`, `build_codebase_evidence_portfolio_report`, `render_codebase_evidence_portfolio_markdown`, or the JSON serialization shape is caught by a single byte-equality assertion against checked-in expected fixtures. The fixture contains only refs, schema-ids, labels, and bounded counts — never raw source bodies, diff hunks, or secrets.

**Architecture:** Add three fixture files plus one test:

1. `tests/fixtures/codebase-evidence-portfolio/m21_dars_bundle.json` — the canonical caller-supplied bundle (top-level object with `line_refs` list).
2. `tests/fixtures/codebase-evidence-portfolio/expected/portfolio-report.json` — the deterministic JSON output of `build_codebase_evidence_portfolio_report(...).model_dump(mode="json")` serialized with `json.dumps(..., indent=2, sort_keys=True) + "\n"` (matching the writer).
3. `tests/fixtures/codebase-evidence-portfolio/expected/portfolio-report.md` — the deterministic Markdown output of `render_codebase_evidence_portfolio_markdown(report)`.
4. Test `test_codebase_evidence_portfolio_golden_round_trip` in `tests/unit/test_codebase_evidence_portfolio.py` that loads the bundle, calls the builder + writer, and asserts byte-equality between the in-memory JSON/Markdown and the checked-in expected fixtures.

The test must not mutate the checked-in fixtures, must not regenerate them, and must not depend on environmental state (date, time, git hash, tempfile UUID). The fixture caller supplies a fixed `current_head_short` for determinism.

**Tech Stack:** Python 3.11, pytest. No new dependency.

**Context Packet:** Required source handles:

- `src/hisys/operations/codebase_evidence_portfolio.py` (builder + writer + markdown renderer; single source of truth).
- `tests/unit/test_codebase_evidence_portfolio.py` (where the golden test will live alongside existing M22 tests).
- `docs/plans/m22-codebase-evidence-portfolio-implementation-plan.md` (parent plan).
- `docs/plans/m22-codebase-evidence-portfolio-implementation-tasks.md` (M22-PORTFOLIO-RED-GREEN task plan with the schema invariant).
- `docs/plans/m22-cli-codebase-evidence-portfolio-implementation-tasks.md` (M22-PORTFOLIO-CLI task plan for the bundle shape).
- `docs/traceability/README.md` (M22-PORTFOLIO-GOLDEN row to prepend).
- `ralph.md` for the Reflection Log update.

**Boundary Record:** Local docs/control + test + fixture writes only. Local commits and normal push to existing `origin/dars` are allowed after focused gates pass. The fixture must not embed raw source bodies, secrets, diff hunks, or any artifact content beyond refs/schema-ids/labels/counts.

---

## Accepted decisions

1. **Caller-supplied `current_head_short`.** The bundle JSON includes a fixed string under `current_head_short`. The builder records it verbatim. The fixture is independent of git state.
2. **Two-line canonical bundle.** Exactly two source lines: `M21` and `DARS_PANEL_LOCAL_COMPLETION`. Adding more lines is deferred to a separate RED.
3. **No unsafe inputs in the canonical bundle.** Unsafe-ref / unsafe-label classification already has dedicated regression tests; the golden fixture covers the happy path only.
4. **Byte-equality assertion.** The test reads expected files with `read_text(encoding="utf-8")` and compares to the in-memory JSON/Markdown string. Any whitespace, ordering, key, or counter drift is a failing test.
5. **Single test, two assertions.** One pytest function holds the JSON byte-equality and the Markdown byte-equality. Separation by assertion message is sufficient.
6. **Fixture under `tests/fixtures/codebase-evidence-portfolio/`.** Mirrors the `tests/fixtures/...` partition convention already used by `tests/fixtures/pass-contracts/code_analysis/`.

---

## Task 0: Reconstruct baseline before any edit

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_codebase_evidence_portfolio.py tests/unit/test_domain_cli.py tests/unit/test_change_impact.py tests/unit/test_architecture_candidates.py tests/unit/test_code_analysis_pass_contract.py tests/unit/test_subagent_evidence_collector_protocol.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_governance_docs_current_state.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

Expected: branch `dars`, HEAD at or after `ec192e3 feat: add codebase-evidence-portfolio CLI wrapper`; combined M21+M22+CLI focused gate passes (89 expected); traceability validator OK; secret scan `hit_count=0`; `git diff --check` clean.

---

## Task 1: Add the canonical bundle fixture

**Files:**

- Create: `tests/fixtures/codebase-evidence-portfolio/m21_dars_bundle.json`

The bundle is the same shape that the CLI accepts. The fixture is small, deterministic, and contains only safe refs.

## Task 2: RED — golden round-trip test fails before expected fixtures exist

**Files:**

- Modify: `tests/unit/test_codebase_evidence_portfolio.py` — append `test_codebase_evidence_portfolio_golden_round_trip`.

**Test sketch:**

```python
FIXTURE_DIR = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "codebase-evidence-portfolio"
)


def _load_bundle_payload() -> dict[str, object]:
    return json.loads(
        (FIXTURE_DIR / "m21_dars_bundle.json").read_text(encoding="utf-8")
    )


def _expected_json() -> str:
    return (FIXTURE_DIR / "expected" / "portfolio-report.json").read_text(
        encoding="utf-8"
    )


def _expected_markdown() -> str:
    return (FIXTURE_DIR / "expected" / "portfolio-report.md").read_text(
        encoding="utf-8"
    )


def test_codebase_evidence_portfolio_golden_round_trip(tmp_path: Path) -> None:
    bundle_payload = _load_bundle_payload()
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    line_refs = tuple(
        EvidenceLineRef(**raw) for raw in bundle_payload["line_refs"]
    )
    request = CodebaseEvidencePortfolioRequest(
        instance_root=instance_root,
        date=bundle_payload["date"],
        line_refs=line_refs,
        current_head_short=bundle_payload["current_head_short"],
    )
    report = build_codebase_evidence_portfolio_report(request=request)
    write_codebase_evidence_portfolio_report(
        instance_root=instance_root, date=bundle_payload["date"], report=report
    )

    json_path = (
        instance_root
        / "runtime-boundary"
        / "codebase-evidence-portfolio"
        / bundle_payload["date"]
        / "portfolio-report.json"
    )
    md_path = (
        instance_root
        / "runtime-boundary"
        / "codebase-evidence-portfolio"
        / bundle_payload["date"]
        / "portfolio-report.md"
    )
    assert json_path.read_text(encoding="utf-8") == _expected_json()
    assert md_path.read_text(encoding="utf-8") == _expected_markdown()
```

**Verify RED:** the test fails because the expected fixture files do not yet exist (`FileNotFoundError`).

## Task 3: GREEN — add the expected JSON and Markdown fixtures

**Files:**

- Create: `tests/fixtures/codebase-evidence-portfolio/expected/portfolio-report.json`
- Create: `tests/fixtures/codebase-evidence-portfolio/expected/portfolio-report.md`

Compute the expected outputs by running the builder + writer once against the canonical bundle (the fixtures are checked in alongside the test).

**Verify GREEN:**

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_evidence_portfolio.py::test_codebase_evidence_portfolio_golden_round_trip -q
```

Expected: the golden test passes. All existing M22 tests continue to pass.

## Task 4: Documentation, gate, and commit

**Files:**

- Modify: `docs/traceability/README.md` — prepend an `M22-PORTFOLIO-GOLDEN` row.
- Modify: `ralph.md` — append a Reflection Log entry with Resume checkpoint, and rewrite Section 16 so the next safe Ralph row is `M22-PORTFOLIO-GATE`.
- Modify: `docs/milestone-bootstrap/profile.yaml` — bump `version` to `v0.0.19`, `next_safe_task` to `M22-PORTFOLIO-GATE`, refresh `planning_baseline_head` / `current_head_at_plan_creation` to the new HEAD label.
- Modify: `tests/unit/test_governance_docs_current_state.py` — assert `v0.0.19` and `M22-PORTFOLIO-GATE`.

**Validation:**

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_evidence_portfolio.py tests/unit/test_domain_cli.py tests/unit/test_change_impact.py tests/unit/test_architecture_candidates.py tests/unit/test_code_analysis_pass_contract.py tests/unit/test_subagent_evidence_collector_protocol.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_governance_docs_current_state.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit:**

```bash
git add tests/fixtures/codebase-evidence-portfolio tests/unit/test_codebase_evidence_portfolio.py docs/plans/m22-golden-codebase-evidence-portfolio-implementation-tasks.md docs/traceability/README.md ralph.md docs/milestone-bootstrap/profile.yaml tests/unit/test_governance_docs_current_state.py
git commit -m "test: pin codebase evidence portfolio golden fixture"
```

---

## Stop conditions

Stop and ask for a new decision if any task would require:

- adding network/browser/connector/model/LSP/subprocess invocation in the golden flow;
- credential lookup or persistence;
- raw source bodies, diff hunks, or secrets inside the fixture;
- crawling `runtime-boundary/`, calling `date.today()`, reading `.git/`, or shelling out;
- changing `EvidenceLineRef` / `CodebaseEvidencePortfolioRequest` / `CodebaseEvidencePortfolioReport` shapes in this increment (those changes require a separate RED on the pure module);
- expanding the bundle vocabulary beyond M21 / DARS_PANEL_LOCAL_COMPLETION.

## Out of scope for M22-PORTFOLIO-GOLDEN (deferred)

- CLI-level golden round-trip (the M22-PORTFOLIO-RED-GREEN module is the single source of truth; the CLI is a thin pass-through and already has 4 focused tests).
- Multi-bundle fixture matrix (single canonical bundle is sufficient regression).
- Live-provider, OSS adapter, or LSP adapter coverage (human-gated).

## Next executable action

After this Prepare plan is committed and pushed, write the bundle fixture, append the golden test, run it RED, add the expected JSON + Markdown fixtures (by computing them from the deterministic builder/writer), confirm GREEN, update docs/traceability/profile/governance test, validate, commit, and push.
