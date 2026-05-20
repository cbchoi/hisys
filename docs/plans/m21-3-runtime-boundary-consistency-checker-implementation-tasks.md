# Milestone M21.3 — Runtime-Boundary Consistency Checker Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for every code-bearing task. This plan is the document-RED/Prepare artifact for Milestone M21 Task M21.3 — runtime-boundary consistency checker — authored after M21.1/M21.2 traceability coverage shipped and the M21 roadmap committed (`028edfb docs: plan m21 advanced codebase roadmap`, refreshed at `5534f8e docs: refresh m21.3 bootstrap readiness`).

**Goal:** Implement M21.3 so a pure, local-only checker over a caller-supplied list of runtime-boundary refs (and optionally a bounded local scan rooted at `<instance>/runtime-boundary/`) produces a deterministic advisory `runtime-boundary consistency report` listing unsafe refs, missing files, malformed JSON, missing companion Markdown pairs, and missing advisory flags. The checker must remain advisory — it never repairs, deletes, retries, or otherwise mutates the runtime artifacts it inspects, and it never authorizes live action.

**Architecture:** Add a new pure-Python module `src/hisys/operations/runtime_boundary_consistency.py` that exposes:

1. A Pydantic `RuntimeBoundaryConsistencyReport` record holding deterministic counts, sorted issue lists, and the existing advisory flag set (`advisory_only`, `requires_human_review`, `external_call_made`, `mutation_performed`, `raw_source_content_persisted`).
2. A pure function `build_runtime_boundary_consistency_report(*, instance_root, candidate_refs, scan_roots=None)` that classifies each ref into one of `ok`, `unsafe_ref`, `missing_file`, `malformed_json`, `missing_markdown_pair`, `missing_advisory_flags`, or `outside_runtime_boundary`. The function reads only local files via the existing `resolve_instance_runtime_ref` chokepoint and does not follow symlinks that escape the instance root.
3. A writer `write_runtime_boundary_consistency_report(*, instance_root, date, report)` that persists JSON + Markdown under `runtime-boundary/runtime-boundary-consistency/<YYYYMMDD>/consistency-report.{json,md}` using the same writer conventions as M21.1.

Reuse the existing slug/date validators and `resolve_instance_runtime_ref` chokepoint from `src/hisys/operations/codebase_analysis.py`. No new dependency, no network call, no model invocation, no credential resolution, no destructive Git, no remote push, no CLI argument expansion, and no raw source archival in this increment. A thin `hisys runtime-boundary-check` CLI wrapper is deferred to M21.3-CLI after the pure checker is stable.

**Tech Stack:** Python 3.11, regex, pathlib, Pydantic v2 for the report record, pytest. No new dependency.

**Context Packet:** Required source handles:

- `src/hisys/operations/codebase_analysis.py` (`resolve_instance_runtime_ref`, runtime-boundary writer conventions, slug/date patterns).
- `src/hisys/operations/traceability_coverage.py` (M21.1 writer/report shape to mirror).
- `src/hisys/operations/lapidary_flow.py` (existing `runtime-boundary/dars` prefix and writer pattern, reference only).
- `runtime-boundary/<surface>/<YYYYMMDD>/` artifact families discoverable under any seeded instance root: `codebase-analysis`, `dars`, `dars-panel`, `domain-investigation`, `hermes`, `investment-decisions`, `reports`, `runtime-index`, `source-connectors`, `topic-gatekeeper`, `traceability-coverage`.
- `tests/unit/test_traceability_coverage.py` (M21.1 test layout to mirror).
- `tests/unit/test_codebase_inventory.py`, `tests/unit/test_codebase_symbol_index.py`, and `tests/unit/test_codebase_scope_map.py` for examples of writing minimal local runtime artifacts in tests.
- `docs/traceability/README.md` and `ralph.md` for documentation updates.

**Boundary Record:** Local fixture-only tests/docs/code mutation and local commit are allowed after validation. Remote push is not authorized. No live external read, no repo clone, no credential resolution, no browser/network/model call, no destructive Git, no publication, no action authority. The consistency report is advisory only and never implies repair, deletion, retry, approval, or readiness for live action.

---

## Accepted decisions

1. **Pure local read-only:** The checker reads only files under `<instance_root>/runtime-boundary/` and only through the existing `resolve_instance_runtime_ref` chokepoint. It does not open caller refs directly and does not follow symlinks that escape the instance root.
2. **Refs and counts over raw content:** The report records ref strings, issue kinds, expected-vs-observed schema IDs where applicable, and bounded issue counts. It does not embed file bodies, source text, or secrets.
3. **Single canonical issue vocabulary:** Issue kinds are limited to `unsafe_ref`, `missing_file`, `malformed_json`, `missing_markdown_pair`, `missing_advisory_flags`, and `outside_runtime_boundary`. Additional kinds may be added later under a separate RED.
4. **Bounded scan root:** When `scan_roots` is supplied, each entry must already start with `runtime-boundary/` and must pass `resolve_instance_runtime_ref` validation. The scan does not recurse outside that root.
5. **No CLI in this increment:** A `hisys runtime-boundary-check` subcommand is M21.3-CLI work, not M21.3 GREEN. M21.3 GREEN ships only the pure module and writer.
6. **Advisory only:** The report explicitly carries `advisory_only=true`, `requires_human_review=true`, `external_call_made=false`, `mutation_performed=false`, and `raw_source_content_persisted=false`. It must not be treated as a quality-gate pass for any other Hisys flow.
7. **No artifact mutation:** The checker never writes outside `runtime-boundary/runtime-boundary-consistency/<YYYYMMDD>/`; it never repairs, rewrites, deletes, or quarantines the artifacts it inspects.
8. **Traceability required:** Update `docs/traceability/README.md` with an `M21.3` row in the implementation increment, and append a Reflection Log entry plus Resume checkpoint to `ralph.md`.

---

## Task 0: Reconstruct baseline before editing

**Objective:** Confirm the M21 roadmap commit is current and the working tree is clean.

**Commands:**

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_traceability_coverage.py tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_cli.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:** branch `dars`, HEAD at or after `5534f8e docs: refresh m21.3 bootstrap readiness`; combined traceability/domain/CLI gate passes (32 expected); DARS critic-panel focused regression passes (48 expected); traceability validator OK; secret scan hit_count=0; `git diff --check` clean.

If any expected outcome diverges, stop and re-run QUEUE-REFILL-PREP before continuing.

---

## Task 1: RED — pure consistency checker flags missing and unsafe refs

**Objective:** Add a failing pytest that constructs a tiny fixture instance with one safe-but-missing ref, one unsafe `..` ref, and one safe-and-present runtime artifact (with proper Markdown companion), then asserts the report classifies each correctly. The test must fail before the module exists.

**Files:**

- Create: `tests/unit/test_runtime_boundary_consistency.py`

**Test sketch:**

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.operations.runtime_boundary_consistency import (
    build_runtime_boundary_consistency_report,
    write_runtime_boundary_consistency_report,
)


def _seed_complete_traceability_coverage_artifact(instance_root: Path) -> tuple[str, str]:
    json_ref = "runtime-boundary/traceability-coverage/20260520/coverage-report.json"
    md_ref = "runtime-boundary/traceability-coverage/20260520/coverage-report.md"
    json_path = instance_root / json_ref
    md_path = instance_root / md_ref
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(
            {
                "schema_id": "hisys.traceability.coverage.v1",
                "advisory_only": True,
                "requires_human_review": True,
                "external_call_made": False,
                "mutation_performed": False,
                "raw_source_content_persisted": False,
                "requirement_count": 1,
                "covered_requirement_count": 1,
                "coverage_ratio": 1.0,
                "unreferenced_requirements": [],
                "orphan_test_ids": [],
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    md_path.write_text("# coverage\n- advisory_only: true\n", encoding="utf-8")
    return json_ref, md_ref


def test_runtime_boundary_consistency_flags_missing_and_unsafe_refs(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    json_ref, md_ref = _seed_complete_traceability_coverage_artifact(instance_root)

    report = build_runtime_boundary_consistency_report(
        instance_root=instance_root,
        candidate_refs=(
            json_ref,
            md_ref,
            "runtime-boundary/codebase-analysis/20260520/REQ-MISSING/inventory.json",
            "runtime-boundary/../escape.txt",
        ),
    )

    assert report.advisory_only is True
    assert report.requires_human_review is True
    assert report.external_call_made is False
    assert report.mutation_performed is False
    assert report.raw_source_content_persisted is False
    assert report.ok_ref_count == 2
    assert report.unsafe_refs == ("runtime-boundary/../escape.txt",)
    assert report.missing_files == (
        "runtime-boundary/codebase-analysis/20260520/REQ-MISSING/inventory.json",
    )
    assert report.malformed_json_refs == ()
    assert report.outside_runtime_boundary_refs == ()
```

**Verify RED:**

```bash
PYTHONPATH=src pytest tests/unit/test_runtime_boundary_consistency.py::test_runtime_boundary_consistency_flags_missing_and_unsafe_refs -q
```

**Expected RED:** `ModuleNotFoundError: No module named 'hisys.operations.runtime_boundary_consistency'` because the module has not been created yet.

---

## Task 2: GREEN — implement minimal pure consistency checker and writer

**Objective:** Add the smallest production logic that satisfies the RED test and the writer invariant.

**Files:**

- Create: `src/hisys/operations/runtime_boundary_consistency.py`

**Module shape:**

```python
"""Advisory runtime-boundary consistency reporting.

M21.3 keeps this surface pure and fixture-local: callers supply a bounded list
of relative runtime-boundary refs, the checker classifies each by safety and
presence, and the optional writer persists only JSON/Markdown summaries under
``runtime-boundary/runtime-boundary-consistency``. The checker never repairs,
deletes, retries, or rewrites the artifacts it inspects, and never authorizes
live action.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel, Field

from hisys.operations.codebase_analysis import resolve_instance_runtime_ref

_DATE_PATTERN = re.compile(r"^\d{8}$")
_RUNTIME_BOUNDARY_ROOT = "runtime-boundary/"
_CONSISTENCY_RUNTIME_PREFIX = "runtime-boundary/runtime-boundary-consistency"


class RuntimeBoundaryConsistencyReport(BaseModel):
    schema_id: str = "hisys.runtime_boundary.consistency.v1"
    ok_ref_count: int
    unsafe_refs: tuple[str, ...]
    missing_files: tuple[str, ...]
    malformed_json_refs: tuple[str, ...]
    missing_markdown_pair_refs: tuple[str, ...]
    missing_advisory_flag_refs: tuple[str, ...]
    outside_runtime_boundary_refs: tuple[str, ...]
    advisory_only: bool = True
    requires_human_review: bool = True
    external_call_made: bool = False
    mutation_performed: bool = False
    raw_source_content_persisted: bool = False


def _normalize(refs: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(refs)))


def build_runtime_boundary_consistency_report(
    *,
    instance_root: Path,
    candidate_refs: Iterable[str],
) -> RuntimeBoundaryConsistencyReport:
    ok: list[str] = []
    unsafe: list[str] = []
    missing: list[str] = []
    malformed: list[str] = []
    missing_md_pair: list[str] = []
    missing_flags: list[str] = []
    outside_root: list[str] = []

    for ref in candidate_refs:
        if not ref.startswith(_RUNTIME_BOUNDARY_ROOT):
            outside_root.append(ref)
            continue
        try:
            path = resolve_instance_runtime_ref(
                instance_root=instance_root, relative_ref=ref
            )
        except ValueError:
            unsafe.append(ref)
            continue
        if not path.is_file():
            missing.append(ref)
            continue
        if ref.endswith(".json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except ValueError:
                malformed.append(ref)
                continue
            if isinstance(data, dict):
                expected_flags = ("advisory_only", "requires_human_review")
                if any(flag not in data for flag in expected_flags):
                    missing_flags.append(ref)
                    continue
            md_ref = ref[:-5] + ".md"
            md_path = resolve_instance_runtime_ref(
                instance_root=instance_root, relative_ref=md_ref
            )
            if not md_path.is_file():
                missing_md_pair.append(ref)
                continue
        ok.append(ref)

    return RuntimeBoundaryConsistencyReport(
        ok_ref_count=len(ok),
        unsafe_refs=_normalize(unsafe),
        missing_files=_normalize(missing),
        malformed_json_refs=_normalize(malformed),
        missing_markdown_pair_refs=_normalize(missing_md_pair),
        missing_advisory_flag_refs=_normalize(missing_flags),
        outside_runtime_boundary_refs=_normalize(outside_root),
    )


def _validate_date(date: str) -> None:
    if not _DATE_PATTERN.fullmatch(date):
        raise ValueError(f"invalid consistency report date: {date!r}")


def render_runtime_boundary_consistency_markdown(
    report: RuntimeBoundaryConsistencyReport,
) -> str:
    ...  # mirrors the M21.1 Markdown renderer; bounded sections only


def write_runtime_boundary_consistency_report(
    *, instance_root: Path, date: str, report: RuntimeBoundaryConsistencyReport
) -> dict[str, object]:
    _validate_date(date)
    rel_dir = f"{_CONSISTENCY_RUNTIME_PREFIX}/{date}"
    json_ref = f"{rel_dir}/consistency-report.json"
    md_ref = f"{rel_dir}/consistency-report.md"
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
        render_runtime_boundary_consistency_markdown(report), encoding="utf-8"
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
PYTHONPATH=src pytest tests/unit/test_runtime_boundary_consistency.py -q
PYTHONPATH=src pytest tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py -q
```

**Expected GREEN:** focused consistency-checker test passes; combined consistency + coverage tests pass.

---

## Task 3: Supplemental regression — writer round-trip and `..` rejection

**Objective:** Pin the writer's safety invariants after the first GREEN.

**Files:**

- Modify: `tests/unit/test_runtime_boundary_consistency.py`

**Test sketch:**

```python
def test_write_runtime_boundary_consistency_report_persists_safe_refs(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    report = build_runtime_boundary_consistency_report(
        instance_root=instance_root, candidate_refs=()
    )
    refs = write_runtime_boundary_consistency_report(
        instance_root=instance_root, date="20260520", report=report
    )
    assert refs["json_ref"] == (
        "runtime-boundary/runtime-boundary-consistency/20260520/consistency-report.json"
    )
    assert refs["external_call_made"] is False
    json_path = instance_root / refs["json_ref"]
    assert json_path.exists()


def test_build_runtime_boundary_consistency_report_rejects_traversal(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    report = build_runtime_boundary_consistency_report(
        instance_root=instance_root,
        candidate_refs=("runtime-boundary/../escape.txt",),
    )
    assert report.unsafe_refs == ("runtime-boundary/../escape.txt",)
    assert report.ok_ref_count == 0
```

**Verify:**

```bash
PYTHONPATH=src pytest tests/unit/test_runtime_boundary_consistency.py -q
```

**Expected:** focused consistency tests pass; no other test regressions.

---

## Task 4: Documentation, gate, and commit

**Objective:** Record M21.3 implementation evidence and keep governance boundaries explicit.

**Files:**

- Modify: `docs/traceability/README.md` — append an `M21.3` row referencing the new module, tests, and the verified governance invariants (advisory-only, no mutation outside report partition, no external calls, no raw source archival).
- Modify: `ralph.md` — append a Reflection Log entry following the existing M21.1/M21.2 format with Resume checkpoint.

**Validation:**

```bash
PYTHONPATH=src pytest tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_cli.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit (after RED/GREEN/regression):**

```bash
git add tests/unit/test_runtime_boundary_consistency.py src/hisys/operations/runtime_boundary_consistency.py docs/traceability/README.md ralph.md
git commit -m "feat: add runtime-boundary consistency checker"
```

---

## Stop conditions

Stop and ask for a new decision if any task would require:

- remote push or any change to remote configuration;
- live external network, browser, connector, model, or LSP/process invocation;
- credential lookup, mutation, or persistence;
- raw source archival or embedding of file bodies/secrets in the report;
- repair, deletion, retry, or quarantine of the runtime artifacts under inspection;
- expanding the checker into approval/safe-to-deploy/readiness language;
- adding the CLI in this increment (CLI is M21.3-CLI, planned separately after GREEN stabilizes).

## Out of scope for M21.3 (deferred)

- `hisys runtime-boundary-check` CLI subcommand (M21.3-CLI).
- Cross-instance comparison or drift across dates (defer to M21.4 codebase map freshness/drift review or a later M21 checker).
- Schema-id-aware deep validation per artifact family (consider after fixture benchmarks in M21.5).
- Subagent-driven evidence collection (human-gated, not part of M21.3).
- Any change to existing runtime-boundary writer modules; M21.3 reads only.
