# Milestone M21.6 — Change-Impact Analyzer Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for every code-bearing task. This file is the document-RED/Prepare artifact for Milestone M21 Task M21.6 — change-impact analyzer — authored after M21.5 regression benchmark fixtures shipped at `641e9a8 feat: add codebase regression benchmarks` and the M21.6 bootstrap refresh at `2d8d4ac docs: refresh m21.6 bootstrap readiness`.

**Goal:** Add a pure, local-only, advisory change-impact analyzer that maps a caller-supplied list of changed file refs to bounded sets of impacted requirement IDs, test IDs, design/interface refs, and runtime-boundary artifact refs by reading existing traceability anchors and the M21.1 coverage data shape. The analyzer must remain advisory; it never repairs, rebases, deletes, retries, fetches remotely, or authorizes live action.

**Architecture:** Add a new pure-Python module `src/hisys/operations/change_impact.py` that exposes:

1. A Pydantic `ChangeImpactRequest` record carrying the caller-supplied `instance_root: Path`, `repo_root: Path`, `changed_file_refs: tuple[str, ...]`, and optional `current_head_short: str | None`. The request is the single intake surface; no implicit `git diff`, `date.today()`, or `subprocess` call may be added in this increment.
2. A Pydantic `ChangeImpactReport` record holding `schema_id = "hisys.change_impact.v1"`, sorted impacted requirement IDs, sorted impacted test IDs/refs, sorted impacted design/interface refs, sorted unsafe/out-of-tree changed refs, sorted unmapped changed refs, sorted runtime-boundary artifact refs touched, the existing advisory flag set (`advisory_only`, `requires_human_review`, `external_call_made`, `mutation_performed`, `raw_source_content_persisted`), and bounded counts.
3. A pure function `build_change_impact_report(*, request, anchors)` that consumes a `TraceabilityAnchors` value from `src/hisys/operations/traceability_coverage.py` and the request, then classifies each changed ref into the impacted/unmapped/unsafe vocabulary using only relative file-ref matching. The function reads no file bodies.
4. A pure helper `match_changed_ref_to_anchors(*, changed_ref, anchors)` that returns a `MatchedAnchors` record naming impacted requirement IDs and test IDs/refs for a single changed file. This helper is internal but exposed for unit testing.
5. A writer `write_change_impact_report(*, instance_root, date, report)` that persists JSON + Markdown only under `runtime-boundary/change-impact/<YYYYMMDD>/impact-report.{json,md}` through the existing `resolve_instance_runtime_ref` chokepoint. The writer never writes outside that partition.

Reuse the `_DATE_PATTERN` and `resolve_instance_runtime_ref` chokepoint from `src/hisys/operations/codebase_analysis.py`. Reuse the `TraceabilityAnchors` shape from `src/hisys/operations/traceability_coverage.py`. No new dependency, no network call, no model invocation, no credential resolution, no destructive Git, no remote push, no `git diff` execution, no CLI argument expansion, and no raw source archival in this increment. A thin `hisys change-impact` CLI wrapper is deferred to a separate M21.6-CLI Prepare/RED after the pure analyzer is stable.

**Tech Stack:** Python 3.11, regex, pathlib, Pydantic v2 for the request/report records, pytest. No new dependency.

**Context Packet:** Required source handles:

- `src/hisys/operations/codebase_analysis.py` (`resolve_instance_runtime_ref`, runtime-boundary writer conventions, slug/date patterns).
- `src/hisys/operations/traceability_coverage.py` (`TraceabilityAnchors`, `load_repo_traceability_anchors`, M21.1 writer/report shape to mirror).
- `src/hisys/operations/runtime_boundary_consistency.py` (M21.3 writer/report shape and ref-safety pattern).
- `src/hisys/operations/codebase_map_freshness.py` (M21.4 writer pattern for partitioned runtime-boundary artifacts).
- `src/hisys/operations/codebase_regression_benchmarks.py` (M21.5 advisory report pattern; do not depend on fixture replay).
- `docs/traceability/README.md` (controlled traceability anchor file with `HISYS-*` and existing `M21.x` rows).
- `tests/unit/test_traceability_coverage.py` and `tests/unit/test_runtime_boundary_consistency.py` (test layout/fixture seeding patterns to mirror).
- `ralph.md` for the Reflection Log update.

**Boundary Record:** Local docs/control writes for this Prepare package, then later local test/code edits in a separate RED/GREEN increment, are allowed. Remote push is not authorized. No live external read, no repo clone, no credential resolution, no browser/network/model call, no destructive Git, no publication, no action authority. No `git diff` shell-out, no `subprocess` invocation, no broad raw source archival in any later M21.6 increment. The change-impact report is advisory only and never implies repair, deletion, retry, approval, or readiness for live action.

---

## Accepted decisions

1. **Caller-supplied refs only.** Changed refs come from the caller (test fixtures or a future CLI front-end). The analyzer does not run `git diff`, does not read `.git/`, does not call `subprocess`, and does not consult the network.
2. **No `date.today()` use.** Partition date is supplied by the caller. The analyzer never reads the system clock.
3. **Refs and counts over raw content.** The report records ref strings, ID strings, schema IDs, and bounded counts. It does not embed file bodies, source text, secrets, or diff hunks.
4. **Single canonical impact vocabulary.** Impact kinds are limited to `impacted_requirement_id`, `impacted_test_id_or_ref`, `impacted_design_or_interface_ref`, `impacted_runtime_boundary_ref`, `unmapped_changed_ref`, and `unsafe_changed_ref`. Additional kinds may be added later under a separate RED.
5. **No deletion/repair authority.** The analyzer never rewrites, deletes, regenerates, or quarantines code, tests, docs, or runtime-boundary artifacts; it only writes its own partition.
6. **Advisory only.** The report explicitly carries `advisory_only=true`, `requires_human_review=true`, `external_call_made=false`, `mutation_performed=false`, and `raw_source_content_persisted=false`. The report must not be treated as a quality-gate pass for any other Hisys flow.
7. **No CLI in this increment.** A `hisys change-impact` subcommand is M21.6-CLI work, planned separately after the pure analyzer is stable. M21.6 GREEN ships only the pure module and writer.
8. **Anchor reuse, not anchor mutation.** M21.6 imports `TraceabilityAnchors` and `load_repo_traceability_anchors` from M21.1 and does not change their shape. If a future field is needed, it must be added to M21.1 under its own RED.
9. **Bounded reads.** The analyzer reads no file bodies beyond what M21.1's anchor loader already reads. Changed refs are matched against IDs/refs already present in the anchors, never against re-parsed source text.
10. **Traceability required.** Update `docs/traceability/README.md` with an `M21.6` row only in the implementation increment, and append a Reflection Log entry plus Resume checkpoint to `ralph.md` for every checkpoint.

---

## Task 0: Reconstruct baseline before any edit

**Objective:** Confirm the M21.5 implementation and M21.6 bootstrap commits are current and the working tree is clean.

**Commands:**

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_codebase_regression_benchmarks.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_cli.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:** branch `dars`, HEAD at or after `2d8d4ac docs: refresh m21.6 bootstrap readiness`; project focused gate passes (46 expected); DARS critic-panel focused regression passes (50 expected); traceability validator OK; secret scan hit_count=0; `git diff --check` clean.

If any expected outcome diverges, stop and re-run QUEUE-REFILL-PREP before continuing.

---

## Task 1: RED — pure change-impact analyzer flags impacted requirements, tests, and unmapped refs

**Objective:** Add a failing pytest that constructs a tiny in-memory `TraceabilityAnchors`, calls `build_change_impact_report` with a small mixed list of changed refs, and asserts the report classifies each ref correctly. The test must fail before the production module exists.

**Files:**

- Create: `tests/unit/test_change_impact.py`

**Test sketch:**

```python
from __future__ import annotations

from pathlib import Path

import pytest

from hisys.operations.change_impact import (
    ChangeImpactRequest,
    build_change_impact_report,
    write_change_impact_report,
)
from hisys.operations.traceability_coverage import TraceabilityAnchors


def _seed_anchors() -> TraceabilityAnchors:
    requirement_ids = ("HISYS-FR-DOM-001", "HISYS-FR-DOM-002", "HISYS-NFR-MNT-001")
    design_requirement_refs = {
        "HISYS-FR-DOM-001": ("docs/traceability/README.md",),
        "HISYS-FR-DOM-002": ("docs/traceability/README.md",),
    }
    interface_requirement_refs = {
        "HISYS-FR-DOM-001": ("src/hisys/schemas/domain_adapter.py",),
        "HISYS-NFR-MNT-001": ("src/hisys/schemas/runtime_boundary.py",),
    }
    test_requirement_refs = {
        "HISYS-FR-DOM-001": ("tests/integration/test_trace_path.py",),
    }
    test_ids = ("STD-DOM-001",)
    test_requirement_links = {
        "STD-DOM-001": ("HISYS-FR-DOM-001", "HISYS-FR-DOM-002"),
    }
    return TraceabilityAnchors(
        requirement_ids=requirement_ids,
        design_requirement_refs=design_requirement_refs,
        interface_requirement_refs=interface_requirement_refs,
        test_requirement_refs=test_requirement_refs,
        test_ids=test_ids,
        test_requirement_links=test_requirement_links,
    )


def test_build_change_impact_report_classifies_changed_refs(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    anchors = _seed_anchors()

    request = ChangeImpactRequest(
        instance_root=instance_root,
        repo_root=repo_root,
        changed_file_refs=(
            "src/hisys/schemas/domain_adapter.py",
            "docs/traceability/README.md",
            "tests/integration/test_trace_path.py",
            "runtime-boundary/codebase-analysis/20260520/REQ-X/inventory.json",
            "src/hisys/agents/unrelated_helper.py",
            "/etc/passwd",
            "runtime-boundary/../escape.txt",
        ),
        current_head_short="2d8d4ac",
    )

    report = build_change_impact_report(request=request, anchors=anchors)

    assert report.schema_id == "hisys.change_impact.v1"
    assert report.advisory_only is True
    assert report.requires_human_review is True
    assert report.external_call_made is False
    assert report.mutation_performed is False
    assert report.raw_source_content_persisted is False
    assert "HISYS-FR-DOM-001" in report.impacted_requirement_ids
    assert "HISYS-NFR-MNT-001" in report.impacted_requirement_ids
    assert "HISYS-FR-DOM-002" in report.impacted_requirement_ids  # via design doc match
    assert "STD-DOM-001" in report.impacted_test_id_or_refs or (
        "tests/integration/test_trace_path.py" in report.impacted_test_id_or_refs
    )
    assert (
        "runtime-boundary/codebase-analysis/20260520/REQ-X/inventory.json"
        in report.impacted_runtime_boundary_refs
    )
    assert "src/hisys/agents/unrelated_helper.py" in report.unmapped_changed_refs
    assert "/etc/passwd" in report.unsafe_changed_refs
    assert "runtime-boundary/../escape.txt" in report.unsafe_changed_refs
    assert report.current_head_short == "2d8d4ac"
```

**Verify RED:**

```bash
PYTHONPATH=src pytest tests/unit/test_change_impact.py::test_build_change_impact_report_classifies_changed_refs -q
```

**Expected RED:** `ModuleNotFoundError: No module named 'hisys.operations.change_impact'` because the module has not been created yet.

---

## Task 2: GREEN — implement minimal pure change-impact analyzer and writer

**Objective:** Add the smallest production logic that satisfies the RED test and the writer invariant.

**Files:**

- Create: `src/hisys/operations/change_impact.py`

**Module shape (illustrative; minor naming may evolve during GREEN):**

```python
"""Advisory change-impact reporting.

M21.6 keeps this surface pure and local-only: callers supply a bounded list of
changed file refs and existing M21.1 traceability anchors, and the analyzer
maps each changed ref to impacted requirement IDs, test IDs/refs,
design/interface refs, or runtime-boundary refs. The optional writer persists
only JSON/Markdown summaries under ``runtime-boundary/change-impact``. The
analyzer never repairs, deletes, retries, fetches remotely, or authorizes
live action.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel, Field

from hisys.operations.codebase_analysis import resolve_instance_runtime_ref
from hisys.operations.traceability_coverage import TraceabilityAnchors

_DATE_PATTERN = re.compile(r"^\d{8}$")
_RUNTIME_BOUNDARY_ROOT = "runtime-boundary/"
_CHANGE_IMPACT_PREFIX = "runtime-boundary/change-impact"


class ChangeImpactRequest(BaseModel):
    instance_root: Path
    repo_root: Path
    changed_file_refs: tuple[str, ...]
    current_head_short: str | None = None


class ChangeImpactReport(BaseModel):
    schema_id: str = "hisys.change_impact.v1"
    current_head_short: str | None
    changed_ref_count: int
    impacted_requirement_ids: tuple[str, ...]
    impacted_test_id_or_refs: tuple[str, ...]
    impacted_design_or_interface_refs: tuple[str, ...]
    impacted_runtime_boundary_refs: tuple[str, ...]
    unmapped_changed_refs: tuple[str, ...]
    unsafe_changed_refs: tuple[str, ...]
    advisory_only: bool = True
    requires_human_review: bool = True
    external_call_made: bool = False
    mutation_performed: bool = False
    raw_source_content_persisted: bool = False


def _normalize(refs: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(refs)))


def _is_unsafe_changed_ref(ref: str) -> bool:
    if not ref:
        return True
    if ref.startswith("/"):
        return True
    parts = ref.split("/")
    if any(part == ".." for part in parts):
        return True
    return False


def build_change_impact_report(
    *,
    request: ChangeImpactRequest,
    anchors: TraceabilityAnchors,
) -> ChangeImpactReport:
    impacted_reqs: set[str] = set()
    impacted_tests: set[str] = set()
    impacted_design_refs: set[str] = set()
    impacted_runtime_refs: set[str] = set()
    unmapped: list[str] = []
    unsafe: list[str] = []

    design_index: dict[str, list[str]] = {}
    for req_id, refs in anchors.design_requirement_refs.items():
        for ref in refs:
            design_index.setdefault(ref, []).append(req_id)
    for req_id, refs in anchors.interface_requirement_refs.items():
        for ref in refs:
            design_index.setdefault(ref, []).append(req_id)

    test_index: dict[str, list[str]] = {}
    for req_id, refs in anchors.test_requirement_refs.items():
        for ref in refs:
            test_index.setdefault(ref, []).append(req_id)
    for test_id, req_ids in anchors.test_requirement_links.items():
        if test_id in anchors.test_ids:
            test_index.setdefault(test_id, []).extend(req_ids)

    for ref in request.changed_file_refs:
        if _is_unsafe_changed_ref(ref):
            unsafe.append(ref)
            continue
        mapped = False
        if ref in design_index:
            mapped = True
            impacted_design_refs.add(ref)
            for req_id in design_index[ref]:
                impacted_reqs.add(req_id)
        if ref in test_index:
            mapped = True
            for req_id in test_index[ref]:
                impacted_reqs.add(req_id)
            impacted_tests.add(ref)
        for test_id in anchors.test_ids:
            if test_id == ref or test_id in ref:
                mapped = True
                impacted_tests.add(test_id)
                for req_id in anchors.test_requirement_links.get(test_id, ()):  # noqa: E501
                    impacted_reqs.add(req_id)
        if ref.startswith(_RUNTIME_BOUNDARY_ROOT):
            mapped = True
            impacted_runtime_refs.add(ref)
        if not mapped:
            unmapped.append(ref)

    return ChangeImpactReport(
        current_head_short=request.current_head_short,
        changed_ref_count=len(request.changed_file_refs),
        impacted_requirement_ids=_normalize(impacted_reqs),
        impacted_test_id_or_refs=_normalize(impacted_tests),
        impacted_design_or_interface_refs=_normalize(impacted_design_refs),
        impacted_runtime_boundary_refs=_normalize(impacted_runtime_refs),
        unmapped_changed_refs=_normalize(unmapped),
        unsafe_changed_refs=_normalize(unsafe),
    )


def _validate_date(date: str) -> None:
    if not _DATE_PATTERN.fullmatch(date):
        raise ValueError(f"invalid change-impact report date: {date!r}")


def render_change_impact_markdown(report: ChangeImpactReport) -> str:
    ...  # bounded sections only; no diff bodies, no raw source


def write_change_impact_report(
    *, instance_root: Path, date: str, report: ChangeImpactReport
) -> dict[str, object]:
    _validate_date(date)
    rel_dir = f"{_CHANGE_IMPACT_PREFIX}/{date}"
    json_ref = f"{rel_dir}/impact-report.json"
    md_ref = f"{rel_dir}/impact-report.md"
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
    md_path.write_text(render_change_impact_markdown(report), encoding="utf-8")
    return {
        "schema_id": report.schema_id,
        "json_ref": json_ref,
        "markdown_ref": md_ref,
        "advisory_only": True,
        "requires_human_review": True,
        "external_call_made": False,
        "mutation_performed": False,
        "raw_source_content_persisted": False,
    }
```

**Verify GREEN:**

```bash
PYTHONPATH=src pytest tests/unit/test_change_impact.py -q
PYTHONPATH=src pytest tests/unit/test_change_impact.py tests/unit/test_traceability_coverage.py tests/unit/test_runtime_boundary_consistency.py -q
```

**Expected GREEN:** focused change-impact test passes; combined change-impact + coverage + consistency tests pass.

---

## Task 3: Supplemental regression — writer round-trip and unsafe-ref rejection

**Objective:** Pin the writer's safety invariants and confirm the analyzer rejects unsafe changed refs without mutating the instance root.

**Files:**

- Modify: `tests/unit/test_change_impact.py`

**Test sketch:**

```python
def test_write_change_impact_report_persists_safe_refs(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    anchors = _seed_anchors()
    request = ChangeImpactRequest(
        instance_root=instance_root,
        repo_root=repo_root,
        changed_file_refs=("docs/traceability/README.md",),
        current_head_short=None,
    )
    report = build_change_impact_report(request=request, anchors=anchors)
    refs = write_change_impact_report(
        instance_root=instance_root, date="20260521", report=report
    )
    assert refs["json_ref"] == (
        "runtime-boundary/change-impact/20260521/impact-report.json"
    )
    assert refs["external_call_made"] is False
    json_path = instance_root / refs["json_ref"]
    md_path = instance_root / refs["markdown_ref"]
    assert json_path.exists()
    assert md_path.exists()


def test_build_change_impact_report_rejects_unsafe_refs(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    anchors = _seed_anchors()
    request = ChangeImpactRequest(
        instance_root=instance_root,
        repo_root=repo_root,
        changed_file_refs=("/etc/passwd", "../escape", "ok/path.py"),
    )
    report = build_change_impact_report(request=request, anchors=anchors)
    assert "/etc/passwd" in report.unsafe_changed_refs
    assert "../escape" in report.unsafe_changed_refs
    assert "ok/path.py" in report.unmapped_changed_refs
    assert report.impacted_requirement_ids == ()


def test_write_change_impact_report_rejects_bad_date(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    anchors = _seed_anchors()
    request = ChangeImpactRequest(
        instance_root=instance_root,
        repo_root=repo_root,
        changed_file_refs=(),
    )
    report = build_change_impact_report(request=request, anchors=anchors)
    with pytest.raises(ValueError):
        write_change_impact_report(
            instance_root=instance_root, date="2026-05-21", report=report
        )
```

**Verify:**

```bash
PYTHONPATH=src pytest tests/unit/test_change_impact.py -q
```

**Expected:** focused change-impact tests pass; no other test regressions.

---

## Task 4: Documentation, gate, and commit

**Objective:** Record M21.6 implementation evidence and keep governance boundaries explicit.

**Files:**

- Modify: `docs/traceability/README.md` — prepend an `M21.6` row referencing the new module, tests, and the verified governance invariants (advisory-only, caller-supplied refs only, no `git diff` shell-out, no `subprocess`, no external calls, no raw source archival, no mutation outside the report partition).
- Modify: `ralph.md` — append a Reflection Log entry following the existing M21.x format with Resume checkpoint.

**Validation:**

```bash
PYTHONPATH=src pytest tests/unit/test_change_impact.py tests/unit/test_codebase_regression_benchmarks.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_cli.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit (after RED/GREEN/regression):**

```bash
git add tests/unit/test_change_impact.py src/hisys/operations/change_impact.py docs/traceability/README.md ralph.md
git commit -m "feat: add change-impact analyzer"
```

---

## Stop conditions

Stop and ask for a new decision if any task would require:

- remote push, fetch, or any change to remote configuration;
- live external network, browser, connector, model, or LSP/process invocation;
- credential lookup, mutation, or persistence;
- shelling out to `git diff`, `git log`, or any `subprocess` call;
- reading `.git/` directly or calling `date.today()` inside the analyzer;
- raw source archival, diff-hunk embedding, or persistence of file bodies/secrets in the report;
- repair, deletion, retry, or quarantine of code/tests/docs/runtime artifacts under inspection;
- expanding the analyzer into approval/safe-to-deploy/readiness language;
- adding the CLI in this increment (CLI is M21.6-CLI, planned separately after the pure analyzer stabilizes);
- changing the M21.1 `TraceabilityAnchors` shape rather than reusing it.

## Out of scope for M21.6 (deferred)

- `hisys change-impact` CLI subcommand (M21.6-CLI).
- Local `git diff` capture front-end. A safe diff-capture helper, if needed, is a separate M21.6-DIFFCAP Prepare/RED and must avoid shelling out from inside the analyzer module.
- Cross-branch comparison, base-branch fetch, or `origin/main` resolution.
- Symbol-level impact (function/class granularity); the MVP is file-ref granularity only.
- Test selection or test runner orchestration; the report names impacted test IDs/refs but does not execute them.
- Schema-id-aware deep validation of cited runtime-boundary refs (deferred to M21.3-SCAN or a successor checker).
- Subagent-driven evidence collection (human-gated).
- Any change to M21.1 `TraceabilityAnchors` shape; M21.6 reuses it as-is.

## Next executable action

After this Prepare plan is committed, run the RED command:

```bash
PYTHONPATH=src pytest tests/unit/test_change_impact.py::test_build_change_impact_report_classifies_changed_refs -q
```

Expected failure: `ModuleNotFoundError: No module named 'hisys.operations.change_impact'`.
