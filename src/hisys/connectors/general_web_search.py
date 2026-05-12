"""Governed general web-search connector with injectable fixture transport.

This connector records search-result evidence from an explicit fixture transport
only. It does not implement unrestricted live web search; the live-network
boundary must be enabled by future approved deployment policy.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .live_source_evidence import SourceAccessRecord, SourceEvidenceItem


@dataclass(frozen=True)
class GeneralWebSearchEvidencePackage:
    """Persisted governed search evidence refs."""

    access_record: SourceAccessRecord
    evidence_items: list[SourceEvidenceItem]
    access_ref: str
    evidence_ref: str


class GeneralWebSearchConnector:
    """Collect governed search results into provenance evidence."""

    def collect_provider_results(
        self,
        *,
        request_id: str,
        query: str,
        provider_name: str,
        provider_url_ref: str,
        provider_payload: dict[str, Any],
        output_root: Path,
        yyyymmdd: str,
    ) -> GeneralWebSearchEvidencePackage:
        """Collect approved provider JSON into provenance evidence without persisting endpoint values."""

        raw = json.dumps(provider_payload, ensure_ascii=False, sort_keys=True)
        result = _first_result(provider_payload)
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        title = str(result.get("title") or f"{provider_name} search result")
        url = str(result.get("url") or f"search-provider://{provider_name}/{query}")
        snippet = str(result.get("snippet") or title)
        access_id = f"ACCESS-{request_id}-{self.connector_id}"
        evidence_id = f"EVID-{request_id}-{self.connector_id}"
        access_ref = f"runtime-boundary/source-connectors/{yyyymmdd}/source-access-{access_id}.json"
        evidence_ref = f"runtime-boundary/source-connectors/{yyyymmdd}/source-evidence-{evidence_id}.json"
        access = SourceAccessRecord(
            access_id=access_id,
            request_id=request_id,
            connector_id=self.connector_id,
            source_url=f"search-provider-ref://{provider_url_ref}",
            accessed_at=f"{yyyymmdd}T00:00:00Z",
            http_status=200,
            content_type="application/json",
            title=title,
            license_signal="not_applicable",
            sha256=digest,
            external_call_made=True,
            policy_refs=["docs/use-cases/live-research-connectors.md", "POLICY-LIVE-SEARCH-001"],
        )
        evidence = SourceEvidenceItem(
            evidence_id=evidence_id,
            access_ref=access_ref,
            quoted_text=snippet,
            interpretation=f"Approved {provider_name} search result for query '{query}' from {url}.",
            claim_type="source_evidence",
            confidence="medium",
            uncertainty="Provider ranking and retrieval are external signals; use with citation and follow-up evidence checks.",
        )
        output_dir = output_root / "runtime-boundary" / "source-connectors" / yyyymmdd
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_root / access_ref).write_text(_json_dump(access), encoding="utf-8")
        (output_root / evidence_ref).write_text(_json_dump(evidence), encoding="utf-8")
        return GeneralWebSearchEvidencePackage(
            access_record=access,
            evidence_items=[evidence],
            access_ref=access_ref,
            evidence_ref=evidence_ref,
        )

    def __init__(self, *, connector_id: str = "general_web_search") -> None:
        self.connector_id = connector_id

    def collect_fixture(
        self,
        *,
        request_id: str,
        query: str,
        fixture_path: Path,
        output_root: Path,
        yyyymmdd: str,
    ) -> GeneralWebSearchEvidencePackage:
        raw = fixture_path.read_text(encoding="utf-8")
        payload = json.loads(raw)
        result = _first_result(payload)
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        title = str(result.get("title") or "fixture search result")
        url = str(result.get("url") or f"search://{query}")
        snippet = str(result.get("snippet") or title)
        access_id = f"ACCESS-{request_id}-{self.connector_id}"
        evidence_id = f"EVID-{request_id}-{self.connector_id}"
        access_ref = f"runtime-boundary/source-connectors/{yyyymmdd}/source-access-{access_id}.json"
        evidence_ref = f"runtime-boundary/source-connectors/{yyyymmdd}/source-evidence-{evidence_id}.json"
        access = SourceAccessRecord(
            access_id=access_id,
            request_id=request_id,
            connector_id=self.connector_id,
            source_url=f"search://{query}",
            accessed_at=f"{yyyymmdd}T00:00:00Z",
            http_status=200,
            content_type="application/json",
            title=title,
            license_signal="not_applicable",
            sha256=digest,
            external_call_made=False,
            policy_refs=["docs/use-cases/live-research-connectors.md", "POLICY-LIVE-SEARCH-001"],
        )
        evidence = SourceEvidenceItem(
            evidence_id=evidence_id,
            access_ref=access_ref,
            quoted_text=snippet,
            interpretation=f"Fixture-backed general search result for query '{query}' from {url}.",
            claim_type="source_evidence",
            confidence="medium",
            uncertainty="Search-A uses injected fixture transport only; live provider ranking and retrieval remain approval-gated.",
        )
        output_dir = output_root / "runtime-boundary" / "source-connectors" / yyyymmdd
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_root / access_ref).write_text(_json_dump(access), encoding="utf-8")
        (output_root / evidence_ref).write_text(_json_dump(evidence), encoding="utf-8")
        return GeneralWebSearchEvidencePackage(
            access_record=access,
            evidence_items=[evidence],
            access_ref=access_ref,
            evidence_ref=evidence_ref,
        )


def _first_result(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("search fixture must be a JSON object")
    results = payload.get("results")
    if not isinstance(results, list) or not results or not isinstance(results[0], dict):
        raise ValueError("search fixture must contain at least one object result")
    return results[0]


def _json_dump(record: SourceAccessRecord | SourceEvidenceItem) -> str:
    return json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


__all__ = ["GeneralWebSearchConnector", "GeneralWebSearchEvidencePackage"]
