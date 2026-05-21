# Milestone M22 — Codebase Evidence Portfolio Implementation Task Plan

> **Row:** This document is the artifact produced by Ralph row `M22-PORTFOLIO-PREP`. Subsequent rows `M22-PORTFOLIO-RED-GREEN`, `M22-PORTFOLIO-CLI`, `M22-PORTFOLIO-GOLDEN`, and `M22-PORTFOLIO-GATE` are scoped below.

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for every code-bearing task. This file is the document-RED/Prepare artifact for Milestone M22 — codebase evidence portfolio — authored after the M22 authorization checkpoint at `50173ba docs: open m22 evidence portfolio queue` and after the M21 queue-end stop verified at `f5b63fb docs: queue-refill-prep verifies m21-6 roll-forward and stops on human-gated backlog`. The M22 line is a local-safe continuation; it does not authorize live provider execution, credential lookup, external repository access, local LSP process spawning, subagent execution, publication, deployment, or raw source archival.

**Goal:** Add a pure, local-only, advisory codebase-evidence-portfolio surface that aggregates the completed M21.1..M21.9 and DARS-panel local-completion evidence by reference, schema id, count, and advisory boundary flags. The portfolio answers `what local evidence exists, which artifacts back each line, which quality gates are reproducible, and which adapters remain human-gated` without copying raw source or implying live readiness.

**Architecture:** Add a new pure-Python module `src/hisys/operations/codebase_evidence_portfolio.py` that exposes:

1. A Pydantic `EvidenceLineRef` record describing one source line (M21, DARS_PANEL_LOCAL_COMPLETION, or other caller-named local line) carrying a `line_label`, sorted `artifact_refs`, sorted `schema_ids`, sorted `quality_gate_refs`, and bounded `implemented_surface_count` / `human_gated_surface_count` counts. The record never embeds artifact bodies, diff hunks, or raw source.
2. A Pydantic `CodebaseEvidencePortfolioRequest` record carrying caller-supplied `instance_root: Path`, `date: str` (`YYYYMMDD`), an ordered `line_refs: tuple[EvidenceLineRef, ...]`, and an optional `current_head_short: str | None`. The request is the single intake surface; no implicit `git log`, `date.today()`, or `subprocess` call may be added in this increment.
3. A Pydantic `CodebaseEvidencePortfolioReport` record holding `schema_id = "hisys.codebase_evidence_portfolio.v1"`, `date`, sorted `source_lines`, deduplicated `artifact_refs`, deduplicated `quality_gate_refs`, deduplicated `schema_ids`, `implemented_surface_count`, `human_gated_surface_count`, sorted `unsafe_refs`, sorted `unsafe_line_labels`, the existing advisory flag set (`advisory_only=true`, `requires_human_review=true`, `external_call_made=false`, `mutation_performed=false`, `raw_source_content_persisted=false`), and an `allowed_actions = "advisory_only"` field.
4. A pure function `build_codebase_evidence_portfolio_report(*, request)` that consumes a `CodebaseEvidencePortfolioRequest`, classifies each line's refs against the existing ref-safety rule (`..`/absolute/empty -> unsafe), aggregates counts and refs across lines, and returns the report. The function reads no file bodies, performs no globbing of `runtime-boundary/`, and does not consult `.git/` or the network.
5. A writer `write_codebase_evidence_portfolio_report(*, instance_root, date, report)` that persists JSON + Markdown only under `runtime-boundary/codebase-evidence-portfolio/<YYYYMMDD>/portfolio-report.{json,md}` through the existing `resolve_instance_runtime_ref` chokepoint. The writer never writes outside that partition.

Reuse the `_DATE_PATTERN` and `resolve_instance_runtime_ref` chokepoint from `src/hisys/operations/codebase_analysis.py`. Mirror the writer convention shared by `change_impact.py`, `architecture_candidates.py`, and `codebase_map_freshness.py`. No new dependency, no network call, no model invocation, no credential resolution, no destructive Git, no remote push, no `git log` execution, no CLI argument expansion in this increment, and no raw source archival. A thin `hisys codebase-evidence-portfolio` CLI wrapper is deferred to `M22-PORTFOLIO-CLI` after the pure builder is stable.

**Tech Stack:** Python 3.11, regex, pathlib, Pydantic v2 for the request/report records, pytest. No new dependency.

**Context Packet:** Required source handles:

- `src/hisys/operations/codebase_analysis.py` (`resolve_instance_runtime_ref`, `_DATE_PATTERN`, runtime-boundary writer conventions).
- `src/hisys/operations/change_impact.py` (M21.6 writer/report shape and `_is_unsafe_changed_ref` reference pattern).
- `src/hisys/operations/architecture_candidates.py` (M21.7 advisory writer pattern with explicit imperative-wording restraint).
- `src/hisys/operations/codebase_map_freshness.py` (M21.4 partitioned runtime-boundary writer pattern).
- `src/hisys/operations/traceability_coverage.py` (M21.1 report-shape patterns; do not import in this increment unless needed).
- `docs/traceability/README.md` (controlled traceability anchor file with `HISYS-*` and `M21.*` rows that the portfolio references by label only).
- `docs/reports/dars-panel-local-completion-audit.md` (existing DARS-panel local-completion audit report referenced by the portfolio).
- `docs/plans/m22-codebase-evidence-portfolio-implementation-plan.md` (parent plan that authorized the M22 task queue).
- `tests/unit/test_change_impact.py` and `tests/unit/test_architecture_candidates.py` (test layout/fixture patterns to mirror).
- `ralph.md` for the Reflection Log update.

**Boundary Record:** Local docs/control writes for this Prepare package, then later local test/code edits in a separate RED/GREEN increment, are allowed. Local commits and normal push to existing `origin/dars` are allowed after focused gates pass. Remote configuration change, force push, credential lookup, live external call, network clone/fetch/search, local LSP subprocess spawning, subagent execution, publication, deployment, destructive Git history, schema/data migrations against non-fixture data, and raw source-content archival beyond bounded refs/counts/digests are **not** authorized in any M22 increment without a separate human-gated approval. The portfolio report is advisory only and never implies repair, deletion, retry, approval, or readiness for live action.

---

## Accepted decisions

1. **Caller-supplied refs only.** Evidence refs come from the caller (test fixtures or a future CLI front-end). The portfolio builder does not crawl `runtime-boundary/`, does not list `docs/`, does not run `git log`, does not call `subprocess`, and does not consult the network.
2. **No `date.today()` use.** Portfolio partition date and `current_head_short` are supplied by the caller. The builder never reads the system clock or `.git/`.
3. **Refs, schema IDs, and counts over raw content.** The report records ref strings, schema-id strings, line-label strings, and bounded counts. It does not embed file bodies, source text, secrets, runtime artifact JSON contents, or diff hunks.
4. **Single canonical line vocabulary, but caller-extensible.** The seed `source_lines` are `M21` and `DARS_PANEL_LOCAL_COMPLETION`; additional line labels are allowed only when the caller supplies them as `EvidenceLineRef.line_label` strings matching `^[A-Z][A-Z0-9_\-]{1,63}$`. Lines that fail the label pattern are recorded in `unsafe_line_labels` rather than persisted as valid lines.
5. **No deletion/repair authority.** The builder never rewrites, deletes, regenerates, or quarantines code, tests, docs, or runtime-boundary artifacts; it only writes its own partition.
6. **Advisory only.** The report explicitly carries `advisory_only=true`, `requires_human_review=true`, `external_call_made=false`, `mutation_performed=false`, `raw_source_content_persisted=false`, and `allowed_actions="advisory_only"`. The report must not be treated as a quality-gate pass for any other Hisys flow.
7. **No CLI in this increment.** A `hisys codebase-evidence-portfolio` subcommand is `M22-PORTFOLIO-CLI` work, planned separately after the pure builder is stable. M22-PORTFOLIO-RED-GREEN ships only the pure module and writer; a golden fixture comes in `M22-PORTFOLIO-GOLDEN`.
8. **Anchor reuse, not anchor mutation.** M22 references M21's `runtime-boundary/...` ref strings and schema IDs (e.g., `hisys.traceability.coverage.v1`, `hisys.change_impact.v1`, `hisys.architecture_candidates.v1`) but does not import or change their record shapes.
9. **Bounded reads.** The builder reads no file bodies. Ref strings are sanitized against the same unsafe-ref rule used in M21.6 (`_is_unsafe_changed_ref`-style: absolute paths, `..` traversal, or empty strings are rejected as unsafe).
10. **Traceability required.** Update `docs/traceability/README.md` with an `M22` row only in the implementation increment, and append a Reflection Log entry plus Resume checkpoint to `ralph.md` for every checkpoint.

---

## Task 0: Reconstruct baseline before any edit

**Objective:** Confirm the M22 authorization commit is current, working tree is clean, and the M21/DARS focused gates remain green.

**Commands:**

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_change_impact.py tests/unit/test_architecture_candidates.py tests/unit/test_code_analysis_pass_contract.py tests/unit/test_subagent_evidence_collector_protocol.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
PYTHONPATH=src pytest tests/unit/test_governance_docs_current_state.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:** branch `dars`, HEAD at or after `50173ba docs: open m22 evidence portfolio queue`; M21 focused gate passes (60 expected); DARS critic-panel focused regression passes (50 expected); governance current-state test passes; traceability validator OK; secret scan `hit_count=0`; `git diff --check` clean.

If any expected outcome diverges, stop and re-run QUEUE-REFILL-PREP before continuing.

---

## Task 1: RED — pure codebase evidence portfolio aggregates M21 and DARS refs without raw source

**Objective:** Add a failing pytest that constructs in-memory `EvidenceLineRef` records for M21 and DARS-panel local completion, calls `build_codebase_evidence_portfolio_report`, and asserts the report aggregates refs, schema ids, counts, and advisory flags correctly. The test must fail before the production module exists.

**Files:**

- Create: `tests/unit/test_codebase_evidence_portfolio.py`

**Test sketch:**

```python
from __future__ import annotations

from pathlib import Path

import pytest

from hisys.operations.codebase_evidence_portfolio import (
    CodebaseEvidencePortfolioRequest,
    EvidenceLineRef,
    build_codebase_evidence_portfolio_report,
    write_codebase_evidence_portfolio_report,
)


def _m21_line() -> EvidenceLineRef:
    return EvidenceLineRef(
        line_label="M21",
        artifact_refs=(
            "docs/plans/m21-1-traceability-coverage-report-implementation-tasks.md",
            "docs/plans/m21-6-change-impact-analyzer-implementation-tasks.md",
            "docs/plans/m21-7-architecture-candidate-generator-implementation-tasks.md",
        ),
        schema_ids=(
            "hisys.traceability.coverage.v1",
            "hisys.change_impact.v1",
            "hisys.architecture_candidates.v1",
        ),
        quality_gate_refs=(
            "tests/unit/test_traceability_coverage.py",
            "tests/unit/test_change_impact.py",
            "tests/unit/test_architecture_candidates.py",
        ),
        implemented_surface_count=9,
        human_gated_surface_count=2,
    )


def _dars_line() -> EvidenceLineRef:
    return EvidenceLineRef(
        line_label="DARS_PANEL_LOCAL_COMPLETION",
        artifact_refs=(
            "docs/plans/dars-panel-completion-before-codebase-return.md",
            "docs/reports/dars-panel-local-completion-audit.md",
        ),
        schema_ids=("hisys.dars_panel_readiness.v1",),
        quality_gate_refs=(
            "tests/unit/test_dars_critic_panel_runtime.py",
            "tests/unit/test_dars_critic_panel_cli.py",
        ),
        implemented_surface_count=5,
        human_gated_surface_count=0,
    )


def test_build_codebase_evidence_portfolio_aggregates_m21_and_dars(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    request = CodebaseEvidencePortfolioRequest(
        instance_root=instance_root,
        date="20260521",
        line_refs=(_m21_line(), _dars_line()),
        current_head_short="50173ba",
    )

    report = build_codebase_evidence_portfolio_report(request=request)

    assert report.schema_id == "hisys.codebase_evidence_portfolio.v1"
    assert report.date == "20260521"
    assert report.current_head_short == "50173ba"
    assert report.source_lines == ("DARS_PANEL_LOCAL_COMPLETION", "M21")
    assert "hisys.change_impact.v1" in report.schema_ids
    assert "hisys.dars_panel_readiness.v1" in report.schema_ids
    assert (
        "docs/reports/dars-panel-local-completion-audit.md"
        in report.artifact_refs
    )
    assert "tests/unit/test_change_impact.py" in report.quality_gate_refs
    assert report.implemented_surface_count == 14
    assert report.human_gated_surface_count == 2
    assert report.unsafe_refs == ()
    assert report.unsafe_line_labels == ()
    assert report.advisory_only is True
    assert report.requires_human_review is True
    assert report.external_call_made is False
    assert report.mutation_performed is False
    assert report.raw_source_content_persisted is False
    assert report.allowed_actions == "advisory_only"
```

**Verify RED:**

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_evidence_portfolio.py::test_build_codebase_evidence_portfolio_aggregates_m21_and_dars -q
```

**Expected RED:** `ModuleNotFoundError: No module named 'hisys.operations.codebase_evidence_portfolio'` because the module has not been created yet.

---

## Task 2: GREEN — implement minimal pure codebase evidence portfolio and writer

**Objective:** Add the smallest production logic that satisfies the RED test and the writer invariant.

**Files:**

- Create: `src/hisys/operations/codebase_evidence_portfolio.py`

**Module shape (illustrative; minor naming may evolve during GREEN):**

```python
"""Advisory codebase evidence portfolio reporting.

M22 keeps this surface pure and local-only: callers supply bounded evidence
line references (M21, DARS_PANEL_LOCAL_COMPLETION, or caller-named lines), and
the builder aggregates artifact refs, schema ids, quality-gate refs, and
bounded counts. The optional writer persists only JSON/Markdown summaries
under ``runtime-boundary/codebase-evidence-portfolio``. The builder never
opens artifact bodies, crawls ``runtime-boundary/``, calls Git or
``subprocess``, contacts the network, executes subagents, or authorizes live
action.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel, Field

from hisys.operations.codebase_analysis import resolve_instance_runtime_ref

_DATE_PATTERN = re.compile(r"^\d{8}$")
_LINE_LABEL_PATTERN = re.compile(r"^[A-Z][A-Z0-9_\-]{1,63}$")
_PORTFOLIO_PREFIX = "runtime-boundary/codebase-evidence-portfolio"


class EvidenceLineRef(BaseModel):
    line_label: str
    artifact_refs: tuple[str, ...] = ()
    schema_ids: tuple[str, ...] = ()
    quality_gate_refs: tuple[str, ...] = ()
    implemented_surface_count: int = 0
    human_gated_surface_count: int = 0


class CodebaseEvidencePortfolioRequest(BaseModel):
    instance_root: Path
    date: str
    line_refs: tuple[EvidenceLineRef, ...] = ()
    current_head_short: str | None = None


class CodebaseEvidencePortfolioReport(BaseModel):
    schema_id: str = "hisys.codebase_evidence_portfolio.v1"
    date: str
    current_head_short: str | None
    source_lines: tuple[str, ...]
    artifact_refs: tuple[str, ...]
    schema_ids: tuple[str, ...]
    quality_gate_refs: tuple[str, ...]
    implemented_surface_count: int
    human_gated_surface_count: int
    unsafe_refs: tuple[str, ...]
    unsafe_line_labels: tuple[str, ...]
    advisory_only: bool = True
    requires_human_review: bool = True
    external_call_made: bool = False
    mutation_performed: bool = False
    raw_source_content_persisted: bool = False
    allowed_actions: str = "advisory_only"


def _normalize(refs: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(refs)))


def _is_unsafe_ref(ref: str) -> bool:
    if not ref:
        return True
    if ref.startswith("/"):
        return True
    parts = ref.split("/")
    if any(part == ".." for part in parts):
        return True
    return False


def build_codebase_evidence_portfolio_report(
    *, request: CodebaseEvidencePortfolioRequest
) -> CodebaseEvidencePortfolioReport:
    if not _DATE_PATTERN.fullmatch(request.date):
        raise ValueError(f"invalid portfolio date: {request.date!r}")
    valid_labels: list[str] = []
    unsafe_labels: list[str] = []
    artifact_refs: set[str] = set()
    schema_ids: set[str] = set()
    quality_gate_refs: set[str] = set()
    unsafe_refs: set[str] = set()
    implemented_total = 0
    human_gated_total = 0

    for line in request.line_refs:
        if not _LINE_LABEL_PATTERN.fullmatch(line.line_label):
            unsafe_labels.append(line.line_label)
            continue
        valid_labels.append(line.line_label)
        for ref in line.artifact_refs:
            (unsafe_refs if _is_unsafe_ref(ref) else artifact_refs).add(ref)
        for ref in line.quality_gate_refs:
            (unsafe_refs if _is_unsafe_ref(ref) else quality_gate_refs).add(ref)
        for sid in line.schema_ids:
            if sid:
                schema_ids.add(sid)
        implemented_total += int(line.implemented_surface_count)
        human_gated_total += int(line.human_gated_surface_count)

    return CodebaseEvidencePortfolioReport(
        date=request.date,
        current_head_short=request.current_head_short,
        source_lines=_normalize(valid_labels),
        artifact_refs=_normalize(artifact_refs),
        schema_ids=_normalize(schema_ids),
        quality_gate_refs=_normalize(quality_gate_refs),
        implemented_surface_count=implemented_total,
        human_gated_surface_count=human_gated_total,
        unsafe_refs=_normalize(unsafe_refs),
        unsafe_line_labels=_normalize(unsafe_labels),
    )


def render_codebase_evidence_portfolio_markdown(
    report: CodebaseEvidencePortfolioReport,
) -> str:
    ...  # bounded sections only; no diff bodies, no raw source, no live wording


def write_codebase_evidence_portfolio_report(
    *,
    instance_root: Path,
    date: str,
    report: CodebaseEvidencePortfolioReport,
) -> dict[str, object]:
    if not _DATE_PATTERN.fullmatch(date):
        raise ValueError(f"invalid portfolio report date: {date!r}")
    rel_dir = f"{_PORTFOLIO_PREFIX}/{date}"
    json_ref = f"{rel_dir}/portfolio-report.json"
    md_ref = f"{rel_dir}/portfolio-report.md"
    json_path = resolve_instance_runtime_ref(
        instance_root=instance_root, relative_ref=json_ref
    )
    md_path = resolve_instance_runtime_ref(
        instance_root=instance_root, relative_ref=md_ref
    )
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(
        render_codebase_evidence_portfolio_markdown(report), encoding="utf-8"
    )
    return {
        "schema_id": report.schema_id,
        "json_ref": json_ref,
        "markdown_ref": md_ref,
        "advisory_only": True,
        "requires_human_review": True,
        "external_call_made": False,
        "mutation_performed": False,
        "raw_source_content_persisted": False,
        "allowed_actions": "advisory_only",
    }
```

**Verify GREEN:**

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_evidence_portfolio.py -q
PYTHONPATH=src pytest tests/unit/test_codebase_evidence_portfolio.py tests/unit/test_change_impact.py tests/unit/test_architecture_candidates.py tests/unit/test_traceability_coverage.py -q
```

**Expected GREEN:** focused portfolio test passes; combined portfolio + M21 sibling tests pass.

---

## Task 3: Supplemental regression — writer round-trip, unsafe-ref rejection, and bad-date rejection

**Objective:** Pin the writer's safety invariants and confirm the builder rejects unsafe artifact refs, malformed line labels, and bad dates without mutating the instance root.

**Files:**

- Modify: `tests/unit/test_codebase_evidence_portfolio.py`

**Test sketch:**

```python
def test_write_codebase_evidence_portfolio_persists_safe_refs(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    request = CodebaseEvidencePortfolioRequest(
        instance_root=instance_root,
        date="20260521",
        line_refs=(_m21_line(),),
    )
    report = build_codebase_evidence_portfolio_report(request=request)
    refs = write_codebase_evidence_portfolio_report(
        instance_root=instance_root, date="20260521", report=report
    )
    assert refs["json_ref"] == (
        "runtime-boundary/codebase-evidence-portfolio/20260521/portfolio-report.json"
    )
    assert refs["external_call_made"] is False
    assert refs["allowed_actions"] == "advisory_only"
    json_path = instance_root / refs["json_ref"]
    md_path = instance_root / refs["markdown_ref"]
    assert json_path.exists()
    assert md_path.exists()


def test_build_portfolio_rejects_unsafe_refs_and_labels(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    request = CodebaseEvidencePortfolioRequest(
        instance_root=instance_root,
        date="20260521",
        line_refs=(
            EvidenceLineRef(
                line_label="M21",
                artifact_refs=(
                    "docs/plans/m21-1-traceability-coverage-report-implementation-tasks.md",
                    "/etc/passwd",
                    "../escape.md",
                ),
                schema_ids=("hisys.traceability.coverage.v1",),
                quality_gate_refs=("tests/unit/test_traceability_coverage.py",),
                implemented_surface_count=1,
                human_gated_surface_count=0,
            ),
            EvidenceLineRef(
                line_label="lowercase-not-allowed",
                artifact_refs=("docs/plans/should-not-leak.md",),
            ),
        ),
    )
    report = build_codebase_evidence_portfolio_report(request=request)
    assert "M21" in report.source_lines
    assert "lowercase-not-allowed" in report.unsafe_line_labels
    assert "/etc/passwd" in report.unsafe_refs
    assert "../escape.md" in report.unsafe_refs
    assert "docs/plans/should-not-leak.md" not in report.artifact_refs
    assert (
        "docs/plans/m21-1-traceability-coverage-report-implementation-tasks.md"
        in report.artifact_refs
    )


def test_build_portfolio_rejects_bad_date(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    request = CodebaseEvidencePortfolioRequest(
        instance_root=instance_root,
        date="2026-05-21",
        line_refs=(),
    )
    with pytest.raises(ValueError):
        build_codebase_evidence_portfolio_report(request=request)


def test_write_codebase_evidence_portfolio_rejects_bad_date(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    request = CodebaseEvidencePortfolioRequest(
        instance_root=instance_root,
        date="20260521",
        line_refs=(_m21_line(),),
    )
    report = build_codebase_evidence_portfolio_report(request=request)
    with pytest.raises(ValueError):
        write_codebase_evidence_portfolio_report(
            instance_root=instance_root, date="2026-05-21", report=report
        )
```

**Verify:**

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_evidence_portfolio.py -q
```

**Expected:** focused portfolio tests pass; no other test regressions.

---

## Task 4: Documentation, gate, and commit

**Objective:** Record M22 implementation evidence and keep governance boundaries explicit.

**Files:**

- Modify: `docs/traceability/README.md` — prepend an `M22` row referencing the new module, tests, parent plan, and the verified governance invariants (advisory-only, caller-supplied refs only, no crawling of `runtime-boundary/`, no `git log` shell-out, no `subprocess`, no external calls, no raw source archival, no mutation outside the report partition).
- Modify: `ralph.md` — append a Reflection Log entry following the existing M21.x format with Resume checkpoint.
- Modify (if appropriate): `docs/milestone-bootstrap/profile.yaml` — bump `next_safe_task` to `M22-PORTFOLIO-CLI` after RED/GREEN is committed, and update the version/baseline-head fields. Mirror the update in `tests/unit/test_governance_docs_current_state.py`.

**Validation:**

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_evidence_portfolio.py tests/unit/test_change_impact.py tests/unit/test_architecture_candidates.py tests/unit/test_code_analysis_pass_contract.py tests/unit/test_subagent_evidence_collector_protocol.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
PYTHONPATH=src pytest tests/unit/test_governance_docs_current_state.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit (after RED/GREEN/regression and traceability update):**

```bash
git add tests/unit/test_codebase_evidence_portfolio.py src/hisys/operations/codebase_evidence_portfolio.py docs/traceability/README.md ralph.md docs/milestone-bootstrap/profile.yaml tests/unit/test_governance_docs_current_state.py
git commit -m "feat: add codebase evidence portfolio"
```

---

## M22-PORTFOLIO-CLI deferral note

After M22-PORTFOLIO-RED-GREEN is committed and the focused gates remain green, the CLI wrapper follows the M21.6-CLI/M21.7-CLI/M21.4-CLI pattern:

- Add `hisys codebase-evidence-portfolio --instance <root> --date <YYYYMMDD> [--line-label <LABEL> --artifact-ref <ref>... --schema-id <id>... --quality-gate-ref <ref>... --implemented-count <int> --human-gated-count <int>]* [--current-head-short <hash>]` to `src/hisys/cli/main.py`.
- Group repeated `--artifact-ref`/`--schema-id`/`--quality-gate-ref` flags under the most recent `--line-label` value via an argparse `Action` that opens a new `EvidenceLineRef` whenever `--line-label` is seen.
- Call `build_codebase_evidence_portfolio_report` and `write_codebase_evidence_portfolio_report`; print bounded `portfolio_count`, `source_lines`, `external_call_made: false`, `allowed_actions: advisory_only` summary lines.
- The CLI must not call `date.today()`, must not read `.git/`, must not call `subprocess`, must not crawl `runtime-boundary/`, and must not infer latest artifacts.

A full RED/GREEN plan for the CLI lives in a separate `docs/plans/m22-cli-codebase-evidence-portfolio-implementation-tasks.md` authored only after the pure builder is committed.

## M22-PORTFOLIO-GOLDEN scope

After the CLI ships, add a deterministic golden-fixture test that pins one canonical M21 + DARS line bundle, runs the pure builder, and compares its JSON output against a checked-in expected file under `tests/fixtures/codebase-evidence-portfolio/`. The golden fixture must not embed raw source bodies; it only pins refs, schema ids, and counts.

## M22-PORTFOLIO-GATE scope

After the golden fixture passes, append a `Done: M22-PORTFOLIO-GATE` line to `ralph.md` Section 16 with full focused/full gate evidence, run a QUEUE-REFILL-PREP preflight, and stop only if no safe local M22 follow-on remains. Live-provider, OSS-comparison adapter, optional local LSP adapter, and subagent-execution candidates remain human-gated.

---

## Stop conditions

Stop and ask for a new decision if any task would require:

- remote configuration change, force push, or any new credential / token / SSH-key handling;
- live external network, browser, connector, model, or LSP/process invocation from the portfolio builder, writer, or CLI;
- credential lookup, mutation, or persistence;
- shelling out to `git log`, `git diff`, or any `subprocess` call from the portfolio module;
- reading `.git/` directly or calling `date.today()` inside the builder;
- raw source archival, diff-hunk embedding, or persistence of file bodies/secrets in the report;
- repair, deletion, retry, or quarantine of artifacts under inspection;
- expanding the report into approval/safe-to-deploy/readiness language;
- adding the CLI in the M22-PORTFOLIO-RED-GREEN increment (CLI is M22-PORTFOLIO-CLI, planned separately after the pure builder stabilizes);
- mutating existing M21 / DARS schema shapes rather than referencing them by label and id.

## Out of scope for M22 (deferred)

- `runtime-boundary/` directory crawling or `--scan` mode; M22 requires caller-supplied refs only.
- Local `git log` capture front-end (`--current-head-short` is caller-supplied).
- Cross-branch comparison, base-branch fetch, or `origin/main` resolution.
- Symbol-level or function-level evidence aggregation; the MVP is line/ref/schema-id granularity only.
- Subagent-driven evidence collection (human-gated).
- Live-provider DARS panel execution (separately governed plan).
- Approved OSS comparison adapter (human-gated per `docs/plans/m21-roadmap-implementation-plan.md`).
- Optional local LSP adapter (human-gated per the same plan).
- Any change to existing M21 schema shapes (`hisys.traceability.coverage.v1`, `hisys.change_impact.v1`, `hisys.architecture_candidates.v1`, etc.).
- Schema-id-aware deep validation of cited runtime-boundary refs (the M21.3 consistency checker already covers that case).

## Next executable action

After this Prepare plan is committed and pushed (normal push to existing `origin/dars`), run the RED command:

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_evidence_portfolio.py::test_build_codebase_evidence_portfolio_aggregates_m21_and_dars -q
```

Expected failure: `ModuleNotFoundError: No module named 'hisys.operations.codebase_evidence_portfolio'`.
