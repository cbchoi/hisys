"""Fixture-local DARS critic panel runtime.

Implements the advisory-only DARS critic panel runtime described by
``HISYS-DARS-CP-SDD-001`` (`docs/design/dars-critic-panel-runtime-sdd.md`).
Hisys remains the system of record; critics here are advisory-only and never
mutate state, make external calls, or grant downstream decision authority.

Traceability:
- Requirements: HISYS-FR-DARS-CP-001..008, HISYS-NFR-DARS-CP-001..002
- SDD: ``docs/design/dars-critic-panel-runtime-sdd.md``
- STD: ``docs/test/dars-critic-panel-runtime-std.md``
- RTM: ``docs/traceability/dars-critic-panel-runtime-traceability.md``
- Pytest anchors: ``tests/unit/test_dars_critic_panel_runtime.py``

External backends and non-fixture dispatch require an explicit ``approval_ref``
and are blocked otherwise. All artifacts persist under the runtime instance root
and never write outside it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from ..config.instance import InstanceRoot

CRITIQUE_RECORD_CONTRACT = "DarsCritiqueRecord"
ADVISORY_ONLY = "advisory_only"
CONCURRENCY_GROUP = "dars-critics"
FAILURE_BACKEND_MARKER = "fail"
EXTERNAL_BACKEND_PREFIX = "external-"

CriticRole = str
TaskStatus = Literal["completed", "failed", "blocked"]
ExecutionMode = Literal["serial", "bounded_parallel"]


@dataclass
class DarsCriticRoleConfig:
    """One critic role inside a panel config (HISYS-FR-DARS-CP-001)."""

    critic_id: str
    critic_role: CriticRole
    backend_id: str
    rubric_ref: str
    critique_dimensions: list[str] = field(default_factory=list)
    enabled: bool = True
    output_contract: str = CRITIQUE_RECORD_CONTRACT
    mutation_allowed: bool = False
    external_call_allowed: bool = False
    approval_ref: str | None = None


@dataclass
class DarsCriticPanelConfig:
    """Panel-level configuration (HISYS-FR-DARS-CP-001, HISYS-FR-DARS-CP-006)."""

    panel_id: str
    critics: list[DarsCriticRoleConfig] = field(default_factory=list)
    max_parallel_critics: int = 1
    failure_policy: str = "continue_collect_errors"
    advisory_only: bool = True
    default_output_contract: str = CRITIQUE_RECORD_CONTRACT


@dataclass
class DarsCriticTask:
    """Independent critic task in the round plan (HISYS-FR-DARS-CP-002..003)."""

    task_id: str
    critic_id: str
    critic_role: CriticRole
    backend_id: str
    candidate_ref: str
    evidence_refs: list[str]
    rubric_ref: str
    expected_output_contract: str = CRITIQUE_RECORD_CONTRACT
    concurrency_group: str = CONCURRENCY_GROUP
    enabled: bool = True
    external_call_allowed: bool = False
    approval_ref: str | None = None


@dataclass
class DarsSynthesisTask:
    """Synthesis dependency target for the round plan (HISYS-FR-DARS-CP-005)."""

    task_id: str
    depends_on_task_ids: list[str]


@dataclass
class DarsRoundEdge:
    """Plan-level dependency edge from critic task to synthesis task."""

    from_task_id: str
    to_task_id: str


@dataclass
class DarsRoundPlan:
    """Round execution plan (HISYS-FR-DARS-CP-002, HISYS-FR-DARS-CP-006)."""

    round_id: str
    candidate_ref: str
    evidence_refs: list[str]
    critic_tasks: list[DarsCriticTask]
    synthesis_task: DarsSynthesisTask
    edges: list[DarsRoundEdge]
    max_parallel_critics: int
    failure_policy: str
    execution_mode: ExecutionMode = "serial"


@dataclass
class DarsTaskResult:
    """Result of a single critic task invocation (HISYS-NFR-DARS-CP-001)."""

    task_id: str
    critic_id: str
    critic_role: CriticRole
    status: TaskStatus
    critique_ref: str | None = None
    external_call_made: bool = False
    mutation_performed: bool = False
    error_message: str | None = None


@dataclass
class DarsRoundResult:
    """Aggregate result for one panel round."""

    round_id: str
    candidate_ref: str
    critique_refs: list[str]
    round_trace_ref: str
    synthesis_ref: str
    task_results: list[DarsTaskResult]


class DarsCriticPanelRuntime:
    """Validate -> plan -> execute -> synthesize -> persist for a panel round.

    The runtime is fixture-local: all artifacts are written under the instance
    root and no external network calls are made. External backends without an
    explicit ``approval_ref`` are blocked at dispatch (HISYS-FR-DARS-CP-007).
    """

    def __init__(self, *, instance: InstanceRoot) -> None:
        self.instance = instance

    def build_round_plan(
        self,
        *,
        yyyymmdd: str,
        request_id: str,
        candidate_ref: str,
        evidence_refs: list[str],
        panel_config: DarsCriticPanelConfig,
    ) -> DarsRoundPlan:
        self._validate_panel_config(panel_config)
        round_id = f"ROUND-{request_id}"
        critic_tasks: list[DarsCriticTask] = []
        for index, critic in enumerate(panel_config.critics):
            critic_tasks.append(
                DarsCriticTask(
                    task_id=f"TASK-{request_id}-{index:02d}-{critic.critic_id}",
                    critic_id=critic.critic_id,
                    critic_role=critic.critic_role,
                    backend_id=critic.backend_id,
                    candidate_ref=candidate_ref,
                    evidence_refs=list(evidence_refs),
                    rubric_ref=critic.rubric_ref,
                    expected_output_contract=critic.output_contract,
                    enabled=critic.enabled,
                    external_call_allowed=critic.external_call_allowed,
                    approval_ref=critic.approval_ref,
                )
            )
        synthesis_task = DarsSynthesisTask(
            task_id=f"TASK-{request_id}-SYNTH",
            depends_on_task_ids=[task.task_id for task in critic_tasks],
        )
        edges = [
            DarsRoundEdge(from_task_id=task.task_id, to_task_id=synthesis_task.task_id)
            for task in critic_tasks
        ]
        execution_mode: ExecutionMode = (
            "bounded_parallel" if panel_config.max_parallel_critics > 1 else "serial"
        )
        _ = yyyymmdd  # plan structure is independent of date; date drives persistence only.
        return DarsRoundPlan(
            round_id=round_id,
            candidate_ref=candidate_ref,
            evidence_refs=list(evidence_refs),
            critic_tasks=critic_tasks,
            synthesis_task=synthesis_task,
            edges=edges,
            max_parallel_critics=panel_config.max_parallel_critics,
            failure_policy=panel_config.failure_policy,
            execution_mode=execution_mode,
        )

    def run_round(
        self,
        *,
        yyyymmdd: str,
        request_id: str,
        candidate_ref: str,
        evidence_refs: list[str],
        panel_config: DarsCriticPanelConfig,
    ) -> DarsRoundResult:
        plan = self.build_round_plan(
            yyyymmdd=yyyymmdd,
            request_id=request_id,
            candidate_ref=candidate_ref,
            evidence_refs=evidence_refs,
            panel_config=panel_config,
        )
        instance_root = Path(self.instance.root)
        panel_dir = self._panel_dir(yyyymmdd, request_id)
        critiques_dir = panel_dir / "critiques"
        critiques_dir.mkdir(parents=True, exist_ok=True)

        task_results: list[DarsTaskResult] = []
        critique_refs: list[str] = []
        for plan_task, critic in zip(plan.critic_tasks, panel_config.critics, strict=True):
            dispatch = self._evaluate_dispatch(critic)
            if dispatch == "blocked":
                task_results.append(
                    DarsTaskResult(
                        task_id=plan_task.task_id,
                        critic_id=plan_task.critic_id,
                        critic_role=plan_task.critic_role,
                        status="blocked",
                        external_call_made=False,
                        error_message="external or non-fixture backend without approval_ref",
                    )
                )
                continue
            if self._is_fixture_failure(critic.backend_id):
                task_results.append(
                    DarsTaskResult(
                        task_id=plan_task.task_id,
                        critic_id=plan_task.critic_id,
                        critic_role=plan_task.critic_role,
                        status="failed",
                        external_call_made=False,
                        error_message=f"fixture failure backend: {critic.backend_id}",
                    )
                )
                continue
            critique_ref = self._write_critique(
                critiques_dir=critiques_dir,
                instance_root=instance_root,
                plan_task=plan_task,
                critic=critic,
                request_id=request_id,
            )
            critique_refs.append(critique_ref)
            task_results.append(
                DarsTaskResult(
                    task_id=plan_task.task_id,
                    critic_id=plan_task.critic_id,
                    critic_role=plan_task.critic_role,
                    status="completed",
                    critique_ref=critique_ref,
                    external_call_made=False,
                    mutation_performed=False,
                )
            )

        synthesis_ref = self._write_synthesis(
            panel_dir=panel_dir,
            instance_root=instance_root,
            request_id=request_id,
            candidate_ref=candidate_ref,
            critique_refs=critique_refs,
            task_results=task_results,
        )
        round_trace_ref = self._write_round_trace(
            panel_dir=panel_dir,
            instance_root=instance_root,
            request_id=request_id,
            plan=plan,
            critique_refs=critique_refs,
            task_results=task_results,
            synthesis_ref=synthesis_ref,
        )
        return DarsRoundResult(
            round_id=plan.round_id,
            candidate_ref=candidate_ref,
            critique_refs=critique_refs,
            round_trace_ref=round_trace_ref,
            synthesis_ref=synthesis_ref,
            task_results=task_results,
        )

    @staticmethod
    def _validate_panel_config(panel_config: DarsCriticPanelConfig) -> None:
        seen_ids: set[str] = set()
        for critic in panel_config.critics:
            if critic.critic_id in seen_ids:
                raise ValueError(f"duplicate critic_id in panel config: {critic.critic_id}")
            seen_ids.add(critic.critic_id)
            if critic.output_contract != CRITIQUE_RECORD_CONTRACT:
                raise ValueError(
                    f"critic {critic.critic_id} must produce {CRITIQUE_RECORD_CONTRACT}; "
                    f"got {critic.output_contract}"
                )

    def _panel_dir(self, yyyymmdd: str, request_id: str) -> Path:
        return Path(self.instance.root) / "data" / "dars-panel" / yyyymmdd / request_id

    @staticmethod
    def _evaluate_dispatch(critic: DarsCriticRoleConfig) -> Literal["allowed", "blocked"]:
        if not critic.enabled:
            return "blocked"
        is_external = critic.backend_id.startswith(EXTERNAL_BACKEND_PREFIX)
        if is_external or critic.external_call_allowed:
            if not critic.approval_ref:
                return "blocked"
        return "allowed"

    @staticmethod
    def _is_fixture_failure(backend_id: str) -> bool:
        return FAILURE_BACKEND_MARKER in backend_id

    def _write_critique(
        self,
        *,
        critiques_dir: Path,
        instance_root: Path,
        plan_task: DarsCriticTask,
        critic: DarsCriticRoleConfig,
        request_id: str,
    ) -> str:
        critique_id = f"CRITIQUE-{request_id}-{critic.critic_id}"
        artifact = {
            "critique_id": critique_id,
            "request_id": request_id,
            "task_id": plan_task.task_id,
            "critic_id": critic.critic_id,
            "critic_role": critic.critic_role,
            "backend_id": critic.backend_id,
            "candidate_ref": plan_task.candidate_ref,
            "evidence_refs": list(plan_task.evidence_refs),
            "rubric_ref": critic.rubric_ref,
            "critique_dimensions": list(critic.critique_dimensions),
            "findings": [],
            "output_contract": critic.output_contract,
            "allowed_actions": ADVISORY_ONLY,
            "action_taken": "none",
            "action_authorized": False,
            "external_call_made": False,
            "mutation_performed": False,
            "advisory_only": True,
            "requires_human_review": True,
            "human_approved": False,
            "policy_refs": [
                "HISYS-FR-DARS-CP-003",
                "HISYS-FR-DARS-CP-008",
                "HISYS-NFR-DARS-CP-002",
            ],
        }
        path = critiques_dir / f"{critique_id}.json"
        path.write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
        return str(path.relative_to(instance_root))

    def _write_synthesis(
        self,
        *,
        panel_dir: Path,
        instance_root: Path,
        request_id: str,
        candidate_ref: str,
        critique_refs: list[str],
        task_results: list[DarsTaskResult],
    ) -> str:
        statuses = {task.status for task in task_results}
        partial_evidence = bool(statuses & {"failed", "blocked"})
        no_completed = "completed" not in statuses
        if no_completed or partial_evidence:
            disposition = "needs_more_evidence"
        else:
            disposition = "revise_candidate"
        synthesis_id = f"SYNTH-{request_id}"
        role_provenance = [
            {
                "critic_id": task.critic_id,
                "critic_role": task.critic_role,
                "status": task.status,
                "critique_ref": task.critique_ref,
            }
            for task in task_results
        ]
        artifact = {
            "synthesis_id": synthesis_id,
            "request_id": request_id,
            "candidate_ref": candidate_ref,
            "critique_refs": list(critique_refs),
            "role_provenance": role_provenance,
            "findings": [],
            "disposition": disposition,
            "advisory_only": True,
            "action_authorized": False,
            "requires_human_review": True,
            "human_approved": False,
            "policy_refs": [
                "HISYS-FR-DARS-CP-005",
                "HISYS-FR-DARS-CP-008",
            ],
        }
        path = panel_dir / f"{synthesis_id}.json"
        path.write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
        return str(path.relative_to(instance_root))

    def _write_round_trace(
        self,
        *,
        panel_dir: Path,
        instance_root: Path,
        request_id: str,
        plan: DarsRoundPlan,
        critique_refs: list[str],
        task_results: list[DarsTaskResult],
        synthesis_ref: str,
    ) -> str:
        trace_id = f"TRACE-{request_id}"
        failed_task_refs = [task.task_id for task in task_results if task.status != "completed"]
        critic_task_refs = [task.task_id for task in plan.critic_tasks]
        artifact = {
            "trace_id": trace_id,
            "round_id": plan.round_id,
            "request_id": request_id,
            "candidate_ref": plan.candidate_ref,
            "critic_task_refs": critic_task_refs,
            "critique_refs": list(critique_refs),
            "failed_task_refs": failed_task_refs,
            "synthesis_ref": synthesis_ref,
            "unresolved_findings": [],
            "stop_condition_met": True,
            "advisory_only": True,
            "requires_human_review": True,
            "human_approved": False,
            "policy_refs": [
                "HISYS-FR-DARS-CP-004",
                "HISYS-FR-DARS-CP-008",
            ],
        }
        path = panel_dir / f"{trace_id}.json"
        path.write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
        return str(path.relative_to(instance_root))


__all__ = [
    "ADVISORY_ONLY",
    "CONCURRENCY_GROUP",
    "CRITIQUE_RECORD_CONTRACT",
    "DarsCriticPanelConfig",
    "DarsCriticPanelRuntime",
    "DarsCriticRoleConfig",
    "DarsCriticTask",
    "DarsRoundEdge",
    "DarsRoundPlan",
    "DarsRoundResult",
    "DarsSynthesisTask",
    "DarsTaskResult",
]
