"""Extract source quote records from promoted OA PDF evidence.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .live_source_evidence import SourceEvidenceItem


class SourceQuoteRecord(BaseModel):
    """Quote-only source record derived from promoted PDF evidence."""

    model_config = ConfigDict(extra="forbid")

    schema_id: Literal["hisys.source_connector.source_quote"] = "hisys.source_connector.source_quote"
    schema_version: Literal["0.1.0"] = "0.1.0"
    quote_id: str
    request_id: str
    connector_id: str
    source_access_ref: str
    source_evidence_ref: str
    source_url: str
    quote_text: str
    quote_sha256: str
    interpretation: None = None
    claim_type: Literal["source_quote"] = "source_quote"
    provenance: dict[str, str] = Field(default_factory=dict)
    external_call_made: bool = False
    mutation_performed: Literal[False] = False
    policy_refs: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class PdfQuoteExtractionResult:
    """Result refs for promoted PDF quote extraction."""

    request_id: str
    source_quote_refs: list[str]
    external_call_made: bool = False
    mutation_performed: bool = False


class PdfQuoteExtractor:
    """Extract quote-only records from explicit promoted PDF evidence refs."""

    connector_id = "open_access_pdf_fetch"

    def __init__(self, *, root: Path) -> None:
        self.root = root

    def extract(
        self,
        *,
        request_id: str,
        promoted_pdf_evidence_refs: list[str],
        yyyymmdd: str,
    ) -> PdfQuoteExtractionResult:
        if not promoted_pdf_evidence_refs:
            raise ValueError("promoted_pdf_evidence_refs are required for PDF quote extraction")
        quote_refs: list[str] = []
        output_dir = self.root / "runtime-boundary" / "source-connectors" / yyyymmdd
        output_dir.mkdir(parents=True, exist_ok=True)
        for index, evidence_ref in enumerate(promoted_pdf_evidence_refs, start=1):
            evidence = self._load_source_evidence(evidence_ref)
            quote_ref = self._write_quote_record(
                request_id=request_id,
                evidence=evidence,
                evidence_ref=evidence_ref,
                output_dir=output_dir,
                yyyymmdd=yyyymmdd,
                index=index,
            )
            quote_refs.append(quote_ref)
        return PdfQuoteExtractionResult(request_id=request_id, source_quote_refs=quote_refs)

    def _load_source_evidence(self, evidence_ref: str) -> SourceEvidenceItem:
        if not evidence_ref.startswith("runtime-boundary/source-connectors/"):
            raise ValueError("source-evidence ref must point under runtime-boundary/source-connectors")
        evidence_path = self.root / evidence_ref
        evidence = SourceEvidenceItem.model_validate_json(evidence_path.read_text(encoding="utf-8"))
        if evidence.claim_type != "source_evidence":
            raise ValueError("PDF quote extraction requires source_evidence items")
        if "open_access_pdf_fetch" not in evidence.evidence_id:
            raise ValueError("PDF quote extraction requires open_access_pdf_fetch evidence")
        return evidence

    def _write_quote_record(
        self,
        *,
        request_id: str,
        evidence: SourceEvidenceItem,
        evidence_ref: str,
        output_dir: Path,
        yyyymmdd: str,
        index: int,
    ) -> str:
        access = json.loads((self.root / evidence.access_ref).read_text(encoding="utf-8"))
        source_url = access["source_url"]
        quote_hash = hashlib.sha256(evidence.quoted_text.encode("utf-8")).hexdigest()
        quote = SourceQuoteRecord(
            quote_id=f"QUOTE-{request_id}-{self.connector_id}-{index:03d}",
            request_id=request_id,
            connector_id=self.connector_id,
            source_access_ref=evidence.access_ref,
            source_evidence_ref=evidence_ref,
            source_url=source_url,
            quote_text=evidence.quoted_text,
            quote_sha256=quote_hash,
            provenance={
                "origin": "promoted_pdf_evidence_ref",
                "yyyymmdd": yyyymmdd,
                "source_access_sha256": access["sha256"],
            },
            policy_refs=["HISYS-T-024", "HISYS-CON-010", "HISYS-CON-011", "HISYS-CON-012"],
        )
        quote_path = output_dir / f"source-quote-{quote.quote_id}.json"
        quote_path.write_text(quote.model_dump_json(indent=2) + "\n", encoding="utf-8")
        return str(quote_path.relative_to(self.root))


__all__ = ["PdfQuoteExtractionResult", "PdfQuoteExtractor", "SourceQuoteRecord"]
