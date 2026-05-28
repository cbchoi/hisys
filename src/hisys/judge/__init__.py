"""Judge subsystem public seam.

This package is a minimal subsystem-level entry point for the Hisys
``Altas + DARS + Judge`` role split. Judge owns bounded advisory judgment,
gates, readiness decisions, and decision packets over already prepared evidence
or review packets. The package records the public boundary without authorizing
live action, mutation, publication, remote synchronization, or human-review
removal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .decision_packet import (
    JUDGE_VERDICTS,
    SCHEMA_VALIDITY_WARNING,
    JudgeAdvisoryDecisionPacket,
    JudgeDecisionPacketValidation,
    validate_judge_decision_packet,
)
from .gate_result import (
    JUDGE_ADVISORY_PANEL_REVIEW_BUNDLE_FINGERPRINT_ALGORITHM,
    JUDGE_GATE_NON_AUTHORIZATION_NOTE,
    JUDGE_GATE_REJECTED_STATUS,
    JUDGE_GATE_STATUS_BY_VERDICT,
    JUDGE_GATE_STATUS_RESTRICTIVENESS,
    JUDGE_PANEL_MALFORMED_GATE_STATUS,
    JUDGE_WORK_QUEUE_UNIDENTIFIED_PACKET_ID,
    JudgeGateResult,
    build_judge_advisory_panel_report,
    build_judge_advisory_panel_review_bundle,
    build_judge_gate_result_packet,
    build_judge_human_review_work_queue,
    fingerprint_judge_advisory_panel_review_bundle,
    render_judge_advisory_panel_report_text,
    render_judge_gate_result,
    serialize_judge_advisory_panel_review_bundle,
    summarize_judge_gate_result_packets,
)


@dataclass(frozen=True)
class JudgeSubsystemManifest:
    """Machine-readable Judge subsystem role and authority boundary."""

    role: Literal["judge"] = "judge"
    responsibility: Literal["bounded advisory judgment/gates"] = (
        "bounded advisory judgment/gates"
    )
    advisory_only: Literal[True] = True
    requires_human_review: Literal[True] = True
    live_external_action_authorized: Literal[False] = False
    mutation_authorized: Literal[False] = False
    publication_authorized: Literal[False] = False
    remote_push_authorized: Literal[False] = False
    human_review_removal_authorized: Literal[False] = False


def get_judge_subsystem_manifest() -> JudgeSubsystemManifest:
    """Return the current Judge subsystem manifest without side effects."""

    return JudgeSubsystemManifest()


@dataclass(frozen=True)
class JudgeSubsystemInvocationMode:
    """A documented Hisys invocation mode that Judge participates in.

    Mirrors the invocation-mode record in
    ``docs/design/hisys-subsystem-architecture.md`` for the modes that involve
    Judge. The other documented modes (``altas-only`` and ``dars-only``) do not
    run Judge and are intentionally not represented here.
    """

    mode_id: Literal["judge-only", "full-loop"]
    description: str
    judge_role: Literal["sole_subsystem", "bounded_advisory_decision_stage"]
    advisory_only: Literal[True] = True
    requires_human_review: Literal[True] = True


def get_judge_subsystem_invocation_modes() -> tuple[
    JudgeSubsystemInvocationMode, ...
]:
    """Return the documented invocation modes that Judge participates in."""

    return (
        JudgeSubsystemInvocationMode(
            mode_id="judge-only",
            description="bounded advisory judgment over already prepared packets",
            judge_role="sole_subsystem",
        ),
        JudgeSubsystemInvocationMode(
            mode_id="full-loop",
            description="Altas -> DARS -> Judge",
            judge_role="bounded_advisory_decision_stage",
        ),
    )


__all__ = [
    "JUDGE_ADVISORY_PANEL_REVIEW_BUNDLE_FINGERPRINT_ALGORITHM",
    "JUDGE_GATE_NON_AUTHORIZATION_NOTE",
    "JUDGE_GATE_REJECTED_STATUS",
    "JUDGE_GATE_STATUS_BY_VERDICT",
    "JUDGE_GATE_STATUS_RESTRICTIVENESS",
    "JUDGE_PANEL_MALFORMED_GATE_STATUS",
    "JUDGE_WORK_QUEUE_UNIDENTIFIED_PACKET_ID",
    "JUDGE_VERDICTS",
    "SCHEMA_VALIDITY_WARNING",
    "JudgeAdvisoryDecisionPacket",
    "JudgeDecisionPacketValidation",
    "JudgeGateResult",
    "JudgeSubsystemInvocationMode",
    "JudgeSubsystemManifest",
    "build_judge_advisory_panel_report",
    "build_judge_advisory_panel_review_bundle",
    "build_judge_gate_result_packet",
    "build_judge_human_review_work_queue",
    "fingerprint_judge_advisory_panel_review_bundle",
    "get_judge_subsystem_invocation_modes",
    "get_judge_subsystem_manifest",
    "render_judge_advisory_panel_report_text",
    "render_judge_gate_result",
    "serialize_judge_advisory_panel_review_bundle",
    "summarize_judge_gate_result_packets",
    "validate_judge_decision_packet",
]
