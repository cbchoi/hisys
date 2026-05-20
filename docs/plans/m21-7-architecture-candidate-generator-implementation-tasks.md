# Milestone M21.7 — Architecture Candidate Generator Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for every code-bearing task. This file is the document-RED/Prepare artifact for Milestone M21 Task M21.7 — architecture candidate generator — authored after M21.6 closed end-to-end at `7c4d5d0 feat: add change-impact analyzer` and `3297909 feat: add change-impact cli wrapper`.

**Goal:** Add a pure, local-only, advisory architecture-candidate generator that consumes trusted M21.1 (`hisys.traceability.coverage.v1`), M21.4 (`hisys.codebase_map.freshness.v1`), and M21.6 (`hisys.change_impact.v1`) report payloads and produces a bounded set of *advisory* architecture candidates plus rationale strings, persisted as `hisys.architecture_candidates.v1`. The generator must never produce approval/safe-to-deploy/readiness wording, must never embed raw source, and must never authorize action.

**Human gate (do not cross without explicit user approval):** Any wording in the candidate output that names a specific architectural change, refactor, replacement, or new dependency as a *recommendation*, *required action*, *next step*, *plan*, *should*, *must*, or *will* requires explicit user approval. The M21.7 GREEN MVP must emit candidate records labeled as *advisory candidate suggestions* only, gated through a `recommendation_strength` field whose only allowed values in M21.7 GREEN are `advisory_candidate` and `advisory_candidate_low_evidence`. Stronger labels (`recommended`, `required`, `approved`) are out of scope for M21.7 and require a separate Prepare/RED with explicit user sign-off.

**Architecture:** Add a new pure-Python module `src/hisys/operations/architecture_candidates.py` that exposes:

1. A Pydantic `ArchitectureCandidateInputs` record carrying caller-supplied:
   - `instance_root: Path`
   - `coverage_report: dict[str, object] | None` (loaded payload of an `hisys.traceability.coverage.v1` artifact)
   - `freshness_report: dict[str, object] | None` (loaded payload of an `hisys.codebase_map.freshness.v1` artifact)
   - `change_impact_report: dict[str, object] | None` (loaded payload of an `hisys.change_impact.v1` artifact)
   - Optional `current_head_short: str | None`
2. A Pydantic `ArchitectureCandidate` record with:
   - `candidate_id: str` (deterministic slug like `cand-coverage-gap-001`).
   - `kind: str` from a bounded vocabulary: `coverage_gap`, `freshness_drift`, `change_impact_concentration`, `cross_signal_alignment`.
   - `summary: str` (≤200 chars, no imperative wording; the Prepare-time guardrail is that summaries must read as *observations*).
   - `supporting_refs: tuple[str, ...]` (relative ref IDs from the input reports; e.g., `HISYS-FR-DOM-002`, `runtime-boundary/codebase-analysis/20260518/REQ-X/`).
   - `recommendation_strength: Literal["advisory_candidate", "advisory_candidate_low_evidence"]`.
   - `rationale: str` (≤400 chars, factual observation referencing the input fields; no imperative wording).
3. A Pydantic `ArchitectureCandidateReport` record holding `schema_id = "hisys.architecture_candidates.v1"`, sorted candidates, bounded counts, advisory flags (`advisory_only`, `requires_human_review`, `external_call_made`, `mutation_performed`, `raw_source_content_persisted`), and the verbatim `current_head_short`.
4. A pure function `build_architecture_candidate_report(*, inputs)` that maps the three input payloads to candidates by applying a small, deterministic, rule-based mapping. The function reads only the dict fields named in M21.1/M21.4/M21.6 schemas; it does not open any new file, does not call `subprocess`, and does not infer new IDs from raw source.
5. A writer `write_architecture_candidate_report(*, instance_root, date, report)` that persists JSON + Markdown only under `runtime-boundary/architecture-candidates/<YYYYMMDD>/architecture-candidates-report.{json,md}` through `resolve_instance_runtime_ref`. The writer never writes outside that partition.

Reuse the `_DATE_PATTERN` and `resolve_instance_runtime_ref` chokepoint from `src/hisys/operations/codebase_analysis.py`. No new dependency, no network call, no model invocation, no credential resolution, no destructive Git, no remote push, no CLI argument expansion, and no raw source archival in this increment. A thin `hisys architecture-candidates` CLI wrapper is deferred to a separate M21.7-CLI Prepare/RED after the pure generator is stable.

**Tech Stack:** Python 3.11, pathlib, Pydantic v2 for the input/candidate/report records, pytest. No new dependency.

**Context Packet:** Required source handles:

- `src/hisys/operations/codebase_analysis.py` (`resolve_instance_runtime_ref`, runtime-boundary writer conventions, slug/date patterns).
- `src/hisys/operations/traceability_coverage.py` (M21.1 schema `hisys.traceability.coverage.v1`).
- `src/hisys/operations/codebase_map_freshness.py` (M21.4 schema `hisys.codebase_map.freshness.v1`).
- `src/hisys/operations/change_impact.py` (M21.6 schema `hisys.change_impact.v1`).
- `src/hisys/operations/runtime_boundary_consistency.py` and `src/hisys/operations/codebase_regression_benchmarks.py` (M21.3/M21.5 writer patterns).
- `tests/unit/test_traceability_coverage.py`, `tests/unit/test_codebase_map_freshness.py`, `tests/unit/test_change_impact.py` (test-fixture seeding patterns).
- `docs/traceability/README.md` and `ralph.md` for documentation updates.

**Boundary Record:** Local docs/control writes for this Prepare package, then later local test/code edits in a separate RED/GREEN increment, are allowed. Remote push is not authorized. No live external read, no repo clone, no credential resolution, no browser/network/model call, no destructive Git, no publication, no action authority. No `subprocess` invocation, no `date.today()` call, no `.git/` read, no raw source archival in any later M21.7 increment. The architecture-candidate report is advisory only and never implies repair, deletion, retry, approval, deployment, or readiness for live action.

---

## Accepted decisions

1. **Pure transform of trusted inputs.** Inputs are M21.1/M21.4/M21.6 dict payloads passed by the caller. The generator does not re-derive coverage, freshness, or impact data; if a needed input is `None`, the corresponding candidate kind is simply not produced.
2. **No raw source reads.** The generator reads no file bodies, only the input dict fields. The fields it touches are limited to: `coverage_ratio`, `unreferenced_requirements`, `orphan_test_ids` (M21.1); `fresh_partitions`, `stale_partitions`, `incomplete_partitions`, `unsafe_partitions` (M21.4); `impacted_requirement_ids`, `impacted_test_id_or_refs`, `impacted_design_or_interface_refs`, `unmapped_changed_refs`, `unsafe_changed_refs` (M21.6).
3. **Bounded candidate vocabulary.** Candidate kinds are limited to `coverage_gap`, `freshness_drift`, `change_impact_concentration`, and `cross_signal_alignment`. Additional kinds require a separate RED.
4. **Bounded recommendation strength vocabulary.** M21.7 GREEN allows only `advisory_candidate` and `advisory_candidate_low_evidence`. The string `recommended`, `required`, `approved`, `next_step`, or `must` must not appear in any candidate `summary` or `rationale` field in M21.7 GREEN; this is enforced by an explicit assertion in the supplemental regression test.
5. **Deterministic candidate IDs.** IDs are computed from a small slugifier on the input ref/ID with a numeric suffix; tests pin the exact ID list.
6. **Refs over content.** Candidates reference IDs and relative refs only. No file body, no diff hunk, no secret may appear in any field.
7. **No CLI in this increment.** A `hisys architecture-candidates` subcommand is M21.7-CLI work, planned separately after the pure generator is stable. M21.7 GREEN ships only the pure module and writer.
8. **Advisory only.** The report explicitly carries `advisory_only=true`, `requires_human_review=true`, `external_call_made=false`, `mutation_performed=false`, and `raw_source_content_persisted=false`.
9. **No artifact mutation.** The generator never writes outside `runtime-boundary/architecture-candidates/<YYYYMMDD>/`; it never repairs, rewrites, deletes, or quarantines the artifacts it inspects.
10. **Traceability required.** Update `docs/traceability/README.md` with an `M21.7` row in the implementation increment, and append a Reflection Log entry plus Resume checkpoint to `ralph.md`.

---

## Task 0: Reconstruct baseline before any edit

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_change_impact.py tests/unit/test_codebase_regression_benchmarks.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_cli.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:** branch `dars`, HEAD at or after `3297909 feat: add change-impact cli wrapper`; extended focused gate ≥52 passes; DARS focused gate 50 passes; traceability validator OK; secret scan hit_count=0; `git diff --check` clean.

---

## Task 1: RED — generator produces bounded advisory candidates from trusted inputs

**Objective:** Add a failing pytest that supplies small fixture payloads for the M21.1/M21.4/M21.6 schemas, calls `build_architecture_candidate_report`, and asserts the resulting candidate list matches a deterministic expected shape. The test must fail before the production module exists.

**Files:**

- Create: `tests/unit/test_architecture_candidates.py`

**Test sketch:**

```python
from __future__ import annotations

from pathlib import Path

import pytest

from hisys.operations.architecture_candidates import (
    ArchitectureCandidateInputs,
    build_architecture_candidate_report,
    write_architecture_candidate_report,
)


def _coverage_payload() -> dict:
    return {
        "schema_id": "hisys.traceability.coverage.v1",
        "advisory_only": True,
        "requires_human_review": True,
        "external_call_made": False,
        "mutation_performed": False,
        "raw_source_content_persisted": False,
        "requirement_count": 3,
        "covered_requirement_count": 1,
        "coverage_ratio": 0.3333,
        "unreferenced_requirements": ["HISYS-FR-DOM-002", "HISYS-NFR-MNT-001"],
        "orphan_test_ids": [],
    }


def _freshness_payload() -> dict:
    return {
        "schema_id": "hisys.codebase_map.freshness.v1",
        "advisory_only": True,
        "requires_human_review": True,
        "external_call_made": False,
        "mutation_performed": False,
        "raw_source_content_persisted": False,
        "current_date": "2026-05-21",
        "max_age_days": 30,
        "current_head_short": "3297909",
        "fresh_partitions": [],
        "stale_partitions": [
            "runtime-boundary/codebase-analysis/20260301/REQ-OLD"
        ],
        "incomplete_partitions": [],
        "unsafe_partitions": [],
    }


def _impact_payload() -> dict:
    return {
        "schema_id": "hisys.change_impact.v1",
        "advisory_only": True,
        "requires_human_review": True,
        "external_call_made": False,
        "mutation_performed": False,
        "raw_source_content_persisted": False,
        "current_head_short": "3297909",
        "changed_ref_count": 5,
        "impacted_requirement_ids": ["HISYS-FR-DOM-001", "HISYS-FR-DOM-002"],
        "impacted_test_id_or_refs": [],
        "impacted_design_or_interface_refs": [
            "docs/traceability/README.md",
            "src/hisys/schemas/domain_adapter.py",
        ],
        "impacted_runtime_boundary_refs": [],
        "unmapped_changed_refs": ["src/hisys/agents/unrelated_helper.py"],
        "unsafe_changed_refs": [],
    }


def test_build_architecture_candidate_report_produces_bounded_candidates(
    tmp_path: Path,
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()

    inputs = ArchitectureCandidateInputs(
        instance_root=instance_root,
        coverage_report=_coverage_payload(),
        freshness_report=_freshness_payload(),
        change_impact_report=_impact_payload(),
        current_head_short="3297909",
    )

    report = build_architecture_candidate_report(inputs=inputs)

    assert report.schema_id == "hisys.architecture_candidates.v1"
    assert report.advisory_only is True
    assert report.requires_human_review is True
    assert report.external_call_made is False
    assert report.mutation_performed is False
    assert report.raw_source_content_persisted is False
    assert report.current_head_short == "3297909"

    kinds = [c.kind for c in report.candidates]
    assert "coverage_gap" in kinds
    assert "freshness_drift" in kinds
    assert "change_impact_concentration" in kinds
    assert "cross_signal_alignment" in kinds

    for candidate in report.candidates:
        assert candidate.recommendation_strength in (
            "advisory_candidate",
            "advisory_candidate_low_evidence",
        )
        for forbidden in ("recommended", "required", "approved", "must", "next_step"):
            assert forbidden not in candidate.summary.lower()
            assert forbidden not in candidate.rationale.lower()
```

**Verify RED:**

```bash
PYTHONPATH=src pytest tests/unit/test_architecture_candidates.py::test_build_architecture_candidate_report_produces_bounded_candidates -q
```

**Expected RED:** `ModuleNotFoundError: No module named 'hisys.operations.architecture_candidates'`.

---

## Task 2: GREEN — implement minimal pure generator and writer

**Objective:** Add the smallest production logic that satisfies the RED test and the writer/no-imperative-wording invariants.

**Files:**

- Create: `src/hisys/operations/architecture_candidates.py`

**Module shape (illustrative; field names/IDs may evolve during GREEN):**

```python
"""Advisory architecture-candidate generation.

M21.7 keeps this surface pure and fixture-local: callers pass in already-trusted
M21.1/M21.4/M21.6 report payloads, and the generator emits bounded advisory
candidate records labeled only as ``advisory_candidate`` or
``advisory_candidate_low_evidence``. Imperative wording such as
``recommended``, ``required``, ``approved``, ``must``, or ``next_step`` is
intentionally rejected at the test-suite level and not introduced by this
module. The generator never opens raw source, never calls ``subprocess``,
never reads ``.git/``, never calls ``date.today()``, and never authorizes
live action.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from hisys.operations.codebase_analysis import resolve_instance_runtime_ref

_DATE_PATTERN = re.compile(r"^\d{8}$")
_ARCH_CAND_PREFIX = "runtime-boundary/architecture-candidates"

CandidateStrength = Literal["advisory_candidate", "advisory_candidate_low_evidence"]


class ArchitectureCandidateInputs(BaseModel):
    instance_root: Path
    coverage_report: dict | None = None
    freshness_report: dict | None = None
    change_impact_report: dict | None = None
    current_head_short: str | None = None


class ArchitectureCandidate(BaseModel):
    candidate_id: str
    kind: Literal[
        "coverage_gap",
        "freshness_drift",
        "change_impact_concentration",
        "cross_signal_alignment",
    ]
    summary: str
    supporting_refs: tuple[str, ...]
    recommendation_strength: CandidateStrength
    rationale: str


class ArchitectureCandidateReport(BaseModel):
    schema_id: str = "hisys.architecture_candidates.v1"
    current_head_short: str | None = None
    candidate_count: int
    candidates: tuple[ArchitectureCandidate, ...]
    advisory_only: bool = True
    requires_human_review: bool = True
    external_call_made: bool = False
    mutation_performed: bool = False
    raw_source_content_persisted: bool = False
```

**Generator rules (in M21.7 GREEN, conservative):**

- `coverage_gap` candidates: emit one per `unreferenced_requirements` entry in the coverage payload (limit to a bounded count, e.g., the first 10 sorted unique IDs). `recommendation_strength = advisory_candidate_low_evidence`. Summary observes which IDs lack references.
- `freshness_drift` candidates: emit one per `stale_partitions` entry. `recommendation_strength = advisory_candidate_low_evidence`. Summary observes which partition is older than `max_age_days`.
- `change_impact_concentration` candidates: emit one when `impacted_requirement_ids` has ≥1 entries and `changed_ref_count` ≤ 10, listing the impacted IDs and supporting refs. `recommendation_strength = advisory_candidate`.
- `cross_signal_alignment` candidates: emit one when an ID appears in both `unreferenced_requirements` (coverage) and `impacted_requirement_ids` (impact). `recommendation_strength = advisory_candidate`.

All candidate text is constructed from format strings with no imperative verbs.

**Verify GREEN:**

```bash
PYTHONPATH=src pytest tests/unit/test_architecture_candidates.py -q
PYTHONPATH=src pytest tests/unit/test_architecture_candidates.py tests/unit/test_change_impact.py tests/unit/test_codebase_map_freshness.py tests/unit/test_traceability_coverage.py -q
```

---

## Task 3: Supplemental regression — writer round-trip, missing-input fallback, imperative-wording rejection

**Objective:** Pin the writer's safety invariants and confirm the generator behaves safely when only one of the three input payloads is provided.

**Files:**

- Modify: `tests/unit/test_architecture_candidates.py`

**Test sketch:**

```python
def test_write_architecture_candidate_report_persists_safe_refs(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    inputs = ArchitectureCandidateInputs(
        instance_root=instance_root,
        coverage_report=_coverage_payload(),
        freshness_report=None,
        change_impact_report=None,
    )
    report = build_architecture_candidate_report(inputs=inputs)
    refs = write_architecture_candidate_report(
        instance_root=instance_root, date="20260521", report=report
    )
    assert refs["json_ref"] == (
        "runtime-boundary/architecture-candidates/20260521/architecture-candidates-report.json"
    )
    assert (instance_root / refs["json_ref"]).is_file()
    assert (instance_root / refs["markdown_ref"]).is_file()


def test_build_architecture_candidate_report_rejects_imperative_wording(
    tmp_path: Path,
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    inputs = ArchitectureCandidateInputs(
        instance_root=instance_root,
        coverage_report=_coverage_payload(),
        freshness_report=_freshness_payload(),
        change_impact_report=_impact_payload(),
    )
    report = build_architecture_candidate_report(inputs=inputs)
    for candidate in report.candidates:
        for forbidden in (
            "recommended",
            "required",
            "approved",
            "must",
            "next step",
            "should",
        ):
            assert forbidden not in candidate.summary.lower()
            assert forbidden not in candidate.rationale.lower()


def test_write_architecture_candidate_report_rejects_bad_date(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    inputs = ArchitectureCandidateInputs(
        instance_root=instance_root,
        coverage_report=None,
        freshness_report=None,
        change_impact_report=None,
    )
    report = build_architecture_candidate_report(inputs=inputs)
    with pytest.raises(ValueError):
        write_architecture_candidate_report(
            instance_root=instance_root, date="2026-05-21", report=report
        )
```

**Verify:**

```bash
PYTHONPATH=src pytest tests/unit/test_architecture_candidates.py -q
```

---

## Task 4: Documentation, gate, and commit

**Objective:** Record M21.7 implementation evidence and keep governance boundaries explicit.

**Files:**

- Modify: `docs/traceability/README.md` — prepend an `M21.7` row referencing the new module, tests, and the verified governance invariants (advisory-only, candidate vocabulary limited to four kinds, recommendation strength limited to two advisory values, imperative wording rejected, no external calls, no raw source archival, no mutation outside the report partition).
- Modify: `ralph.md` — append a Reflection Log entry following the existing M21.x format with Resume checkpoint.

**Validation:**

```bash
PYTHONPATH=src pytest tests/unit/test_architecture_candidates.py tests/unit/test_change_impact.py tests/unit/test_codebase_regression_benchmarks.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_cli.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit (after RED/GREEN/regression):**

```bash
git add tests/unit/test_architecture_candidates.py src/hisys/operations/architecture_candidates.py docs/traceability/README.md ralph.md
git commit -m "feat: add architecture candidate generator"
```

---

## Stop conditions

Stop and ask for a new decision if any task would require:

- remote push or any change to remote configuration;
- live external network, browser, connector, model, or LSP/process invocation;
- credential lookup, mutation, or persistence;
- shelling out to `git diff`, `git log`, or any `subprocess` call;
- reading `.git/` directly or calling `date.today()` inside the generator;
- raw source archival or persistence of file bodies/secrets in the report;
- candidate strings using `recommended`, `required`, `approved`, `must`, `next step`, or `should` wording (these require explicit user approval as a separate Prepare/RED);
- expanding the recommendation-strength vocabulary beyond `advisory_candidate` and `advisory_candidate_low_evidence`;
- expanding the candidate-kind vocabulary beyond the four allowed kinds;
- repair, deletion, retry, or quarantine of artifacts the generator inspects;
- adding the CLI in this increment (CLI is M21.7-CLI, planned separately after GREEN stabilizes);
- re-deriving coverage/freshness/impact data from raw source rather than from the provided dict payloads;
- changing M21.1/M21.4/M21.6 schemas as a side-effect of M21.7 (those schemas remain stable; growth requires a separate RED).

## Out of scope for M21.7 (deferred)

- `hisys architecture-candidates` CLI subcommand (M21.7-CLI).
- Stronger recommendation labels such as `recommended`, `required`, or `approved` — these are gated behind explicit user approval.
- Architectural change proposals that name specific refactors, replacements, or dependencies.
- Cross-instance / cross-branch comparison.
- Subagent-driven evidence collection (human-gated).
- Code-analysis pass-contract loop (M21.8+).
- Any change to M21.1/M21.4/M21.6 schemas; M21.7 reuses them as-is.

## Next executable action

After this Prepare plan is committed, run the RED command:

```bash
PYTHONPATH=src pytest tests/unit/test_architecture_candidates.py::test_build_architecture_candidate_report_produces_bounded_candidates -q
```

Expected failure: `ModuleNotFoundError: No module named 'hisys.operations.architecture_candidates'`.
