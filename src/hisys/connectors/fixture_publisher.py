"""Local fixture publisher page connector.

This connector reads publisher-shaped static HTML fixtures only. It never opens a
network connection and exists to validate evidence/provenance shape before live
source adapters are considered.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from html import unescape
from pathlib import Path

from .live_source_evidence import SourceAccessRecord, SourceEvidenceItem


@dataclass(frozen=True)
class FixturePublisherEvidencePackage:
    """Persisted fixture publisher evidence refs."""

    access_record: SourceAccessRecord
    evidence_items: list[SourceEvidenceItem]
    access_ref: str
    evidence_ref: str


class FixturePublisherConnector:
    """Read local static publisher HTML fixtures into source evidence records."""

    def __init__(self, *, connector_id: str = "fixture_publisher_page_reader") -> None:
        self.connector_id = connector_id

    def collect(self, *, request_id: str, fixture_path: Path, output_root: Path, yyyymmdd: str) -> FixturePublisherEvidencePackage:
        html = fixture_path.read_text(encoding="utf-8")
        digest = hashlib.sha256(html.encode("utf-8")).hexdigest()
        title = _extract_tag_text(html, "title") or fixture_path.stem
        quoted = _extract_class_text(html, "abstract") or _strip_html(html)
        access_id = f"ACCESS-{request_id}-{self.connector_id}"
        evidence_id = f"EVID-{request_id}-{self.connector_id}"
        access = SourceAccessRecord(
            access_id=access_id,
            request_id=request_id,
            connector_id=self.connector_id,
            source_url=f"file://{fixture_path}",
            accessed_at=f"{yyyymmdd}T00:00:00Z",
            http_status=None,
            content_type="text/html",
            title=title,
            license_signal="open_access" if "open access" in html.lower() else "not_applicable",
            sha256=digest,
            external_call_made=False,
            policy_refs=["docs/use-cases/live-research-connectors.md"],
        )
        evidence = SourceEvidenceItem(
            evidence_id=evidence_id,
            access_ref=f"runtime-boundary/source-connectors/{yyyymmdd}/source-access-{access_id}.json",
            quoted_text=quoted,
            interpretation=(
                "Fixture publisher evidence supports the research-gap criterion that self-organizing structure "
                "formalisms need a unified account of local rewrite rules, feedback, topology/behavior co-evolution, "
                "and executable/analyzable semantics."
            ),
            claim_type="source_evidence",
            confidence="medium",
            uncertainty="Fixture page validates evidence shape only; publisher-source validation is still required.",
        )
        output_dir = output_root / "runtime-boundary" / "source-connectors" / yyyymmdd
        output_dir.mkdir(parents=True, exist_ok=True)
        access_ref = f"runtime-boundary/source-connectors/{yyyymmdd}/source-access-{access_id}.json"
        evidence_ref = f"runtime-boundary/source-connectors/{yyyymmdd}/source-evidence-{evidence_id}.json"
        (output_root / access_ref).write_text(_json_dump(access), encoding="utf-8")
        (output_root / evidence_ref).write_text(_json_dump(evidence), encoding="utf-8")
        return FixturePublisherEvidencePackage(
            access_record=access,
            evidence_items=[evidence],
            access_ref=access_ref,
            evidence_ref=evidence_ref,
        )


def _json_dump(record: SourceAccessRecord | SourceEvidenceItem) -> str:
    return json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _extract_tag_text(html: str, tag: str) -> str:
    match = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", html, flags=re.IGNORECASE | re.DOTALL)
    return _normalize_text(match.group(1)) if match else ""


def _extract_class_text(html: str, class_name: str) -> str:
    match = re.search(rf"<[^>]+class=[\"'][^\"']*{class_name}[^\"']*[\"'][^>]*>(.*?)</[^>]+>", html, flags=re.IGNORECASE | re.DOTALL)
    return _normalize_text(match.group(1)) if match else ""


def _strip_html(html: str) -> str:
    return _normalize_text(re.sub(r"<[^>]+>", " ", html))


def _normalize_text(text: str) -> str:
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", text)).split())


__all__ = ["FixturePublisherConnector", "FixturePublisherEvidencePackage"]
