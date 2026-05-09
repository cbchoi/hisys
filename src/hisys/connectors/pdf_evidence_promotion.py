"""Promote approved OA PDF source refs into investigation inputs.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .live_source_evidence import SourceAccessRecord, SourceEvidenceItem


@dataclass(frozen=True)
class PromotedPdfEvidence:
    """Validated refs for an explicitly promoted OA PDF evidence set."""

    status: str
    source_access_refs: list[str]
    source_evidence_refs: list[str]
    promoted_pdf_evidence_refs: list[str]
    source_urls: list[str]
    pdf_downloaded: bool
    external_call_made: bool
    mutation_performed: bool


class PdfEvidencePromotionLoader:
    """Load and validate explicit OA PDF source refs before investigation promotion."""

    def __init__(self, *, root: Path) -> None:
        self.root = root

    def promote(self, *, source_access_refs: list[str], source_evidence_refs: list[str]) -> PromotedPdfEvidence:
        if not source_access_refs or not source_evidence_refs:
            raise ValueError("source-access and source-evidence refs are required for PDF evidence promotion")
        access_records = [self._load_access(ref) for ref in source_access_refs]
        evidence_items = [self._load_evidence(ref) for ref in source_evidence_refs]
        access_by_ref = dict(zip(source_access_refs, access_records, strict=True))
        source_urls: list[str] = []
        external_call_made = False
        for ref, access in access_by_ref.items():
            if not ref.startswith("runtime-boundary/source-connectors/"):
                raise ValueError("promoted PDF access refs must stay under runtime-boundary/source-connectors")
            if access.connector_id != "open_access_pdf_fetch":
                raise ValueError("promoted PDF access requires connector_id=open_access_pdf_fetch")
            if not access.pdf_downloaded:
                raise ValueError("promoted PDF access requires pdf_downloaded=true")
            if access.license_signal != "open_access":
                raise ValueError("promoted PDF access requires license_signal=open_access")
            if access.mutation_performed is not False:
                raise ValueError("promoted PDF access must not record mutation")
            source_urls.append(access.source_url)
            external_call_made = external_call_made or access.external_call_made
        for ref, evidence in zip(source_evidence_refs, evidence_items, strict=True):
            if evidence.access_ref not in access_by_ref:
                raise ValueError("promoted PDF evidence must reference a promoted access ref")
            if evidence.claim_type != "source_evidence":
                raise ValueError("promoted PDF evidence must remain source_evidence")
        return PromotedPdfEvidence(
            status="promoted",
            source_access_refs=source_access_refs,
            source_evidence_refs=source_evidence_refs,
            promoted_pdf_evidence_refs=source_evidence_refs,
            source_urls=source_urls,
            pdf_downloaded=True,
            external_call_made=external_call_made,
            mutation_performed=False,
        )

    def _load_access(self, ref: str) -> SourceAccessRecord:
        return SourceAccessRecord.model_validate_json((self.root / ref).read_text(encoding="utf-8"))

    def _load_evidence(self, ref: str) -> SourceEvidenceItem:
        return SourceEvidenceItem.model_validate_json((self.root / ref).read_text(encoding="utf-8"))


__all__ = ["PdfEvidencePromotionLoader", "PromotedPdfEvidence"]
