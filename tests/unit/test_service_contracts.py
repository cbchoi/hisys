"""Pure subsystem service contract tests for Altas, DARS, and Judge.

Traceability: docs/plans/hisys-mcp-docker-service-implementation-tasks.md Task 6.1.
"""

from __future__ import annotations

import dataclasses
import importlib
import subprocess

import pytest

from hisys.mcp.contracts import McpSafetyFlags


def test_service_invocation_envelope_is_frozen_and_fail_closed() -> None:
    services = importlib.import_module("hisys.services")

    envelope = services.ServiceInvocationEnvelope(
        request_id="REQ-SVC-001",
        trace_id=None,
        objective="build evidence package",
        evidence_refs=("evidence/source-a",),
        safety=McpSafetyFlags(),
    )

    assert dataclasses.is_dataclass(envelope)
    assert envelope.approval_ref is None
    assert envelope.evidence_refs == ("evidence/source-a",)
    assert envelope.safety.external_call_allowed is False
    assert envelope.safety.mutation_allowed is False
    assert envelope.safety.publication_allowed is False
    assert envelope.safety.live_provider_allowed is False
    with pytest.raises(dataclasses.FrozenInstanceError):
        envelope.objective = "mutate"  # type: ignore[misc]


def test_altas_contracts_are_sensor_first_evidence_resolution_data() -> None:
    altas = importlib.import_module("hisys.services.altas")
    services = importlib.import_module("hisys.services")

    request = altas.AltasEvidenceResolutionRequest(
        envelope=services.ServiceInvocationEnvelope(
            request_id="REQ-ALTAS-001",
            trace_id="TRACE-ALTAS-001",
            objective="resolve source handles",
            evidence_refs=("sensor://source/1",),
            safety=McpSafetyFlags(),
        ),
        source_handles=("sensor://source/1",),
    )
    package = altas.AltasEvidencePackage(
        package_id="PKG-ALTAS-001",
        resolved_handles=(
            altas.AltasResolvedSourceHandle(
                handle="sensor://source/1",
                evidence_ref="evidence/1",
                sensor_first=True,
            ),
        ),
    )

    assert request.sensor_first is True
    assert request.external_call_authorized is False
    assert package.sensor_first is True
    assert package.mutation_performed is False
    assert package.publication_performed is False
    assert package.resolved_handles[0].sensor_first is True


def test_dars_contracts_are_advisory_only_residual_risk_data() -> None:
    dars = importlib.import_module("hisys.services.dars")
    services = importlib.import_module("hisys.services")

    critique = dars.DarsAdversarialCritique(
        envelope=services.ServiceInvocationEnvelope(
            request_id="REQ-DARS-001",
            trace_id=None,
            objective="surface residual risks",
            evidence_refs=("evidence/1",),
            safety=McpSafetyFlags(),
        ),
        critique_points=("source corroboration is thin",),
        residual_risks=("single-source residual risk",),
    )

    assert critique.advisory_only is True
    assert critique.decision_authorized is False
    assert critique.mutation_authorized is False
    assert critique.residual_risks == ("single-source residual risk",)


def test_judge_contracts_bound_decision_packet_behind_human_review_gate() -> None:
    judge = importlib.import_module("hisys.services.judge")
    services = importlib.import_module("hisys.services")

    score = judge.JudgeRubricScore(
        rubric_id="RUBRIC-001",
        score=0.72,
        rationale="meets minimum evidence threshold with caveats",
    )
    packet = judge.JudgeBoundedDecisionPacket(
        envelope=services.ServiceInvocationEnvelope(
            request_id="REQ-JUDGE-001",
            trace_id="TRACE-JUDGE-001",
            objective="score and gate recommendation",
            evidence_refs=("evidence/1", "dars/critique/1"),
            safety=McpSafetyFlags(),
        ),
        rubric_scores=(score,),
        decision="human_review_required",
    )

    assert packet.human_review_required is True
    assert packet.publication_authorized is False
    assert packet.mutation_authorized is False
    assert packet.remote_push_authorized is False
    assert packet.rubric_scores == (score,)


def test_importing_service_contracts_does_not_start_subprocesses(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[object] = []

    def fail_popen(*args: object, **kwargs: object) -> None:
        calls.append((args, kwargs))
        raise AssertionError("service contracts must not start subprocesses")

    monkeypatch.setattr(subprocess, "Popen", fail_popen)

    for module_name in (
        "hisys.services",
        "hisys.services.altas",
        "hisys.services.dars",
        "hisys.services.judge",
    ):
        importlib.import_module(module_name)

    assert calls == []
