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
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from ..config.instance import InstanceRoot
from .dars_panel_graph import (
    DARS_CRITICS_CONCURRENCY_GROUP,
    DARS_SYNTHESIS_CONCURRENCY_GROUP,
    TERMINAL_TASK_STATUSES,
    ExecutionGraphEdge,
    ExecutionGraphNode,
    ExecutionGraphPlan,
)

CRITIQUE_RECORD_CONTRACT = "DarsCritiqueRecord"
ADVISORY_ONLY = "advisory_only"
CONCURRENCY_GROUP = "dars-critics"
EXTERNAL_BACKEND_PREFIX = "external-"

CriticRole = str
TaskStatus = Literal["completed", "failed", "blocked"]
ExecutionMode = Literal["serial", "bounded_parallel"]
AdapterClass = Literal["fixture", "loopback", "external"]
BackendDispatchOutcome = Literal["completed", "failed", "blocked", "skipped"]
DispatchDecision = Literal["allowed", "blocked"]

# Slug shapes mirror the writer convention in
# ``src/hisys/operations/codebase_analysis.py``: dates are exactly eight digits,
# request and task ids are restricted to a conservative alphanumeric/underscore/
# hyphen set so the writer cannot be tricked into composing paths outside the
# ``<instance>/runtime-boundary/dars-panel/...`` subtree via traversal segments.
_DATE_PATTERN = re.compile(r"^[0-9]{8}$")
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
_TASK_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")

RUNTIME_BOUNDARY_SUBTREE = Path("runtime-boundary") / "dars-panel"


def _validate_slug(name: str, value: str, pattern: re.Pattern[str]) -> None:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise ValueError(
            f"invalid {name} for dars-panel writer: {value!r}; "
            f"must match {pattern.pattern}"
        )
    if value in {".", ".."}:
        raise ValueError(
            f"invalid {name} for dars-panel writer: {value!r}; "
            "traversal segments are not allowed"
        )


def _format_iso_timestamp(moment: datetime) -> str:
    """Format a clock reading as a deterministic UTC ISO-8601 ``...Z`` string.

    M-CP-EXT-5: routes ``run_round``'s wall-clock read through a single seam so
    tests can inject a fixed clock and assert byte-identical boundary-record
    output across invocations. Naive datetimes are rejected because the
    persisted timestamp must be unambiguous.
    """

    if moment.tzinfo is None:
        raise ValueError("clock must return timezone-aware datetime")
    return moment.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


@dataclass
class FixtureCriticAdapter:
    """Typed adapter binding a critic role and backend id to a declared outcome.

    M-CP-EXT-1: replaces the ``"fail" in backend_id`` substring heuristic with
    an explicit ``fixture_outcome`` field. The adapter is the runtime's single
    source of truth for dispatch class (``fixture``/``loopback``/``external``)
    and fixture outcome; ``DarsCriticPanelRuntime`` never inspects backend ids
    for failure or external classification.
    """

    critic_role: CriticRole
    backend_id: str
    adapter_class: AdapterClass = "fixture"
    fixture_outcome: BackendDispatchOutcome = "completed"

    def __post_init__(self) -> None:
        if self.adapter_class not in ("fixture", "loopback", "external"):
            raise ValueError(
                f"adapter_class must be fixture|loopback|external; got {self.adapter_class}"
            )
        if self.fixture_outcome not in ("completed", "failed", "blocked", "skipped"):
            raise ValueError(
                f"fixture_outcome must be completed|failed|blocked|skipped; "
                f"got {self.fixture_outcome}"
            )


class CriticAdapterRegistry:
    """Explicit critic adapter registry (M-CP-EXT-1).

    The registry rejects duplicate ``(critic_role, backend_id)`` registrations
    and blocks external adapter dispatch unless ``external_dispatch_allowed``
    is True *and* the resolver receives a truthy ``approval_ref``. There is no
    fallback to backend-name heuristics: every adapter must be registered.
    """

    def __init__(self, *, external_dispatch_allowed: bool = False) -> None:
        self.external_dispatch_allowed = external_dispatch_allowed
        self._adapters: dict[tuple[str, str], FixtureCriticAdapter] = {}

    def register(self, adapter: FixtureCriticAdapter) -> None:
        key = (adapter.critic_role, adapter.backend_id)
        if key in self._adapters:
            raise ValueError(
                f"duplicate critic adapter for role={adapter.critic_role} "
                f"backend_id={adapter.backend_id}"
            )
        self._adapters[key] = adapter

    def resolve(
        self,
        *,
        critic_role: CriticRole,
        backend_id: str,
        approval_ref: str | None = None,
    ) -> FixtureCriticAdapter:
        try:
            adapter = self._adapters[(critic_role, backend_id)]
        except KeyError as exc:
            raise LookupError(
                f"no critic adapter registered for role={critic_role} backend_id={backend_id}"
            ) from exc
        if adapter.adapter_class == "external":
            if not self.external_dispatch_allowed:
                raise PermissionError(
                    "external adapter dispatch is disabled by the registry"
                )
            if not approval_ref:
                raise PermissionError(
                    "external adapter dispatch requires approval_ref"
                )
        return adapter


class _DefaultFixturePolicy(CriticAdapterRegistry):
    """Permissive fixture-only fallback that preserves M-CP-EXT-0 behavior.

    Used when ``DarsCriticPanelRuntime`` is constructed without an explicit
    registry. Backends prefixed ``external-`` are classified as external (and
    therefore blocked at resolve time); ``fixture-failing-critic`` resolves to
    a typed ``failed`` outcome; any other fixture/loopback backend resolves to
    ``completed``. No external dispatch is ever authorized through this
    fallback.
    """

    _FAILING_FIXTURE_BACKEND_ID = "fixture-failing-critic"

    def __init__(self) -> None:
        super().__init__(external_dispatch_allowed=False)

    def resolve(
        self,
        *,
        critic_role: CriticRole,
        backend_id: str,
        approval_ref: str | None = None,
    ) -> FixtureCriticAdapter:
        key = (critic_role, backend_id)
        if key not in self._adapters:
            adapter_class: AdapterClass = (
                "external" if backend_id.startswith(EXTERNAL_BACKEND_PREFIX) else "fixture"
            )
            fixture_outcome: BackendDispatchOutcome = (
                "failed" if backend_id == self._FAILING_FIXTURE_BACKEND_ID else "completed"
            )
            self._adapters[key] = FixtureCriticAdapter(
                critic_role=critic_role,
                backend_id=backend_id,
                adapter_class=adapter_class,
                fixture_outcome=fixture_outcome,
            )
        return super().resolve(
            critic_role=critic_role,
            backend_id=backend_id,
            approval_ref=approval_ref,
        )


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
class ExecutionBoundaryRecord:
    """Per-task dispatch boundary record (HISYS-FR-DARS-CP-003, M-CP-EXT-2).

    Persisted as JSON under
    ``<instance>/runtime-boundary/dars-panel/<YYYYMMDD>/<REQUEST_ID>/<TASK_ID>.json``
    once per critic task. The safety envelope is locked: any attempt to
    construct a record with ``external_call_made=True``, ``mutation_performed=True``,
    or ``action_authorized=True`` raises ``ValueError``.
    """

    task_id: str
    critic_id: str
    critic_role: CriticRole
    adapter_class: AdapterClass
    backend_id: str
    dispatch_decision: DispatchDecision
    dispatch_reason: str
    started_at: str
    completed_at: str
    approval_ref: str | None = None
    critique_ref: str | None = None
    external_call_made: bool = False
    mutation_performed: bool = False
    action_authorized: bool = False
    advisory_only: bool = True
    requires_human_review: bool = True

    def __post_init__(self) -> None:
        if self.dispatch_decision not in ("allowed", "blocked"):
            raise ValueError(
                f"dispatch_decision must be allowed|blocked; got {self.dispatch_decision}"
            )
        if self.external_call_made is not False:
            raise ValueError("external_call_made must remain False on ExecutionBoundaryRecord")
        if self.mutation_performed is not False:
            raise ValueError("mutation_performed must remain False on ExecutionBoundaryRecord")
        if self.action_authorized is not False:
            raise ValueError("action_authorized must remain False on ExecutionBoundaryRecord")
        if self.advisory_only is not True:
            raise ValueError("advisory_only must remain True on ExecutionBoundaryRecord")
        if self.requires_human_review is not True:
            raise ValueError("requires_human_review must remain True on ExecutionBoundaryRecord")


def write_execution_boundary_record(
    *,
    instance_root: Path | str,
    date: str,
    request_id: str,
    record: ExecutionBoundaryRecord,
) -> str:
    """Persist a per-task ``ExecutionBoundaryRecord`` as deterministic JSON.

    Validates ``date``, ``request_id``, and ``record.task_id`` against the
    dars-panel slug patterns before composing any path. Returns the
    instance-relative ref as a POSIX-style string.
    """

    _validate_slug("date", date, _DATE_PATTERN)
    _validate_slug("request_id", request_id, _REQUEST_ID_PATTERN)
    _validate_slug("task_id", record.task_id, _TASK_ID_PATTERN)
    relative = RUNTIME_BOUNDARY_SUBTREE / date / request_id / f"{record.task_id}.json"
    instance_path = Path(instance_root)
    target = instance_path / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(record)
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return relative.as_posix()


@dataclass
class DarsRoundResult:
    """Aggregate result for one panel round."""

    round_id: str
    candidate_ref: str
    critique_refs: list[str]
    round_trace_ref: str
    synthesis_ref: str
    task_results: list[DarsTaskResult]
    execution_boundary_refs: list[str] = field(default_factory=list)


class DarsCriticPanelRuntime:
    """Validate -> plan -> execute -> synthesize -> persist for a panel round.

    The runtime is fixture-local: all artifacts are written under the instance
    root and no external network calls are made. External backends without an
    explicit ``approval_ref`` are blocked at dispatch (HISYS-FR-DARS-CP-007).
    """

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
        _validate_slug("yyyymmdd", yyyymmdd, _DATE_PATTERN)
        _validate_slug("request_id", request_id, _REQUEST_ID_PATTERN)
        plan = self.build_round_plan(
            yyyymmdd=yyyymmdd,
            request_id=request_id,
            candidate_ref=candidate_ref,
            evidence_refs=evidence_refs,
            panel_config=panel_config,
        )
        # M-CP-EXT-3: build a pure ExecutionGraphPlan as a consistency guard.
        # The runtime remains serial; this assertion only catches structural
        # divergence between the round plan and a schedulable graph.
        graph_plan = ExecutionGraphPlan.from_round_plan(plan)
        expected_ready = [task.task_id for task in sorted(plan.critic_tasks, key=lambda task: task.task_id)]
        if graph_plan.ready_set(terminal_task_ids=frozenset()) != expected_ready:
            raise ValueError("round plan is not graph-schedulable")
        instance_root = Path(self.instance.root)
        panel_dir = self._panel_dir(yyyymmdd, request_id)
        critiques_dir = panel_dir / "critiques"
        critiques_dir.mkdir(parents=True, exist_ok=True)
        # M-CP-EXT-2 records started_at == completed_at because no real
        # per-task timing is captured in this increment. M-CP-EXT-5 routes the
        # single round-level clock read through ``self._clock`` so tests can
        # inject a fixed clock and assert byte-identical boundary records.
        timestamp = _format_iso_timestamp(self._clock())

        task_results: list[DarsTaskResult] = []
        critique_refs: list[str] = []
        execution_boundary_refs: list[str] = []
        for plan_task, critic in zip(plan.critic_tasks, panel_config.critics, strict=True):
            adapter: FixtureCriticAdapter | None = None
            critique_ref: str | None = None
            if not critic.enabled:
                dispatch_decision: DispatchDecision = "blocked"
                dispatch_reason = "critic disabled"
                task_results.append(
                    DarsTaskResult(
                        task_id=plan_task.task_id,
                        critic_id=plan_task.critic_id,
                        critic_role=plan_task.critic_role,
                        status="blocked",
                        external_call_made=False,
                        error_message=dispatch_reason,
                    )
                )
            else:
                try:
                    adapter = self.adapter_registry.resolve(
                        critic_role=critic.critic_role,
                        backend_id=critic.backend_id,
                        approval_ref=critic.approval_ref,
                    )
                except (LookupError, PermissionError) as exc:
                    dispatch_decision = "blocked"
                    dispatch_reason = str(exc)
                    task_results.append(
                        DarsTaskResult(
                            task_id=plan_task.task_id,
                            critic_id=plan_task.critic_id,
                            critic_role=plan_task.critic_role,
                            status="blocked",
                            external_call_made=False,
                            error_message=dispatch_reason,
                        )
                    )
                else:
                    if (
                        adapter.adapter_class != "external"
                        and critic.external_call_allowed
                        and not critic.approval_ref
                    ):
                        dispatch_decision = "blocked"
                        dispatch_reason = "external_call_allowed without approval_ref"
                        task_results.append(
                            DarsTaskResult(
                                task_id=plan_task.task_id,
                                critic_id=plan_task.critic_id,
                                critic_role=plan_task.critic_role,
                                status="blocked",
                                external_call_made=False,
                                error_message=dispatch_reason,
                            )
                        )
                    elif adapter.fixture_outcome == "failed":
                        dispatch_decision = "allowed"
                        dispatch_reason = (
                            f"adapter outcome=failed for backend {critic.backend_id}"
                        )
                        task_results.append(
                            DarsTaskResult(
                                task_id=plan_task.task_id,
                                critic_id=plan_task.critic_id,
                                critic_role=plan_task.critic_role,
                                status="failed",
                                external_call_made=False,
                                error_message=dispatch_reason,
                            )
                        )
                    elif adapter.fixture_outcome in ("blocked", "skipped"):
                        dispatch_decision = "blocked"
                        dispatch_reason = f"adapter outcome={adapter.fixture_outcome}"
                        task_results.append(
                            DarsTaskResult(
                                task_id=plan_task.task_id,
                                critic_id=plan_task.critic_id,
                                critic_role=plan_task.critic_role,
                                status="blocked",
                                external_call_made=False,
                                error_message=dispatch_reason,
                            )
                        )
                    else:
                        critique_ref = self._write_critique(
                            critiques_dir=critiques_dir,
                            instance_root=instance_root,
                            plan_task=plan_task,
                            critic=critic,
                            request_id=request_id,
                        )
                        critique_refs.append(critique_ref)
                        dispatch_decision = "allowed"
                        dispatch_reason = "adapter resolved"
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
            boundary_record = ExecutionBoundaryRecord(
                task_id=plan_task.task_id,
                critic_id=plan_task.critic_id,
                critic_role=plan_task.critic_role,
                adapter_class=adapter.adapter_class if adapter is not None else "fixture",
                backend_id=plan_task.backend_id,
                dispatch_decision=dispatch_decision,
                dispatch_reason=dispatch_reason,
                started_at=timestamp,
                completed_at=timestamp,
                approval_ref=critic.approval_ref,
                critique_ref=critique_ref,
            )
            boundary_ref = write_execution_boundary_record(
                instance_root=instance_root,
                date=yyyymmdd,
                request_id=request_id,
                record=boundary_record,
            )
            execution_boundary_refs.append(boundary_ref)

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
            execution_boundary_refs=execution_boundary_refs,
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
        _validate_slug("yyyymmdd", yyyymmdd, _DATE_PATTERN)
        _validate_slug("request_id", request_id, _REQUEST_ID_PATTERN)
        return Path(self.instance.root) / "data" / "dars-panel" / yyyymmdd / request_id

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
    "AdapterClass",
    "BackendDispatchOutcome",
    "CONCURRENCY_GROUP",
    "CRITIQUE_RECORD_CONTRACT",
    "CriticAdapterRegistry",
    "DARS_CRITICS_CONCURRENCY_GROUP",
    "DARS_SYNTHESIS_CONCURRENCY_GROUP",
    "DarsCriticPanelConfig",
    "DarsCriticPanelRuntime",
    "DarsCriticRoleConfig",
    "DarsCriticTask",
    "DarsRoundEdge",
    "DarsRoundPlan",
    "DarsRoundResult",
    "DarsSynthesisTask",
    "DarsTaskResult",
    "DispatchDecision",
    "ExecutionBoundaryRecord",
    "ExecutionGraphEdge",
    "ExecutionGraphNode",
    "ExecutionGraphPlan",
    "FixtureCriticAdapter",
    "RUNTIME_BOUNDARY_SUBTREE",
    "TERMINAL_TASK_STATUSES",
    "write_execution_boundary_record",
]
