"""Hardware sensor mock adapter.

Traceability: HISYS-FR-DS-001..002, HISYS-FIXTURE-001 (hardware-mock-temperature),
HISYS-T-003.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..core.ids import IdNamespace, make_id
from ..core.time import utc_now
from ..schemas.observation import DataQuality, ProvenanceBundle
from .base import DataSource, RawCollectionResult, _hash_payload


class HardwareMockSource(DataSource):
    """Reads a fixed payload from in-memory fixture data."""

    def __init__(self, source, *, payload: dict[str, Any], device_identity: str = "mock-device") -> None:
        super().__init__(source)
        self._payload = payload
        self._device_identity = device_identity

    def collect(self, collection_context: Mapping[str, Any] | None = None) -> RawCollectionResult:
        run_id = make_id(IdNamespace.COLLECTION_RUN)
        provenance = ProvenanceBundle(
            collector_kind="hardware_sensor",
            method="mock_in_memory",
            device_identity=self._device_identity,
            calibration_ref="cal-mock-001",
        )
        anomalies = ["over_threshold"] if self._payload.get("temperature_c", 0) > 80 else []
        quality = DataQuality(
            completeness="full",
            freshness="current",
            anomaly_flags=anomalies,
            source_confidence=0.9,
        )
        payload_ref = f"fixture://hardware/{run_id}.json"
        return RawCollectionResult(
            source_id=self.source.source_id,
            collection_run_id=run_id,
            collected_at=utc_now(),
            payload=self._payload,
            payload_ref=payload_ref,
            payload_hash=_hash_payload(self._payload),
            provenance_bundle=provenance,
            data_quality=quality,
        )
