# DARS Critic Panel M-CP-EXT-5 Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for every code-bearing task. This plan is the `MB-DARS-CP-EXT5-T001` document-RED/Prepare artifact. It authorizes only local RED/GREEN work for a deterministic clock-injection seam on `DarsCriticPanelRuntime`.

**Goal:** Implement `M-CP-EXT-5` from `docs/plans/dars-critic-panel-platform-runtime-next.md`: introduce a deterministic clock injection point on `DarsCriticPanelRuntime` so that `ExecutionBoundaryRecord.started_at` / `completed_at` (and any other wall-clock-derived field added later) can be pinned in tests, enabling byte-identical assertion of round outputs across invocations without changing the production wall-clock default.

**Architecture:** Modify only `DarsCriticPanelRuntime.__init__` and `DarsCriticPanelRuntime.run_round` in `src/hisys/agents/dars_panel.py`. Add an optional `clock: Callable[[], datetime] | None = None` constructor parameter that defaults to a wall-clock UTC `datetime.now(timezone.utc)` lambda. Replace the existing `timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()...` line in `run_round` with `timestamp = _format_iso_timestamp(self._clock())`. No new module, no new CLI, no schema change, no parallel execution change.

**Tech Stack:** Python 3.11, `Callable`, `datetime`, pytest. No new runtime dependency.

**Context Packet:** Required source handles are `docs/plans/dars-critic-panel-platform-runtime-next.md`, `docs/plans/dars-critic-panel-mcp-ext-4-implementation-tasks.md`, `docs/traceability/dars-critic-panel-runtime-traceability.md`, `src/hisys/agents/dars_panel.py`, `tests/unit/test_dars_critic_panel_runtime.py`, `tests/unit/test_dars_critic_panel_adapters.py`, `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`, and `tests/unit/test_dars_critic_panel_execution_graph_plan.py`. Validation handles are the focused panel regression, `scripts/validate_traceability.py`, `scripts/scan_secrets.py`, and `git diff --check`.

**Boundary Record:** Local fixture-only code/tests/docs mutation and local commit are allowed after validation. Remote push is not authorized by this plan. Live DARS dispatch, external adapter activation, browser/network calls, credential resolution, publication, destructive Git, CLI activation, and actual bounded-parallel execution are out of scope. The advisory-only invariants from M-CP-EXT-1/2/3/4 remain mandatory.

---

## Accepted decisions

1. **Constructor injection over per-call argument:** add the optional clock to `DarsCriticPanelRuntime.__init__` (the same pattern as `adapter_registry`). Per-call clock arguments would couple every caller to clock semantics; constructor injection keeps `run_round` signature stable.
2. **Default behavior unchanged:** when no clock is supplied, `_clock = lambda: datetime.now(timezone.utc)`. The existing production wall-clock semantics persist; only tests that supply a fixed clock get deterministic timestamps.
3. **Clock returns a `datetime`, not a string:** the seam is `Callable[[], datetime]`. The runtime then formats the result through a single private helper that applies `.replace(microsecond=0).isoformat().replace("+00:00", "Z")`. This keeps the timezone normalization and second-truncation logic in one place and is identical to the existing format.
4. **Naïve datetime rejected at format time:** if a caller-supplied clock returns a naïve `datetime` (no `tzinfo`), `_format_iso_timestamp` raises `ValueError("clock must return timezone-aware datetime")`. The default wall-clock lambda always returns a timezone-aware UTC datetime, so production callers are unaffected.
5. **Single timestamp per round preserved:** `run_round` continues to call the clock exactly once at the top of the round; per-task `started_at == completed_at` is preserved (real per-task timing remains a deferred increment). The injection seam makes it possible to assert byte-identical record JSON across calls in tests, which the M-CP-EXT-2 reflection explicitly pinned as the natural next gate.
6. **No new artifact schema field:** `ExecutionBoundaryRecord` is unchanged. No new field on `DarsRoundResult`, `DarsTaskResult`, or critique/synthesis/round-trace records.
7. **Scope excludes per-task timing:** real per-task timing (distinct `started_at` and `completed_at` per critic execution) is not in scope; that would require a serial-execution-loop refactor and is deferred. The injection seam keeps that future increment cheap because the clock is already a per-runtime dependency.

---

## Task 0: Reconstruct baseline before editing

**Objective:** Confirm the repository state and current GREEN baseline before writing the RED test.

**Files:** none.

**Commands:**

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
```

**Expected:**

- Branch is `dars`.
- Existing focused suites report `39 passed` (post-M-CP-EXT-4).
- Working tree is clean (or contains only intentional changes for this increment).

---

## Task 1: RED/GREEN — deterministic clock yields byte-identical boundary record across runs

**Objective:** Pin the new behavior with a failing test, then add the constructor clock seam and route the timestamp through it.

**Files:**

- Modify: `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`
- Modify: `src/hisys/agents/dars_panel.py`

**Step 1: Write failing test**

Add to `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`:

```python
def test_panel_runtime_with_injected_clock_yields_byte_identical_boundary_records(tmp_path: Path):
    """M-CP-EXT-5: a fixed clock makes run_round output byte-identical across invocations."""

    from datetime import datetime, timezone

    from hisys.agents.dars_panel import (
        CriticAdapterRegistry,
        DarsCriticPanelConfig,
        DarsCriticPanelRuntime,
        DarsCriticRoleConfig,
        FixtureCriticAdapter,
    )

    fixed_moment = datetime(2026, 5, 20, 12, 0, 0, tzinfo=timezone.utc)
    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    registry = CriticAdapterRegistry()
    registry.register(
        FixtureCriticAdapter(
            critic_role="logical_devil",
            backend_id="fixture-logical-clock-001",
            fixture_outcome="completed",
        )
    )
    config = DarsCriticPanelConfig(
        panel_id="PANEL-DARS-CP-EXT-5",
        critics=[
            DarsCriticRoleConfig(
                critic_id="logical-devil",
                critic_role="logical_devil",
                backend_id="fixture-logical-clock-001",
                rubric_ref=rubric_ref,
                critique_dimensions=["logical_validity"],
            ),
        ],
    )

    runtime = DarsCriticPanelRuntime(
        instance=InstanceRoot(tmp_path),
        adapter_registry=registry,
        clock=lambda: fixed_moment,
    )
    first = runtime.run_round(
        yyyymmdd="20260520",
        request_id="REQ-DARS-CP-EXT-5-A",
        candidate_ref=candidate_ref,
        evidence_refs=evidence_refs,
        panel_config=config,
    )
    second = runtime.run_round(
        yyyymmdd="20260520",
        request_id="REQ-DARS-CP-EXT-5-B",
        candidate_ref=candidate_ref,
        evidence_refs=evidence_refs,
        panel_config=config,
    )

    first_boundary = json.loads((tmp_path / first.execution_boundary_refs[0]).read_text(encoding="utf-8"))
    second_boundary = json.loads((tmp_path / second.execution_boundary_refs[0]).read_text(encoding="utf-8"))

    assert first_boundary["started_at"] == "2026-05-20T12:00:00Z"
    assert first_boundary["completed_at"] == "2026-05-20T12:00:00Z"
    assert second_boundary["started_at"] == "2026-05-20T12:00:00Z"
    assert second_boundary["completed_at"] == "2026-05-20T12:00:00Z"


def test_panel_runtime_rejects_naive_clock(tmp_path: Path):
    """M-CP-EXT-5: a naive clock (no tzinfo) must raise rather than persist ambiguous timestamps."""

    from datetime import datetime

    from hisys.agents.dars_panel import (
        DarsCriticPanelConfig,
        DarsCriticPanelRuntime,
        DarsCriticRoleConfig,
    )

    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    config = DarsCriticPanelConfig(
        panel_id="PANEL-DARS-CP-EXT-5-NAIVE",
        critics=[
            DarsCriticRoleConfig(
                critic_id="logical-devil",
                critic_role="logical_devil",
                backend_id="fixture-logical-clock-naive",
                rubric_ref=rubric_ref,
                critique_dimensions=["logical_validity"],
            ),
        ],
    )

    runtime = DarsCriticPanelRuntime(
        instance=InstanceRoot(tmp_path),
        clock=lambda: datetime(2026, 5, 20, 12, 0, 0),  # naive
    )

    with pytest.raises(ValueError, match="timezone-aware"):
        runtime.run_round(
            yyyymmdd="20260520",
            request_id="REQ-DARS-CP-EXT-5-NAIVE",
            candidate_ref=candidate_ref,
            evidence_refs=evidence_refs,
            panel_config=config,
        )
```

The shared helper `_candidate_fixture` already exists in this test module; reuse it.

**Step 2: Verify RED**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_tool_execution_runtime.py::test_panel_runtime_with_injected_clock_yields_byte_identical_boundary_records tests/unit/test_dars_critic_panel_tool_execution_runtime.py::test_panel_runtime_rejects_naive_clock -q
```

**Expected RED:** `TypeError: DarsCriticPanelRuntime.__init__() got an unexpected keyword argument 'clock'` from both tests.

**Step 3: Minimal GREEN implementation**

In `src/hisys/agents/dars_panel.py`:

1. Add `from collections.abc import Callable` to the imports (or extend the existing `typing` imports).

2. Add a private helper near the top of the module (after the slug-validation helpers):

```python
def _format_iso_timestamp(moment: datetime) -> str:
    if moment.tzinfo is None:
        raise ValueError("clock must return timezone-aware datetime")
    return moment.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
```

3. Extend `DarsCriticPanelRuntime.__init__`:

```python
    def __init__(
        self,
        *,
        instance: InstanceRoot,
        adapter_registry: CriticAdapterRegistry | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.instance = instance
        self.adapter_registry = adapter_registry or _DefaultFixturePolicy()
        self._clock: Callable[[], datetime] = clock or (lambda: datetime.now(timezone.utc))
```

4. In `DarsCriticPanelRuntime.run_round`, replace:

```python
        timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
            "+00:00", "Z"
        )
```

with:

```python
        timestamp = _format_iso_timestamp(self._clock())
```

**Step 4: Verify GREEN**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_tool_execution_runtime.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
```

**Expected GREEN:** both new tests pass; existing focused panel + adapters + tool-execution + graph suites remain GREEN.

---

## Task 2: Documentation and traceability update

**Objective:** Record M-CP-EXT-5 in the DARS critic panel RTM, the traceability summary README, and the Ralph reflection log.

**Files:**

- Modify: `docs/traceability/dars-critic-panel-runtime-traceability.md` (bump version to `0.6.0`, dated `2026-05-20`; add the new pytest anchors to the HISYS-FR-DARS-CP-003 and HISYS-NFR-DARS-CP-002 rows; add a new `M-CP-EXT-5 — Deterministic clock injection seam (2026-05-20)` section).
- Modify: `docs/traceability/README.md` (add an `M-CP-EXT-5` row in the Implemented-increments table after the `M-CP-EXT-4` row, enumerating the constructor `clock` parameter, the `_format_iso_timestamp` helper, the naive-datetime rejection, and the gate command).
- Modify: `ralph.md` (append a new Reflection Log entry for 2026-05-20 covering Prepare/RED/GREEN/Refactor/Gate, controlled anchors, RED command + observed failure, GREEN command + pass result, quality gate result, potential issues / open items, success likelihood, continue decision, and a resume checkpoint).

**Validation:**

```bash
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

---

## Task 3: Full quality gate and local commit

**Objective:** Validate the complete M-CP-EXT-5 increment and commit locally.

**Commands:**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:**

- New clock-seam tests pass alongside the existing focused panel + adapters + tool-execution + graph suites (41 passed).
- Traceability validator passes.
- Secret scan reports `hit_count=0`.
- Whitespace diff check is clean.

**Commit:**

```bash
git add \
  src/hisys/agents/dars_panel.py \
  tests/unit/test_dars_critic_panel_tool_execution_runtime.py \
  docs/plans/dars-critic-panel-mcp-ext-5-implementation-tasks.md \
  docs/traceability/dars-critic-panel-runtime-traceability.md \
  docs/traceability/README.md \
  ralph.md

git commit -m "feat: add deterministic clock seam to DARS critic panel"
```

**Remote push:** not authorized by this plan; remote push remains human-gated and out of scope.

---

## Stop conditions

Stop and report before proceeding if any of the following occurs:

- The implementation would require changing the public shape of `DarsTaskResult`, `ExecutionBoundaryRecord`, or `DarsRoundResult` beyond adding the constructor parameter.
- Existing 39 focused panel tests fail for a reason not directly tied to the intentional clock seam.
- Any implementation would require live external dispatch, process spawning, thread pools, `asyncio`, browser/network libraries, or credential access.
- Traceability validator or secret scan fails.

## Next increment candidates after M-CP-EXT-5

- M-CP-EXT-6: read-only `hisys run-dars-panel` CLI consuming `ExecutionGraphPlan` after a separate approval gate.
- Adapter-class literal extension: `adapter_class="unresolved"` (separate Prepare cycle).
- Per-task `started_at` / `completed_at` timing distinct from a single round-level clock tick (would require a serial-loop refactor; the M-CP-EXT-5 seam keeps this future increment cheap).
- Future activation: actual bounded-parallel execution, only after a separate governance/approval increment.
