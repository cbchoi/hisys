"""DataSource adapter base contract.

Traceability: HISYS-IDD-001 Section 4 (initialize, health_check, collect,
normalize, capture_provenance, report_error); HISYS-FR-DS-001..006.

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


@dataclass(frozen=True)
class NormalizedObservationDraft:
    """Transport-neutral observation draft before immutable record write."""

    source_id: str
    collection_run_id: str
    collected_at: datetime
    payload_ref: str
    payload_hash: str
    provenance_bundle: ProvenanceBundle
    data_quality: DataQuality
    usage_constraints: list[str]
    retention_rule: str


@dataclass(frozen=True)
class AdapterErrorRecord:
    """Failure record emitted without blocking unrelated adapters."""

    source_id: str
    collection_run_id: str | None
    error_type: str
    message: str
    recoverable: bool = True
    timestamp: datetime = field(default_factory=utc_now)
    context: Mapping[str, Any] = field(default_factory=dict)


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

    def normalize(self, raw_result: RawCollectionResult) -> NormalizedObservationDraft:
        """Normalize subtype output into the common observation draft.

        Subclasses keep subtype-specific provenance in ``ProvenanceBundle``;
        the common draft prevents hardware/web/agent/Hermes details from being
        erased while giving the investigator runtime a stable boundary.
        """

        return NormalizedObservationDraft(
            source_id=raw_result.source_id,
            collection_run_id=raw_result.collection_run_id,
            collected_at=raw_result.collected_at,
            payload_ref=raw_result.payload_ref,
            payload_hash=raw_result.payload_hash,
            provenance_bundle=raw_result.provenance_bundle,
            data_quality=raw_result.data_quality,
            usage_constraints=list(self.source.usage_constraints),
            retention_rule=self.source.retention_rule,
        )

    def capture_provenance(self, raw_result: RawCollectionResult) -> ProvenanceBundle:
        """Return the subtype-specific provenance bundle for audit/storage."""

        return raw_result.provenance_bundle

    def report_error(
        self,
        error: BaseException,
        *,
        collection_run_id: str | None = None,
        context: Mapping[str, Any] | None = None,
        recoverable: bool = True,
    ) -> AdapterErrorRecord:
        """Convert adapter exceptions into bounded failure records."""

        return AdapterErrorRecord(
            source_id=self.source.source_id,
            collection_run_id=collection_run_id,
            error_type=type(error).__name__,
            message=str(error),
            recoverable=recoverable,
            context=dict(context or {}),
        )

    def to_observation(
        self,
        result: RawCollectionResult,
        *,
        producer_id: str,
        retention_rule: str | None = None,
        usage_constraints: list[str] | None = None,
    ) -> RawObservation:
        draft = self.normalize(result)
        return RawObservation(
            observation_id=make_id(IdNamespace.OBSERVATION),
            source_id=draft.source_id,
            collection_run_id=draft.collection_run_id,
            collected_at=draft.collected_at,
            collector_id=producer_id,
            payload_ref=draft.payload_ref,
            payload_hash=draft.payload_hash,
            provenance_bundle=draft.provenance_bundle,
            data_quality=draft.data_quality,
            usage_constraints=list(usage_constraints or draft.usage_constraints),
            retention_rule=retention_rule or draft.retention_rule,
            producer_id=producer_id,
            status="captured",
        )


__all__ = [
    "AdapterStatus",
    "HealthStatus",
    "DataSource",
    "RawCollectionResult",
    "NormalizedObservationDraft",
    "AdapterErrorRecord",
    "_hash_payload",
]
