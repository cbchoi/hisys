"""Registry-gated adapter runtime and failure isolation.

Traceability:
- HISYS-IDD-001 HISYS-IF-003 (DataSource Adapter Contract) and HISYS-IF-015
  (Health Status).
- HISYS-FR-DS-001..006, HISYS-NFR-REL-001, HISYS-CON-014.
- HISYS-T-003..006 including HISYS-T-005A.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from ..registry import SourceBlockedError, SourceRegistry
from .base import AdapterErrorRecord, DataSource, HealthStatus, RawCollectionResult


@dataclass(frozen=True)
class AdapterCollectionOutcome:
    """Result for one adapter collection attempt."""

    source_id: str
    result: RawCollectionResult | None = None
    error: AdapterErrorRecord | None = None

    @property
    def ok(self) -> bool:
        return self.result is not None and self.error is None


@dataclass(frozen=True)
class AdapterRunReport:
    """Batch report preserving successes and failures independently."""

    outcomes: dict[str, AdapterCollectionOutcome] = field(default_factory=dict)

    @property
    def successes(self) -> dict[str, RawCollectionResult]:
        return {
            source_id: outcome.result
            for source_id, outcome in self.outcomes.items()
            if outcome.result is not None
        }

    @property
    def errors(self) -> dict[str, AdapterErrorRecord]:
        return {
            source_id: outcome.error
            for source_id, outcome in self.outcomes.items()
            if outcome.error is not None
        }


class AdapterRuntime:
    """Executes adapters through source governance and bounded failures."""

    def __init__(self, registry: SourceRegistry, adapters: Mapping[str, DataSource]) -> None:
        self.registry = registry
        self.adapters = dict(adapters)

    def health_report(self) -> dict[str, HealthStatus]:
        report: dict[str, HealthStatus] = {}
        for source_id, adapter in self.adapters.items():
            try:
                self.registry.assert_collectable(source_id)
                report[source_id] = adapter.health_check()
            except Exception as exc:  # bounded health failure; do not stop report
                report[source_id] = HealthStatus(source_id, healthy=False, detail=str(exc))
        return report

    def collect_one(
        self,
        source_id: str,
        collection_context: Mapping[str, object] | None = None,
    ) -> AdapterCollectionOutcome:
        adapter = self.adapters[source_id]
        try:
            self.registry.assert_collectable(source_id)
            result = adapter.collect(collection_context)
            return AdapterCollectionOutcome(source_id=source_id, result=result)
        except Exception as exc:
            return AdapterCollectionOutcome(
                source_id=source_id,
                error=adapter.report_error(
                    exc,
                    context={"stage": "collect_one", "source_id": source_id},
                    recoverable=not isinstance(exc, SourceBlockedError),
                ),
            )

    def collect_all(
        self,
        collection_context: Mapping[str, object] | None = None,
    ) -> AdapterRunReport:
        outcomes: dict[str, AdapterCollectionOutcome] = {}
        for source_id in self.adapters:
            outcomes[source_id] = self.collect_one(source_id, collection_context)
        return AdapterRunReport(outcomes=outcomes)


__all__ = ["AdapterCollectionOutcome", "AdapterRunReport", "AdapterRuntime"]
