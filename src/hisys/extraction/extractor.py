"""Fixture-backed I5 signal extractor.

Traceability: HISYS-FR-EXT-001..005, HISYS-DATA-002, HISYS-T-009,
HISYS-T-010.
"""

from __future__ import annotations

from ..core.ids import IdNamespace, make_id
from ..schemas import ExtractedSignal, RawObservation


class FixtureSignalExtractor:
    """Deterministic extractor for local fixture observations.

    The extractor produces interpretation records that reference observations;
    it never copies raw payload content into the signal body.
    """

    def __init__(self, *, method: str = "fixture-rule-v0") -> None:
        self.method = method

    def extract(self, observation: RawObservation) -> list[ExtractedSignal]:
        anomaly_flags = list(observation.data_quality.anomaly_flags)
        if anomaly_flags:
            return [self._anomaly_signal(observation, anomaly_flags)]
        return [self._fact_signal(observation)]

    def _anomaly_signal(
        self,
        observation: RawObservation,
        anomaly_flags: list[str],
    ) -> ExtractedSignal:
        primary_flag = anomaly_flags[0]
        return ExtractedSignal(
            signal_id=make_id(IdNamespace.SIGNAL, f"{observation.source_id}-{primary_flag}"),
            observation_refs=[observation.observation_id],
            signal_type="anomaly",
            claim_or_event=f"{observation.provenance_bundle.collector_kind} reported {primary_flag} anomaly",
            entities=[observation.source_id],
            confidence=observation.data_quality.source_confidence,
            uncertainty="bounded_by_fixture_rules",
            contradictions=[],
            extraction_method=self.method,
            version="1",
            producer_id=self.method,
            status="proposed",
        )

    def _fact_signal(self, observation: RawObservation) -> ExtractedSignal:
        return ExtractedSignal(
            signal_id=make_id(IdNamespace.SIGNAL, f"{observation.source_id}-captured"),
            observation_refs=[observation.observation_id],
            signal_type="fact",
            claim_or_event=f"{observation.provenance_bundle.collector_kind} observation captured",
            entities=[observation.source_id],
            confidence=observation.data_quality.source_confidence,
            uncertainty="bounded_by_fixture_rules",
            contradictions=[],
            extraction_method=self.method,
            version="1",
            producer_id=self.method,
            status="proposed",
        )


__all__ = ["FixtureSignalExtractor"]
