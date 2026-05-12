"""Read-only DOI metadata connector for manual smoke testing.

This module supports Live-C by isolating the public metadata call behind an
injectable transport. Unit tests use a fake transport; CI must not perform live
network calls.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import quote
from urllib.request import Request, urlopen

from .live_source_evidence import SourceAccessRecord, SourceEvidenceItem

FetchFn = Callable[[str], tuple[int, str, str]]


@dataclass(frozen=True)
class DoiMetadataEvidencePackage:
    """Persisted DOI metadata evidence refs."""

    access_record: SourceAccessRecord
    evidence_items: list[SourceEvidenceItem]
    access_ref: str
    evidence_ref: str


class DoiMetadataConnector:
    """Collect Crossref DOI metadata through a read-only injected transport."""

    connector_id = "doi_metadata_search"

    def __init__(self, *, fetch: FetchFn | None = None) -> None:
        self._fetch = fetch or _urllib_fetch
        self._external_call_made = fetch is None

    def collect(self, *, request_id: str, doi: str, output_root: Path, yyyymmdd: str) -> DoiMetadataEvidencePackage:
        encoded = quote(doi, safe="")
        url = f"https://api.crossref.org/works/{encoded}"
        status, content_type, body = self._fetch(url)
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        metadata = json.loads(body)
        message = metadata.get("message", {}) if isinstance(metadata, dict) else {}
        title = _first_text(message.get("title")) or message.get("DOI") or doi
        publisher = str(message.get("publisher") or "unknown publisher")
        landing_url = str(message.get("URL") or f"https://doi.org/{doi}")
        quoted = f"{title} | DOI: {message.get('DOI', doi)} | publisher: {publisher} | URL: {landing_url}"
        access_id = f"ACCESS-{request_id}-{self.connector_id}"
        evidence_id = f"EVID-{request_id}-{self.connector_id}"
        access_ref = f"runtime-boundary/source-connectors/{yyyymmdd}/source-access-{access_id}.json"
        evidence_ref = f"runtime-boundary/source-connectors/{yyyymmdd}/source-evidence-{evidence_id}.json"
        access = SourceAccessRecord(
            access_id=access_id,
            request_id=request_id,
            connector_id=self.connector_id,
            source_url=url,
            accessed_at=f"{yyyymmdd}T00:00:00Z",
            http_status=status,
            content_type=content_type,
            title=title,
            license_signal="not_applicable",
            sha256=digest,
            external_call_made=self._external_call_made,
            policy_refs=["docs/use-cases/live-research-connectors.md"],
        )
        evidence = SourceEvidenceItem(
            evidence_id=evidence_id,
            access_ref=access_ref,
            quoted_text=quoted,
            interpretation="Read-only DOI metadata confirms source identity and publisher/landing-page metadata for downstream evidence validation.",
            claim_type="source_evidence",
            confidence="medium",
            uncertainty="Metadata smoke validates public metadata retrieval only; it does not validate full-text novelty claims.",
        )
        output_dir = output_root / "runtime-boundary" / "source-connectors" / yyyymmdd
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_root / access_ref).write_text(_json_dump(access), encoding="utf-8")
        (output_root / evidence_ref).write_text(_json_dump(evidence), encoding="utf-8")
        return DoiMetadataEvidencePackage(
            access_record=access,
            evidence_items=[evidence],
            access_ref=access_ref,
            evidence_ref=evidence_ref,
        )


def _first_text(value: object) -> str:
    if isinstance(value, list) and value:
        return str(value[0])
    if isinstance(value, str):
        return value
    return ""


def _json_dump(record: SourceAccessRecord | SourceEvidenceItem) -> str:
    return json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _urllib_fetch(url: str) -> tuple[int, str, str]:
    request = Request(url, headers={"User-Agent": "Hisys manual metadata smoke/0.1 (mailto:operator@example.invalid)"})
    with urlopen(request, timeout=20) as response:  # noqa: S310 - gated by CLI/env/approval; not used in CI tests.
        status = int(getattr(response, "status", 200))
        content_type = response.headers.get_content_type()
        body = response.read().decode("utf-8")
    return status, content_type, body


__all__ = ["DoiMetadataConnector", "DoiMetadataEvidencePackage"]
