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
from typing import Any, Iterable, Mapping

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

JUDGE_PANEL_MALFORMED_GATE_STATUS = "malformed"

# Ascending restrictiveness of an advisory gate status: ``advisory_pass`` is the
# least blocking outcome and ``rejected`` (a packet that failed validation) the
# most. ``needs_human_review`` is a soft hold ranked below a determined ``fail``,
# which in turn ranks below a hard ``block``. A status that is missing or
# unrecognized is treated as the most restrictive (see ``_restrictiveness``) so
# the panel summary never under-reports how blocking a result set is.
JUDGE_GATE_STATUS_RESTRICTIVENESS: dict[str, int] = {
    "advisory_pass": 0,
    "advisory_needs_human_review": 1,
    "advisory_fail": 2,
    "advisory_block": 3,
    JUDGE_GATE_REJECTED_STATUS: 4,
}

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


def _project_decision_packet(
    packet: JudgeAdvisoryDecisionPacket,
) -> dict[str, Any]:
    return {
        "packet_id": packet.packet_id,
        "decision_subject_ref": packet.decision_subject_ref,
        "verdict": packet.verdict,
        "rationale": packet.rationale,
        "evidence_refs": list(packet.evidence_refs),
        "opposition_refs": list(packet.opposition_refs),
        "authority_locks": {
            "advisory_only": packet.advisory_only,
            "requires_human_review": packet.requires_human_review,
            "live_external_action_authorized": (
                packet.live_external_action_authorized
            ),
            "mutation_authorized": packet.mutation_authorized,
            "publication_authorized": packet.publication_authorized,
            "human_review_removal_authorized": (
                packet.human_review_removal_authorized
            ),
        },
    }


def build_judge_gate_result_packet(result: JudgeGateResult) -> dict[str, Any]:
    """Project a rendered gate result into a JSON-serializable mapping.

    Returns a plain, deterministic mapping built only from ``str``, ``bool``,
    ``None``, ``list``, and nested ``dict`` values so the advisory gate outcome
    can be consumed by local tooling (logging, status surfaces, fixtures). The
    function performs no I/O and no external action of any kind, does not mutate
    ``result``, and returns a fresh mapping on every call.

    The projection grants no execution authority: the top-level
    ``authority_locks`` pin ``advisory_only=true`` / ``requires_human_review=
    true``, the embedded ``decision_packet`` (when present) carries the packet's
    pinned advisory-only authority locks, and ``non_authorization_note`` repeats
    that a human reviewer must decide before any action is taken.
    """

    return {
        "subsystem": "judge",
        "kind": "advisory_gate_result",
        "rendered": result.rendered,
        "gate_status": result.gate_status,
        "verdict": result.verdict,
        "packet_id": result.packet_id,
        "headline": result.headline,
        "body": result.body,
        "failures": list(result.failures),
        "warnings": list(result.warnings),
        "authority_locks": {
            "advisory_only": result.advisory_only,
            "requires_human_review": result.requires_human_review,
        },
        "decision_packet": (
            _project_decision_packet(result.packet)
            if result.packet is not None
            else None
        ),
        "non_authorization_note": JUDGE_GATE_NON_AUTHORIZATION_NOTE,
    }


def _packet_gate_status(packet: Any) -> str:
    if isinstance(packet, Mapping):
        status = packet.get("gate_status")
        if isinstance(status, str) and status.strip() != "":
            return status
    return JUDGE_PANEL_MALFORMED_GATE_STATUS


def _restrictiveness(gate_status: str) -> int:
    return JUDGE_GATE_STATUS_RESTRICTIVENESS.get(
        gate_status, max(JUDGE_GATE_STATUS_RESTRICTIVENESS.values()) + 1
    )


def summarize_judge_gate_result_packets(
    packets: Iterable[Mapping[str, Any] | Any],
) -> dict[str, Any]:
    """Aggregate advisory gate-result packets into a bounded panel summary.

    ``packets`` is any iterable of the JSON-serializable mappings produced by
    :func:`build_judge_gate_result_packet`. The returned mapping is plain,
    deterministic, and JSON-serializable, carrying ``gate_status_counts`` (counts
    per gate status, ordered by status name), the ``most_restrictive_gate_status``
    present in the panel, and the pinned Judge authority locks. An entry that is
    not a mapping, or whose ``gate_status`` is missing or not a non-empty string,
    is counted under :data:`JUDGE_PANEL_MALFORMED_GATE_STATUS` and treated as the
    most restrictive outcome so the panel never under-reports how blocking the
    result set is. An empty panel reports ``packet_count=0``, no counts, and a
    ``None`` most-restrictive status.

    The function performs no I/O and no external action of any kind, does not
    mutate its inputs, and returns a fresh mapping on every call. It grants no
    execution authority: the ``authority_locks`` pin ``advisory_only=true`` /
    ``requires_human_review=true`` and ``non_authorization_note`` repeats that a
    human reviewer must decide before any action is taken.
    """

    statuses = [_packet_gate_status(packet) for packet in packets]

    counts: dict[str, int] = {}
    for status in statuses:
        counts[status] = counts.get(status, 0) + 1
    gate_status_counts = {status: counts[status] for status in sorted(counts)}

    most_restrictive = (
        max(
            gate_status_counts,
            key=lambda status: (_restrictiveness(status), status),
        )
        if gate_status_counts
        else None
    )

    return {
        "subsystem": "judge",
        "kind": "advisory_gate_result_panel_summary",
        "packet_count": len(statuses),
        "gate_status_counts": gate_status_counts,
        "most_restrictive_gate_status": most_restrictive,
        "authority_locks": {
            "advisory_only": True,
            "requires_human_review": True,
        },
        "non_authorization_note": JUDGE_GATE_NON_AUTHORIZATION_NOTE,
    }


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
    "JUDGE_GATE_STATUS_RESTRICTIVENESS",
    "JUDGE_PANEL_MALFORMED_GATE_STATUS",
    "JudgeGateResult",
    "build_judge_gate_result_packet",
    "render_judge_gate_result",
    "summarize_judge_gate_result_packets",
]
