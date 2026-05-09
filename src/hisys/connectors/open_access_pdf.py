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
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .live_source_evidence import SourceAccessRecord, SourceEvidenceItem


@dataclass(frozen=True)
class OpenAccessPdfEvidencePackage:
    """Persisted open-access PDF evidence refs."""

    access_record: SourceAccessRecord
    evidence_items: list[SourceEvidenceItem]
    access_ref: str
    evidence_ref: str


class OpenAccessPdfConnector:
    """Collect local OA PDF fixtures into governed source evidence records."""

    connector_id = "open_access_pdf_fetch"

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


def _json_dump(record: SourceAccessRecord | SourceEvidenceItem) -> str:
    return json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


__all__ = ["OpenAccessPdfConnector", "OpenAccessPdfEvidencePackage"]
