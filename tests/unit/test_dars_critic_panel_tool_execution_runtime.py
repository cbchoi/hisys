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

import json
from pathlib import Path

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


def test_execution_boundary_record_rejects_unsafe_envelope_overrides():
    from hisys.agents.dars_panel import ExecutionBoundaryRecord

    base_kwargs = dict(
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
    for forbidden in ("external_call_made", "mutation_performed", "action_authorized"):
        kwargs = dict(base_kwargs)
        kwargs[forbidden] = True
        with pytest.raises(ValueError):
            ExecutionBoundaryRecord(**kwargs)


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
    assert ref == expected.as_posix()
    on_disk = (tmp_path / ref).read_text(encoding="utf-8")
    payload = json.loads(on_disk)
    assert payload["task_id"] == "TASK-REQ-001-00-logical"
    assert payload["external_call_made"] is False
    assert payload["mutation_performed"] is False
    assert payload["action_authorized"] is False
    assert payload["advisory_only"] is True
    assert payload["requires_human_review"] is True
    assert payload["critique_ref"] == record.critique_ref
    # Determinism: writing the same record again produces byte-identical content.
    second_ref = write_execution_boundary_record(
        instance_root=tmp_path,
        date="20260519",
        request_id="REQ-001",
        record=record,
    )
    assert second_ref == ref
    assert (tmp_path / second_ref).read_text(encoding="utf-8") == on_disk


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
        {"date": "2026-05-19", "request_id": "REQ-001"},
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
    from hisys.config.instance import InstanceRoot

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
        assert boundary_ref.startswith("runtime-boundary/dars-panel/20260519/REQ-DARS-CP-EXT-2/")
    failed_payload = next(
        json.loads((tmp_path / ref).read_text(encoding="utf-8"))
        for ref in result.execution_boundary_refs
        if "evidence" in ref
    )
    assert failed_payload["critique_ref"] is None
    assert failed_payload["dispatch_decision"] in {"allowed", "blocked"}


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
    from hisys.config.instance import InstanceRoot

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
    from hisys.config.instance import InstanceRoot

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
    from hisys.config.instance import InstanceRoot

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


def test_panel_runtime_marks_unresolved_adapter_class_for_disabled_critic(tmp_path: Path):
    """M-CP-EXT-7: when no adapter is resolved, the boundary record marks `adapter_class="unresolved"`."""

    from hisys.agents.dars_panel import (
        CriticAdapterRegistry,
        DarsCriticPanelConfig,
        DarsCriticPanelRuntime,
        DarsCriticRoleConfig,
    )
    from hisys.config.instance import InstanceRoot

    candidate_ref, evidence_refs, rubric_ref = _candidate_fixture(tmp_path)
    registry = CriticAdapterRegistry()  # empty
    config = DarsCriticPanelConfig(
        panel_id="PANEL-DARS-CP-EXT-7",
        critics=[
            DarsCriticRoleConfig(
                critic_id="disabled-devil",
                critic_role="logical_devil",
                backend_id="fixture-disabled",
                rubric_ref=rubric_ref,
                critique_dimensions=["logical_validity"],
                enabled=False,
            ),
            DarsCriticRoleConfig(
                critic_id="missing-devil",
                critic_role="standards_reviewer",
                backend_id="fixture-missing",
                rubric_ref=rubric_ref,
                critique_dimensions=["standards_alignment"],
            ),
        ],
    )

    result = DarsCriticPanelRuntime(
        instance=InstanceRoot(tmp_path),
        adapter_registry=registry,
    ).run_round(
        yyyymmdd="20260520",
        request_id="REQ-DARS-CP-EXT-7",
        candidate_ref=candidate_ref,
        evidence_refs=evidence_refs,
        panel_config=config,
    )

    boundary_payloads = [
        json.loads((tmp_path / ref).read_text(encoding="utf-8"))
        for ref in result.execution_boundary_refs
    ]
    assert [payload["adapter_class"] for payload in boundary_payloads] == [
        "unresolved",
        "unresolved",
    ]
    for payload in boundary_payloads:
        assert payload["dispatch_decision"] == "blocked"
        assert payload["external_call_made"] is False
        assert payload["mutation_performed"] is False
        assert payload["action_authorized"] is False
        assert payload["advisory_only"] is True
        assert payload["requires_human_review"] is True


def test_fixture_critic_adapter_rejects_unresolved_adapter_class():
    """M-CP-EXT-7: the `unresolved` literal is reserved for boundary records, not real adapters."""

    from hisys.agents.dars_panel import FixtureCriticAdapter

    with pytest.raises(ValueError, match="adapter_class must be fixture\\|loopback\\|external"):
        FixtureCriticAdapter(
            critic_role="logical_devil",
            backend_id="fixture-logical",
            adapter_class="unresolved",  # type: ignore[arg-type]
        )


def test_panel_runtime_records_distinct_started_and_completed_per_task(tmp_path: Path):
    """M-CP-EXT-8: per-task distinct started_at/completed_at under an injected counter clock."""

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
        json.loads((tmp_path / ref).read_text(encoding="utf-8"))
        for ref in result.execution_boundary_refs
    ]
    starts = [record["started_at"] for record in boundary_records]
    completes = [record["completed_at"] for record in boundary_records]
    for record in boundary_records:
        assert record["started_at"] != record["completed_at"], record
    assert len(set(starts)) == len(starts)
    assert len(set(completes)) == len(completes)
