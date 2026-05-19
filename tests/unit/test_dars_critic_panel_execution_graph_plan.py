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


def test_execution_graph_plan_from_round_plan_preserves_critic_before_synthesis_edges(tmp_path):
    from hisys.agents.dars_panel import (
        DarsCriticPanelConfig,
        DarsCriticPanelRuntime,
        DarsCriticRoleConfig,
    )
    from hisys.agents.dars_panel_graph import ExecutionGraphPlan
    from hisys.config.instance import InstanceRoot

    config = DarsCriticPanelConfig(
        panel_id="panel-test",
        critics=[
            DarsCriticRoleConfig(
                critic_id="logical-devil",
                critic_role="logical_devil",
                backend_id="fixture-logical",
                rubric_ref="rubric://test",
            ),
            DarsCriticRoleConfig(
                critic_id="standards-reviewer",
                critic_role="standards_reviewer",
                backend_id="fixture-standards",
                rubric_ref="rubric://test",
            ),
        ],
    )
    runtime = DarsCriticPanelRuntime(instance=InstanceRoot(tmp_path))
    round_plan = runtime.build_round_plan(
        yyyymmdd="20260520",
        request_id="REQ-001",
        candidate_ref="candidate://fixture/1",
        evidence_refs=["evidence://fixture/1"],
        panel_config=config,
    )

    graph = ExecutionGraphPlan.from_round_plan(round_plan)

    assert graph.ready_set(terminal_task_ids=frozenset()) == [
        "TASK-REQ-001-00-logical-devil",
        "TASK-REQ-001-01-standards-reviewer",
    ]
    terminal = frozenset(graph.ready_set(terminal_task_ids=frozenset()))
    assert graph.ready_set(terminal_task_ids=terminal) == ["TASK-REQ-001-SYNTH"]


def test_dars_panel_reexports_execution_graph_plan_for_compatibility():
    from hisys.agents.dars_panel import ExecutionGraphPlan
    from hisys.agents.dars_panel_graph import ExecutionGraphPlan as GraphPlan

    assert ExecutionGraphPlan is GraphPlan


def test_dars_panel_runtime_remains_serial_after_graph_integration(tmp_path):
    from hisys.agents.dars_panel import (
        DarsCriticPanelConfig,
        DarsCriticPanelRuntime,
        DarsCriticRoleConfig,
    )
    from hisys.config.instance import InstanceRoot

    config = DarsCriticPanelConfig(
        panel_id="panel-test",
        critics=[
            DarsCriticRoleConfig(
                critic_id="b-critic",
                critic_role="b_role",
                backend_id="fixture-b",
                rubric_ref="rubric://test",
            ),
            DarsCriticRoleConfig(
                critic_id="a-critic",
                critic_role="a_role",
                backend_id="fixture-a",
                rubric_ref="rubric://test",
            ),
        ],
    )
    runtime = DarsCriticPanelRuntime(instance=InstanceRoot(tmp_path))
    result = runtime.run_round(
        yyyymmdd="20260520",
        request_id="REQ-001",
        candidate_ref="candidate://fixture/1",
        evidence_refs=["evidence://fixture/1"],
        panel_config=config,
    )

    assert [task.critic_id for task in result.task_results] == ["b-critic", "a-critic"]
