# M23 — Approved OSS Comparison Adapter Implementation Task Plan

> **Row:** This document is the artifact produced by Ralph row `M23-OSS-ADAPTER-PREP`. Subsequent rows `M23-OSS-ADAPTER-RED-GREEN`, and the later `M23-OSS-ADAPTER-CLI` / `M23-OSS-ADAPTER-GOLDEN` follow-ons are scoped at the end of this file.

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for every code-bearing task. This file is the document-RED/Prepare artifact for the M23 approved OSS comparison adapter line, authored after the M23 authorization checkpoint at `9c095dd docs: open m23 advanced adapter queue` and after the M22 codebase evidence portfolio closed at `cd944cc docs: close m22 codebase evidence portfolio milestone`. The M23 OSS adapter is fixture-local only: it does not authorize network fetch, repository clone, credential lookup, live OSS API access, subagent execution, LSP subprocess spawning, publication, deployment, or raw source-content archival.

**Goal:** Add a pure, local-only, advisory `OSS comparison adapter` surface that compares a caller-named local codebase evidence line (e.g., `M21`, `DARS_PANEL_LOCAL_COMPLETION`, or any portfolio line) against caller-supplied **approved OSS source descriptors**. The adapter records which evidence categories the local line and each approved source declare, computes set-based overlap/gap counts, and emits an advisory comparison report. The report links back to the M22 codebase evidence portfolio by reference and never embeds OSS source bodies, secrets, license text, or runtime artifact JSON contents.

**Architecture:** Add a new pure-Python module `src/hisys/operations/oss_comparison_adapter.py` exposing:

1. A Pydantic `ApprovedOssSource` record describing one caller-supplied OSS reference: `source_id` (matching `^[a-z][a-z0-9_\-]{1,63}$`), `source_name` (human-readable label), `license_tag` (e.g., `MIT`, `Apache-2.0`, `BSD-3-Clause`, `n/a`), sorted `category_refs: tuple[str, ...]` (e.g., `traceability_coverage`, `change_impact`, `architecture_candidates`, `dars_panel_runtime`), sorted `approved_refs: tuple[str, ...]` (paths under `docs/` describing the approval), sorted `local_fixture_refs: tuple[str, ...]` (paths under `tests/fixtures/` that pin the approved source description for tests), and optional `notes` (bounded free text, plain ASCII, no embedded raw source).
2. A Pydantic `LocalCodebaseLine` record describing the local subject: `line_label` (matching `^[A-Z][A-Z0-9_\-]{1,63}$`), sorted `category_refs: tuple[str, ...]`, sorted `portfolio_refs: tuple[str, ...]` (paths under `docs/`, `tests/fixtures/`, or runtime-boundary refs the M22 portfolio already covers), and bounded `implemented_surface_count` / `human_gated_surface_count` integers.
3. A Pydantic `OssComparisonRequest` record carrying `instance_root: Path`, `date: str` (`YYYYMMDD`), `local_line: LocalCodebaseLine`, ordered `approved_sources: tuple[ApprovedOssSource, ...]`, and optional `current_head_short: str | None`. The request is the single intake surface; no implicit `git log`, `date.today()`, `subprocess`, network call, package import, or filesystem crawl may be added.
4. A Pydantic `OssComparisonReport` record holding `schema_id = "hisys.oss_comparison_adapter.v1"`, `date`, `current_head_short`, `local_line_label`, sorted `compared_source_ids`, sorted `compared_source_license_tags`, sorted `local_category_refs`, sorted `union_category_refs`, sorted `intersection_category_refs`, sorted `local_only_category_refs` (local categories absent from every approved source), sorted `oss_only_category_refs` (approved-source categories absent from the local line), sorted `unsafe_refs`, sorted `unsafe_source_ids`, sorted `unsafe_line_labels`, `compared_source_count`, `union_category_count`, `intersection_category_count`, `local_only_category_count`, `oss_only_category_count`, the existing advisory flag set (`advisory_only=true`, `requires_human_review=true`, `external_call_made=false`, `mutation_performed=false`, `raw_source_content_persisted=false`, `live_external_action_authorized=false`), and `allowed_actions = "advisory_only"`.
5. A pure function `build_oss_comparison_report(*, request)` that consumes an `OssComparisonRequest`, classifies refs through the existing safety rule (`..`, absolute path, empty -> unsafe), rejects sources whose `source_id` fails the source-id pattern (collected into `unsafe_source_ids`), rejects local lines whose `line_label` fails the label pattern, computes set-based union/intersection/diff over normalized category refs, and returns the report. The function reads no file bodies, performs no globbing of `runtime-boundary/`, does not consult `.git/`, and does not contact the network.
6. A writer `write_oss_comparison_report(*, instance_root, date, report)` that persists JSON + Markdown only under `runtime-boundary/oss-comparison/<YYYYMMDD>/comparison-report.{json,md}` through the existing `resolve_instance_runtime_ref` chokepoint. The writer never writes outside that partition.

Reuse the `_DATE_PATTERN`, `resolve_instance_runtime_ref`, and unsafe-ref rule from `src/hisys/operations/codebase_analysis.py` and `src/hisys/operations/codebase_evidence_portfolio.py`. Mirror the writer convention shared by `change_impact.py`, `architecture_candidates.py`, `codebase_map_freshness.py`, and `codebase_evidence_portfolio.py`. No new dependency, no network call, no model invocation, no credential resolution, no destructive Git, no remote push, no `git log` execution, no CLI argument expansion in this RED-GREEN increment, no raw source archival, and no OSS package installation. A thin `hisys oss-comparison-adapter` CLI wrapper is deferred to `M23-OSS-ADAPTER-CLI` after the pure builder is stable. A deterministic golden-fixture round-trip is deferred to `M23-OSS-ADAPTER-GOLDEN`.

**Tech Stack:** Python 3.11, regex, pathlib, Pydantic v2 for the request/report records, pytest. No new dependency.

**Context Packet:** Required source handles:

- `docs/plans/m23-advanced-codebase-adapter-integration-plan.md` (parent M23 plan; lists the OSS adapter as the first executable row and pins the M23 authorization boundary).
- `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.21.md` (user authorization record for M23).
- `docs/plans/m22-codebase-evidence-portfolio-implementation-plan.md` and `docs/plans/m22-codebase-evidence-portfolio-implementation-tasks.md` (analogous local-fixture-only PREP/RED/GREEN shape; mirror caller-supplied input, no crawling, advisory-only output).
- `docs/plans/m21-roadmap-implementation-plan.md` (lines 37-38 originally human-gated the OSS comparison adapter; M23 authorization opens the docs/control + fixture-local path while preserving the same no-credential / no-network / no-clone boundary).
- `src/hisys/operations/codebase_evidence_portfolio.py` (`EvidenceLineRef`, `_LINE_LABEL_PATTERN`, `_DATE_PATTERN`, `_is_unsafe_ref`, `_normalize`, writer chokepoint; the OSS adapter reuses the patterns but does not import the portfolio types).
- `src/hisys/operations/codebase_analysis.py` (`resolve_instance_runtime_ref` chokepoint).
- `src/hisys/operations/change_impact.py`, `src/hisys/operations/architecture_candidates.py`, `src/hisys/operations/codebase_map_freshness.py` (sibling writer/report shapes for record consistency).
- `docs/traceability/README.md` (controlled traceability anchor; an `M23-OSS-ADAPTER-RED-GREEN` row is appended only in the implementation increment).
- `tests/unit/test_codebase_evidence_portfolio.py` (test layout pattern; mirror its `tmp_path` plus `EvidenceLineRef` fixtures).
- `ralph.md` Section 16 + Reflection Log (PREP/RED/GREEN/GATE checkpoints).

**Boundary Record:** This Prepare packet performs only docs/control writes. Subsequent rows perform fixture-local test/code edits inside the M23 authorization boundary recorded in `ralph.md` Section 16. **Not authorized** in any M23 OSS adapter increment without a separate human gate: network fetch, OSS repository clone, package installation, license-text capture, raw OSS source archival, credential lookup, live OSS API access, secret capture, subagent execution, LSP subprocess spawning, publication / deployment / release, remote configuration change, force push, destructive Git/history actions, mutation of non-fixture user/live data, raw source bodies inside fixture descriptors, or repair/deletion/quarantine of artifacts under inspection. The adapter is advisory only and never claims compliance, fitness, approval, deployment, or readiness for live action.

---

## Accepted decisions

1. **Caller-supplied refs only.** Approved OSS sources are described by caller fixtures or a future CLI front-end. The adapter does not crawl `tests/fixtures/`, does not glob `docs/`, does not run `git log`, does not call `subprocess`, does not contact the network, and does not install or import OSS packages.
2. **No `date.today()` use.** The partition `date` and `current_head_short` are supplied by the caller. The builder never reads the system clock or `.git/`.
3. **Category refs, license tags, and counts over raw OSS content.** The report records normalized category-ref strings, license-tag strings, approved-source IDs, fixture refs, and bounded counts. It does not embed OSS file bodies, OSS license text, source code snapshots, secrets, runtime artifact JSON contents, or diff hunks.
4. **Two label vocabularies.** Approved-source IDs match `^[a-z][a-z0-9_\-]{1,63}$` (lowercase, hyphen/underscore allowed). Local line labels match `^[A-Z][A-Z0-9_\-]{1,63}$` (uppercase, matching the existing M22 portfolio vocabulary). Sources/lines that fail the pattern are collected into `unsafe_source_ids` / `unsafe_line_labels` rather than persisted as valid records.
5. **Set-based comparison only.** The adapter computes union, intersection, local-only, and OSS-only category sets over normalized strings. It performs no fuzzy matching, no embedding similarity, no model call, no semantic-rewrite expansion, and no token-level diff.
6. **No deletion/repair authority.** The builder never rewrites, deletes, regenerates, or quarantines code, tests, docs, runtime-boundary artifacts, or fixture sources; it only writes its own runtime-boundary partition.
7. **Advisory only.** The report carries `advisory_only=true`, `requires_human_review=true`, `external_call_made=false`, `mutation_performed=false`, `raw_source_content_persisted=false`, `live_external_action_authorized=false`, and `allowed_actions="advisory_only"`. The report must not be treated as a quality-gate pass, license-compliance certificate, or fitness-for-purpose claim.
8. **No CLI in this increment.** A `hisys oss-comparison-adapter` subcommand is `M23-OSS-ADAPTER-CLI` work, planned separately after the pure builder is stable. `M23-OSS-ADAPTER-RED-GREEN` ships only the pure module and writer; a golden fixture comes in `M23-OSS-ADAPTER-GOLDEN`.
9. **Anchor reuse, not anchor mutation.** M23 references portfolio refs and category labels from `docs/traceability/README.md`, M21 schemas, and DARS panel docs, but does not import or change M22 portfolio record shapes.
10. **Bounded reads.** The builder reads no file bodies. Ref strings are sanitized against the same unsafe-ref rule used in M21.6/M22 (`_is_unsafe_ref`-style: absolute paths, `..` traversal, or empty strings are rejected as unsafe). Notes are clamped to a max length of 1024 characters and to printable ASCII (no embedded control characters) so a malformed fixture cannot smuggle binary content through `notes`.
11. **Traceability required.** Update `docs/traceability/README.md` with an `M23-OSS-ADAPTER-RED-GREEN` row only in the implementation increment, and append a Reflection Log entry plus Resume checkpoint to `ralph.md` for every M23 checkpoint.

---

## Task 0: Reconstruct baseline before any edit

**Objective:** Confirm the M23 authorization commit is current, the working tree is clean, and the M22/M21/DARS focused gates remain green.

**Commands:**

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_codebase_evidence_portfolio.py tests/unit/test_change_impact.py tests/unit/test_architecture_candidates.py tests/unit/test_code_analysis_pass_contract.py tests/unit/test_subagent_evidence_collector_protocol.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
PYTHONPATH=src pytest tests/unit/test_governance_docs_current_state.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:** branch `dars`, HEAD at or after `9c095dd docs: open m23 advanced adapter queue`; M22+M21 combined focused gate passes; DARS critic-panel focused regression passes; governance current-state test passes; traceability validator OK; secret scan `hit_count=0`; `git diff --check` clean.

If any expected outcome diverges, stop and re-run QUEUE-REFILL-PREP before continuing.

---

## Task 1: RED — pure OSS comparison adapter aggregates a local line and approved sources without raw content

**Objective:** Add a failing pytest that constructs in-memory `LocalCodebaseLine` plus two `ApprovedOssSource` records, calls `build_oss_comparison_report`, and asserts the report computes set-based overlap counts and carries the advisory boundary flags. The test must fail before the production module exists.

**Files:**

- Create: `tests/unit/test_oss_comparison_adapter.py`
- Create: `tests/fixtures/oss/approved/` (empty directory placeholder under `tests/fixtures/oss/` to host later in-test descriptor JSON; this PREP packet does not yet add fixture files — the RED-GREEN increment adds bounded JSON descriptors inline in the test and only persists fixture files if needed for the golden round-trip in `M23-OSS-ADAPTER-GOLDEN`).

**Test sketch:**

```python
from __future__ import annotations

from pathlib import Path

import pytest

from hisys.operations.oss_comparison_adapter import (
    ApprovedOssSource,
    LocalCodebaseLine,
    OssComparisonRequest,
    build_oss_comparison_report,
    write_oss_comparison_report,
)


def _m21_local_line() -> LocalCodebaseLine:
    return LocalCodebaseLine(
        line_label="M21",
        category_refs=(
            "architecture_candidates",
            "change_impact",
            "code_analysis_pass_contract",
            "codebase_map_freshness",
            "runtime_boundary_consistency",
            "subagent_evidence_collector_protocol",
            "traceability_coverage",
        ),
        portfolio_refs=(
            "docs/plans/m21-1-traceability-coverage-report-implementation-tasks.md",
            "docs/plans/m21-6-change-impact-analyzer-implementation-tasks.md",
            "docs/plans/m21-7-architecture-candidate-generator-implementation-tasks.md",
        ),
        implemented_surface_count=9,
        human_gated_surface_count=2,
    )


def _approved_oss_understand() -> ApprovedOssSource:
    return ApprovedOssSource(
        source_id="understand-static-analysis",
        source_name="Approved static-analysis reference",
        license_tag="n/a",
        category_refs=(
            "architecture_candidates",
            "change_impact",
            "traceability_coverage",
        ),
        approved_refs=(
            "docs/plans/m23-advanced-codebase-adapter-integration-plan.md",
        ),
        local_fixture_refs=(
            "tests/fixtures/oss/approved/understand-static-analysis.json",
        ),
        notes="Local fixture descriptor only; no upstream content fetched.",
    )


def _approved_oss_pylint() -> ApprovedOssSource:
    return ApprovedOssSource(
        source_id="pylint-style-rules",
        source_name="Approved style/lint reference",
        license_tag="GPL-2.0-or-later",
        category_refs=(
            "code_analysis_pass_contract",
            "runtime_boundary_consistency",
            "style_conventions",
        ),
        approved_refs=(
            "docs/plans/m23-advanced-codebase-adapter-integration-plan.md",
        ),
        local_fixture_refs=(
            "tests/fixtures/oss/approved/pylint-style-rules.json",
        ),
        notes="Local fixture descriptor only.",
    )


def test_build_oss_comparison_aggregates_local_line_and_approved_sources(
    tmp_path: Path,
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    request = OssComparisonRequest(
        instance_root=instance_root,
        date="20260521",
        local_line=_m21_local_line(),
        approved_sources=(_approved_oss_understand(), _approved_oss_pylint()),
        current_head_short="9c095dd",
    )

    report = build_oss_comparison_report(request=request)

    assert report.schema_id == "hisys.oss_comparison_adapter.v1"
    assert report.date == "20260521"
    assert report.current_head_short == "9c095dd"
    assert report.local_line_label == "M21"
    assert report.compared_source_ids == (
        "pylint-style-rules",
        "understand-static-analysis",
    )
    assert report.compared_source_license_tags == ("GPL-2.0-or-later", "n/a")
    assert report.compared_source_count == 2
    assert "traceability_coverage" in report.intersection_category_refs
    assert "code_analysis_pass_contract" in report.intersection_category_refs
    assert "subagent_evidence_collector_protocol" in report.local_only_category_refs
    assert "style_conventions" in report.oss_only_category_refs
    assert report.union_category_count >= 8
    assert report.unsafe_refs == ()
    assert report.unsafe_source_ids == ()
    assert report.unsafe_line_labels == ()
    assert report.advisory_only is True
    assert report.requires_human_review is True
    assert report.external_call_made is False
    assert report.mutation_performed is False
    assert report.raw_source_content_persisted is False
    assert report.live_external_action_authorized is False
    assert report.allowed_actions == "advisory_only"
```

**Verify RED:**

```bash
PYTHONPATH=src pytest tests/unit/test_oss_comparison_adapter.py::test_build_oss_comparison_aggregates_local_line_and_approved_sources -q
```

**Expected RED:** `ModuleNotFoundError: No module named 'hisys.operations.oss_comparison_adapter'` because the module has not been created yet.

---

## Task 2: GREEN — implement minimal pure OSS comparison adapter and writer

**Objective:** Add the smallest production logic that satisfies the RED test and the writer invariant.

**Files:**

- Create: `src/hisys/operations/oss_comparison_adapter.py`

**Module shape (illustrative; minor naming may evolve during GREEN):**

```python
"""Advisory approved-OSS comparison adapter (M23, fixture-local).

The adapter compares one caller-named local codebase evidence line against
caller-supplied approved-OSS source descriptors. All inputs are bounded
fixture/config records; the adapter never crawls ``tests/fixtures/``, opens
upstream OSS repositories, calls Git or ``subprocess``, contacts the network,
installs or imports OSS packages, or persists raw OSS source content.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel

from hisys.operations.codebase_analysis import resolve_instance_runtime_ref

_DATE_PATTERN = re.compile(r"^\d{8}$")
_LINE_LABEL_PATTERN = re.compile(r"^[A-Z][A-Z0-9_\-]{1,63}$")
_SOURCE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_\-]{1,63}$")
_NOTES_MAX_LENGTH = 1024
_OSS_PREFIX = "runtime-boundary/oss-comparison"


class ApprovedOssSource(BaseModel):
    source_id: str
    source_name: str = ""
    license_tag: str = "n/a"
    category_refs: tuple[str, ...] = ()
    approved_refs: tuple[str, ...] = ()
    local_fixture_refs: tuple[str, ...] = ()
    notes: str = ""


class LocalCodebaseLine(BaseModel):
    line_label: str
    category_refs: tuple[str, ...] = ()
    portfolio_refs: tuple[str, ...] = ()
    implemented_surface_count: int = 0
    human_gated_surface_count: int = 0


class OssComparisonRequest(BaseModel):
    instance_root: Path
    date: str
    local_line: LocalCodebaseLine
    approved_sources: tuple[ApprovedOssSource, ...] = ()
    current_head_short: str | None = None


class OssComparisonReport(BaseModel):
    schema_id: str = "hisys.oss_comparison_adapter.v1"
    date: str
    current_head_short: str | None = None
    local_line_label: str
    compared_source_ids: tuple[str, ...] = ()
    compared_source_license_tags: tuple[str, ...] = ()
    local_category_refs: tuple[str, ...] = ()
    union_category_refs: tuple[str, ...] = ()
    intersection_category_refs: tuple[str, ...] = ()
    local_only_category_refs: tuple[str, ...] = ()
    oss_only_category_refs: tuple[str, ...] = ()
    unsafe_refs: tuple[str, ...] = ()
    unsafe_source_ids: tuple[str, ...] = ()
    unsafe_line_labels: tuple[str, ...] = ()
    compared_source_count: int = 0
    union_category_count: int = 0
    intersection_category_count: int = 0
    local_only_category_count: int = 0
    oss_only_category_count: int = 0
    advisory_only: bool = True
    requires_human_review: bool = True
    external_call_made: bool = False
    mutation_performed: bool = False
    raw_source_content_persisted: bool = False
    live_external_action_authorized: bool = False
    allowed_actions: str = "advisory_only"


def _normalize(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(values)))


def _is_unsafe_ref(ref: str) -> bool:
    if not ref:
        return True
    if ref.startswith("/"):
        return True
    parts = ref.replace("\\", "/").split("/")
    if any(part == ".." for part in parts):
        return True
    return False


def _is_unsafe_notes(notes: str) -> bool:
    if len(notes) > _NOTES_MAX_LENGTH:
        return True
    return any((ch < " " and ch not in "\t\n") for ch in notes)


def build_oss_comparison_report(
    *, request: OssComparisonRequest
) -> OssComparisonReport: ...


def render_oss_comparison_markdown(report: OssComparisonReport) -> str: ...


def write_oss_comparison_report(
    *,
    instance_root: Path,
    date: str,
    report: OssComparisonReport,
) -> dict[str, object]: ...
```

**GREEN behavior contract:**

1. Reject malformed `date` with `ValueError("invalid oss comparison date: ...")`.
2. If the local line label fails `_LINE_LABEL_PATTERN`, collect it in `unsafe_line_labels` and emit a report whose `local_category_refs`/`union_category_refs`/etc. are empty (no exception).
3. For each approved source: if `source_id` fails `_SOURCE_ID_PATTERN`, collect it in `unsafe_source_ids` and skip its categories. Otherwise: classify each `category_refs`, `approved_refs`, `local_fixture_refs` entry through `_is_unsafe_ref`; unsafe values go to `unsafe_refs`. Notes that fail `_is_unsafe_notes` cause the source to be added to `unsafe_source_ids` (a malformed-notes source must not leak into the comparison surface).
4. Build the local category set from the local line (after the same unsafe-ref filter on `portfolio_refs`). Compute set-based `union`, `intersection`, `local_only`, `oss_only`. Sort all output tuples.
5. `compared_source_ids` lists every safe approved source id (sorted). `compared_source_license_tags` lists the unique license tags from safe approved sources (sorted; empty tag becomes `"n/a"`).
6. Counts are derived from the sorted tuples; the function does not mutate any input record.

**Verify GREEN:**

```bash
PYTHONPATH=src pytest tests/unit/test_oss_comparison_adapter.py -q
PYTHONPATH=src pytest tests/unit/test_oss_comparison_adapter.py tests/unit/test_codebase_evidence_portfolio.py tests/unit/test_change_impact.py tests/unit/test_architecture_candidates.py tests/unit/test_traceability_coverage.py -q
```

**Expected GREEN:** focused OSS adapter test passes; combined OSS adapter + M22 portfolio + M21 sibling tests pass.

---

## Task 3: Supplemental regression — writer round-trip, unsafe rejection, and bad-date rejection

**Objective:** Pin the writer's safety invariants and confirm the builder rejects unsafe artifact/source-id/line-label inputs and bad dates without mutating the instance root.

**Files:**

- Modify: `tests/unit/test_oss_comparison_adapter.py`

**Test sketch:**

```python
def test_write_oss_comparison_persists_safe_refs(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    request = OssComparisonRequest(
        instance_root=instance_root,
        date="20260521",
        local_line=_m21_local_line(),
        approved_sources=(_approved_oss_understand(),),
    )
    report = build_oss_comparison_report(request=request)
    refs = write_oss_comparison_report(
        instance_root=instance_root, date="20260521", report=report
    )
    assert refs["json_ref"] == (
        "runtime-boundary/oss-comparison/20260521/comparison-report.json"
    )
    assert refs["external_call_made"] is False
    assert refs["allowed_actions"] == "advisory_only"
    json_path = instance_root / refs["json_ref"]
    md_path = instance_root / refs["markdown_ref"]
    assert json_path.exists()
    assert md_path.exists()


def test_build_oss_comparison_rejects_unsafe_refs_and_ids(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    request = OssComparisonRequest(
        instance_root=instance_root,
        date="20260521",
        local_line=LocalCodebaseLine(
            line_label="M21",
            category_refs=("traceability_coverage",),
            portfolio_refs=(
                "docs/plans/m22-codebase-evidence-portfolio-implementation-tasks.md",
                "../escape.md",
                "/etc/passwd",
            ),
            implemented_surface_count=1,
        ),
        approved_sources=(
            ApprovedOssSource(
                source_id="UPPERCASE_SOURCE",
                source_name="invalid id",
                category_refs=("foo",),
            ),
            ApprovedOssSource(
                source_id="approved-fixture",
                category_refs=("traceability_coverage", "extra_topic"),
                approved_refs=("../bad.md",),
                local_fixture_refs=("tests/fixtures/oss/approved/foo.json",),
                notes="ok",
            ),
            ApprovedOssSource(
                source_id="malformed-notes",
                category_refs=("traceability_coverage",),
                notes="\x00binary",
            ),
        ),
    )
    report = build_oss_comparison_report(request=request)
    assert report.local_line_label == "M21"
    assert "UPPERCASE_SOURCE" in report.unsafe_source_ids
    assert "malformed-notes" in report.unsafe_source_ids
    assert "approved-fixture" in report.compared_source_ids
    assert "/etc/passwd" in report.unsafe_refs
    assert "../escape.md" in report.unsafe_refs
    assert "../bad.md" in report.unsafe_refs
    assert "extra_topic" in report.oss_only_category_refs


def test_build_oss_comparison_rejects_unsafe_line_label(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    request = OssComparisonRequest(
        instance_root=instance_root,
        date="20260521",
        local_line=LocalCodebaseLine(
            line_label="lowercase-not-allowed",
            category_refs=("traceability_coverage",),
        ),
        approved_sources=(_approved_oss_understand(),),
    )
    report = build_oss_comparison_report(request=request)
    assert "lowercase-not-allowed" in report.unsafe_line_labels
    assert report.local_category_refs == ()
    assert report.intersection_category_refs == ()


def test_build_oss_comparison_rejects_bad_date(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    request = OssComparisonRequest(
        instance_root=instance_root,
        date="2026-05-21",
        local_line=_m21_local_line(),
        approved_sources=(_approved_oss_understand(),),
    )
    with pytest.raises(ValueError):
        build_oss_comparison_report(request=request)


def test_write_oss_comparison_rejects_bad_date(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    request = OssComparisonRequest(
        instance_root=instance_root,
        date="20260521",
        local_line=_m21_local_line(),
        approved_sources=(_approved_oss_understand(),),
    )
    report = build_oss_comparison_report(request=request)
    with pytest.raises(ValueError):
        write_oss_comparison_report(
            instance_root=instance_root, date="2026-05-21", report=report
        )
```

**Verify:**

```bash
PYTHONPATH=src pytest tests/unit/test_oss_comparison_adapter.py -q
```

**Expected:** focused OSS adapter tests pass; no other test regressions.

---

## Task 4: Documentation, gate, and commit

**Objective:** Record M23-OSS-ADAPTER-RED-GREEN implementation evidence and keep governance boundaries explicit.

**Files:**

- Modify: `docs/traceability/README.md` — prepend an `M23-OSS-ADAPTER-RED-GREEN` row referencing the new module, tests, parent plan, the M23 authorization decision record, and the verified governance invariants (advisory-only, caller-supplied refs only, fixture-local descriptors only, no OSS clone/install/import, no network, no credential lookup, no raw source archival, no mutation outside the report partition).
- Modify: `ralph.md` — append a Reflection Log entry following the existing M22-PORTFOLIO format with Resume checkpoint and an updated Section 16 next-row pointer to `M23-OSS-ADAPTER-CLI` (or, if the user pauses, to `QUEUE-REFILL-PREP-STOP` pending the next decision).
- Modify: `docs/milestone-bootstrap/profile.yaml` — bump `next_safe_task` to `M23-OSS-ADAPTER-RED-GREEN` after this PREP commit, then to `M23-OSS-ADAPTER-CLI` after RED/GREEN commits. Bump the profile version and update `previous_bootstrap_version`. Mirror the update in `tests/unit/test_governance_docs_current_state.py`.

**Validation:**

```bash
PYTHONPATH=src pytest tests/unit/test_oss_comparison_adapter.py tests/unit/test_codebase_evidence_portfolio.py tests/unit/test_change_impact.py tests/unit/test_architecture_candidates.py tests/unit/test_code_analysis_pass_contract.py tests/unit/test_subagent_evidence_collector_protocol.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
PYTHONPATH=src pytest tests/unit/test_governance_docs_current_state.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit (after RED/GREEN/regression and traceability update):**

```bash
git add tests/unit/test_oss_comparison_adapter.py src/hisys/operations/oss_comparison_adapter.py docs/traceability/README.md ralph.md docs/milestone-bootstrap/profile.yaml tests/unit/test_governance_docs_current_state.py
git commit -m "feat: add oss comparison adapter"
```

---

## M23-OSS-ADAPTER-CLI deferral note

After `M23-OSS-ADAPTER-RED-GREEN` is committed and the focused gates remain green, the CLI wrapper follows the `M22-PORTFOLIO-CLI` pattern:

- Add `hisys oss-comparison-adapter --instance <root> --date <YYYYMMDD> --line-bundle <json> [--current-head-short <hash>]` to `src/hisys/cli/main.py`. The bundle JSON contains a top-level `local_line` object plus an `approved_sources` list of objects matching the Pydantic shapes.
- Reuse the existing `_load_json_report` helper. Build the request through `LocalCodebaseLine` / `ApprovedOssSource` / `OssComparisonRequest` Pydantic models so the CLI does not duplicate the M23 shape.
- Print bounded summary lines: `oss-comparison-adapter report`, `markdown`, `compared_source_count`, `union_category_count`, `intersection_category_count`, `local_only_category_count`, `oss_only_category_count`, `unsafe_ref_count`, `unsafe_source_id_count`, `unsafe_line_label_count`, `advisory_only: true`, `requires_human_review: true`, `external_call_made: false`, `mutation_performed: false`, `raw_source_content_persisted: false`, `live_external_action_authorized: false`, `allowed_actions: advisory_only`. Return exit code `0` on success and propagate `ValueError` non-zero.
- The CLI must not call `date.today()`, must not read `.git/`, must not call `subprocess`, must not crawl `tests/fixtures/`, must not infer latest fixtures, must not auto-discover bundle files, must not open `local_fixture_refs` to verify file existence, must not install OSS packages, and must not expand the source-id or category vocabulary.

A full RED/GREEN plan for the CLI lives in a separate `docs/plans/m23-cli-oss-comparison-adapter-implementation-tasks.md` authored only after the pure builder is committed.

## M23-OSS-ADAPTER-GOLDEN scope

After the CLI ships, add a deterministic golden-fixture test that pins one canonical local-line + approved-source bundle, runs the pure builder, and compares its JSON output against a checked-in expected file under `tests/fixtures/oss-comparison/`. The fixture must not embed raw OSS source bodies, OSS license text beyond the bounded `license_tag` field, or secrets; it only pins refs, source ids, category strings, license tags, and counts.

## M23-OSS-ADAPTER-GATE scope

After the golden fixture passes, append a `Done: M23-OSS-ADAPTER-GATE` line to `ralph.md` Section 16 with full focused/full gate evidence, run a QUEUE-REFILL-PREP preflight, and continue to `M23-LSP-ADAPTER-PREP`. The LSP adapter remains separately governed (subprocess command allowlist, timeout, workspace-root restriction, output schema, and kill policy must be authored in PREP before any product code).

---

## Stop conditions

Stop and ask for a new decision if any task would require:

- network fetch, OSS repository clone, package installation, license-text capture, or any external HTTP call from the adapter, writer, or CLI;
- credential lookup, mutation, or persistence;
- shelling out to `git log`, `git diff`, or any `subprocess` call from the adapter module;
- reading `.git/` directly or calling `date.today()` inside the builder;
- raw OSS source archival, diff-hunk embedding, or persistence of file bodies/secrets in the report;
- repair, deletion, retry, or quarantine of artifacts under inspection;
- expanding the report into approval / safe-to-deploy / compliance / license-fitness language;
- adding the CLI in the `M23-OSS-ADAPTER-RED-GREEN` increment (CLI is `M23-OSS-ADAPTER-CLI`, planned separately after the pure builder stabilizes);
- mutating existing M21 / M22 / DARS schema shapes rather than referencing them by id;
- LSP subprocess spawning, subagent execution, model invocation, or any live external provider call from this OSS adapter line.

## Out of scope for the OSS adapter (deferred or human-gated)

- `tests/fixtures/` directory crawling or `--scan` mode; the adapter requires caller-supplied descriptors only.
- Local `git log` capture front-end (`--current-head-short` is caller-supplied).
- Cross-branch comparison, base-branch fetch, or `origin/main` resolution.
- Symbol-level or function-level OSS comparison; the MVP is category/ref granularity only.
- Subagent-driven OSS discovery (separately human-gated).
- Live-provider DARS panel execution (separately governed plan).
- Optional local LSP adapter (deferred to `M23-LSP-ADAPTER-PREP`).
- Any change to existing M21 / M22 / DARS schema shapes.
- Embedding-based or model-based similarity scoring (not authorized; M23 OSS adapter is set-based only).

## Next executable action

After this Prepare plan is committed and pushed (normal push to existing `origin/dars`), run the RED command:

```bash
PYTHONPATH=src pytest tests/unit/test_oss_comparison_adapter.py::test_build_oss_comparison_aggregates_local_line_and_approved_sources -q
```

Expected failure: `ModuleNotFoundError: No module named 'hisys.operations.oss_comparison_adapter'`.
