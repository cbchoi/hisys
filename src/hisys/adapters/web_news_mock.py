"""Web/news mock adapter.

Traceability: HISYS-FR-DS-001, HISYS-FR-DS-003, HISYS-NFR-SEC-005,
HISYS-CON-022..023, HISYS-FIXTURE-001 (web-news-rss-permitted), HISYS-T-004.

This adapter never opens a network socket. It returns a deterministic
fixture payload supplied at construction time and records the citation
metadata needed for the compliance gate.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..core.ids import IdNamespace, make_id
from ..core.time import utc_now
from ..schemas.observation import DataQuality, ProvenanceBundle
from .base import DataSource, RawCollectionResult, _hash_payload


class WebNewsMockSource(DataSource):
    def __init__(
        self,
        source,
        *,
        payload: dict[str, Any],
        citation_url: str,
        citation_title: str,
        fetch_method: str = "mock_rss",
    ) -> None:
        super().__init__(source)
        self._payload = payload
        self._citation_url = citation_url
        self._citation_title = citation_title
        self._fetch_method = fetch_method

    def collect(self, collection_context: Mapping[str, Any] | None = None) -> RawCollectionResult:
        run_id = make_id(IdNamespace.COLLECTION_RUN)
        provenance = ProvenanceBundle(
            collector_kind="web_news",
            method=self._fetch_method,
            citation_url=self._citation_url,
            citation_title=self._citation_title,
            fetch_method=self._fetch_method,
        )
        quality = DataQuality(
            completeness="full",
            freshness="recent",
            anomaly_flags=[],
            source_confidence=0.7,
        )
        payload_ref = f"fixture://web-news/{run_id}.json"
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
