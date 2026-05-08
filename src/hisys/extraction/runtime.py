"""I5 extraction runtime.

Traceability: HISYS-FR-EXT-001..005, HISYS-DATA-002, HISYS-D-015,
HISYS-T-009, HISYS-T-010.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Protocol

from pydantic import BaseModel

from ..config import InstanceRoot
from ..schemas import ExtractedSignal, RawObservation


class SignalExtractor(Protocol):
    """Protocol for evidence-to-signal extractors."""

    def extract(self, observation: RawObservation) -> list[ExtractedSignal]:
        """Return interpretation records that reference, but do not copy, evidence."""


@dataclass(frozen=True)
class ExtractionReport:
    """Machine-checkable I5 extraction report."""

    requested_observation_refs: list[str]
    extracted_signal_refs: list[str] = field(default_factory=list)
    skipped_observation_refs: list[str] = field(default_factory=list)
    policy_refs: list[str] = field(
        default_factory=lambda: ["HISYS-FR-EXT-001", "HISYS-DATA-002"]
    )


class ExtractionRuntime:
    """Persist extracted signals under the runtime instance root."""

    def __init__(
        self,
        *,
        instance: InstanceRoot,
        extractor: SignalExtractor,
        producer_id: str,
    ) -> None:
        self.instance = instance
        self.extractor = extractor
        self.producer_id = producer_id

    def extract_run(
        self,
        observations: Iterable[RawObservation],
        *,
        yyyymmdd: str,
    ) -> ExtractionReport:
        requested: list[str] = []
        signal_refs: list[str] = []
        skipped: list[str] = []
        for observation in observations:
            requested.append(observation.observation_id)
            signals = self.extractor.extract(observation)
            if not signals:
                skipped.append(observation.observation_id)
                continue
            for signal in signals:
                self._write_signal(signal, yyyymmdd)
                signal_refs.append(signal.signal_id)
        return ExtractionReport(
            requested_observation_refs=requested,
            extracted_signal_refs=signal_refs,
            skipped_observation_refs=skipped,
        )

    def _write_signal(self, signal: ExtractedSignal, yyyymmdd: str) -> Path:
        directory = self.instance.root / "data" / "extracted-signals" / yyyymmdd
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{signal.signal_id}.json"
        path.write_text(_to_json(signal), encoding="utf-8")
        return path


def _to_json(record: BaseModel) -> str:
    return json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True)


__all__ = ["ExtractionReport", "ExtractionRuntime", "SignalExtractor"]
