"""Agent-system mock adapter (e.g., DARS critique fixture).

Traceability: HISYS-FR-DS-004, HISYS-FR-AGT-* (advisory until approved),
HISYS-FIXTURE-001 (agent-dars-critique), HISYS-T-005.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..core.ids import IdNamespace, make_id
from ..core.time import utc_now
from ..schemas.observation import DataQuality, ProvenanceBundle
from .base import DataSource, RawCollectionResult, _hash_payload


class AgentSystemMockSource(DataSource):
    def __init__(
        self,
        source,
        *,
        payload: dict[str, Any],
        agent_identity: str,
        advisory_label: str = "advisory_only",
    ) -> None:
        super().__init__(source)
        self._payload = payload
        self._agent_identity = agent_identity
        self._advisory_label = advisory_label

    def collect(self, collection_context: Mapping[str, Any] | None = None) -> RawCollectionResult:
        run_id = make_id(IdNamespace.COLLECTION_RUN)
        provenance = ProvenanceBundle(
            collector_kind="agent_system",
            method="mock_handoff_file",
            agent_identity=self._agent_identity,
            agent_advisory_label=self._advisory_label,
        )
        quality = DataQuality(
            completeness="full",
            freshness="recent",
            anomaly_flags=[],
            source_confidence=0.6,
        )
        payload_ref = f"fixture://agent-system/{run_id}.json"
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
