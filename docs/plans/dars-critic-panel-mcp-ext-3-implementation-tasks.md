# DARS Critic Panel M-CP-EXT-3 Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for every code-bearing task. This plan is the `MB-DARS-CP-EXT3-T001` document-RED/Prepare artifact. It authorizes only local RED/GREEN work for a fixture-local execution-graph scheduling primitive after this plan is validated.

**Goal:** Implement `M-CP-EXT-3` from `docs/plans/dars-critic-panel-platform-runtime-next.md`: add a pure `ExecutionGraphPlan` and deterministic ready-set / bounded-parallel chunking primitives while keeping `DarsCriticPanelRuntime.run_round` serial by default.

**Architecture:** Add a sidecar module `src/hisys/agents/dars_panel_graph.py` instead of extending the already-large `src/hisys/agents/dars_panel.py` (784 lines at Prepare time). Re-export graph symbols from `dars_panel.py` for compatibility. The graph primitive is pure and timestamp-free; it does not execute critics, spawn workers, call external services, or activate bounded-parallel runtime execution.

**Tech Stack:** Python 3.11, dataclasses, pytest. No new runtime dependency. No network/browser/CLI/process-spawn dependency.

**Context Packet:** Required source handles are `docs/plans/dars-critic-panel-platform-runtime-next.md`, `docs/milestone-bootstrap/tasks/milestone_tasks_v0.0.2.yaml`, `docs/traceability/dars-critic-panel-runtime-traceability.md`, `src/hisys/agents/dars_panel.py`, `tests/unit/test_dars_critic_panel_runtime.py`, `tests/unit/test_dars_critic_panel_adapters.py`, and `tests/unit/test_dars_critic_panel_tool_execution_runtime.py`. Omit raw large `ralph.md` context during implementation; retrieve only the reflection section when updating the final handoff. Validation handles are the focused panel regression, the new graph suite, `scripts/validate_traceability.py`, `scripts/scan_secrets.py`, and `git diff --check`.

**Boundary Record:** Local fixture-only code/tests/docs mutation and local commit are allowed after validation. Remote push is not authorized by this plan. Live DARS dispatch, external adapter activation, browser/network calls, credential resolution, publication, destructive Git, CLI activation, and actual bounded-parallel execution are out of scope. The advisory-only invariants from M-CP-EXT-1/2 remain mandatory.

---

## Accepted decisions

1. **Package split:** create `src/hisys/agents/dars_panel_graph.py` as a sidecar module. Do not convert `dars_panel.py` into a directory package in this increment. Re-export graph symbols from `dars_panel.py` for compatibility.
2. **Primary import:** tests import graph primitives from `hisys.agents.dars_panel_graph`; one compatibility test imports `ExecutionGraphPlan` from `hisys.agents.dars_panel`.
3. **Ready-set input:** interpret the parent plan's `completed_task_ids` as `terminal_task_ids`. Terminal means `completed`, `failed`, `blocked`, or `skipped`.
4. **Ready-set semantics:** a task is ready when it is not terminal, not in progress, and every dependency is terminal.
5. **Synthesis readiness:** the synthesis task becomes ready only after every critic task is terminal. Critics do not all have to complete successfully.
6. **Ordering:** ready-set and chunks are deterministic lexical `task_id` order. No priority field is introduced in this increment.
7. **Chunking:** `bounded_parallel_chunks(max_parallel=...)` chunks the current sorted ready-set into deterministic lists of at most `max_parallel` task IDs. `max_parallel < 1` raises `ValueError`.
8. **Concurrency group:** define the graph node field but do not implement group-specific scheduler policy beyond deterministic chunking. Group-specific scheduling remains a future increment.
9. **Invalid graph:** unknown dependency endpoints and cycles raise `ValueError` at graph construction.
10. **Registry lookup failures:** keep explicit `CriticAdapterRegistry.resolve(...)` `LookupError` as a hard configuration error in M-CP-EXT-3; typed blocked adapter-missing results are deferred to M-CP-EXT-4.
11. **Clock injection:** defer deterministic clock injection. `ExecutionGraphPlan` is pure and timestamp-free.
12. **CLI:** defer `hisys run-dars-panel`. This increment adds only the primitive and optional serial-runtime consumption.
13. **Runtime wiring:** `DarsCriticPanelRuntime.run_round` may construct `ExecutionGraphPlan.from_round_plan(plan)` and use its order/ready-set as a consistency guard, but it must remain serial and preserve existing output artifacts and boundary records.

---

## Task 0: Reconstruct baseline before editing

**Objective:** Confirm the repository state and current GREEN baseline before writing RED tests.

**Files:** none.

**Commands:**

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py -q
```

**Expected:**

- Branch is `dars`.
- Existing focused suites report `28 passed`.
- Working tree contains only intentional changes for this increment.

---

## Task 1: RED/GREEN — create graph module with deterministic ready-set ordering

**Objective:** Add the first graph primitive test and minimal sidecar module.

**Files:**

- Create: `tests/unit/test_dars_critic_panel_execution_graph_plan.py`
- Create: `src/hisys/agents/dars_panel_graph.py`

**Step 1: Write failing test**

```python
"""DARS critic panel execution-graph plan tests.

Traceability:
- HISYS-FR-DARS-CP-006
- HISYS-NFR-DARS-CP-001
- M-CP-EXT-3 in docs/plans/dars-critic-panel-platform-runtime-next.md
"""

from __future__ import annotations

import pytest


def test_execution_graph_plan_ready_set_is_deterministic_and_sorted():
    from hisys.agents.dars_panel_graph import ExecutionGraphPlan

    graph = ExecutionGraphPlan.from_task_ids(
        critic_task_ids=["TASK-REQ-001-02-security", "TASK-REQ-001-01-logical"],
        synthesis_task_id="TASK-REQ-001-99-synthesis",
    )

    assert graph.ready_set(terminal_task_ids=frozenset()) == [
        "TASK-REQ-001-01-logical",
        "TASK-REQ-001-02-security",
    ]
```

**Step 2: Verify RED**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_execution_graph_plan.py::test_execution_graph_plan_ready_set_is_deterministic_and_sorted -q
```

**Expected RED:** `ModuleNotFoundError` for `hisys.agents.dars_panel_graph` or `ImportError` for `ExecutionGraphPlan`.

**Step 3: Minimal GREEN implementation**

Create `src/hisys/agents/dars_panel_graph.py`:

```python
"""Pure execution-graph primitives for the DARS critic panel runtime."""

from __future__ import annotations

from dataclasses import dataclass, field

TERMINAL_TASK_STATUSES = frozenset({"completed", "failed", "blocked", "skipped"})
DARS_CRITICS_CONCURRENCY_GROUP = "dars-critics"
DARS_SYNTHESIS_CONCURRENCY_GROUP = "dars-synthesis"


@dataclass(frozen=True)
class ExecutionGraphNode:
    task_id: str
    task_kind: str
    concurrency_group: str


@dataclass(frozen=True)
class ExecutionGraphEdge:
    source_task_id: str
    target_task_id: str


@dataclass(frozen=True)
class ExecutionGraphPlan:
    nodes: tuple[ExecutionGraphNode, ...]
    edges: tuple[ExecutionGraphEdge, ...] = field(default_factory=tuple)

    @classmethod
    def from_task_ids(
        cls,
        *,
        critic_task_ids: list[str] | tuple[str, ...],
        synthesis_task_id: str,
    ) -> "ExecutionGraphPlan":
        nodes = tuple(
            ExecutionGraphNode(
                task_id=task_id,
                task_kind="critic",
                concurrency_group=DARS_CRITICS_CONCURRENCY_GROUP,
            )
            for task_id in critic_task_ids
        ) + (
            ExecutionGraphNode(
                task_id=synthesis_task_id,
                task_kind="synthesis",
                concurrency_group=DARS_SYNTHESIS_CONCURRENCY_GROUP,
            ),
        )
        edges = tuple(
            ExecutionGraphEdge(source_task_id=task_id, target_task_id=synthesis_task_id)
            for task_id in critic_task_ids
        )
        return cls(nodes=nodes, edges=edges)

    def ready_set(
        self,
        terminal_task_ids: set[str] | frozenset[str],
        *,
        in_progress_task_ids: set[str] | frozenset[str] = frozenset(),
    ) -> list[str]:
        node_ids = {node.task_id for node in self.nodes}
        ready: list[str] = []
        for node_id in node_ids:
            if node_id in terminal_task_ids or node_id in in_progress_task_ids:
                continue
            dependencies = {
                edge.source_task_id for edge in self.edges if edge.target_task_id == node_id
            }
            if dependencies.issubset(terminal_task_ids):
                ready.append(node_id)
        return sorted(ready)
```

**Step 4: Verify GREEN**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
```

**Expected GREEN:** 1 passed.

---

## Task 2: RED/GREEN — synthesis waits until every critic is terminal

**Objective:** Pin synthesis readiness and terminal-status interpretation.

**Files:**

- Modify: `tests/unit/test_dars_critic_panel_execution_graph_plan.py`
- Modify: `src/hisys/agents/dars_panel_graph.py`

**Step 1: Add failing tests**

```python
def test_execution_graph_plan_synthesis_waits_until_all_critics_terminal():
    from hisys.agents.dars_panel_graph import ExecutionGraphPlan

    graph = ExecutionGraphPlan.from_task_ids(
        critic_task_ids=["TASK-B", "TASK-A"],
        synthesis_task_id="TASK-Z-SYNTHESIS",
    )

    assert graph.ready_set(terminal_task_ids=frozenset({"TASK-A"})) == ["TASK-B"]
    assert graph.ready_set(terminal_task_ids=frozenset({"TASK-A", "TASK-B"})) == [
        "TASK-Z-SYNTHESIS"
    ]


def test_execution_graph_plan_treats_failed_blocked_and_skipped_as_terminal():
    from hisys.agents.dars_panel_graph import ExecutionGraphPlan, TERMINAL_TASK_STATUSES

    assert TERMINAL_TASK_STATUSES == frozenset({"completed", "failed", "blocked", "skipped"})
    graph = ExecutionGraphPlan.from_task_ids(
        critic_task_ids=["TASK-COMPLETED", "TASK-FAILED", "TASK-BLOCKED", "TASK-SKIPPED"],
        synthesis_task_id="TASK-SYNTHESIS",
    )

    terminal = frozenset({"TASK-COMPLETED", "TASK-FAILED", "TASK-BLOCKED", "TASK-SKIPPED"})
    assert graph.ready_set(terminal_task_ids=terminal) == ["TASK-SYNTHESIS"]
```

**Step 2: Verify RED/GREEN**

The minimal Task 1 implementation may already pass these tests. If so, treat them as contract-pinning GREEN tests rather than forcing an artificial RED.

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
```

---

## Task 3: RED/GREEN — bounded-parallel chunks are deterministic

**Objective:** Add the bounded scheduling primitive without enabling runtime parallel execution.

**Files:**

- Modify: `tests/unit/test_dars_critic_panel_execution_graph_plan.py`
- Modify: `src/hisys/agents/dars_panel_graph.py`

**Step 1: Add failing tests**

```python
def test_execution_graph_plan_bounded_parallel_chunks_are_deterministic():
    from hisys.agents.dars_panel_graph import ExecutionGraphPlan

    graph = ExecutionGraphPlan.from_task_ids(
        critic_task_ids=["TASK-C", "TASK-A", "TASK-B"],
        synthesis_task_id="TASK-Z-SYNTHESIS",
    )

    assert graph.bounded_parallel_chunks(
        terminal_task_ids=frozenset(),
        max_parallel=2,
    ) == [["TASK-A", "TASK-B"], ["TASK-C"]]


def test_execution_graph_plan_rejects_invalid_max_parallel():
    from hisys.agents.dars_panel_graph import ExecutionGraphPlan

    graph = ExecutionGraphPlan.from_task_ids(
        critic_task_ids=["TASK-A"],
        synthesis_task_id="TASK-Z-SYNTHESIS",
    )

    with pytest.raises(ValueError, match="max_parallel"):
        graph.bounded_parallel_chunks(
            terminal_task_ids=frozenset(),
            max_parallel=0,
        )
```

**Step 2: Verify RED**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_execution_graph_plan.py::test_execution_graph_plan_bounded_parallel_chunks_are_deterministic -q
```

**Expected RED:** `AttributeError: 'ExecutionGraphPlan' object has no attribute 'bounded_parallel_chunks'`.

**Step 3: Minimal GREEN implementation**

Add to `ExecutionGraphPlan`:

```python
    def bounded_parallel_chunks(
        self,
        *,
        terminal_task_ids: set[str] | frozenset[str] = frozenset(),
        in_progress_task_ids: set[str] | frozenset[str] = frozenset(),
        max_parallel: int,
    ) -> list[list[str]]:
        if max_parallel < 1:
            raise ValueError("max_parallel must be >= 1")
        ready = self.ready_set(
            terminal_task_ids=terminal_task_ids,
            in_progress_task_ids=in_progress_task_ids,
        )
        return [ready[index : index + max_parallel] for index in range(0, len(ready), max_parallel)]
```

**Step 4: Verify GREEN**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
```

---

## Task 4: RED/GREEN — reject unknown dependency endpoints and dependency cycles

**Objective:** Make malformed graphs fail at construction rather than silently yielding no ready set.

**Files:**

- Modify: `tests/unit/test_dars_critic_panel_execution_graph_plan.py`
- Modify: `src/hisys/agents/dars_panel_graph.py`

**Step 1: Add failing tests**

```python
def test_execution_graph_plan_rejects_unknown_dependency_node():
    from hisys.agents.dars_panel_graph import (
        ExecutionGraphEdge,
        ExecutionGraphNode,
        ExecutionGraphPlan,
    )

    with pytest.raises(ValueError, match="unknown dependency"):
        ExecutionGraphPlan(
            nodes=(ExecutionGraphNode("TASK-A", "critic", "dars-critics"),),
            edges=(ExecutionGraphEdge("TASK-MISSING", "TASK-A"),),
        )


def test_execution_graph_plan_rejects_dependency_cycle():
    from hisys.agents.dars_panel_graph import (
        ExecutionGraphEdge,
        ExecutionGraphNode,
        ExecutionGraphPlan,
    )

    with pytest.raises(ValueError, match="cycle"):
        ExecutionGraphPlan(
            nodes=(
                ExecutionGraphNode("TASK-A", "critic", "dars-critics"),
                ExecutionGraphNode("TASK-B", "critic", "dars-critics"),
            ),
            edges=(
                ExecutionGraphEdge("TASK-A", "TASK-B"),
                ExecutionGraphEdge("TASK-B", "TASK-A"),
            ),
        )
```

**Step 2: Verify RED**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_execution_graph_plan.py::test_execution_graph_plan_rejects_unknown_dependency_node -q
```

**Expected RED:** test does not raise `ValueError` yet.

**Step 3: Minimal GREEN implementation**

Add `__post_init__` and helpers:

```python
    def __post_init__(self) -> None:
        node_ids = [node.task_id for node in self.nodes]
        if len(set(node_ids)) != len(node_ids):
            raise ValueError("duplicate task_id in execution graph")
        known = set(node_ids)
        for edge in self.edges:
            if edge.source_task_id not in known or edge.target_task_id not in known:
                raise ValueError(
                    f"unknown dependency endpoint: {edge.source_task_id}->{edge.target_task_id}"
                )
        if self._has_cycle():
            raise ValueError("dependency cycle in execution graph")

    def _has_cycle(self) -> bool:
        outgoing: dict[str, list[str]] = {node.task_id: [] for node in self.nodes}
        for edge in self.edges:
            outgoing[edge.source_task_id].append(edge.target_task_id)
        temporary: set[str] = set()
        permanent: set[str] = set()

        def visit(task_id: str) -> bool:
            if task_id in permanent:
                return False
            if task_id in temporary:
                return True
            temporary.add(task_id)
            for child in outgoing[task_id]:
                if visit(child):
                    return True
            temporary.remove(task_id)
            permanent.add(task_id)
            return False

        return any(visit(node.task_id) for node in self.nodes)
```

**Step 4: Verify GREEN**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
```

---

## Task 5: RED/GREEN — build graph from existing `DarsRoundPlan`

**Objective:** Bridge existing panel plan data to the new graph module without changing runtime behavior.

**Files:**

- Modify: `tests/unit/test_dars_critic_panel_execution_graph_plan.py`
- Modify: `src/hisys/agents/dars_panel_graph.py`

**Step 1: Add failing test**

```python
def test_execution_graph_plan_from_round_plan_preserves_critic_before_synthesis_edges():
    from hisys.agents.dars_panel import DarsCriticPanelConfig, DarsRoundPlan
    from hisys.agents.dars_panel_graph import ExecutionGraphPlan

    config = DarsCriticPanelConfig(
        critics=[
            {"critic_id": "logical-devil", "critic_role": "logical_devil", "backend_id": "fixture-logical"},
            {"critic_id": "standards-reviewer", "critic_role": "standards_reviewer", "backend_id": "fixture-standards"},
        ]
    )
    round_plan = DarsRoundPlan.from_config(config, request_id="REQ-001")

    graph = ExecutionGraphPlan.from_round_plan(round_plan)

    assert graph.ready_set(terminal_task_ids=frozenset()) == [
        "TASK-REQ-001-00-logical-devil",
        "TASK-REQ-001-01-standards-reviewer",
    ]
    terminal = frozenset(graph.ready_set(terminal_task_ids=frozenset()))
    assert graph.ready_set(terminal_task_ids=terminal) == ["TASK-REQ-001-synthesis"]
```

**Step 2: Verify RED**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_execution_graph_plan.py::test_execution_graph_plan_from_round_plan_preserves_critic_before_synthesis_edges -q
```

**Expected RED:** `AttributeError` for `from_round_plan`.

**Step 3: Minimal GREEN implementation**

Add a duck-typed classmethod to avoid import cycles:

```python
    @classmethod
    def from_round_plan(cls, round_plan: object) -> "ExecutionGraphPlan":
        critic_task_ids = [task.task_id for task in round_plan.critic_tasks]
        synthesis_task_id = round_plan.synthesis_task.task_id
        return cls.from_task_ids(
            critic_task_ids=critic_task_ids,
            synthesis_task_id=synthesis_task_id,
        )
```

**Step 4: Verify GREEN**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
```

---

## Task 6: RED/GREEN — re-export graph symbols from `dars_panel.py`

**Objective:** Preserve import compatibility while using the sidecar module as the primary implementation home.

**Files:**

- Modify: `tests/unit/test_dars_critic_panel_execution_graph_plan.py`
- Modify: `src/hisys/agents/dars_panel.py`

**Step 1: Add failing test**

```python
def test_dars_panel_reexports_execution_graph_plan_for_compatibility():
    from hisys.agents.dars_panel import ExecutionGraphPlan
    from hisys.agents.dars_panel_graph import ExecutionGraphPlan as GraphPlan

    assert ExecutionGraphPlan is GraphPlan
```

**Step 2: Verify RED**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_execution_graph_plan.py::test_dars_panel_reexports_execution_graph_plan_for_compatibility -q
```

**Expected RED:** `ImportError` from `hisys.agents.dars_panel`.

**Step 3: Minimal GREEN implementation**

In `src/hisys/agents/dars_panel.py`, add near imports:

```python
from .dars_panel_graph import (
    DARS_CRITICS_CONCURRENCY_GROUP,
    DARS_SYNTHESIS_CONCURRENCY_GROUP,
    TERMINAL_TASK_STATUSES,
    ExecutionGraphEdge,
    ExecutionGraphNode,
    ExecutionGraphPlan,
)
```

If the module has an `__all__`, add these names. If no `__all__` exists, do not introduce one only for this task.

**Step 4: Verify GREEN**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py -q
```

---

## Task 7: RED/GREEN — serial runtime consumes graph order as a consistency guard

**Objective:** Wire `DarsCriticPanelRuntime.run_round` to construct the graph without changing serial behavior or artifacts.

**Files:**

- Modify: `tests/unit/test_dars_critic_panel_execution_graph_plan.py`
- Modify: `src/hisys/agents/dars_panel.py`

**Step 1: Add test**

```python
def test_dars_panel_runtime_remains_serial_after_graph_integration(tmp_path):
    from hisys.agents.dars_panel import DarsCriticPanelConfig, DarsCriticPanelRuntime

    config = DarsCriticPanelConfig(
        critics=[
            {"critic_id": "b-critic", "critic_role": "b_role", "backend_id": "fixture-b"},
            {"critic_id": "a-critic", "critic_role": "a_role", "backend_id": "fixture-a"},
        ]
    )
    result = DarsCriticPanelRuntime(instance_root=tmp_path).run_round(
        config=config,
        request_id="REQ-001",
        yyyymmdd="20260519",
        candidate_ref="candidate://fixture/1",
        evidence_refs=["evidence://fixture/1"],
    )

    assert [record.critic_id for record in result.critiques] == ["b-critic", "a-critic"]
    assert result.trace.execution_mode == "serial"
```

**Step 2: Verify behavior**

This test may pass before the implementation because it preserves current behavior. Treat it as a regression guard.

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_execution_graph_plan.py::test_dars_panel_runtime_remains_serial_after_graph_integration -q
```

**Step 3: Minimal implementation**

Inside `DarsCriticPanelRuntime.run_round`, after `round_plan` creation, construct the graph:

```python
graph_plan = ExecutionGraphPlan.from_round_plan(round_plan)
if graph_plan.ready_set(terminal_task_ids=frozenset()) != [
    task.task_id for task in sorted(round_plan.critic_tasks, key=lambda task: task.task_id)
]:
    raise ValueError("round plan is not graph-schedulable")
```

Do not reorder actual execution in this task. Existing serial execution order remains the `round_plan.critic_tasks` order. The graph acts as a consistency guard only.

**Step 4: Verify GREEN**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py -q
```

---

## Task 8: Documentation and traceability update

**Objective:** Record M-CP-EXT-3 in traceability and Ralph handoff after GREEN.

**Files:**

- Modify: `docs/traceability/dars-critic-panel-runtime-traceability.md`
- Modify: `docs/traceability/README.md`
- Modify: `ralph.md`

**Required content:**

- RTM `HISYS-FR-DARS-CP-006` row mentions `ExecutionGraphPlan`, ready-set determinism, synthesis-after-terminal-critics, and bounded chunking.
- Add a new M-CP-EXT-3 section with tests added and validation commands.
- Ralph reflection records RED observed, GREEN observed, package split decision, CLI deferral, clock-injection deferral, registry `LookupError` deferral, validation results, and next stop condition.

**Validation:**

```bash
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

---

## Task 9: Full quality gate and local commit

**Objective:** Validate the complete M-CP-EXT-3 increment and commit locally.

**Commands:**

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py -q
PYTHONPATH=src:. pytest tests/unit/test_dars_runtime.py tests/unit/test_dars_config.py tests/unit/test_dars_dispatch.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:**

- New graph suite passes.
- Existing focused panel suite remains 28 passed.
- Adjacent DARS regression remains GREEN.
- Traceability validator passes.
- Secret scan reports `hit_count=0`.
- Whitespace diff check is clean.

**Commit:**

```bash
git add \
  src/hisys/agents/dars_panel_graph.py \
  src/hisys/agents/dars_panel.py \
  tests/unit/test_dars_critic_panel_execution_graph_plan.py \
  docs/traceability/dars-critic-panel-runtime-traceability.md \
  docs/traceability/README.md \
  ralph.md

git commit -m "feat: add DARS execution graph plan"
```

**Remote push:** not authorized by this plan; remote push remains human-gated and out of scope.

---

## Stop conditions

Stop and report before proceeding if any of the following occurs:

- The graph primitive requires changing existing public artifact schemas beyond adding graph symbols.
- Existing 28 focused panel tests fail for a reason not directly tied to the intentional graph integration.
- Any implementation would require live external dispatch, process spawning, thread pools, `asyncio`, browser/network libraries, or credential access.
- Package split cannot be done with a sidecar module and would require converting `dars_panel.py` into a directory package.
- Traceability validator or secret scan fails.

## Next increment candidates after M-CP-EXT-3

- M-CP-EXT-4: typed adapter-missing blocked result instead of hard `LookupError`.
- M-CP-EXT-5: deterministic runtime clock seam for boundary record timestamps.
- M-CP-EXT-6: read-only `hisys run-dars-panel` CLI consuming `ExecutionGraphPlan` after a separate approval gate.
- Future activation: actual bounded-parallel execution, only after a separate governance/approval increment.
