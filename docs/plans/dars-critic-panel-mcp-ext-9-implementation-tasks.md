# DARS Critic Panel M-CP-EXT-9 Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for every code-bearing task. This plan is the document-RED/Prepare artifact for per-task `duration_ms` on `ExecutionBoundaryRecord`. It authorizes only local RED/GREEN work after this Prepare checkpoint is committed.

**Goal:** Implement `M-CP-EXT-9`: add a derived per-task `duration_ms` field to persisted `ExecutionBoundaryRecord` JSON, computed from the existing per-task `started_at` and `completed_at` timestamps introduced by M-CP-EXT-8.

**Architecture:** Extend the `ExecutionBoundaryRecord` dataclass in `src/hisys/agents/dars_panel.py` with `duration_ms: int`, derive it in `DarsCriticPanelRuntime.run_round` from the two timezone-aware clock readings before formatting, and persist it through the existing `write_execution_boundary_record(... asdict(record) ...)` path. Keep serial execution, the existing clock seam, slug validation, safety-envelope defaults, and CLI behavior unchanged.

**Tech Stack:** Python 3.11, `datetime`, dataclasses, pytest. No new runtime dependency.

**Context Packet:** Required source handles are `src/hisys/agents/dars_panel.py`, `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`, `tests/unit/test_dars_critic_panel_cli.py`, `docs/plans/dars-critic-panel-mcp-ext-8-implementation-tasks.md`, `docs/traceability/dars-critic-panel-runtime-traceability.md`, `docs/traceability/README.md`, and `ralph.md`. Validation handles are the focused tool-execution suite, combined CLI/panel/adapters/tool-execution/graph regression, `scripts/validate_traceability.py`, `scripts/scan_secrets.py`, and `git diff --check`.

**Boundary Record:** Local fixture-only code/tests/docs mutation and local commit are allowed after validation. Remote push is not authorized. Live DARS dispatch, external adapter activation, browser/network calls, credential resolution, publication, destructive Git, CLI argument expansion, parallel execution activation, and downstream action authorization are out of scope. This increment changes one persisted advisory record schema field and must update traceability before commit.

---

## Accepted decisions

1. **Add `duration_ms` as an integer field:** Persist `duration_ms` in every `ExecutionBoundaryRecord` JSON object. The unit is milliseconds. The field is derived from runtime clock readings, not caller input.
2. **Compute from datetimes before formatting:** In `run_round`, keep the task start and completion clock readings as timezone-aware `datetime` values, compute `duration_ms = max(0, int((completed - started).total_seconds() * 1000))`, then format `started_at` and `completed_at` with `_format_iso_timestamp`. This avoids parsing the truncated string timestamps.
3. **Keep non-negative duration:** Clamp negative durations to `0` to preserve advisory record stability if an injected or system clock moves backward. A separate test pins the non-negative property for a backward counter clock.
4. **Preserve timestamp string behavior:** `started_at` and `completed_at` stay second-truncated UTC `...Z` strings via `_format_iso_timestamp`. The new field may be non-zero even when formatted timestamps are equal due to truncation; tests must use injected second-level or millisecond-level clocks intentionally.
5. **No CLI change:** `hisys run-dars-panel` inherits the new persisted field through the runtime. No CLI flag, output contract expansion, or config schema change is required in this increment unless a failing test proves the current JSON summary depends on explicit field enumeration.
6. **No parallel execution:** The runtime remains serial. `duration_ms` describes the advisory boundary interval for one critic task, not wall-clock parallel scheduling.
7. **Safety envelope unchanged:** `external_call_made`, `mutation_performed`, `action_authorized`, `advisory_only`, and `requires_human_review` invariants remain locked exactly as before.
8. **Traceability required:** Because this is a persisted JSON schema addition, update RTM/traceability docs and Ralph reflection in the same implementation increment.

---

## Task 0: Reconstruct baseline before editing

**Objective:** Confirm current repository state and current GREEN baseline before writing the RED test.

**Files:** none.

**Commands:**

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
```

**Expected:**

- Branch is `dars`.
- HEAD is at or after `aa707ca feat: record per-task DARS boundary timing`.
- Existing focused suites report `46 passed`.
- Working tree is clean or contains only intentional M-CP-EXT-9 Prepare changes.

---

## Task 1: RED/GREEN — persist derived per-task duration_ms

**Objective:** Pin the new persisted schema field with a failing test, then derive it from the existing per-task clock readings.

**Files:**

- Modify: `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`
- Modify: `src/hisys/agents/dars_panel.py`

**Step 1: Write failing test**

Add to `tests/unit/test_dars_critic_panel_tool_execution_runtime.py` near the M-CP-EXT-8 timing test:

```python
def test_panel_runtime_records_duration_ms_per_task(tmp_path: Path):
    """M-CP-EXT-9: duration_ms is derived from per-task start/end readings."""

    import json as _json
    from datetime import datetime, timedelta, timezone

    from hisys.agents.dars_panel import (
        DarsCriticPanelConfig,
        DarsCriticPanelRuntime,
        DarsCriticRoleConfig,
    )
    from hisys.config.instance import InstanceRoot

    base = datetime(2026, 5, 20, 12, 0, 0, tzinfo=timezone.utc)
    offsets = iter([
        timedelta(seconds=0),
        timedelta(milliseconds=250),
        timedelta(seconds=1),
        timedelta(seconds=1, milliseconds=750),
    ])

    def counter_clock() -> datetime:
        return base + next(offsets)

    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    runtime = DarsCriticPanelRuntime(instance=InstanceRoot(tmp_path), clock=counter_clock)
    config = DarsCriticPanelConfig(
        panel_id="PANEL-EXT-9",
        critics=[
            DarsCriticRoleConfig(
                critic_id="logical-devil",
                critic_role="logical_devil",
                backend_id="fixture-logical-001",
                rubric_ref=rubric_ref,
                critique_dimensions=["logical_validity"],
            ),
            DarsCriticRoleConfig(
                critic_id="evidence-detective",
                critic_role="evidence_detective",
                backend_id="fixture-evidence-001",
                rubric_ref=rubric_ref,
                critique_dimensions=["evidence_grounding"],
            ),
        ],
    )

    result = runtime.run_round(
        yyyymmdd="20260520",
        request_id="REQ-EXT-9",
        candidate_ref=candidate_ref,
        evidence_refs=evidence_refs,
        panel_config=config,
    )

    boundary_records = [
        _json.loads((tmp_path / ref).read_text(encoding="utf-8"))
        for ref in result.execution_boundary_refs
    ]
    assert [record["duration_ms"] for record in boundary_records] == [250, 750]
    assert all(isinstance(record["duration_ms"], int) for record in boundary_records)
```

**Step 2: Verify RED**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_tool_execution_runtime.py::test_panel_runtime_records_duration_ms_per_task -q
```

**Expected RED:** `KeyError: 'duration_ms'` or equivalent assertion failure because persisted boundary records do not contain the field yet.

**Step 3: Minimal GREEN implementation**

In `src/hisys/agents/dars_panel.py`:

1. Add `duration_ms: int` to `ExecutionBoundaryRecord` immediately after `completed_at: str`.
2. In `DarsCriticPanelRuntime.run_round`, change the per-task clock reads from immediate formatted strings to raw datetimes:
   - `task_started = self._clock()` at the top of the critic loop.
   - `task_started_at = _format_iso_timestamp(task_started)` after the raw start read.
   - `task_completed = self._clock()` immediately before `ExecutionBoundaryRecord(...)`.
   - `task_completed_at = _format_iso_timestamp(task_completed)`.
   - `task_duration_ms = max(0, int((task_completed.astimezone(timezone.utc) - task_started.astimezone(timezone.utc)).total_seconds() * 1000))`.
3. Pass `duration_ms=task_duration_ms` into `ExecutionBoundaryRecord(...)`.
4. Do not add any CLI flag, process, registry override, or external-dispatch path.

**Step 4: Verify GREEN**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_tool_execution_runtime.py::test_panel_runtime_records_duration_ms_per_task -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_tool_execution_runtime.py -q
```

**Expected GREEN:** the new test passes; existing M-CP-EXT-5 and M-CP-EXT-8 timing tests still pass.

---

## Task 2: RED/GREEN — clamp negative duration to zero

**Objective:** Preserve record stability if the injected clock moves backward.

**Files:**

- Modify: `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`
- Modify only if needed: `src/hisys/agents/dars_panel.py`

**Step 1: Write failing/safety test**

```python
def test_panel_runtime_clamps_negative_duration_ms_to_zero(tmp_path: Path):
    """M-CP-EXT-9: duration_ms remains non-negative if a clock moves backward."""

    import json as _json
    from datetime import datetime, timedelta, timezone

    from hisys.agents.dars_panel import (
        DarsCriticPanelConfig,
        DarsCriticPanelRuntime,
        DarsCriticRoleConfig,
    )
    from hisys.config.instance import InstanceRoot

    base = datetime(2026, 5, 20, 12, 0, 0, tzinfo=timezone.utc)
    offsets = iter([timedelta(seconds=2), timedelta(seconds=1)])

    def backward_clock() -> datetime:
        return base + next(offsets)

    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    runtime = DarsCriticPanelRuntime(instance=InstanceRoot(tmp_path), clock=backward_clock)
    config = DarsCriticPanelConfig(
        panel_id="PANEL-EXT-9-NEGATIVE",
        critics=[
            DarsCriticRoleConfig(
                critic_id="logical-devil",
                critic_role="logical_devil",
                backend_id="fixture-logical-001",
                rubric_ref=rubric_ref,
                critique_dimensions=["logical_validity"],
            )
        ],
    )

    result = runtime.run_round(
        yyyymmdd="20260520",
        request_id="REQ-EXT-9-NEGATIVE",
        candidate_ref=candidate_ref,
        evidence_refs=evidence_refs,
        panel_config=config,
    )

    boundary_record = _json.loads(
        (tmp_path / result.execution_boundary_refs[0]).read_text(encoding="utf-8")
    )
    assert boundary_record["duration_ms"] == 0
```

**Step 2: Verify RED or immediate GREEN intentionally**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_tool_execution_runtime.py::test_panel_runtime_clamps_negative_duration_ms_to_zero -q
```

If Task 1 already used `max(0, ...)`, this test may pass immediately. That is acceptable only because Task 1's accepted minimal implementation already included the non-negative invariant; record it as a safety characterization rather than a separate production-code trigger.

---

## Task 3: Documentation and traceability update

**Objective:** Record the persisted schema field addition and validation anchors.

**Files:**

- Modify: `docs/traceability/dars-critic-panel-runtime-traceability.md`.
  - Bump version to the next local traceability version.
  - Add `duration_ms` to the `ExecutionBoundaryRecord` field contract section.
  - Add pytest anchors for the two M-CP-EXT-9 tests to the HISYS-FR-DARS-CP-003 / HISYS-FR-DARS-CP-004 / HISYS-NFR-DARS-CP-001 rows as appropriate.
  - Add a new `M-CP-EXT-9 — Per-task duration_ms boundary timing (2026-05-20)` section.
- Modify: `docs/traceability/README.md`.
  - Add an `M-CP-EXT-9` row with field addition, derivation rule, non-negative invariant, gate command, and deferred items.
- Modify: `ralph.md`.
  - Append a reflection entry covering RED, GREEN, docs, gate result, open items, and resume checkpoint.

**Validation:**

```bash
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

---

## Task 4: Full quality gate and local commit

**Objective:** Validate the complete M-CP-EXT-9 implementation and commit locally.

**Commands:**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:**

- Combined focused suites pass with the two new M-CP-EXT-9 tests added.
- Traceability validator passes.
- Secret scan reports `hit_count=0`.
- Whitespace diff check is clean.

**Commit:**

```bash
git add \
  src/hisys/agents/dars_panel.py \
  tests/unit/test_dars_critic_panel_tool_execution_runtime.py \
  docs/traceability/dars-critic-panel-runtime-traceability.md \
  docs/traceability/README.md \
  ralph.md

git commit -m "feat: record DARS boundary duration"
```

**Remote push:** not authorized by this plan; remote push remains human-gated and out of scope.

---

## Stop conditions

Stop and report before proceeding if any of the following occurs:

- The implementation requires parsing timestamp strings instead of using raw clock datetimes.
- The implementation requires changing the public CLI argument shape or CLI config schema.
- The implementation requires adding parallel execution, workers, threads, async tasks, subprocesses, or live dispatch.
- The implementation requires external calls, credential resolution, approval authorization, publication, or remote push.
- Existing focused panel/CLI/graph/adapter tests fail for a reason not directly tied to the new duration field.
- Traceability validator, secret scan, or `git diff --check` fails.

## Next increment candidates after M-CP-EXT-9

- Behavior-preserving package split of `src/hisys/agents/dars_panel.py` into adapter/runtime/record modules.
- M20 codebase-domain bridge, after a separate Prepare plan.
- Future bounded-parallel execution activation, only after separate governance/approval and fixture scheduler harness.
