"""Investigator collection runtime.

Traceability: HISYS-INST-INV-001, HISYS-D-015, HISYS-D-016,
HISYS-FR-INV-001..006, HISYS-FR-ADM-002, HISYS-T-007, HISYS-T-008.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from pydantic import BaseModel

from ..adapters import AdapterRuntime, DataSource
from ..adapters.base import AdapterErrorRecord
from ..audit import AuditJsonlWriter
from ..config import InstanceRoot
from ..core.ids import IdNamespace, make_id
from ..registry import SourceRegistry
from ..schemas import AuditEvent, RawObservation


@dataclass(frozen=True)
class CollectionReport:
    """Machine-checkable I4 collection report contract."""

    collection_run_id: str
    requested_source_ids: list[str]
    collected_observation_refs: list[str] = field(default_factory=list)
    skipped_source_ids: list[str] = field(default_factory=list)
    adapter_errors: dict[str, str] = field(default_factory=dict)
    audit_event_refs: list[str] = field(default_factory=list)
    hermes_trace_refs: list[str] = field(default_factory=list)
    health_summary: dict[str, str] = field(default_factory=dict)
    policy_refs: list[str] = field(default_factory=list)


class InvestigatorRuntime:
    """Registry-gated Investigator runtime for fixture-backed I4 collection."""

    def __init__(
        self,
        *,
        registry: SourceRegistry,
        adapters: Mapping[str, DataSource],
        instance: InstanceRoot,
        collector_id: str,
    ) -> None:
        self.registry = registry
        self.adapters = dict(adapters)
        self.instance = instance
        self.collector_id = collector_id
        self.adapter_runtime = AdapterRuntime(registry, self.adapters)
        self.audit_writer = AuditJsonlWriter(instance)

    def collect_run(self, source_ids: list[str], *, yyyymmdd: str) -> CollectionReport:
        run_id = make_id(IdNamespace.COLLECTION_RUN)
        observations: list[str] = []
        skipped: list[str] = []
        errors: dict[str, str] = {}
        audit_refs: list[str] = []
        hermes_refs: list[str] = []

        for source_id in source_ids:
            adapter = self.adapters.get(source_id)
            if adapter is None:
                skipped.append(source_id)
                errors[source_id] = "source adapter is not registered for this runtime"
                audit_refs.append(
                    self._audit(
                        yyyymmdd,
                        event_type="failure",
                        record_refs=[source_id],
                        summary=f"Skipped unregistered source adapter: {source_id}",
                        result="skipped",
                    )
                )
                continue

            outcome = self.adapter_runtime.collect_one(source_id, {"collection_run_id": run_id})
            if not outcome.ok or outcome.result is None:
                skipped.append(source_id)
                message = self._format_error(outcome.error)
                errors[source_id] = message
                audit_refs.append(
                    self._audit(
                        yyyymmdd,
                        event_type="failure",
                        record_refs=[source_id],
                        summary=message,
                        result="failure",
                    )
                )
                continue

            observation = adapter.to_observation(outcome.result, producer_id=self.collector_id)
            obs_path = self._write_observation(observation, yyyymmdd)
            observations.append(observation.observation_id)
            audit_id = self._audit(
                yyyymmdd,
                event_type="collection_run",
                record_refs=[observation.observation_id, str(obs_path)],
                summary=f"Collected RawObservation {observation.observation_id} from {source_id}",
                result="success",
            )
            audit_refs.append(audit_id)

            build_trace = getattr(adapter, "build_trace", None)
            if callable(build_trace):
                trace = build_trace(
                    producer_id=self.collector_id,
                    observation_refs=[observation.observation_id],
                    audit_event_refs=[audit_id],
                )
                trace_path = self._write_hermes_trace(trace, yyyymmdd)
                hermes_refs.append(str(trace_path))

        health = {
            source_id: ("healthy" if status.healthy else f"unhealthy: {status.detail}")
            for source_id, status in self.adapter_runtime.health_report().items()
        }
        return CollectionReport(
            collection_run_id=run_id,
            requested_source_ids=list(source_ids),
            collected_observation_refs=observations,
            skipped_source_ids=skipped,
            adapter_errors=errors,
            audit_event_refs=audit_refs,
            hermes_trace_refs=hermes_refs,
            health_summary=health,
            policy_refs=["HISYS-INST-INV-001", "HISYS-D-015", "HISYS-D-016"],
        )

    def _write_observation(self, observation: RawObservation, yyyymmdd: str) -> Path:
        directory = self.instance.raw_observations_dir(yyyymmdd)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{observation.observation_id}.json"
        path.write_text(_to_json(observation), encoding="utf-8")
        return path

    def _write_hermes_trace(self, trace: BaseModel, yyyymmdd: str) -> Path:
        directory = self.instance.hermes_traces_dir(yyyymmdd)
        directory.mkdir(parents=True, exist_ok=True)
        name = f"HTRACE-{trace.campaign_id}.json"
        path = directory / name
        path.write_text(_to_json(trace), encoding="utf-8")
        return path

    def _audit(
        self,
        yyyymmdd: str,
        *,
        event_type: str,
        record_refs: list[str],
        summary: str,
        result: str,
    ) -> str:
        event = AuditEvent(
            audit_id=make_id(IdNamespace.AUDIT),
            event_type=event_type,
            actor_id=self.collector_id,
            record_refs=record_refs,
            summary=summary,
            result=result,
            producer_id=self.collector_id,
            status=result,
        )
        self.audit_writer.append(event, yyyymmdd=yyyymmdd)
        return event.audit_id

    @staticmethod
    def _format_error(error: AdapterErrorRecord | None) -> str:
        if error is None:
            return "unknown adapter error"
        return f"{error.source_id}: {error.error_type}: {error.message}"


def _to_json(record: BaseModel) -> str:
    return json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True)


__all__ = ["CollectionReport", "InvestigatorRuntime"]
