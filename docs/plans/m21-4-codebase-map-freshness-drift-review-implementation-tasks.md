# Milestone M21.4 — Codebase Map Freshness / Drift Review Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for every code-bearing task. This plan is the document-RED/Prepare artifact for M21.4, authored after the M21.3 / M21.3-CLI runtime-boundary consistency surface stabilized (`3c3e0bd feat: add runtime-boundary-check cli wrapper`).

**Goal:** Implement M21.4 so a pure local-only checker over the existing `runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/` artifact partitions produces a deterministic advisory `codebase map freshness/drift report` listing fresh, stale, and incomplete partitions, plus partitions whose names fail the YYYYMMDD safety pattern. The reviewer must remain advisory — it never repairs, deletes, regenerates, or otherwise mutates the artifact partitions it inspects, and it never authorizes live action.

**Architecture:** Add a new pure-Python module `src/hisys/operations/codebase_map_freshness.py` that exposes:

1. A Pydantic `CodebaseMapFreshnessReport` record holding deterministic counts and sorted issue lists (fresh, stale, incomplete, unsafe-partition refs) plus the advisory flag set (`advisory_only`, `requires_human_review`, `external_call_made`, `mutation_performed`, `raw_source_content_persisted`).
2. A pure function `build_codebase_map_freshness_report(*, instance_root, current_date, max_age_days, current_head_short=None)` that lists `<YYYYMMDD>/<REQUEST_ID>/` partitions under `<instance>/runtime-boundary/codebase-analysis/`, classifies each by age and completeness, and emits a deterministic sorted report. Partitions whose `YYYYMMDD` name fails the `^\d{8}$` pattern, whose `REQUEST_ID` contains traversal segments, or whose absolute resolved path escapes the instance root are classified as `unsafe_partition` without further reads.
3. A writer `write_codebase_map_freshness_report(*, instance_root, date, report)` that persists JSON + Markdown under `runtime-boundary/codebase-map-freshness/<YYYYMMDD>/freshness-report.{json,md}` through `resolve_instance_runtime_ref`.

Reuse the existing slug/date validators, `resolve_instance_runtime_ref` chokepoint, and `_REQUIRED_ARTIFACT_NAMES` tuple from `src/hisys/operations/codebase_analysis.py`. The checker does not read artifact bodies; presence and partition-name safety are the entire signal. No new dependency, no network call, no model invocation, no credential resolution, no destructive Git, no remote push, no CLI argument expansion, no raw source archival in this increment.

**Tech Stack:** Python 3.11, regex, pathlib, datetime (caller-provided current date — no system clock side effects), Pydantic v2, pytest. No new dependency.

**Context Packet:** Required source handles:

- `src/hisys/operations/codebase_analysis.py` (`resolve_instance_runtime_ref`, `_REQUIRED_ARTIFACT_NAMES`, `INVENTORY_RUNTIME_PREFIX`, writer/ref conventions).
- `src/hisys/operations/runtime_boundary_consistency.py` (M21.3 writer/report shape to mirror).
- `src/hisys/operations/traceability_coverage.py` (M21.1 writer pattern reference).
- Existing focused gate suites under `tests/unit/test_codebase_*` for fixture-writing patterns.
- `docs/traceability/README.md` and `ralph.md` for documentation updates.

**Boundary Record:** Local fixture-only tests/docs/code mutation and local commit are allowed after validation. Remote push, repository cloning, live external read/write, credential resolution, browser/network/model invocation, destructive Git, publication, action authority, artifact repair/regeneration/deletion, and raw source archival are not authorized. The report is advisory only and never implies the freshness boundary has been crossed for action purposes.

---

## Accepted decisions

1. **Pure local read-only:** The checker reads directory listings and file presence only, through bounded paths under `<instance>/runtime-boundary/codebase-analysis/`. It does not open artifact bodies, parse JSON, or follow symlinks that escape the instance root.
2. **Caller-supplied current date:** Tests pass an explicit `current_date` (e.g. `date(2026, 5, 20)`) and `max_age_days` (e.g. `30`). The checker does not call `date.today()` or any system-clock surface, so output is deterministic and reproducible.
3. **Refs and counts over raw content:** The report records ref strings, classified partition counts, fresh/stale/incomplete partition lists, and `unsafe_partition` lists. It does not embed file bodies or raw source.
4. **Partition vocabulary:** Each partition under `runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/` is exactly one of `fresh`, `stale`, `incomplete`, or `unsafe_partition` for the purposes of M21.4. Cross-partition drift across multiple instances or branches is intentionally out of scope.
5. **No CLI in this increment:** A `hisys codebase-map-freshness-review` subcommand is M21.4-CLI work, not M21.4 GREEN. M21.4 GREEN ships only the pure module and writer.
6. **Advisory only:** The report carries `advisory_only=true`, `requires_human_review=true`, `external_call_made=false`, `mutation_performed=false`, and `raw_source_content_persisted=false`. It must not be treated as a quality gate or freshness pass for any other Hisys flow.
7. **No artifact mutation:** The checker never writes outside `runtime-boundary/codebase-map-freshness/<YYYYMMDD>/`; it never repairs, rewrites, deletes, regenerates, or quarantines codebase-analysis artifacts.
8. **Optional caller HEAD hash:** Tests may pass a `current_head_short` string for traceability (e.g. `"6a067ed"`); the checker records it verbatim in the report but does not call git or read `.git/` metadata.
9. **Traceability required:** Update `docs/traceability/README.md` with an `M21.4` row in the implementation increment, and append a `ralph.md` Reflection Log entry plus Resume checkpoint.

---

## Task 0: Reconstruct baseline before editing

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_cli.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:** branch `dars`, HEAD at or after `3c3e0bd feat: add runtime-boundary-check cli wrapper`; extended focused gate (≥38) passes; DARS focused gate 48 passes; traceability validator OK; secret scan hit_count=0; `git diff --check` clean.

If any expected outcome diverges, stop and re-run QUEUE-REFILL-PREP before continuing.

---

## Task 1: RED — pure freshness checker classifies fresh / stale / incomplete / unsafe partitions

**Objective:** Add a failing pytest that seeds three partitions under a temp instance root — one complete-and-fresh, one complete-but-stale, one incomplete-fresh — plus one partition whose `YYYYMMDD` directory name is not 8 digits, then asserts the report classifies each correctly. The test must fail before the module exists.

**Files:**

- Create: `tests/unit/test_codebase_map_freshness.py`

**Test sketch:**

```python
from __future__ import annotations

from datetime import date
from pathlib import Path

from hisys.operations.codebase_map_freshness import (
    build_codebase_map_freshness_report,
    write_codebase_map_freshness_report,
)


_REQUIRED = ("inventory.json", "symbol-index.json", "scope-map.json", "risk-scan.json")


def _seed_partition(instance_root: Path, yyyymmdd: str, request_id: str, *, complete: bool) -> str:
    partition = f"runtime-boundary/codebase-analysis/{yyyymmdd}/{request_id}"
    partition_dir = instance_root / partition
    partition_dir.mkdir(parents=True, exist_ok=True)
    files = _REQUIRED if complete else _REQUIRED[:2]
    for name in files:
        (partition_dir / name).write_text("{}\n", encoding="utf-8")
    return partition


def test_codebase_map_freshness_classifies_partitions(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    fresh = _seed_partition(instance_root, "20260518", "REQ-FRESH", complete=True)
    stale = _seed_partition(instance_root, "20260101", "REQ-STALE", complete=True)
    incomplete = _seed_partition(instance_root, "20260519", "REQ-INCOMPLETE", complete=False)
    unsafe_dir = instance_root / "runtime-boundary" / "codebase-analysis" / "not-a-date" / "REQ-OOPS"
    unsafe_dir.mkdir(parents=True, exist_ok=True)
    (unsafe_dir / "inventory.json").write_text("{}\n", encoding="utf-8")

    report = build_codebase_map_freshness_report(
        instance_root=instance_root,
        current_date=date(2026, 5, 20),
        max_age_days=30,
        current_head_short="3c3e0bd",
    )

    assert report.advisory_only is True
    assert report.requires_human_review is True
    assert report.external_call_made is False
    assert report.mutation_performed is False
    assert report.raw_source_content_persisted is False
    assert report.current_head_short == "3c3e0bd"
    assert report.fresh_partitions == (fresh,)
    assert report.stale_partitions == (stale,)
    assert report.incomplete_partitions == (incomplete,)
    assert report.unsafe_partitions == (
        "runtime-boundary/codebase-analysis/not-a-date/REQ-OOPS",
    )
```

**Verify RED:**

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_map_freshness.py::test_codebase_map_freshness_classifies_partitions -q
```

**Expected RED:** `ModuleNotFoundError: No module named 'hisys.operations.codebase_map_freshness'` because the module has not been created yet.

---

## Task 2: GREEN — implement minimal pure freshness checker and writer

**Objective:** Add the smallest production logic that satisfies the RED.

**Files:**

- Create: `src/hisys/operations/codebase_map_freshness.py`

**Module shape:**

```python
"""Advisory codebase map freshness/drift reporting.

M21.4 keeps this surface pure and fixture-local: callers pass an instance
root, a current date, and a max-age threshold; the checker classifies each
existing ``runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/``
partition as fresh, stale, incomplete, or unsafe-partition; and the writer
persists only JSON/Markdown summaries under
``runtime-boundary/codebase-map-freshness``. The checker never reads
artifact bodies, never repairs/regenerates partitions, and never authorizes
live action.
"""

from __future__ import annotations

import json
import re
from datetime import date as _date
from pathlib import Path

from pydantic import BaseModel

from hisys.operations.codebase_analysis import (
    INVENTORY_RUNTIME_PREFIX,
    resolve_instance_runtime_ref,
)

_DATE_PATTERN = re.compile(r"^\d{8}$")
_REQUIRED_FILES: tuple[str, ...] = (
    "inventory.json",
    "symbol-index.json",
    "scope-map.json",
    "risk-scan.json",
)
_FRESHNESS_RUNTIME_PREFIX = "runtime-boundary/codebase-map-freshness"


class CodebaseMapFreshnessReport(BaseModel):
    schema_id: str = "hisys.codebase_map.freshness.v1"
    current_date: str  # YYYY-MM-DD
    max_age_days: int
    current_head_short: str | None = None
    fresh_partitions: tuple[str, ...]
    stale_partitions: tuple[str, ...]
    incomplete_partitions: tuple[str, ...]
    unsafe_partitions: tuple[str, ...]
    advisory_only: bool = True
    requires_human_review: bool = True
    external_call_made: bool = False
    mutation_performed: bool = False
    raw_source_content_persisted: bool = False


def _normalize(refs: list[str]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(refs)))


def _partition_age_days(yyyymmdd: str, current_date: _date) -> int:
    year = int(yyyymmdd[:4])
    month = int(yyyymmdd[4:6])
    day = int(yyyymmdd[6:8])
    return (current_date - _date(year, month, day)).days


def build_codebase_map_freshness_report(
    *,
    instance_root: Path,
    current_date: _date,
    max_age_days: int,
    current_head_short: str | None = None,
) -> CodebaseMapFreshnessReport:
    fresh: list[str] = []
    stale: list[str] = []
    incomplete: list[str] = []
    unsafe: list[str] = []

    root_rel = INVENTORY_RUNTIME_PREFIX
    root_dir = instance_root / root_rel
    if not root_dir.is_dir():
        return CodebaseMapFreshnessReport(
            current_date=current_date.isoformat(),
            max_age_days=max_age_days,
            current_head_short=current_head_short,
            fresh_partitions=(),
            stale_partitions=(),
            incomplete_partitions=(),
            unsafe_partitions=(),
        )

    for date_dir in sorted(p for p in root_dir.iterdir() if p.is_dir()):
        date_name = date_dir.name
        for request_dir in sorted(p for p in date_dir.iterdir() if p.is_dir()):
            partition_rel = f"{root_rel}/{date_name}/{request_dir.name}"
            try:
                resolved = resolve_instance_runtime_ref(
                    instance_root=instance_root, relative_ref=partition_rel
                )
            except ValueError:
                unsafe.append(partition_rel)
                continue
            if not _DATE_PATTERN.fullmatch(date_name):
                unsafe.append(partition_rel)
                continue
            present = {p.name for p in resolved.iterdir() if p.is_file()}
            if any(req not in present for req in _REQUIRED_FILES):
                incomplete.append(partition_rel)
                continue
            if _partition_age_days(date_name, current_date) > max_age_days:
                stale.append(partition_rel)
            else:
                fresh.append(partition_rel)

    return CodebaseMapFreshnessReport(
        current_date=current_date.isoformat(),
        max_age_days=max_age_days,
        current_head_short=current_head_short,
        fresh_partitions=_normalize(fresh),
        stale_partitions=_normalize(stale),
        incomplete_partitions=_normalize(incomplete),
        unsafe_partitions=_normalize(unsafe),
    )


def render_codebase_map_freshness_markdown(report: CodebaseMapFreshnessReport) -> str:
    ...  # bounded sections only; mirrors the M21.3 renderer style


def write_codebase_map_freshness_report(
    *,
    instance_root: Path,
    date: str,
    report: CodebaseMapFreshnessReport,
) -> dict[str, object]:
    if not _DATE_PATTERN.fullmatch(date):
        raise ValueError(f"invalid freshness report date: {date!r}")
    rel_dir = f"{_FRESHNESS_RUNTIME_PREFIX}/{date}"
    json_ref = f"{rel_dir}/freshness-report.json"
    md_ref = f"{rel_dir}/freshness-report.md"
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
        render_codebase_map_freshness_markdown(report), encoding="utf-8"
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
    }
```

**Verify GREEN:**

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_map_freshness.py -q
PYTHONPATH=src pytest tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py -q
```

**Expected GREEN:** focused freshness test passes; combined M21.1/M21.3/M21.4 suite passes.

---

## Task 3: Supplemental regression — writer round-trip, missing-root fallback, traversal rejection

**Objective:** Pin the writer and edge-case invariants after the first GREEN.

**Files:**

- Modify: `tests/unit/test_codebase_map_freshness.py`

**Test sketch:**

```python
def test_write_codebase_map_freshness_report_persists_safe_refs(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    report = build_codebase_map_freshness_report(
        instance_root=instance_root,
        current_date=date(2026, 5, 20),
        max_age_days=30,
    )
    refs = write_codebase_map_freshness_report(
        instance_root=instance_root, date="20260520", report=report
    )
    expected_json = (
        "runtime-boundary/codebase-map-freshness/20260520/freshness-report.json"
    )
    assert refs["json_ref"] == expected_json
    assert refs["external_call_made"] is False
    assert (instance_root / expected_json).is_file()


def test_build_codebase_map_freshness_handles_missing_root(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()  # no runtime-boundary/codebase-analysis tree
    report = build_codebase_map_freshness_report(
        instance_root=instance_root,
        current_date=date(2026, 5, 20),
        max_age_days=30,
    )
    assert report.fresh_partitions == ()
    assert report.stale_partitions == ()
    assert report.incomplete_partitions == ()
    assert report.unsafe_partitions == ()


def test_write_codebase_map_freshness_report_rejects_invalid_date(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    report = build_codebase_map_freshness_report(
        instance_root=instance_root,
        current_date=date(2026, 5, 20),
        max_age_days=30,
    )
    try:
        write_codebase_map_freshness_report(
            instance_root=instance_root, date="2026-05-20", report=report
        )
    except ValueError as exc:
        assert "invalid" in str(exc).lower()
    else:  # pragma: no cover - defensive
        raise AssertionError("expected ValueError for non-YYYYMMDD date")
```

**Verify:**

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_map_freshness.py -q
```

**Expected:** focused freshness tests pass; no other test regressions.

---

## Task 4: Documentation, gate, and commit

**Objective:** Record M21.4 implementation evidence and keep governance boundaries explicit.

**Files:**

- Modify: `docs/traceability/README.md` — prepend an `M21.4` row referencing the new module, tests, and the verified governance invariants.
- Modify: `ralph.md` — append a Reflection Log entry following the M21.3 format with Resume checkpoint.

**Validation:**

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_cli.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit:**

```bash
git add tests/unit/test_codebase_map_freshness.py src/hisys/operations/codebase_map_freshness.py docs/traceability/README.md ralph.md
git commit -m "feat: add codebase map freshness review"
```

---

## Stop conditions

Stop and ask for a new decision if any task would require:

- remote push or any change to remote configuration;
- live external network, browser, connector, model, or LSP/process invocation;
- credential lookup, mutation, or persistence;
- reading artifact bodies or embedding raw source content in the freshness report;
- repair, deletion, regeneration, or quarantine of codebase-analysis partitions;
- expanding the checker into approval/safe-to-deploy/readiness language;
- adding a CLI in this increment (CLI is a separate M21.4-CLI increment, planned later);
- calling git or any system-clock surface inside the checker (caller supplies date and optional HEAD short).

## Out of scope for M21.4 (deferred)

- `hisys codebase-map-freshness-review` CLI subcommand (M21.4-CLI).
- Cross-instance / cross-branch drift comparison.
- Schema-id-aware deep validation of artifact bodies (still bounded to presence; M21.5 fixture benchmarks may cover this).
- Subagent-driven freshness collection (human-gated, not part of M21.4).
- Any change to existing codebase-analysis writer modules; M21.4 reads only directory listings.
