# Milestone M23 — Adapter Portfolio Integration Implementation Task Plan

> **Row:** This document is the artifact produced by Ralph row `M23-ADAPTER-PORTFOLIO-INTEGRATION-PREP`. Subsequent rows `M23-ADAPTER-PORTFOLIO-INTEGRATION-RED-GREEN` and `M23-LIVE-LSP-SMOKE-GATE` are scoped below.

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for every code-bearing task. This file is the document-RED/Prepare artifact for the post-M23 adapter portfolio integration follow-up authorized in `docs/plans/m23-adapter-portfolio-integration-followup-plan.md` and supported by the user authorization recorded in `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.33.md`. M23 advanced codebase adapter milestone closed at `local_fixture_advisory_complete` (`5a633dd docs: close m23 advanced codebase adapter milestone`). The live LSP smoke under candidate 2 landed evidence at `docs/reports/m23-live-lsp-server-smoke.md`, `runtime-boundary/lsp-adapter/20260522/ruff-check-live/lsp-report.json`, and `runtime-boundary/lsp-adapter/20260522/pyright-check-live/lsp-report.json` (the eslint smoke ran against a tmp instance and is referenced by the report only). This integration line is a local-safe continuation; it does not authorize credential lookup, secret capture, real OSS clone, license-text capture, license adjudication, new or changed remote configuration, force push, publication/deployment/release, mutation of non-fixture user/live data, unbounded live external provider execution, or raw source-content/raw diagnostic-message archival beyond bounded redacted reports.

**Goal:** Add governed M23 adapter evidence lines (`M23_OSS_ADAPTER`, `M23_LSP_ADAPTER`) to the local-only codebase evidence portfolio so the portfolio aggregates the OSS comparison adapter and the local LSP adapter alongside `M21` and `DARS_PANEL_LOCAL_COMPLETION`. The integration must use refs, counts, schema ids, and quality-gate refs only. It must not copy raw source content, raw diagnostic messages, license texts, or runtime artifact bodies into the fixture.

**Architecture:** No new production module. The existing pure builder `src/hisys/operations/codebase_evidence_portfolio.py` already accepts caller-supplied `EvidenceLineRef` records (the `_LINE_LABEL_PATTERN = ^[A-Z][A-Z0-9_\-]{1,63}$` already accepts `M23_OSS_ADAPTER` and `M23_LSP_ADAPTER`). The integration ships a new caller-authored bundle and the deterministic expected report so the four-line portfolio is pinned by golden byte-equality. The existing `m21_dars_bundle.json` golden is preserved unchanged.

**Tech Stack:** Python 3.11, json, pathlib, pytest. No new dependency. No subprocess, no network, no model invocation, no `subprocess.run`, no `git log`, no `date.today()`, no `runtime-boundary/` crawl.

**Context Packet:** Required source handles:

- `src/hisys/operations/codebase_evidence_portfolio.py` (`EvidenceLineRef`, `CodebaseEvidencePortfolioRequest`, `CodebaseEvidencePortfolioReport`, `build_codebase_evidence_portfolio_report`, `write_codebase_evidence_portfolio_report`, `render_codebase_evidence_portfolio_markdown`).
- `tests/unit/test_codebase_evidence_portfolio.py` (existing 6 tests; `_FIXTURE_DIR` resolver and `_load_golden_bundle` helper to mirror).
- `tests/fixtures/codebase-evidence-portfolio/m21_dars_bundle.json` (existing M21+DARS bundle, preserved unchanged).
- `tests/fixtures/codebase-evidence-portfolio/expected/portfolio-report.{json,md}` (existing expected files, preserved unchanged).
- `src/hisys/operations/oss_comparison_adapter.py` (`schema_id="hisys.oss_comparison_adapter.v1"`).
- `src/hisys/operations/lsp_adapter.py` (`schema_id="hisys.lsp_adapter.v1"`).
- `src/hisys/cli/main.py` (subcommands `oss-comparison-adapter` and `lsp-adapter`).
- `tests/unit/test_oss_comparison_adapter.py` (7 tests; includes the OSS-ADAPTER-GOLDEN round-trip).
- `tests/unit/test_lsp_adapter.py` (14 tests; includes the LSP-ADAPTER-GOLDEN round-trip).
- `tests/fixtures/oss-comparison/m23_local_oss_bundle.json`, `tests/fixtures/oss-comparison/expected/comparison-report.{json,md}` (M23 OSS golden fixture).
- `tests/fixtures/lsp-adapter/m23_lsp_bundle.json`, `tests/fixtures/lsp-adapter/expected/lsp-report.{json,md}`, `tests/fixtures/lsp-adapter/ruff/canned_ruff_output.json` (M23 LSP golden fixture and canned ruff stdout).
- `docs/plans/m23-advanced-codebase-adapter-integration-plan.md` (M23 parent plan).
- `docs/plans/m23-oss-comparison-adapter-implementation-tasks.md`, `docs/plans/m23-cli-oss-comparison-adapter-implementation-tasks.md`, `docs/plans/m23-golden-oss-comparison-adapter-implementation-tasks.md` (OSS sub-line PREPs).
- `docs/plans/m23-lsp-adapter-implementation-tasks.md`, `docs/plans/m23-cli-lsp-adapter-implementation-tasks.md`, `docs/plans/m23-golden-lsp-adapter-implementation-tasks.md` (LSP sub-line PREPs).
- `docs/plans/m23-adapter-portfolio-integration-followup-plan.md` (parent follow-up plan that authorized this PREP).
- `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.33.md` (user authorization packet for candidate 1 and candidate 2).
- `docs/reports/m23-live-lsp-server-smoke.md` (live LSP smoke report; ruff/pyright/eslint installation + first execution evidence).
- `runtime-boundary/lsp-adapter/20260522/ruff-check-live/lsp-report.{json,md}` and `runtime-boundary/lsp-adapter/20260522/pyright-check-live/lsp-report.{json,md}` (live LSP runtime reports preserved under the repo).
- `docs/traceability/README.md` (controlled traceability anchor file).
- `docs/milestone-bootstrap/profile.yaml`, `tests/unit/test_governance_docs_current_state.py` (governance current-state contract).
- `ralph.md` (control plan / Reflection Log).

**Boundary Record:** Local docs/control writes for this Prepare package, then later local test/fixture edits in a separate RED/GREEN increment, are allowed. Local commits and normal push to existing `origin/dars` are allowed after focused gates pass. Remote configuration change, force push, credential lookup, live external call, network clone/fetch/search, real OSS clone, license-text capture, license adjudication, local LSP subprocess spawning beyond the already-recorded smoke evidence, subagent execution, publication, deployment, destructive Git history, schema/data migrations against non-fixture data, and raw source-content/raw diagnostic-message archival beyond bounded refs/counts/digests are **not** authorized in any M23 integration increment without a separate human-gated approval. The expanded portfolio remains advisory only and never implies repair, deletion, retry, approval, or readiness for live action. The DARS completion claim remains `local_fixture_localhost_controlled_advisory_complete`; this integration does not claim live provider execution has been smoked.

---

## Accepted decisions

1. **Caller-supplied refs only.** Evidence refs continue to come from the caller (the new bundle fixture). The portfolio builder is unchanged; it does not crawl `runtime-boundary/`, does not list `docs/`, does not run `git log`, does not call `subprocess`, and does not consult the network.
2. **No production code change in this integration.** `src/hisys/operations/codebase_evidence_portfolio.py` already accepts arbitrary caller-named `EvidenceLineRef` line labels matching `^[A-Z][A-Z0-9_\-]{1,63}$`. `M23_OSS_ADAPTER` and `M23_LSP_ADAPTER` both match. No schema or writer change is allowed by this increment; if a schema change is later needed, that work belongs to a separate PREP.
3. **Preserve the existing M21+DARS golden.** `tests/fixtures/codebase-evidence-portfolio/m21_dars_bundle.json` and `tests/fixtures/codebase-evidence-portfolio/expected/portfolio-report.{json,md}` stay unchanged. The integration adds a new bundle `m21_dars_m23_bundle.json` and a new expected pair under `tests/fixtures/codebase-evidence-portfolio/expected-m21-dars-m23/`. The two golden round-trip tests coexist.
4. **Bundle pins exact M23 refs by label only.** The new bundle records label strings for the M23 adapter modules, CLI subcommands, sibling PREPs, sibling golden PREPs, sibling test files, live LSP smoke report, and the two repo-scoped live LSP runtime report files. No raw upstream content, no diagnostic message body, no license text, no runtime artifact body, no secret is embedded.
5. **Implemented vs human-gated counts are explicit.** Counts reflect what is locally implemented + golden-pinned vs what remains human-gated for the M23 adapter family. The plan declares these counts and the rationale before the RED test pins them.
6. **No deletion/repair authority.** The integration never rewrites, deletes, regenerates, or quarantines existing OSS or LSP adapter code, tests, docs, runtime-boundary artifacts, or the existing portfolio golden. It only adds new fixture/expected files and one new test.
7. **Advisory only.** The expanded report continues to carry `advisory_only=true`, `requires_human_review=true`, `external_call_made=false`, `mutation_performed=false`, `raw_source_content_persisted=false`, `allowed_actions="advisory_only"`. The integration must not introduce live-call or readiness language.
8. **No CLI in this increment.** No CLI change is in scope. The existing `hisys codebase-evidence-portfolio` CLI already accepts caller-supplied lines; an operator who wants to surface the M23 lines through the CLI can pass them today.
9. **Bounded reads.** The integration tests reads only the new bundle JSON and the two new expected files; no file bodies of the OSS/LSP modules, no `runtime-boundary/` artifact bodies, and no `.git/` content are read.
10. **Traceability required.** Update `docs/traceability/README.md` with an `M23-ADAPTER-PORTFOLIO-INTEGRATION` row only in the RED/GREEN increment, and append a Reflection Log entry plus Resume checkpoint to `ralph.md` for every checkpoint.

---

## Authoritative M23 adapter portfolio line content

The RED/GREEN row shall encode the lines below verbatim into the new bundle. The label and ref strings are normative.

### `M23_OSS_ADAPTER`

- `line_label`: `M23_OSS_ADAPTER`
- `artifact_refs` (alphabetical inside the bundle for byte-stability):
  - `docs/plans/m23-advanced-codebase-adapter-integration-plan.md`
  - `docs/plans/m23-cli-oss-comparison-adapter-implementation-tasks.md`
  - `docs/plans/m23-golden-oss-comparison-adapter-implementation-tasks.md`
  - `docs/plans/m23-oss-comparison-adapter-implementation-tasks.md`
- `schema_ids`:
  - `hisys.oss_comparison_adapter.v1`
- `quality_gate_refs`:
  - `tests/unit/test_oss_comparison_adapter.py`
- `implemented_surface_count`: `3`
  - Rationale: pure builder/writer at `src/hisys/operations/oss_comparison_adapter.py`, CLI subcommand `oss-comparison-adapter` in `src/hisys/cli/main.py`, golden byte-equality round-trip in `tests/unit/test_oss_comparison_adapter.py` pinned by `tests/fixtures/oss-comparison/m23_local_oss_bundle.json`.
- `human_gated_surface_count`: `3`
  - Rationale: (a) real OSS repository clone/fetch, (b) license-text capture and adjudication, (c) raw source-content archival. None are implemented; all require separate explicit user authorization per `docs/plans/m23-advanced-codebase-adapter-integration-plan.md` boundary record.

### `M23_LSP_ADAPTER`

- `line_label`: `M23_LSP_ADAPTER`
- `artifact_refs` (alphabetical inside the bundle for byte-stability):
  - `docs/plans/m23-cli-lsp-adapter-implementation-tasks.md`
  - `docs/plans/m23-golden-lsp-adapter-implementation-tasks.md`
  - `docs/plans/m23-lsp-adapter-implementation-tasks.md`
  - `docs/reports/m23-live-lsp-server-smoke.md`
  - `runtime-boundary/lsp-adapter/20260522/pyright-check-live/lsp-report.json`
  - `runtime-boundary/lsp-adapter/20260522/ruff-check-live/lsp-report.json`
- `schema_ids`:
  - `hisys.lsp_adapter.v1`
- `quality_gate_refs`:
  - `tests/unit/test_lsp_adapter.py`
- `implemented_surface_count`: `6`
  - Rationale: pure governed runner/writer at `src/hisys/operations/lsp_adapter.py`, CLI subcommand `lsp-adapter` in `src/hisys/cli/main.py`, golden byte-equality round-trip in `tests/unit/test_lsp_adapter.py` pinned by `tests/fixtures/lsp-adapter/m23_lsp_bundle.json`, plus three first-smoke runs through the governed boundary (ruff repo-scoped, pyright repo-scoped, eslint tmp-fixture) recorded in `docs/reports/m23-live-lsp-server-smoke.md`. Only the ruff and pyright reports are repo-resident; eslint ran against a tmp instance.
- `human_gated_surface_count`: `2`
  - Rationale: (a) any unbounded live external provider execution outside ruff/pyright/eslint allowlist, (b) any expansion of the command allowlist or removal of the workspace-root/timeout/kill-policy constraints. Both require separate explicit user authorization per `docs/plans/m23-lsp-adapter-implementation-tasks.md` and `docs/plans/m23-adapter-portfolio-integration-followup-plan.md`.

### Aggregated expected portfolio fields (M21 + DARS + M23_OSS_ADAPTER + M23_LSP_ADAPTER)

The four-line aggregation is mechanically determined by the existing builder. The new `expected-m21-dars-m23/portfolio-report.json` shall match the deterministic builder output exactly. For reviewer reference, the following invariants are expected (the test is byte-equal, so any drift fails the golden):

- `schema_id`: `hisys.codebase_evidence_portfolio.v1`
- `source_lines`: `["DARS_PANEL_LOCAL_COMPLETION", "M21", "M23_LSP_ADAPTER", "M23_OSS_ADAPTER"]` (alphabetical).
- `schema_ids`: union of `hisys.architecture_candidates.v1`, `hisys.change_impact.v1`, `hisys.dars_panel_readiness.v1`, `hisys.lsp_adapter.v1`, `hisys.oss_comparison_adapter.v1`, `hisys.traceability.coverage.v1`.
- `artifact_refs`: deduplicated union of all M21+DARS+M23_OSS_ADAPTER+M23_LSP_ADAPTER artifact refs above; `runtime-boundary/lsp-adapter/20260522/...` refs are safe under the existing `_is_unsafe_ref` rule (no leading `/`, no `..` traversal, non-empty), so they appear in `artifact_refs`, not in `unsafe_refs`.
- `quality_gate_refs`: union of the existing M21+DARS quality gate refs plus `tests/unit/test_lsp_adapter.py` and `tests/unit/test_oss_comparison_adapter.py`.
- `implemented_surface_count`: `9 + 5 + 3 + 6 = 23`.
- `human_gated_surface_count`: `2 + 0 + 3 + 2 = 7`.
- `unsafe_refs`: `[]`.
- `unsafe_line_labels`: `[]`.
- `advisory_only`: `true`; `requires_human_review`: `true`; `external_call_made`: `false`; `mutation_performed`: `false`; `raw_source_content_persisted`: `false`; `allowed_actions`: `advisory_only`.
- `current_head_short`: TBD by the RED/GREEN row; pin whichever short hash is current at that increment's HEAD (e.g., `78e226c` or its successor after this PREP commits). The bundle records that head and the expected JSON reflects it.

The expected Markdown shall be the verbatim output of `render_codebase_evidence_portfolio_markdown` against the same report. It is never hand-edited; it is regenerated by the writer.

---

## Task 0: Reconstruct baseline before any edit

**Objective:** Confirm the post-M23 authorization commit is current, working tree is clean, and the M21/M22/M23/DARS focused gates remain green.

**Commands:**

```bash
git status --short --branch
git log --oneline -8
PYTHONPATH=src pytest tests/unit/test_codebase_evidence_portfolio.py tests/unit/test_oss_comparison_adapter.py tests/unit/test_lsp_adapter.py tests/unit/test_domain_cli.py tests/unit/test_governance_docs_current_state.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:** branch `dars`, HEAD at or after `78e226c docs: authorize m23 adapter portfolio follow-up`; combined gate passes; traceability OK; secret scan `hit_count=0`; `git diff --check` clean.

If any expected outcome diverges, stop and re-run QUEUE-REFILL-PREP before continuing.

---

## Task 1: RED — golden round-trip pins the four-line portfolio

**Objective:** Add a failing pytest that loads the new four-line bundle (`m21_dars_m23_bundle.json`), calls `build_codebase_evidence_portfolio_report` and `write_codebase_evidence_portfolio_report`, and byte-compares the resulting JSON and Markdown files against checked-in expected artifacts under `tests/fixtures/codebase-evidence-portfolio/expected-m21-dars-m23/`. The test must fail before the bundle and expected files exist.

**Files:**

- Modify: `tests/unit/test_codebase_evidence_portfolio.py`
- Create (deferred to Task 2): `tests/fixtures/codebase-evidence-portfolio/m21_dars_m23_bundle.json`
- Create (deferred to Task 2): `tests/fixtures/codebase-evidence-portfolio/expected-m21-dars-m23/portfolio-report.json`
- Create (deferred to Task 2): `tests/fixtures/codebase-evidence-portfolio/expected-m21-dars-m23/portfolio-report.md`

**Test sketch (added to `tests/unit/test_codebase_evidence_portfolio.py`):**

```python
def _load_m23_golden_bundle() -> dict[str, object]:
    return json.loads(
        (_FIXTURE_DIR / "m21_dars_m23_bundle.json").read_text(encoding="utf-8")
    )


def _expected_m23_golden_json() -> str:
    return (
        _FIXTURE_DIR
        / "expected-m21-dars-m23"
        / "portfolio-report.json"
    ).read_text(encoding="utf-8")


def _expected_m23_golden_markdown() -> str:
    return (
        _FIXTURE_DIR
        / "expected-m21-dars-m23"
        / "portfolio-report.md"
    ).read_text(encoding="utf-8")


def test_codebase_evidence_portfolio_accepts_m23_adapter_lines(
    tmp_path: Path,
) -> None:
    bundle = _load_m23_golden_bundle()
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    line_refs = tuple(EvidenceLineRef(**raw) for raw in bundle["line_refs"])
    request = CodebaseEvidencePortfolioRequest(
        instance_root=instance_root,
        date=bundle["date"],
        line_refs=line_refs,
        current_head_short=bundle["current_head_short"],
    )
    report = build_codebase_evidence_portfolio_report(request=request)
    write_codebase_evidence_portfolio_report(
        instance_root=instance_root, date=bundle["date"], report=report
    )

    json_path = (
        instance_root
        / "runtime-boundary"
        / "codebase-evidence-portfolio"
        / bundle["date"]
        / "portfolio-report.json"
    )
    md_path = (
        instance_root
        / "runtime-boundary"
        / "codebase-evidence-portfolio"
        / bundle["date"]
        / "portfolio-report.md"
    )
    assert json_path.read_text(encoding="utf-8") == _expected_m23_golden_json()
    assert md_path.read_text(encoding="utf-8") == _expected_m23_golden_markdown()
    assert "M23_LSP_ADAPTER" in report.source_lines
    assert "M23_OSS_ADAPTER" in report.source_lines
    assert "hisys.lsp_adapter.v1" in report.schema_ids
    assert "hisys.oss_comparison_adapter.v1" in report.schema_ids
    assert (
        "runtime-boundary/lsp-adapter/20260522/ruff-check-live/lsp-report.json"
        in report.artifact_refs
    )
    assert (
        "runtime-boundary/lsp-adapter/20260522/pyright-check-live/lsp-report.json"
        in report.artifact_refs
    )
    assert "tests/unit/test_lsp_adapter.py" in report.quality_gate_refs
    assert "tests/unit/test_oss_comparison_adapter.py" in report.quality_gate_refs
    assert report.unsafe_refs == ()
    assert report.unsafe_line_labels == ()
    assert report.raw_source_content_persisted is False
    assert report.external_call_made is False
```

**Verify RED:**

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_evidence_portfolio.py::test_codebase_evidence_portfolio_accepts_m23_adapter_lines -q
```

**Expected RED:** `FileNotFoundError: [Errno 2] No such file or directory: '.../tests/fixtures/codebase-evidence-portfolio/m21_dars_m23_bundle.json'` (or the equivalent missing-bundle/expected-file error before Task 2 lands).

---

## Task 2: GREEN — author the new bundle and expected artifacts

**Objective:** Add the new caller-authored bundle and its deterministic expected files so the RED test passes. The expected files must be the verbatim writer output for the bundle.

**Files:**

- Create: `tests/fixtures/codebase-evidence-portfolio/m21_dars_m23_bundle.json`
- Create: `tests/fixtures/codebase-evidence-portfolio/expected-m21-dars-m23/portfolio-report.json`
- Create: `tests/fixtures/codebase-evidence-portfolio/expected-m21-dars-m23/portfolio-report.md`

**Bundle content (illustrative; exact JSON is the normative artifact authored at GREEN time):**

```json
{
  "date": "20260522",
  "current_head_short": "78e226c",
  "line_refs": [
    {
      "line_label": "M21",
      "artifact_refs": [
        "docs/plans/m21-1-traceability-coverage-report-implementation-tasks.md",
        "docs/plans/m21-6-change-impact-analyzer-implementation-tasks.md",
        "docs/plans/m21-7-architecture-candidate-generator-implementation-tasks.md"
      ],
      "schema_ids": [
        "hisys.architecture_candidates.v1",
        "hisys.change_impact.v1",
        "hisys.traceability.coverage.v1"
      ],
      "quality_gate_refs": [
        "tests/unit/test_architecture_candidates.py",
        "tests/unit/test_change_impact.py",
        "tests/unit/test_traceability_coverage.py"
      ],
      "implemented_surface_count": 9,
      "human_gated_surface_count": 2
    },
    {
      "line_label": "DARS_PANEL_LOCAL_COMPLETION",
      "artifact_refs": [
        "docs/plans/dars-panel-completion-before-codebase-return.md",
        "docs/reports/dars-panel-local-completion-audit.md"
      ],
      "schema_ids": [
        "hisys.dars_panel_readiness.v1"
      ],
      "quality_gate_refs": [
        "tests/unit/test_dars_critic_panel_cli.py",
        "tests/unit/test_dars_critic_panel_runtime.py"
      ],
      "implemented_surface_count": 5,
      "human_gated_surface_count": 0
    },
    {
      "line_label": "M23_OSS_ADAPTER",
      "artifact_refs": [
        "docs/plans/m23-advanced-codebase-adapter-integration-plan.md",
        "docs/plans/m23-cli-oss-comparison-adapter-implementation-tasks.md",
        "docs/plans/m23-golden-oss-comparison-adapter-implementation-tasks.md",
        "docs/plans/m23-oss-comparison-adapter-implementation-tasks.md"
      ],
      "schema_ids": [
        "hisys.oss_comparison_adapter.v1"
      ],
      "quality_gate_refs": [
        "tests/unit/test_oss_comparison_adapter.py"
      ],
      "implemented_surface_count": 3,
      "human_gated_surface_count": 3
    },
    {
      "line_label": "M23_LSP_ADAPTER",
      "artifact_refs": [
        "docs/plans/m23-cli-lsp-adapter-implementation-tasks.md",
        "docs/plans/m23-golden-lsp-adapter-implementation-tasks.md",
        "docs/plans/m23-lsp-adapter-implementation-tasks.md",
        "docs/reports/m23-live-lsp-server-smoke.md",
        "runtime-boundary/lsp-adapter/20260522/pyright-check-live/lsp-report.json",
        "runtime-boundary/lsp-adapter/20260522/ruff-check-live/lsp-report.json"
      ],
      "schema_ids": [
        "hisys.lsp_adapter.v1"
      ],
      "quality_gate_refs": [
        "tests/unit/test_lsp_adapter.py"
      ],
      "implemented_surface_count": 6,
      "human_gated_surface_count": 2
    }
  ]
}
```

**Expected-file regeneration procedure (used only at GREEN time, never as part of CI):**

Generate the expected files deterministically by running the existing writer against a tmp instance with the new bundle, then copy the output bytes into the new `expected-m21-dars-m23/` directory. The pseudo-script below is illustrative; do not check it in:

```bash
PYTHONPATH=src python3 - <<'PY'
import json
from pathlib import Path
from hisys.operations.codebase_evidence_portfolio import (
    CodebaseEvidencePortfolioRequest, EvidenceLineRef,
    build_codebase_evidence_portfolio_report,
    write_codebase_evidence_portfolio_report,
)
fixture_dir = Path("tests/fixtures/codebase-evidence-portfolio")
bundle = json.loads((fixture_dir / "m21_dars_m23_bundle.json").read_text(encoding="utf-8"))
instance_root = Path("/tmp/m23-portfolio-integration-prep")
instance_root.mkdir(parents=True, exist_ok=True)
line_refs = tuple(EvidenceLineRef(**raw) for raw in bundle["line_refs"])
request = CodebaseEvidencePortfolioRequest(
    instance_root=instance_root, date=bundle["date"], line_refs=line_refs,
    current_head_short=bundle["current_head_short"],
)
report = build_codebase_evidence_portfolio_report(request=request)
write_codebase_evidence_portfolio_report(
    instance_root=instance_root, date=bundle["date"], report=report,
)
src = instance_root / "runtime-boundary" / "codebase-evidence-portfolio" / bundle["date"]
dst = fixture_dir / "expected-m21-dars-m23"
dst.mkdir(parents=True, exist_ok=True)
(dst / "portfolio-report.json").write_bytes((src / "portfolio-report.json").read_bytes())
(dst / "portfolio-report.md").write_bytes((src / "portfolio-report.md").read_bytes())
PY
```

The regeneration step must be performed locally during the RED/GREEN row, not by CI. Once committed, the expected files are the canonical golden; the RED/GREEN row never overwrites them in subsequent runs.

**Verify GREEN:**

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_evidence_portfolio.py -q
PYTHONPATH=src pytest tests/unit/test_codebase_evidence_portfolio.py tests/unit/test_oss_comparison_adapter.py tests/unit/test_lsp_adapter.py -q
```

**Expected GREEN:** existing 6 portfolio tests + new 7th `test_codebase_evidence_portfolio_accepts_m23_adapter_lines` pass; combined OSS/LSP/portfolio suite passes; the previously-pinned `m21_dars_bundle.json` golden remains untouched.

---

## Task 3: Documentation, gate, and commit

**Objective:** Record M23 portfolio integration evidence and keep governance boundaries explicit.

**Files:**

- Modify: `docs/traceability/README.md` — prepend an `M23-ADAPTER-PORTFOLIO-INTEGRATION` row referencing the new bundle, the new expected JSON/Markdown, the new test, the M23 OSS/LSP module/CLI/test/golden files referenced by the bundle, the live LSP smoke report, the two repo-scoped live LSP runtime reports, and the verified governance invariants (`raw_source_content_persisted=false`, `external_call_made=false`, `mutation_performed=false`, `live_external_action_authorized=false`, no real OSS clone, no license-text capture, no license adjudication, DARS completion claim unchanged).
- Modify: `ralph.md` — append a Reflection Log entry following the existing M21.x/M22/M23 format with Resume checkpoint.
- Modify (if appropriate): `docs/milestone-bootstrap/profile.yaml` — bump `next_safe_task` to `M23-LIVE-LSP-SMOKE-GATE` (or `QUEUE-REFILL-PREP-STOP` if no further safe row remains) after RED/GREEN is committed, and update version/baseline-head fields. Mirror the update in `tests/unit/test_governance_docs_current_state.py`.

**Validation:**

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_evidence_portfolio.py tests/unit/test_oss_comparison_adapter.py tests/unit/test_lsp_adapter.py tests/unit/test_domain_cli.py tests/unit/test_change_impact.py tests/unit/test_architecture_candidates.py tests/unit/test_code_analysis_pass_contract.py tests/unit/test_subagent_evidence_collector_protocol.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
PYTHONPATH=src pytest tests/unit/test_governance_docs_current_state.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit (after RED/GREEN/regression and traceability update):**

```bash
git add \
  tests/unit/test_codebase_evidence_portfolio.py \
  tests/fixtures/codebase-evidence-portfolio/m21_dars_m23_bundle.json \
  tests/fixtures/codebase-evidence-portfolio/expected-m21-dars-m23/portfolio-report.json \
  tests/fixtures/codebase-evidence-portfolio/expected-m21-dars-m23/portfolio-report.md \
  docs/traceability/README.md \
  ralph.md \
  docs/milestone-bootstrap/profile.yaml \
  tests/unit/test_governance_docs_current_state.py
git commit -m "test: integrate m23 adapter lines into codebase evidence portfolio"
```

---

## M23-LIVE-LSP-SMOKE-GATE scope

After the portfolio integration RED/GREEN is committed, the optional `M23-LIVE-LSP-SMOKE-GATE` row preserves the existing live LSP smoke evidence as a controlled gate:

- Confirm `docs/reports/m23-live-lsp-server-smoke.md` records the install commands, executable versions (ruff 0.15.10, pyright 1.1.409, eslint v10.4.0), command ids (`ruff-check-live`, `pyright-check-live`, `eslint-check-live`), scopes, diagnostic counts, and exit codes.
- Confirm the two repo-scoped runtime reports `runtime-boundary/lsp-adapter/20260522/ruff-check-live/lsp-report.{json,md}` and `runtime-boundary/lsp-adapter/20260522/pyright-check-live/lsp-report.{json,md}` are referenced by the new bundle and remain in tree.
- The eslint smoke ran against a `/tmp/hisys-lsp-live-smoke/eslint-instance/` instance and is referenced only by the report; do not promote the eslint runtime report into the repo as part of this gate.
- No new live LSP execution is performed. No additional install. No additional executable. No raw diagnostic-message archival beyond the already-redacted (SHA-256-digested) `lsp-report.json` shape.
- The DARS completion claim remains `local_fixture_localhost_controlled_advisory_complete`; this gate must not claim live provider execution has been smoked from the DARS line.

The gate row produces only docs/control updates (Reflection Log + traceability + ralph.md) — no source/test/fixture change.

---

## Stop conditions

Stop and ask for a new decision if any task would require:

- remote configuration change, force push, or any new credential / token / SSH-key handling;
- live external network, browser, connector, model, or LSP/process invocation from the portfolio builder, writer, fixture, or test;
- credential lookup, mutation, or persistence;
- shelling out to `git log`, `git diff`, or any `subprocess` call from the portfolio module, fixture, or test;
- reading `.git/` directly or calling `date.today()` inside the builder or fixture;
- raw source archival, diff-hunk embedding, license-text capture, license adjudication, or persistence of file bodies/secrets in the new bundle or expected files;
- repair, deletion, retry, or quarantine of existing OSS/LSP adapter artifacts or the existing portfolio golden;
- expanding the report into approval/safe-to-deploy/readiness language;
- mutating existing M21 / DARS / M23 OSS / M23 LSP schema shapes rather than referencing them by label and id;
- adding a new line to the portfolio that has not been recorded in this PREP plan (any new line requires a fresh PREP before RED/GREEN).

## Out of scope for M23-ADAPTER-PORTFOLIO-INTEGRATION (deferred)

- New `EvidenceLineRef` fields or schema changes; the existing 5 fields are sufficient.
- New `CodebaseEvidencePortfolioReport` fields, including any signal of `live_external_action_authorized` or any LSP/OSS-specific aggregation field.
- Crawling `runtime-boundary/lsp-adapter/` or auto-discovering ruff/pyright/eslint live runs.
- Importing or invoking `src/hisys/operations/lsp_adapter.py` or `src/hisys/operations/oss_comparison_adapter.py` from the portfolio builder/test.
- Live-provider DARS panel execution.
- Real OSS repository clone, license-text capture, or license adjudication.
- Additional live LSP smoke runs beyond the existing ruff/pyright/eslint evidence.
- Any change to the existing M21+DARS bundle fixture or its expected files (`tests/fixtures/codebase-evidence-portfolio/m21_dars_bundle.json` and `expected/portfolio-report.{json,md}`).
- Any subagent execution or remote dispatch.

## Next executable action

After this Prepare plan is committed and pushed (normal push to existing `origin/dars`), run the RED command:

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_evidence_portfolio.py::test_codebase_evidence_portfolio_accepts_m23_adapter_lines -q
```

Expected failure: `FileNotFoundError` for `tests/fixtures/codebase-evidence-portfolio/m21_dars_m23_bundle.json` (or for one of the two new expected files under `expected-m21-dars-m23/`).
