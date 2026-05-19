# DARS Critic Panel M-CP-EXT-2 Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for every code-bearing task. This plan is a task-generation artifact for the next executable work after `M-CP-EXT-1`; it does not authorize live DARS dispatch, external calls, credential resolution, publication, deployment, remote push, or bounded-parallel activation.

**Goal:** Implement `M-CP-EXT-2` from `docs/plans/dars-critic-panel-platform-runtime-next.md`: persist a per-task `ExecutionBoundaryRecord` JSON artifact for every critic dispatch decision and enforce slug validation on `yyyymmdd` and `request_id` before any path is composed under the runtime instance root. Targets accepted requirements (2) and (5).

**Current baseline:** Branch `dars`, observed HEAD `3cc58ed feat: add DARS critic adapter registry`; `PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py -q` is GREEN with `13 passed`.

**Architecture:** Keep the existing public `hisys.agents.dars_panel` API backward-compatible for `tests/unit/test_dars_critic_panel_runtime.py` and `tests/unit/test_dars_critic_panel_adapters.py`. Add the `ExecutionBoundaryRecord` dataclass plus a `write_execution_boundary_record` writer in the same module to avoid package-split churn this increment. The writer composes paths under `<instance>/runtime-boundary/dars-panel/<YYYYMMDD>/<REQUEST_ID>/<TASK_ID>.json` (mirrors the existing codebase-analysis `runtime-boundary/` subtree convention; deliberately distinct from the existing `data/dars-panel/` subtree used for advisory critique/synthesis/trace content). `DarsCriticPanelRuntime.run_round` writes one boundary record per critic task (`allowed`/`blocked`/`failed`) before persisting any critique or synthesis. Boundary writes use the same `_validate_slug` style as `src/hisys/operations/codebase_analysis.py` so traversal/absolute/empty slugs are rejected before any directory is created. The pre-existing `data/dars-panel/...` writes for critique/synthesis/trace remain unchanged in this increment; their slug enforcement is added in the same hardening step so all five persistence sites share one validator.

**Tech stack:** Python 3.11, dataclasses, pytest. No new dependency. No network/browser libraries.

**Context packet:**

- Requirements: `docs/requirements/dars-critic-panel-runtime-requirements.md` — HISYS-FR-DARS-CP-003, HISYS-FR-DARS-CP-004, HISYS-FR-DARS-CP-007, HISYS-NFR-DARS-CP-001, HISYS-NFR-DARS-CP-002.
- Design: `docs/design/dars-critic-panel-runtime-sdd.md` — dispatch gate, failure isolation, advisory-only artifact rules.
- Next-increment plan: `docs/plans/dars-critic-panel-platform-runtime-next.md` — requirements (2) and (5), M-CP-EXT-2 exit criteria, "open question (b)" subtree recommendation (`runtime-boundary/dars-panel/...`).
- M-CP-EXT-1 surface: `src/hisys/agents/dars_panel.py` — `CriticAdapterRegistry`, `FixtureCriticAdapter`, `BackendDispatchOutcome`, `DarsCriticPanelRuntime.run_round` (resolves adapter, treats `PermissionError` as `blocked`, treats `fixture_outcome="failed"` as `failed`).
- Existing writer convention: `src/hisys/operations/codebase_analysis.py` — `_validate_slug`, `_DATE_PATTERN`, `_REQUEST_ID_PATTERN`, the `runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/` subtree pattern, the safety-envelope record shape.
- Existing regression: `tests/unit/test_dars_critic_panel_runtime.py` (9) and `tests/unit/test_dars_critic_panel_adapters.py` (4) must keep passing unchanged.

**Boundary record:** Local fixture-only code/tests/docs mutation is allowed. Local commit is allowed after validation. Remote push is deferred unless explicitly requested or a separate repository-sync gate is satisfied. No live DARS dispatch is authorized. No live external adapter class shall execute; external adapter records may be represented only as blocked/disabled metadata. Every `ExecutionBoundaryRecord` shall record `external_call_made=false`, `mutation_performed=false`, `action_authorized=false`, `advisory_only=true`, and `requires_human_review=true`.

---

## Accepted implementation target

Implement only `M-CP-EXT-2`:

1. `ExecutionBoundaryRecord` dataclass captures one critic-task dispatch boundary with: `task_id`, `critic_id`, `critic_role`, `adapter_class`, `backend_id`, `dispatch_decision in {"allowed", "blocked"}`, `dispatch_reason`, `started_at`, `completed_at`, `approval_ref` (nullable), `critique_ref` (nullable), and the five safety-envelope fields (`external_call_made=false`, `mutation_performed=false`, `action_authorized=false`, `advisory_only=true`, `requires_human_review=true`).
2. `write_execution_boundary_record(*, instance_root, date, request_id, record)` persists deterministic JSON (UTF-8, indent=2, sort_keys=True) under `<instance>/runtime-boundary/dars-panel/<YYYYMMDD>/<REQUEST_ID>/<TASK_ID>.json` after slug-validating `date`, `request_id`, and the task id segment. Returns the instance-relative ref.
3. `DarsCriticPanelRuntime.run_round` records one boundary record per critic task (allowed/blocked/failed) and exposes the resulting refs on `DarsRoundResult.execution_boundary_refs: list[str]`. Adding the new attribute must remain backwards-compatible with `tests/unit/test_dars_critic_panel_runtime.py` and `tests/unit/test_dars_critic_panel_adapters.py`.
4. `run_round` rejects malformed `yyyymmdd` or `request_id` (empty string, absolute path, `..` segment, traversal characters) before composing any path under the instance root. The same validator is shared with `write_execution_boundary_record`.

Do **not** implement M-CP-EXT-3 execution-graph scheduling, do **not** introduce a `hisys run-dars-panel` CLI, and do **not** split `dars_panel.py` into a package. Keep the package layout open question deferred per `docs/plans/dars-critic-panel-platform-runtime-next.md`.

---

## Task 0: Reconstruct baseline before editing

**Objective:** Confirm the repository state and current GREEN baseline before any new RED test is written.

**Files:** none.

**Commands:**

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py -q
```

**Expected:**

- Branch is `dars`.
- Combined adapter + panel suite reports `13 passed`.
- If the working tree is dirty, inspect the diff before proceeding and do not mix unrelated changes.

---

## Task 1: RED/GREEN — `ExecutionBoundaryRecord` dataclass and safety-envelope defaults

**Objective:** Capture the per-task boundary contract as a typed record with locked safety-envelope defaults.

**Files:**

- Create: `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`
- Modify: `src/hisys/agents/dars_panel.py`

**Step 1: Write failing test**

```python
"""DARS critic panel tool-execution runtime tests.

Traceability:
- HISYS-FR-DARS-CP-003
- HISYS-FR-DARS-CP-004
- HISYS-FR-DARS-CP-007
- HISYS-NFR-DARS-CP-001
- HISYS-NFR-DARS-CP-002
- M-CP-EXT-2 in docs/plans/dars-critic-panel-platform-runtime-next.md
"""

from __future__ import annotations

import pytest


def test_execution_boundary_record_locks_safety_envelope_defaults():
    from hisys.agents.dars_panel import ExecutionBoundaryRecord

    record = ExecutionBoundaryRecord(
        task_id="TASK-REQ-001-00-logical",
        critic_id="logical-devil",
        critic_role="logical_devil",
        adapter_class="fixture",
        backend_id="fixture-logical",
        dispatch_decision="allowed",
        dispatch_reason="adapter resolved",
        started_at="2026-05-19T12:00:00Z",
        completed_at="2026-05-19T12:00:01Z",
    )

    assert record.external_call_made is False
    assert record.mutation_performed is False
    assert record.action_authorized is False
    assert record.advisory_only is True
    assert record.requires_human_review is True
    assert record.approval_ref is None
    assert record.critique_ref is None
```

**Step 2: Verify RED**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_tool_execution_runtime.py::test_execution_boundary_record_locks_safety_envelope_defaults -q
```

**Expected RED:** `ImportError` for `ExecutionBoundaryRecord`.

**Step 3: Minimal GREEN implementation**

In `src/hisys/agents/dars_panel.py`, add the `ExecutionBoundaryRecord` dataclass with the field set above. Reject any attempt to construct with `external_call_made=True`, `mutation_performed=True`, or `action_authorized=True` via `__post_init__` (raise `ValueError`).

**Step 4: Verify GREEN**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_tool_execution_runtime.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py -q
```

---

## Task 2: RED/GREEN — `write_execution_boundary_record` persists deterministic JSON under `runtime-boundary/dars-panel`

**Objective:** Add the boundary writer with slug validation and instance-relative ref return.

**Files:**

- Modify: `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`
- Modify: `src/hisys/agents/dars_panel.py`

**Step 1: Add failing test**

```python
import json
from pathlib import Path


def test_write_execution_boundary_record_writes_deterministic_json_under_instance_root(tmp_path: Path):
    from hisys.agents.dars_panel import ExecutionBoundaryRecord, write_execution_boundary_record

    record = ExecutionBoundaryRecord(
        task_id="TASK-REQ-001-00-logical",
        critic_id="logical-devil",
        critic_role="logical_devil",
        adapter_class="fixture",
        backend_id="fixture-logical",
        dispatch_decision="allowed",
        dispatch_reason="adapter resolved",
        started_at="2026-05-19T12:00:00Z",
        completed_at="2026-05-19T12:00:01Z",
        critique_ref="data/dars-panel/20260519/REQ-001/critiques/CRITIQUE-REQ-001-logical-devil.json",
    )

    ref = write_execution_boundary_record(
        instance_root=tmp_path,
        date="20260519",
        request_id="REQ-001",
        record=record,
    )

    expected = Path("runtime-boundary") / "dars-panel" / "20260519" / "REQ-001" / "TASK-REQ-001-00-logical.json"
    assert ref == str(expected)
    payload = json.loads((tmp_path / ref).read_text(encoding="utf-8"))
    assert payload["task_id"] == "TASK-REQ-001-00-logical"
    assert payload["external_call_made"] is False
    assert payload["mutation_performed"] is False
    assert payload["action_authorized"] is False
    assert payload["advisory_only"] is True
    assert payload["requires_human_review"] is True
    # Determinism: writing the same record again produces byte-identical content.
    second_ref = write_execution_boundary_record(
        instance_root=tmp_path,
        date="20260519",
        request_id="REQ-001",
        record=record,
    )
    assert second_ref == ref
```

**Step 2: Verify RED**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_tool_execution_runtime.py::test_write_execution_boundary_record_writes_deterministic_json_under_instance_root -q
```

**Expected RED:** `ImportError` for `write_execution_boundary_record`.

**Step 3: Minimal GREEN implementation**

In `src/hisys/agents/dars_panel.py`:

- Add `_DATE_PATTERN = re.compile(r"^[0-9]{8}$")` and `_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")` and `_TASK_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")` constants (mirror `src/hisys/operations/codebase_analysis.py` style).
- Add `_validate_slug(name: str, value: str, pattern: re.Pattern[str]) -> None` raising `ValueError` for empty values, absolute paths (`startswith("/")` or contains `":"` on POSIX), `..` segments, or any value that does not match the pattern.
- Add `RUNTIME_BOUNDARY_SUBTREE = Path("runtime-boundary") / "dars-panel"`.
- Add `write_execution_boundary_record(*, instance_root: Path | str, date: str, request_id: str, record: ExecutionBoundaryRecord) -> str` that slug-validates `date` against `_DATE_PATTERN`, `request_id` against `_REQUEST_ID_PATTERN`, and `record.task_id` against `_TASK_ID_PATTERN`; composes the deterministic path; serializes the record as JSON (UTF-8, `indent=2`, `sort_keys=True`); writes it; and returns the instance-relative ref as a POSIX-style string.

**Step 4: Verify GREEN**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_tool_execution_runtime.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py -q
```

---

## Task 3: RED/GREEN — writer rejects traversal, absolute, and empty slugs

**Objective:** Pin the slug-validation contract before any caller composes a path.

**Files:**

- Modify: `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`
- Modify: `src/hisys/agents/dars_panel.py`

**Step 1: Add failing tests**

```python
def _ok_record():
    from hisys.agents.dars_panel import ExecutionBoundaryRecord

    return ExecutionBoundaryRecord(
        task_id="TASK-REQ-001-00-logical",
        critic_id="logical-devil",
        critic_role="logical_devil",
        adapter_class="fixture",
        backend_id="fixture-logical",
        dispatch_decision="allowed",
        dispatch_reason="adapter resolved",
        started_at="2026-05-19T12:00:00Z",
        completed_at="2026-05-19T12:00:01Z",
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"date": "", "request_id": "REQ-001"},
        {"date": "2026-05-19", "request_id": "REQ-001"},  # not yyyymmdd
        {"date": "20260519", "request_id": ""},
        {"date": "20260519", "request_id": "../escape"},
        {"date": "20260519", "request_id": "/abs"},
    ],
)
def test_write_execution_boundary_record_rejects_invalid_slug(tmp_path: Path, kwargs):
    from hisys.agents.dars_panel import write_execution_boundary_record

    with pytest.raises(ValueError):
        write_execution_boundary_record(
            instance_root=tmp_path,
            record=_ok_record(),
            **kwargs,
        )


def test_write_execution_boundary_record_rejects_traversal_in_task_id(tmp_path: Path):
    from hisys.agents.dars_panel import ExecutionBoundaryRecord, write_execution_boundary_record

    bad = ExecutionBoundaryRecord(
        task_id="../escape",
        critic_id="logical-devil",
        critic_role="logical_devil",
        adapter_class="fixture",
        backend_id="fixture-logical",
        dispatch_decision="allowed",
        dispatch_reason="adapter resolved",
        started_at="2026-05-19T12:00:00Z",
        completed_at="2026-05-19T12:00:01Z",
    )
    with pytest.raises(ValueError):
        write_execution_boundary_record(
            instance_root=tmp_path,
            date="20260519",
            request_id="REQ-001",
            record=bad,
        )
```

**Step 2: Verify RED**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_tool_execution_runtime.py -q
```

**Expected RED:** Slug-validation tests fail until `_validate_slug` is wired (some may already pass from Task 2 — that is acceptable; the parametrized matrix still binds the contract).

**Step 3: Minimal GREEN implementation**

Ensure `_validate_slug` raises `ValueError` for the listed failure modes. Apply it to all three of `date`, `request_id`, and `record.task_id` before any directory is created.

**Step 4: Verify GREEN**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_tool_execution_runtime.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py -q
```

---

## Task 4: RED/GREEN — `DarsCriticPanelRuntime.run_round` records one boundary record per critic task

**Objective:** Wire boundary persistence into the run loop so every critic task — allowed, blocked, or failed — produces exactly one boundary record. Expose the refs on `DarsRoundResult.execution_boundary_refs`.

**Files:**

- Modify: `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`
- Modify: `src/hisys/agents/dars_panel.py`

**Step 1: Add failing test**

```python
import json
from pathlib import Path

from hisys.config.instance import InstanceRoot


def _candidate_fixture(tmp_path: Path) -> tuple[str, list[str], str]:
    data_dir = tmp_path / "data" / "dars-panel-fixtures" / "20260519"
    data_dir.mkdir(parents=True)
    candidate = data_dir / "candidate-001.json"
    evidence = data_dir / "evidence-001.json"
    rubric = data_dir / "rubric-001.json"
    candidate.write_text(json.dumps({"candidate_id": "CAND-001"}), encoding="utf-8")
    evidence.write_text(json.dumps({"evidence_id": "EVID-001"}), encoding="utf-8")
    rubric.write_text(json.dumps({"rubric_id": "RUBRIC-DARS-001"}), encoding="utf-8")
    return (
        str(candidate.relative_to(tmp_path)),
        [str(evidence.relative_to(tmp_path))],
        str(rubric.relative_to(tmp_path)),
    )


def test_panel_runtime_writes_one_boundary_record_per_task(tmp_path: Path):
    from hisys.agents.dars_panel import (
        CriticAdapterRegistry,
        DarsCriticPanelConfig,
        DarsCriticPanelRuntime,
        DarsCriticRoleConfig,
        FixtureCriticAdapter,
    )

    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    registry = CriticAdapterRegistry()
    registry.register(
        FixtureCriticAdapter(
            critic_role="logical_devil",
            backend_id="fixture-logical",
            fixture_outcome="completed",
        )
    )
    registry.register(
        FixtureCriticAdapter(
            critic_role="evidence_governance_devil",
            backend_id="fixture-evidence-outcome-002",
            fixture_outcome="failed",
        )
    )
    config = DarsCriticPanelConfig(
        panel_id="PANEL-DARS-CP-EXT-2",
        critics=[
            DarsCriticRoleConfig(
                critic_id="logical-devil",
                critic_role="logical_devil",
                backend_id="fixture-logical",
                rubric_ref=rubric_ref,
                critique_dimensions=["logical_validity"],
            ),
            DarsCriticRoleConfig(
                critic_id="evidence-devil",
                critic_role="evidence_governance_devil",
                backend_id="fixture-evidence-outcome-002",
                rubric_ref=rubric_ref,
                critique_dimensions=["source_quality"],
            ),
        ],
    )

    result = DarsCriticPanelRuntime(
        instance=InstanceRoot(tmp_path),
        adapter_registry=registry,
    ).run_round(
        yyyymmdd="20260519",
        request_id="REQ-DARS-CP-EXT-2",
        candidate_ref=candidate_ref,
        evidence_refs=evidence_refs,
        panel_config=config,
    )

    assert len(result.execution_boundary_refs) == 2
    for boundary_ref in result.execution_boundary_refs:
        payload = json.loads((tmp_path / boundary_ref).read_text(encoding="utf-8"))
        assert payload["external_call_made"] is False
        assert payload["mutation_performed"] is False
        assert payload["action_authorized"] is False
        assert payload["advisory_only"] is True
        assert payload["requires_human_review"] is True
    # The failed critic still produced a boundary record with critique_ref=null.
    failed_payload = next(
        json.loads((tmp_path / ref).read_text(encoding="utf-8"))
        for ref in result.execution_boundary_refs
        if "evidence" in ref
    )
    assert failed_payload["critique_ref"] is None
    assert failed_payload["dispatch_decision"] in {"allowed", "blocked"}
```

**Step 2: Verify RED**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_tool_execution_runtime.py::test_panel_runtime_writes_one_boundary_record_per_task -q
```

**Expected RED:** `AttributeError: 'DarsRoundResult' object has no attribute 'execution_boundary_refs'` or the boundary record file is missing.

**Step 3: Minimal GREEN implementation**

- Add `execution_boundary_refs: list[str] = field(default_factory=list)` to `DarsRoundResult`.
- In `run_round`, for each critic task — before the existing fixture-failure / blocked / completed branches — capture `started_at = datetime.utcnow().isoformat() + "Z"` (or pass an injectable clock if needed for determinism in later increments; this increment may use `started_at == completed_at` if no real timing is recorded).
- For each branch (`blocked`, `failed`, `completed`), construct an `ExecutionBoundaryRecord` and call `write_execution_boundary_record(...)`; append the returned ref to `execution_boundary_refs`.
- Make sure `dispatch_decision` is `allowed` for `failed`/`completed` branches (the adapter resolved) and `blocked` for `blocked` branches; `dispatch_reason` records the human-readable reason (matches the existing `error_message` values where applicable).
- Slug-validate `yyyymmdd` and `request_id` once at the top of `run_round` before composing any path, raising `ValueError` early.

**Step 4: Verify GREEN**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_tool_execution_runtime.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py -q
```

---

## Task 5: RED/GREEN — `run_round` rejects malformed `yyyymmdd` / `request_id`

**Objective:** Pin the slug-rejection contract on the run loop itself so callers cannot escape the writer chokepoint by skipping it.

**Files:**

- Modify: `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`
- Modify: `src/hisys/agents/dars_panel.py` (if slug validation was not already added at the top of `run_round` in Task 4).

**Step 1: Add failing tests**

```python
@pytest.mark.parametrize(
    "kwargs",
    [
        {"yyyymmdd": "", "request_id": "REQ-VALID"},
        {"yyyymmdd": "2026-05-19", "request_id": "REQ-VALID"},
        {"yyyymmdd": "20260519", "request_id": ""},
        {"yyyymmdd": "20260519", "request_id": "../escape"},
        {"yyyymmdd": "20260519", "request_id": "/abs"},
    ],
)
def test_panel_runtime_rejects_invalid_slug(tmp_path: Path, kwargs):
    from hisys.agents.dars_panel import (
        CriticAdapterRegistry,
        DarsCriticPanelConfig,
        DarsCriticPanelRuntime,
        DarsCriticRoleConfig,
        FixtureCriticAdapter,
    )

    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    registry = CriticAdapterRegistry()
    registry.register(
        FixtureCriticAdapter(
            critic_role="logical_devil",
            backend_id="fixture-logical",
            fixture_outcome="completed",
        )
    )
    config = DarsCriticPanelConfig(
        panel_id="PANEL-DARS-CP-EXT-2-SLUG",
        critics=[
            DarsCriticRoleConfig(
                critic_id="logical-devil",
                critic_role="logical_devil",
                backend_id="fixture-logical",
                rubric_ref=rubric_ref,
                critique_dimensions=["logical_validity"],
            )
        ],
    )

    with pytest.raises(ValueError):
        DarsCriticPanelRuntime(
            instance=InstanceRoot(tmp_path),
            adapter_registry=registry,
        ).run_round(
            candidate_ref=candidate_ref,
            evidence_refs=evidence_refs,
            panel_config=config,
            **kwargs,
        )
```

**Step 2: Verify RED/GREEN**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_tool_execution_runtime.py::test_panel_runtime_rejects_invalid_slug -q
```

If Task 4 already raised `ValueError` at the top of `run_round`, this test is GREEN immediately. Otherwise add the validation now.

---

## Task 6: Refactor only after GREEN

**Objective:** Tidy duplicated slug-validation, share the validator across `_panel_dir` / critique / synthesis / trace writers, and ensure no stale comments reference removed M-CP-EXT-1 heuristics.

**Files:**

- Modify: `src/hisys/agents/dars_panel.py`

**Steps:**

1. Apply the shared `_validate_slug` to the existing `_panel_dir`, critique writer, synthesis writer, and trace writer entry points so all five persistence sites enforce the same contract. Do not change the existing artifact contents.
2. Add new exported symbols to `__all__`:
   - `ExecutionBoundaryRecord`
   - `write_execution_boundary_record`
3. Do not change JSON artifact shapes except for the new `runtime-boundary/dars-panel/...` boundary records.
4. Keep the package layout decision deferred (no module split this increment).

**Verification:**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_tool_execution_runtime.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py -q
```

---

## Task 7: Update traceability/reflection for M-CP-EXT-2

**Objective:** Record the completed implementation in durable project docs.

**Files:**

- Modify: `docs/traceability/dars-critic-panel-runtime-traceability.md`
- Modify: `docs/traceability/README.md` Implemented-increments table.
- Modify: `ralph.md` Reflection Log.

**Required content:**

- State M-CP-EXT-2 implemented `ExecutionBoundaryRecord` + writer + run-round wiring + slug validation.
- Link tests:
  - `tests/unit/test_dars_critic_panel_tool_execution_runtime.py` (new)
  - existing `tests/unit/test_dars_critic_panel_adapters.py`
  - existing `tests/unit/test_dars_critic_panel_runtime.py`
- Preserve boundary statement: no live DARS dispatch, no credential use, no mutation authority, no external calls; every boundary record validates `external_call_made=false`, `mutation_performed=false`, `action_authorized=false`, `advisory_only=true`, `requires_human_review=true`.
- Record RED and GREEN commands exactly.

---

## Task 8: Quality gate and local commit

**Objective:** Validate the increment and commit only if the tree is coherent.

**Commands:**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_tool_execution_runtime.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py -q
PYTHONPATH=src:. pytest tests/unit/test_dars_runtime.py tests/unit/test_dars_config.py tests/unit/test_dars_dispatch.py -q
PYTHONPATH=src:. pytest -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
git status --short --branch
```

**Expected:**

- New tool-execution-runtime suite passes.
- Existing panel + adapter suites remain `13 passed` combined.
- Adjacent DARS suites pass.
- Full repo pytest still passes.
- Traceability and secret scans pass.
- `git diff --check` has no output.

**Commit:**

```bash
git add src/hisys/agents/dars_panel.py \
  tests/unit/test_dars_critic_panel_tool_execution_runtime.py \
  docs/traceability/dars-critic-panel-runtime-traceability.md \
  docs/traceability/README.md \
  ralph.md

git commit -m "feat: add DARS execution-boundary record writer"
```

**Post-commit verification:**

```bash
git status --short --branch
git log --oneline -1
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py -q
```

---

## Stop conditions

Stop before implementation if any of the following occurs:

- Combined panel + adapter suites are not GREEN before writing the first new RED test.
- Any proposed test requires live network, browser, credential, or external DARS service access.
- The implementation needs to break `tests/unit/test_dars_critic_panel_runtime.py` or `tests/unit/test_dars_critic_panel_adapters.py` public API expectations.
- The writer design requires a package split that would also require CLI/import migration. Record that as a new plan instead of expanding M-CP-EXT-2.
- Traceability anchors are missing or contradictory.
- A boundary record cannot be written without violating any of `external_call_made=false`, `mutation_performed=false`, or `action_authorized=false`.

## Next action command

If proceeding with implementation, start with Task 0 and then Task 1 RED:

```bash
cd /home/cbchoi/workspaces/develop/repos/hisys
git status --short --branch
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py -q
```
