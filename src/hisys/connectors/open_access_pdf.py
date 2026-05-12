"""Fixture-first legal open-access PDF collector.

This connector validates the PDF provenance/evidence record shape using local
fixtures before any live PDF retrieval can be manually approved. CI must use
`collect_fixture`; live transport is introduced only through the smoke CLI gate.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import hashlib
import json
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal, TypedDict

from .live_source_evidence import SourceAccessRecord, SourceEvidenceItem


class PdfTransportResponse(TypedDict):
    status_code: int
    content_type: str
    content: bytes


PdfTransport = Callable[[str], PdfTransportResponse]


@dataclass(frozen=True)
class OpenAccessPdfEvidencePackage:
    """Persisted open-access PDF evidence refs."""

    access_record: SourceAccessRecord
    evidence_items: list[SourceEvidenceItem]
    access_ref: str
    evidence_ref: str


class OpenAccessPdfConnector:
    """Collect OA PDF bytes into governed source evidence records."""

    connector_id = "open_access_pdf_fetch"

    def __init__(self, *, transport: PdfTransport | None = None) -> None:
        self._transport = transport or _urllib_pdf_transport
        self._external_call_made = transport is None

    def collect_fixture(
        self,
        *,
        request_id: str,
        fixture_path: Path,
        source_url: str,
        license_signal: Literal["open_access", "closed", "unknown", "not_applicable"],
        output_root: Path,
        yyyymmdd: str,
    ) -> OpenAccessPdfEvidencePackage:
        """Collect a local PDF fixture only after legal OA evidence is present."""

        if license_signal != "open_access":
            raise ValueError("PDF collection requires license_signal=open_access before bytes are persisted")
        pdf_bytes = fixture_path.read_bytes()
        digest = hashlib.sha256(pdf_bytes).hexdigest()
        access_id = f"ACCESS-{request_id}-{self.connector_id}"
        evidence_id = f"EVID-{request_id}-{self.connector_id}"
        access_ref = f"runtime-boundary/source-connectors/{yyyymmdd}/source-access-{access_id}.json"
        evidence_ref = f"runtime-boundary/source-connectors/{yyyymmdd}/source-evidence-{evidence_id}.json"
        access = SourceAccessRecord(
            access_id=access_id,
            request_id=request_id,
            connector_id=self.connector_id,
            source_url=source_url,
            accessed_at=f"{yyyymmdd}T00:00:00Z",
            http_status=None,
            content_type="application/pdf",
            title=fixture_path.stem,
            license_signal="open_access",
            oa_pdf_url=source_url,
            sha256=digest,
            pdf_downloaded=True,
            external_call_made=False,
            policy_refs=["docs/use-cases/live-research-connectors.md"],
        )
        evidence = SourceEvidenceItem(
            evidence_id=evidence_id,
            access_ref=access_ref,
            quoted_text=(
                f"PDF bytes collected from legal open-access fixture {fixture_path.name}; "
                f"sha256={digest}; byte_count={len(pdf_bytes)}."
            ),
            interpretation=(
                "Fixture OA PDF collection validates license-gated full-text provenance and hash recording; "
                "it does not perform live PDF retrieval or establish publication-level claims."
            ),
            claim_type="source_evidence",
            confidence="medium",
            uncertainty="Fixture-only PDF collector; live OA PDF smoke still requires approval, allowlist, and operator env flag.",
        )
        output_dir = output_root / "runtime-boundary" / "source-connectors" / yyyymmdd
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_root / access_ref).write_text(_json_dump(access), encoding="utf-8")
        (output_root / evidence_ref).write_text(_json_dump(evidence), encoding="utf-8")
        return OpenAccessPdfEvidencePackage(
            access_record=access,
            evidence_items=[evidence],
            access_ref=access_ref,
            evidence_ref=evidence_ref,
        )

    def collect_manual_smoke(
        self,
        *,
        request_id: str,
        source_url: str,
        license_signal: Literal["open_access", "closed", "unknown", "not_applicable"],
        output_root: Path,
        yyyymmdd: str,
    ) -> OpenAccessPdfEvidencePackage:
        """Collect an approved manual OA PDF smoke response via injected transport."""

        if license_signal != "open_access":
            raise ValueError("PDF collection requires license_signal=open_access before bytes are persisted")
        response = self._transport(source_url)
        status_code = int(response["status_code"])
        content_type = response["content_type"]
        pdf_bytes = response["content"]
        if status_code < 200 or status_code >= 300 or "pdf" not in content_type.lower() or not pdf_bytes:
            raise ValueError("manual PDF smoke transport failed before bytes were persisted")
        digest = hashlib.sha256(pdf_bytes).hexdigest()
        access_id = f"ACCESS-{request_id}-{self.connector_id}"
        evidence_id = f"EVID-{request_id}-{self.connector_id}"
        access_ref = f"runtime-boundary/source-connectors/{yyyymmdd}/source-access-{access_id}.json"
        evidence_ref = f"runtime-boundary/source-connectors/{yyyymmdd}/source-evidence-{evidence_id}.json"
        access = SourceAccessRecord(
            access_id=access_id,
            request_id=request_id,
            connector_id=self.connector_id,
            source_url=source_url,
            accessed_at=f"{yyyymmdd}T00:00:00Z",
            http_status=status_code,
            content_type=content_type,
            title=Path(source_url).name or "manual-oa-pdf-smoke",
            license_signal="open_access",
            oa_pdf_url=source_url,
            sha256=digest,
            pdf_downloaded=True,
            external_call_made=self._external_call_made,
            policy_refs=["docs/use-cases/live-research-connectors.md"],
        )
        evidence = SourceEvidenceItem(
            evidence_id=evidence_id,
            access_ref=access_ref,
            quoted_text=(
                "PDF bytes collected from approved manual OA smoke; "
                f"sha256={digest}; byte_count={len(pdf_bytes)}."
            ),
            interpretation=(
                "Manual OA PDF smoke verifies the governed live retrieval boundary after approval/env/dispatch gates; "
                "it is not general crawling or publication-level validation."
            ),
            claim_type="source_evidence",
            confidence="medium",
            uncertainty="Manual smoke result; downstream use still requires source review and license validation.",
        )
        output_dir = output_root / "runtime-boundary" / "source-connectors" / yyyymmdd
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_root / access_ref).write_text(_json_dump(access), encoding="utf-8")
        (output_root / evidence_ref).write_text(_json_dump(evidence), encoding="utf-8")
        return OpenAccessPdfEvidencePackage(
            access_record=access,
            evidence_items=[evidence],
            access_ref=access_ref,
            evidence_ref=evidence_ref,
        )


def _urllib_pdf_transport(url: str) -> PdfTransportResponse:
    request = urllib.request.Request(url, headers={"User-Agent": "hisys-manual-oa-pdf-smoke/0.1"})
    with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310 - manual smoke only after policy gates.
        return {
            "status_code": int(response.status),
            "content_type": response.headers.get("Content-Type", "application/octet-stream"),
            "content": response.read(),
        }


def _json_dump(record: SourceAccessRecord | SourceEvidenceItem) -> str:
    return json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


__all__ = ["OpenAccessPdfConnector", "OpenAccessPdfEvidencePackage", "PdfTransportResponse"]
