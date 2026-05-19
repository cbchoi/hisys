# DARS Critic Panel M-CP-EXT-1 Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for every code-bearing task. This plan is a task-generation artifact for the next executable work after `MB-DARS-CP-T004`; it does not authorize live DARS dispatch, external calls, credential resolution, publication, deployment, remote push, or bounded-parallel activation.

**Goal:** Implement `M-CP-EXT-1` from `docs/plans/dars-critic-panel-platform-runtime-next.md`: introduce an explicit fixture/loopback critic adapter registry and remove backend-name heuristics from the fixture-local DARS critic panel runtime.

**Current baseline:** Branch `dars`, observed HEAD `d42cb93 docs: record DARS critic panel platform/runtime next-increment plan`; `PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_runtime.py -q` is already GREEN with `9 passed`.

**Architecture:** Keep the existing public `hisys.agents.dars_panel` API backward-compatible for `tests/unit/test_dars_critic_panel_runtime.py`. Add a narrow adapter contract in the same module for this increment to avoid package-split churn; split into `hisys.agents.dars_panel.adapters` only after the file exceeds the small-increment threshold or M-CP-EXT-2 needs it. `DarsCriticPanelRuntime.run_round` should delegate dispatch and fixture outcome classification to typed adapters instead of checking `backend_id.startswith("external-")` and `"fail" in backend_id` directly.

**Tech stack:** Python 3.11, dataclasses, pytest. No new dependency. No network/browser libraries.

**Context packet:**

- Requirements: `docs/requirements/dars-critic-panel-runtime-requirements.md` — HISYS-FR-DARS-CP-001, HISYS-FR-DARS-CP-007, HISYS-NFR-DARS-CP-001, HISYS-NFR-DARS-CP-002.
- Design: `docs/design/dars-critic-panel-runtime-sdd.md` — panel config, dispatch gate, failure isolation, advisory-only artifact rules.
- Next-increment plan: `docs/plans/dars-critic-panel-platform-runtime-next.md` — requirements (1) and (4), M-CP-EXT-1 exit criteria.
- Existing implementation: `src/hisys/agents/dars_panel.py`, especially `_evaluate_dispatch`, `_is_fixture_failure`, and `run_round` task loop.
- Existing regression: `tests/unit/test_dars_critic_panel_runtime.py` must keep passing unchanged.

**Boundary record:** Local fixture-only code/tests/docs mutation is allowed. Local commit is allowed after validation. Remote push is deferred unless explicitly requested or a separate repository-sync gate is satisfied. No live DARS dispatch is authorized. No live external adapter class shall execute; external adapter records may be represented only as blocked/disabled metadata.

---

## Accepted implementation target

Implement only `M-CP-EXT-1`:

1. `CriticAdapterRegistry` validates and resolves explicit fixture/loopback adapters.
2. `FixtureCriticAdapter` declares `fixture_outcome` instead of relying on a backend ID substring.
3. External adapters remain blocked unless both registry-level external dispatch and critic-level approval are explicitly present. For this increment, no live external adapter execution exists.
4. Existing `DarsCriticPanelRuntime` public behavior and artifact contracts remain unchanged.

Do **not** implement M-CP-EXT-2 boundary-record persistence or M-CP-EXT-3 execution graph scheduling in this increment.

---

## Task 0: Reconstruct baseline before editing

**Objective:** Confirm the repository state and current GREEN baseline before any new RED test is written.

**Files:** none.

**Commands:**

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_runtime.py -q
```

**Expected:**

- Branch is `dars`.
- Focused panel suite reports `9 passed`.
- If the working tree is dirty, inspect the diff before proceeding and do not mix unrelated changes.

---

## Task 1: RED — adapter registry blocks external adapters without registry allow flag

**Objective:** Add the first failing test for explicit adapter-class dispatch control.

**Files:**

- Create: `tests/unit/test_dars_critic_panel_adapters.py`
- Later modify: `src/hisys/agents/dars_panel.py`

**Step 1: Write failing test**

Add the following initial test module:

```python
"""DARS critic panel adapter registry tests.

Traceability:
- HISYS-FR-DARS-CP-001
- HISYS-FR-DARS-CP-007
- M-CP-EXT-1 in docs/plans/dars-critic-panel-platform-runtime-next.md
"""

from __future__ import annotations

import pytest


def test_critic_adapter_registry_blocks_external_without_explicit_allow_flag():
    from hisys.agents.dars_panel import CriticAdapterRegistry, FixtureCriticAdapter

    registry = CriticAdapterRegistry(external_dispatch_allowed=False)
    registry.register(
        FixtureCriticAdapter(
            critic_role="logical_devil",
            backend_id="external-dars",
            adapter_class="external",
        )
    )

    with pytest.raises(PermissionError, match="external adapter dispatch is disabled"):
        registry.resolve(
            critic_role="logical_devil",
            backend_id="external-dars",
            approval_ref="APPROVAL-DARS-001",
        )
```

**Step 2: Verify RED**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py::test_critic_adapter_registry_blocks_external_without_explicit_allow_flag -q
```

**Expected RED:** Import failure for `CriticAdapterRegistry` / `FixtureCriticAdapter` or an equivalent missing-symbol failure.

**Step 3: Minimal GREEN implementation**

In `src/hisys/agents/dars_panel.py`, add:

- `AdapterClass = Literal["fixture", "loopback", "external"]`
- `BackendDispatchOutcome = Literal["completed", "failed", "blocked", "skipped"]`
- dataclass `FixtureCriticAdapter` with fields:
  - `critic_role: str`
  - `backend_id: str`
  - `adapter_class: AdapterClass = "fixture"`
  - `fixture_outcome: BackendDispatchOutcome = "completed"`
- class `CriticAdapterRegistry` with:
  - `__init__(self, *, external_dispatch_allowed: bool = False)`
  - `register(adapter)` rejecting duplicate `(critic_role, backend_id)`
  - `resolve(critic_role, backend_id, approval_ref=None)`
  - external resolution blocked unless `external_dispatch_allowed is True` and `approval_ref` is truthy.

**Step 4: Verify GREEN**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py::test_critic_adapter_registry_blocks_external_without_explicit_allow_flag -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_runtime.py -q
```

---

## Task 2: RED/GREEN — registry rejects duplicate adapter registrations

**Objective:** Ensure adapter resolution is deterministic and cannot silently override a role/backend pair.

**Files:**

- Modify: `tests/unit/test_dars_critic_panel_adapters.py`
- Modify: `src/hisys/agents/dars_panel.py`

**Step 1: Add failing test**

```python
def test_critic_adapter_registry_rejects_duplicate_role_backend_pair():
    from hisys.agents.dars_panel import CriticAdapterRegistry, FixtureCriticAdapter

    registry = CriticAdapterRegistry()
    registry.register(FixtureCriticAdapter(critic_role="logical_devil", backend_id="fixture-logical"))

    with pytest.raises(ValueError, match="duplicate critic adapter"):
        registry.register(FixtureCriticAdapter(critic_role="logical_devil", backend_id="fixture-logical"))
```

**Step 2: Verify RED**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py::test_critic_adapter_registry_rejects_duplicate_role_backend_pair -q
```

**Step 3: Minimal GREEN implementation**

If Task 1 did not already reject duplicates, implement duplicate detection in `CriticAdapterRegistry.register`.

**Step 4: Verify GREEN**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_runtime.py -q
```

---

## Task 3: RED/GREEN — fixture adapter outcome replaces backend substring failure heuristic

**Objective:** Remove reliance on `"fail" in backend_id` for failure simulation.

**Files:**

- Modify: `tests/unit/test_dars_critic_panel_adapters.py`
- Modify: `src/hisys/agents/dars_panel.py`

**Step 1: Add failing test**

```python
def test_fixture_critic_adapter_records_declared_outcome_without_keyword_match():
    from hisys.agents.dars_panel import FixtureCriticAdapter

    adapter = FixtureCriticAdapter(
        critic_role="logical_devil",
        backend_id="fixture-logical-outcome-001",
        fixture_outcome="failed",
    )

    assert adapter.fixture_outcome == "failed"
    assert "fail" not in adapter.backend_id
```

**Step 2: Verify RED**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py::test_fixture_critic_adapter_records_declared_outcome_without_keyword_match -q
```

**Expected RED:** Missing `fixture_outcome` support or unsupported typed outcome.

**Step 3: Minimal GREEN implementation**

Ensure `FixtureCriticAdapter.fixture_outcome` exists and validates the literal outcome values. If using dataclasses only, validation can be in `__post_init__`.

**Step 4: Verify GREEN**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py -q
```

---

## Task 4: RED/GREEN — panel runtime isolates declared failed adapter outcome without keyword match

**Objective:** Route `DarsCriticPanelRuntime.run_round` through the registry so failure isolation comes from adapter outcome, not backend naming.

**Files:**

- Modify: `tests/unit/test_dars_critic_panel_adapters.py`
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
    return str(candidate.relative_to(tmp_path)), [str(evidence.relative_to(tmp_path))], str(rubric.relative_to(tmp_path))


def test_panel_runtime_isolates_failed_adapter_outcome_without_keyword_match(tmp_path: Path):
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
            backend_id="fixture-logical-outcome-001",
            fixture_outcome="failed",
        )
    )
    registry.register(
        FixtureCriticAdapter(
            critic_role="evidence_governance_devil",
            backend_id="fixture-evidence-outcome-001",
            fixture_outcome="completed",
        )
    )
    config = DarsCriticPanelConfig(
        panel_id="PANEL-DARS-CP-EXT-1",
        critics=[
            DarsCriticRoleConfig(
                critic_id="logical-devil",
                critic_role="logical_devil",
                backend_id="fixture-logical-outcome-001",
                rubric_ref=rubric_ref,
                critique_dimensions=["logical_validity"],
            ),
            DarsCriticRoleConfig(
                critic_id="evidence-devil",
                critic_role="evidence_governance_devil",
                backend_id="fixture-evidence-outcome-001",
                rubric_ref=rubric_ref,
                critique_dimensions=["source_quality"],
            ),
        ],
    )

    result = DarsCriticPanelRuntime(instance=InstanceRoot(tmp_path), adapter_registry=registry).run_round(
        yyyymmdd="20260519",
        request_id="REQ-DARS-CP-EXT-FAIL",
        candidate_ref=candidate_ref,
        evidence_refs=evidence_refs,
        panel_config=config,
    )

    statuses = [task.status for task in result.task_results]
    assert statuses == ["failed", "completed"]
    assert len(result.critique_refs) == 1
```

**Step 2: Verify RED**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py::test_panel_runtime_isolates_failed_adapter_outcome_without_keyword_match -q
```

**Expected RED:** `DarsCriticPanelRuntime.__init__` does not accept `adapter_registry`, or runtime still ignores adapter outcome.

**Step 3: Minimal GREEN implementation**

Modify `DarsCriticPanelRuntime`:

- `__init__(self, *, instance: InstanceRoot, adapter_registry: CriticAdapterRegistry | None = None)`
- store `self.adapter_registry = adapter_registry or CriticAdapterRegistry.with_default_fixture_policy()`.
- add a default registry factory that preserves existing test behavior:
  - `fixture-logical` -> completed
  - `fixture-evidence` -> completed
  - `fixture-failing-critic` -> failed
  - optionally unknown `fixture-*`/`loopback-*` -> completed via a fallback adapter, if needed to preserve existing permissive fixture behavior.
- replace `_is_fixture_failure(critic.backend_id)` in `run_round` with adapter resolution and `adapter.fixture_outcome`.
- keep external/non-fixture without approval blocked.

**Step 4: Verify GREEN**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_runtime.py -q
```

---

## Task 5: Refactor only after GREEN

**Objective:** Remove dead heuristic constants and keep exports stable.

**Files:**

- Modify: `src/hisys/agents/dars_panel.py`

**Steps:**

1. Remove `FAILURE_BACKEND_MARKER` if no longer used.
2. Remove `_is_fixture_failure` if no longer used.
3. Keep `EXTERNAL_BACKEND_PREFIX` only if the registry still uses it for default external classification; otherwise replace with adapter class checks.
4. Add new exported symbols to `__all__`:
   - `BackendDispatchOutcome`
   - `CriticAdapterRegistry`
   - `FixtureCriticAdapter`
5. Do not change JSON artifact shapes except where tests explicitly require no heuristic failure.

**Verification:**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_runtime.py -q
```

---

## Task 6: Update traceability/reflection for M-CP-EXT-1

**Objective:** Record the completed implementation in durable project docs.

**Files:**

- Modify: `docs/traceability/dars-critic-panel-runtime-traceability.md`
- Modify: `docs/traceability/README.md` if it has an implemented-increments table for DARS panel work.
- Modify: `ralph.md` Reflection Log.

**Required content:**

- State M-CP-EXT-1 implemented `CriticAdapterRegistry` + `FixtureCriticAdapter` and removed failure-substring reliance.
- Link tests:
  - `tests/unit/test_dars_critic_panel_adapters.py`
  - existing `tests/unit/test_dars_critic_panel_runtime.py`
- Preserve boundary statement: no live DARS dispatch, no credential use, no mutation authority, no external calls.
- Record RED and GREEN commands exactly.

---

## Task 7: Quality gate and local commit

**Objective:** Validate the increment and commit only if the tree is coherent.

**Commands:**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_runtime.py -q
PYTHONPATH=src:. pytest tests/unit/test_dars_runtime.py tests/unit/test_dars_config.py tests/unit/test_dars_dispatch.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
git status --short --branch
```

**Expected:**

- New adapter suite passes.
- Existing panel suite remains `9 passed`.
- Adjacent DARS suites pass.
- Traceability and secret scans pass.
- `git diff --check` has no output.

**Commit:**

```bash
git add src/hisys/agents/dars_panel.py \
  tests/unit/test_dars_critic_panel_adapters.py \
  docs/traceability/dars-critic-panel-runtime-traceability.md \
  docs/traceability/README.md \
  ralph.md

git commit -m "feat: add DARS critic adapter registry"
```

**Post-commit verification:**

```bash
git status --short --branch
git log --oneline -1
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py -q
```

---

## Stop conditions

Stop before implementation if any of the following occurs:

- Current focused panel suite is not GREEN before writing the first new RED test.
- Any proposed test requires live network, browser, credential, or external DARS service access.
- The implementation needs to break `tests/unit/test_dars_critic_panel_runtime.py` public API expectations.
- The adapter registry design requires a package split that would also require CLI/import migration. Record that as a new plan instead of expanding M-CP-EXT-1.
- Traceability anchors are missing or contradictory.

## Next action command

If proceeding with implementation, start with Task 0 and then Task 1 RED:

```bash
cd /home/cbchoi/workspaces/develop/repos/hisys
git status --short --branch
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_runtime.py -q
```
