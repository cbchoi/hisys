"""DataSource adapter base contract.

Traceability: HISYS-IDD-001 Section 4 (initialize, health_check, collect,
normalize, capture_provenance, report_error); HISYS-FR-DS-001..002.

Implementations in this package are mocks. They never reach external
networks or hardware (HISYS-CON-022..023, HISYS-NFR-SEC-005).
"""

from __future__ import annotations

import abc
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping

from ..core.ids import IdNamespace, make_id
from ..core.time import utc_now
from ..schemas.observation import (
    DataQuality,
    ProvenanceBundle,
    RawObservation,
)
from ..schemas.source import SourceRegistryEntry


@dataclass(frozen=True)
class AdapterStatus:
    source_id: str
    initialized: bool
    detail: str = ""


@dataclass(frozen=True)
class HealthStatus:
    source_id: str
    healthy: bool
    detail: str = ""


@dataclass(frozen=True)
class RawCollectionResult:
    source_id: str
    collection_run_id: str
    collected_at: datetime
    payload: Any
    payload_ref: str
    payload_hash: str
    provenance_bundle: ProvenanceBundle
    data_quality: DataQuality
    extra: Mapping[str, Any] = field(default_factory=dict)


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(repr(payload).encode("utf-8")).hexdigest()


class DataSource(abc.ABC):
    """Common parent for hardware/web/agent/Hermes mock adapters."""

    def __init__(self, source: SourceRegistryEntry) -> None:
        self.source = source

    # HISYS-IDD-001 Section 4 minimum logical methods.
    def initialize(self, config_ref: str | None = None) -> AdapterStatus:
        return AdapterStatus(self.source.source_id, initialized=True, detail=config_ref or "")

    def health_check(self) -> HealthStatus:
        # Mocks are always healthy; subclasses may override.
        return HealthStatus(self.source.source_id, healthy=True, detail="mock")

    @abc.abstractmethod
    def collect(self, collection_context: Mapping[str, Any] | None = None) -> RawCollectionResult:
        ...

    def to_observation(
        self,
        result: RawCollectionResult,
        *,
        producer_id: str,
        retention_rule: str = "P30D",
        usage_constraints: list[str] | None = None,
    ) -> RawObservation:
        return RawObservation(
            observation_id=make_id(IdNamespace.OBSERVATION),
            source_id=result.source_id,
            collection_run_id=result.collection_run_id,
            collected_at=result.collected_at,
            collector_id=producer_id,
            payload_ref=result.payload_ref,
            payload_hash=result.payload_hash,
            provenance_bundle=result.provenance_bundle,
            data_quality=result.data_quality,
            usage_constraints=list(usage_constraints or self.source.usage_constraints),
            retention_rule=retention_rule,
            producer_id=producer_id,
            status="captured",
        )


__all__ = [
    "AdapterStatus",
    "HealthStatus",
    "DataSource",
    "RawCollectionResult",
    "_hash_payload",
]
