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

    @classmethod
    def from_round_plan(cls, round_plan: object) -> "ExecutionGraphPlan":
        critic_task_ids = [task.task_id for task in round_plan.critic_tasks]
        synthesis_task_id = round_plan.synthesis_task.task_id
        return cls.from_task_ids(
            critic_task_ids=critic_task_ids,
            synthesis_task_id=synthesis_task_id,
        )

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
