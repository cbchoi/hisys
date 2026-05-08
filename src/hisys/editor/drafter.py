"""Fixture-backed I6 memo drafter.

Traceability: HISYS-FR-PER-001..004, HISYS-FR-MEM-001..005,
HISYS-DATA-002, HISYS-T-011, HISYS-T-012.
"""

from __future__ import annotations

from ..core.ids import IdNamespace, make_id
from ..schemas import ExtractedSignal, PerspectiveProfile, RawObservation, ZettelMemo


class FixtureMemoDrafter:
    """Deterministic Associate Editor fixture drafter.

    The drafter creates interpretation memo drafts from signal records and
    evidence references without copying raw payload values into the memo body.
    """

    def __init__(self, *, template_id: str) -> None:
        self.template_id = template_id

    def draft(
        self,
        signal: ExtractedSignal,
        *,
        perspective: PerspectiveProfile,
        observations: list[RawObservation],
    ) -> ZettelMemo:
        observation_ids = set(signal.observation_refs)
        matched_observations = [obs for obs in observations if obs.observation_id in observation_ids]
        source_refs = sorted({obs.source_id for obs in matched_observations})
        if not source_refs:
            source_refs = sorted(signal.entities)[:1]
        title = f"{perspective.title}: {signal.signal_type} signal"
        body = _format_memo_body(signal, perspective, matched_observations, self.template_id)
        return ZettelMemo(
            memo_id=make_id(IdNamespace.MEMO),
            title=title,
            summary=signal.claim_or_event,
            body=body,
            source_refs=source_refs,
            signal_refs=[signal.signal_id],
            perspective_id=perspective.perspective_id,
            confidence=signal.confidence,
            tags=[
                "hisys",
                "zettel-draft",
                f"perspective:{perspective.perspective_id}",
                f"signal-type:{signal.signal_type}",
            ],
            links=[*signal.observation_refs],
            revision="1",
            review_status="draft",
            status="draft",
            producer_id="fixture-memo-drafter",
        )


def _format_memo_body(
    signal: ExtractedSignal,
    perspective: PerspectiveProfile,
    observations: list[RawObservation],
    template_id: str,
) -> str:
    observation_refs = ", ".join(signal.observation_refs)
    source_refs = ", ".join(sorted({obs.source_id for obs in observations})) or "unresolved"
    focus = ", ".join(perspective.focus_areas) or "general review"
    return "\n".join(
        [
            f"# {perspective.title}",
            "",
            f"Template: `{template_id}`",
            f"Perspective: `{perspective.perspective_id}`",
            f"Focus: {focus}",
            "",
            "## Atomic Claim",
            signal.claim_or_event,
            "",
            "## Trace References",
            f"- signal_id: `{signal.signal_id}`",
            f"- observation_refs: {observation_refs}",
            f"- source_refs: {source_refs}",
            "",
            "## Confidence and Uncertainty",
            f"- confidence: {signal.confidence}",
            f"- uncertainty: {signal.uncertainty}",
            f"- contradictions: {', '.join(signal.contradictions) if signal.contradictions else 'none'}",
            "",
            "## Editorial Status",
            "Draft for review; evidence remains in linked RawObservation records.",
            "",
        ]
    )


__all__ = ["FixtureMemoDrafter"]
