# DARS Critic Panel M-CP-EXT-8 Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for every code-bearing task. This plan is the `MB-DARS-CP-EXT8-T001` document-RED/Prepare artifact. It authorizes only local RED/GREEN work for per-task distinct `started_at`/`completed_at` timing inside `DarsCriticPanelRuntime.run_round`, reusing the existing M-CP-EXT-5 clock injection seam.

**Goal:** Implement `M-CP-EXT-8`: replace the single round-level clock read in `DarsCriticPanelRuntime.run_round` with two clock reads per critic task (one before dispatch, one after) so each `ExecutionBoundaryRecord` carries a distinct `started_at` and `completed_at`. Preserve the existing M-CP-EXT-5 clock injection seam (`self._clock`), the `_format_iso_timestamp` helper, the naive-datetime rejection invariant, and serial execution. No new module, no new CLI, no schema field added or removed, no parallel execution change.

**Architecture:** Modify only `DarsCriticPanelRuntime.run_round` in `src/hisys/agents/dars_panel.py`. The runtime currently reads `timestamp = _format_iso_timestamp(self._clock())` once before the critic loop and uses the same value for every per-task `started_at`/`completed_at`. The new code reads the clock twice per task — `task_started_at = _format_iso_timestamp(self._clock())` before adapter resolution and dispatch decision logic, and `task_completed_at = _format_iso_timestamp(self._clock())` immediately before constructing the `ExecutionBoundaryRecord` — and threads those distinct values into the record. Execution remains serial, the clock is still callable-injected, and the synthesis/round-trace artifacts are unchanged.

**Tech Stack:** Python 3.11, `datetime`, pytest. No new runtime dependency.

**Context Packet:** Required source handles are `docs/plans/dars-critic-panel-platform-runtime-next.md`, `docs/plans/dars-critic-panel-mcp-ext-5-implementation-tasks.md`, `docs/plans/dars-critic-panel-mcp-ext-6-implementation-tasks.md`, `docs/traceability/dars-critic-panel-runtime-traceability.md`, `src/hisys/agents/dars_panel.py`, `src/hisys/agents/dars_panel_graph.py`, `tests/unit/test_dars_critic_panel_runtime.py`, `tests/unit/test_dars_critic_panel_adapters.py`, `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`, `tests/unit/test_dars_critic_panel_execution_graph_plan.py`, and `tests/unit/test_dars_critic_panel_cli.py`. Validation handles are the focused panel + CLI regression, `scripts/validate_traceability.py`, `scripts/scan_secrets.py`, and `git diff --check`.

**Boundary Record:** Local fixture-only code/tests/docs mutation and local commit are allowed after validation. Remote push is not authorized by this plan. Live DARS dispatch, external adapter activation, browser/network calls, credential resolution, publication, destructive Git, CLI surface expansion, parallel execution activation, and any operator approval of downstream decisions are out of scope. The advisory-only invariants from M-CP-EXT-1/2/3/4/5/6/7 remain mandatory.

---

## Accepted decisions

1. **Two clock reads per task, not one:** the existing round-level single clock read is replaced by two per-task reads — `task_started_at` immediately before the dispatch-decision logic for each critic task, and `task_completed_at` immediately before the `ExecutionBoundaryRecord` is constructed for that same task. The recorded values are byte-identical only for tests that inject a constant clock; production callers (wall-clock lambda) see naturally increasing values.
2. **No new clock seam:** the M-CP-EXT-5 seam (`self._clock: Callable[[], datetime]`) and `_format_iso_timestamp` helper are reused unchanged. Naive datetimes continue to raise `ValueError("clock must return timezone-aware datetime")`. No constructor signature change.
3. **No schema field added:** `ExecutionBoundaryRecord` already exposes `started_at` and `completed_at` as separate fields; the M-CP-EXT-2 contract reserved that schema shape and M-CP-EXT-5 documented "the natural next gate" as making them distinct. No new field added; no field renamed; no field removed.
4. **Serial execution preserved:** the runtime still iterates `zip(plan.critic_tasks, panel_config.critics, strict=True)` serially. `execution_mode` continues to report `serial` or `bounded_parallel` from `max_parallel_critics` as a label only; no worker, thread, async task, or subprocess is spawned.
5. **Default-clock invariant preserved:** when no `clock` is injected, `self._clock = lambda: datetime.now(timezone.utc)`. Two consecutive default-clock reads within a sub-millisecond window may return the same `_format_iso_timestamp` value (microseconds are truncated); tests must not assert default-clock distinctness. Distinctness is tested only against an injected counter clock.
6. **Counter-clock test pattern:** the RED test injects a tiny stateful clock — for example, a generator or a closure over a `nonlocal` `datetime` counter that advances by one second each call — and asserts that the persisted `ExecutionBoundaryRecord` JSON shows `started_at != completed_at` for at least one critic task. For multi-critic configs the test additionally asserts that consecutive tasks observe distinct `started_at` values.
7. **Naive-datetime rejection unchanged:** the per-task clock read still flows through `_format_iso_timestamp`, so a naive `datetime` returned from the second clock read raises `ValueError` from `run_round` exactly like the M-CP-EXT-5 regression test expects.
8. **Critique/synthesis/round-trace artifacts unchanged:** only the `ExecutionBoundaryRecord` `started_at`/`completed_at` fields observe the new behavior. The critique JSON, synthesis JSON, and round-trace JSON do not currently embed a timestamp; this increment does not change that.
9. **CLI surface unchanged:** the `hisys run-dars-panel` CLI (M-CP-EXT-6) inherits the new behavior automatically because it constructs `DarsCriticPanelRuntime(instance=...)` without an explicit clock, so production wall-clock timestamps are used; no CLI argument is added.

---

## Task 0: Reconstruct baseline before editing

**Objective:** Confirm repository state and current GREEN baseline before writing the RED test.

**Files:** none.

**Commands:**

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
```

**Expected:**

- Branch is `dars`.
- Existing focused suites report `45 passed` (post-M-CP-EXT-6).
- Working tree is clean or contains only intentional changes for this increment.

---

## Task 1: RED/GREEN — per-task distinct started_at/completed_at under an injected counter clock

**Objective:** Pin the per-task distinct timing behavior with a failing test, then move the clock reads into the loop body.

**Files:**

- Modify: `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`
- Modify: `src/hisys/agents/dars_panel.py`

**Step 1: Write failing test**

Add to `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`:

```python
def test_panel_runtime_records_distinct_started_and_completed_per_task(tmp_path: Path):
    """M-CP-EXT-8: per-task distinct started_at/completed_at under an injected counter clock."""

    import json as _json
    from datetime import datetime, timedelta, timezone

    from hisys.agents.dars_panel import (
        DarsCriticPanelConfig,
        DarsCriticPanelRuntime,
        DarsCriticRoleConfig,
    )
    from hisys.config.instance import InstanceRoot

    base = datetime(2026, 5, 20, 12, 0, 0, tzinfo=timezone.utc)
    tick = {"n": 0}

    def counter_clock() -> datetime:
        moment = base + timedelta(seconds=tick["n"])
        tick["n"] += 1
        return moment

    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    runtime = DarsCriticPanelRuntime(instance=InstanceRoot(tmp_path), clock=counter_clock)
    config = DarsCriticPanelConfig(
        panel_id="PANEL-EXT-8",
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
        request_id="REQ-EXT-8",
        candidate_ref=candidate_ref,
        evidence_refs=evidence_refs,
        panel_config=config,
    )

    boundary_records = [
        _json.loads((tmp_path / ref).read_text(encoding="utf-8"))
        for ref in result.execution_boundary_refs
    ]
    starts = [record["started_at"] for record in boundary_records]
    completes = [record["completed_at"] for record in boundary_records]
    for record in boundary_records:
        assert record["started_at"] != record["completed_at"], record
    assert len(set(starts)) == len(starts)
    assert len(set(completes)) == len(completes)
```

**Step 2: Verify RED**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_tool_execution_runtime.py::test_panel_runtime_records_distinct_started_and_completed_per_task -q
```

**Expected RED:** the assertion `record["started_at"] != record["completed_at"]` fails because the existing round-level single clock read populates both fields with the same string.

**Step 3: Minimal GREEN implementation**

In `src/hisys/agents/dars_panel.py`:

1. Remove the single pre-loop `timestamp = _format_iso_timestamp(self._clock())` read from `DarsCriticPanelRuntime.run_round`.
2. Inside the `for plan_task, critic in zip(plan.critic_tasks, panel_config.critics, strict=True):` loop, add `task_started_at = _format_iso_timestamp(self._clock())` immediately at the top of the loop body (before any branch).
3. Immediately before the `boundary_record = ExecutionBoundaryRecord(...)` construction, add `task_completed_at = _format_iso_timestamp(self._clock())`.
4. Replace the existing `started_at=timestamp, completed_at=timestamp` keyword arguments with `started_at=task_started_at, completed_at=task_completed_at`.
5. Update the comment that documents the timestamp seam to describe the new per-task reads.

**Step 4: Verify GREEN**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_tool_execution_runtime.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
```

**Expected GREEN:** new per-task timing test passes; the M-CP-EXT-5 byte-identical-under-fixed-clock regression continues to pass (because both reads of a constant clock return the same value); the M-CP-EXT-5 naive-datetime rejection regression continues to pass (both reads still flow through `_format_iso_timestamp`).

---

## Task 2: Documentation and traceability update

**Objective:** Record M-CP-EXT-8 in the DARS critic panel RTM, traceability summary README, and Ralph reflection log.

**Files:**

- Modify: `docs/traceability/dars-critic-panel-runtime-traceability.md` (bump version to `0.9.0`, dated `2026-05-20`; add the new pytest anchor to the HISYS-FR-DARS-CP-003 and HISYS-FR-DARS-CP-004 rows; add a new `M-CP-EXT-8 — Per-task distinct started_at/completed_at (2026-05-20)` section).
- Modify: `docs/traceability/README.md` (add an `M-CP-EXT-8` row enumerating the per-task clock read pattern, the seam reuse, the unchanged schema field set, the gate command, and the deferred items).
- Modify: `ralph.md` (append a new Reflection Log entry covering Prepare/RED/GREEN/Refactor/Gate, controlled anchors, RED command + observed failure, GREEN command + pass result, quality gate result, potential issues / open items, success likelihood, continue decision, and a resume checkpoint).

**Validation:**

```bash
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

---

## Task 3: Full quality gate and local commit

**Objective:** Validate the complete M-CP-EXT-8 implementation and commit locally.

**Commands:**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:**

- All focused suites pass alongside the new per-task timing test (`46 passed` = `45 baseline + 1 new`).
- Traceability validator passes.
- Secret scan reports `hit_count=0`.
- Whitespace diff check is clean.

**Commit:**

```bash
git add \
  src/hisys/agents/dars_panel.py \
  tests/unit/test_dars_critic_panel_tool_execution_runtime.py \
  docs/plans/dars-critic-panel-mcp-ext-8-implementation-tasks.md \
  docs/traceability/dars-critic-panel-runtime-traceability.md \
  docs/traceability/README.md \
  ralph.md

git commit -m "feat: record per-task DARS boundary timing"
```

**Remote push:** not authorized by this plan; remote push remains human-gated and out of scope.

---

## Stop conditions

Stop and report before proceeding if any of the following occurs:

- The implementation requires changing the constructor signature, adding a new clock seam, or introducing a per-task clock argument.
- The implementation requires adding parallel execution (workers, threads, async tasks, subprocesses) or changing the serial execution invariant.
- The implementation requires altering the `ExecutionBoundaryRecord` schema (field add/remove/rename) or the locked safety envelope.
- Existing focused panel/CLI/graph/adapter tests fail for a reason not directly tied to the new per-task timing.
- Traceability validator, secret scan, or `git diff --check` fails.

## Next increment candidates after M-CP-EXT-8

- Package split of `src/hisys/agents/dars_panel.py` (now ~830 lines) into adapter/runtime/record modules after a behavior-preserving plan.
- Optional per-task `duration_ms` field derived from `started_at`/`completed_at`, only after a separate schema and traceability increment.
- Future bounded-parallel execution activation, only after a separate governance/approval increment and fixture scheduler harness.
