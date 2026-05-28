"""Judge advisory gate-result renderer.

Judge issues bounded advisory judgments, gate outcomes, and decision packets
from already prepared evidence, Altas retrieval packets, and DARS opposition
packets (see ``docs/design/hisys-subsystem-architecture.md``). This module turns
a validated :class:`JudgeAdvisoryDecisionPacket` -- or an already-prepared local
packet mapping of the same shape the decision-packet validator accepts -- into a
deterministic, human-readable advisory gate result.

The renderer is pure and side-effect free: it performs no live provider/model
call, no raw provider API call, no network request, no credential lookup, no
vault or evidence mutation, no remote push, no publication, and no
cross-subsystem call. It only inspects the value passed in by the caller.

The renderer grants no execution authority. Every rendered gate result stays
advisory-only and always requires human review, matching the Judge authority
locks in ``src/hisys/judge/ralph.md``. Even an ``advisory_pass`` result
explicitly states that it does not authorize any execution, mutation,
publication, or removal of human review; a human reviewer must decide.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .decision_packet import (
    JUDGE_VERDICTS,
    SCHEMA_VALIDITY_WARNING,
    JudgeAdvisoryDecisionPacket,
    validate_judge_decision_packet,
)

JUDGE_GATE_STATUS_BY_VERDICT: dict[str, str] = {
    verdict: f"advisory_{verdict}" for verdict in JUDGE_VERDICTS
}

JUDGE_GATE_REJECTED_STATUS = "rejected"

JUDGE_GATE_NON_AUTHORIZATION_NOTE = (
    "This gate result is advisory only and does not authorize any execution, "
    "mutation, publication, or removal of human review. A human reviewer must "
    "decide before any action is taken."
)


@dataclass(frozen=True)
class JudgeGateResult:
    """A deterministic, human-readable Judge advisory gate result.

    ``rendered`` is ``True`` only when a valid decision packet was rendered. A
    rejected result (an invalid mapping or unsupported source) carries the
    deterministic validation ``failures`` and the rejected gate status. The
    authority locks are pinned: a gate result never grants execution authority
    and always requires human review, including for an ``advisory_pass``.
    """

    rendered: bool
    gate_status: str
    headline: str
    body: str
    verdict: str | None = None
    packet_id: str | None = None
    packet: JudgeAdvisoryDecisionPacket | None = None
    failures: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    advisory_only: bool = True
    requires_human_review: bool = True


def _render_ref_lines(refs: tuple[str, ...]) -> str:
    if not refs:
        return "  (none)"
    return "\n".join(f"  - {ref}" for ref in refs)


def _render_valid_body(
    packet: JudgeAdvisoryDecisionPacket, gate_status: str
) -> str:
    return "\n".join(
        (
            "Judge Advisory Gate Result",
            "==========================",
            f"Packet: {packet.packet_id}",
            f"Subject: {packet.decision_subject_ref}",
            f"Verdict: {packet.verdict}",
            f"Gate status: {gate_status}",
            "Advisory only: yes",
            "Requires human review: yes",
            "",
            "Rationale:",
            f"  {packet.rationale}",
            "",
            "Evidence refs:",
            _render_ref_lines(packet.evidence_refs),
            "",
            "Opposition refs:",
            _render_ref_lines(packet.opposition_refs),
            "",
            f"Note: {JUDGE_GATE_NON_AUTHORIZATION_NOTE}",
        )
    )


def _render_rejected_body(failures: tuple[str, ...]) -> str:
    return "\n".join(
        (
            "Judge Advisory Gate Result",
            "==========================",
            "Status: rejected (decision packet failed validation)",
            f"Gate status: {JUDGE_GATE_REJECTED_STATUS}",
            "Advisory only: yes",
            "Requires human review: yes",
            "",
            "Validation failures:",
            _render_ref_lines(failures),
            "",
            f"Note: {JUDGE_GATE_NON_AUTHORIZATION_NOTE}",
        )
    )


def _rejected_result(failures: tuple[str, ...]) -> JudgeGateResult:
    return JudgeGateResult(
        rendered=False,
        gate_status=JUDGE_GATE_REJECTED_STATUS,
        headline=(
            "Judge advisory gate: REJECTED "
            "(decision packet failed validation; human review required)"
        ),
        body=_render_rejected_body(failures),
        failures=failures,
    )


def _rendered_result(
    packet: JudgeAdvisoryDecisionPacket, warnings: tuple[str, ...]
) -> JudgeGateResult:
    gate_status = JUDGE_GATE_STATUS_BY_VERDICT[packet.verdict]
    headline = (
        f"Judge advisory gate: {gate_status.upper()} (human review required)"
    )
    return JudgeGateResult(
        rendered=True,
        gate_status=gate_status,
        headline=headline,
        body=_render_valid_body(packet, gate_status),
        verdict=packet.verdict,
        packet_id=packet.packet_id,
        packet=packet,
        warnings=warnings,
    )


def render_judge_gate_result(
    source: JudgeAdvisoryDecisionPacket | Mapping[str, Any] | Any,
) -> JudgeGateResult:
    """Render a deterministic advisory gate result from a packet or mapping.

    ``source`` may be a validated :class:`JudgeAdvisoryDecisionPacket` or an
    already-prepared local packet mapping. A mapping is validated through
    :func:`validate_judge_decision_packet` first; if validation fails, the
    returned result is a rejected (non-rendered) gate result carrying the
    deterministic failure codes. The function never mutates ``source`` and
    performs no external action of any kind.
    """

    if isinstance(source, JudgeAdvisoryDecisionPacket):
        return _rendered_result(source, (SCHEMA_VALIDITY_WARNING,))

    if isinstance(source, Mapping):
        validation = validate_judge_decision_packet(source)
        if not validation.valid or validation.packet is None:
            return _rejected_result(validation.failures)
        return _rendered_result(validation.packet, validation.warnings)

    return _rejected_result(("judge_gate_result_unsupported_source",))


__all__ = [
    "JUDGE_GATE_NON_AUTHORIZATION_NOTE",
    "JUDGE_GATE_REJECTED_STATUS",
    "JUDGE_GATE_STATUS_BY_VERDICT",
    "JudgeGateResult",
    "render_judge_gate_result",
]
