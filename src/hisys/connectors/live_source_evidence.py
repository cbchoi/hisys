"""Live source evidence provenance records.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SourceAccessRecord(BaseModel):
    """Provenance record for a live or local source access attempt."""

    model_config = ConfigDict(extra="forbid")

    schema_id: Literal["hisys.source_connector.source_access"] = "hisys.source_connector.source_access"
    schema_version: Literal["0.1.0"] = "0.1.0"
    access_id: str
    request_id: str
    connector_id: str
    source_url: str
    accessed_at: str
    http_status: int | None = None
    content_type: str | None = None
    title: str | None = None
    license_signal: Literal["open_access", "closed", "unknown", "not_applicable"] = "unknown"
    oa_pdf_url: str | None = None
    sha256: str
    pdf_downloaded: bool = False
    external_call_made: bool = False
    mutation_performed: Literal[False] = False
    policy_refs: list[str] = Field(default_factory=list)

    @field_validator("sha256")
    @classmethod
    def _validate_sha256(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdefABCDEF" for char in value):
            raise ValueError("sha256 must be a 64-character hexadecimal digest")
        return value.lower()

    @model_validator(mode="after")
    def _validate_pdf_access(self) -> "SourceAccessRecord":
        if self.pdf_downloaded and self.license_signal != "open_access":
            raise ValueError("pdf_downloaded requires license_signal=open_access")
        return self


class SourceEvidenceItem(BaseModel):
    """Evidence item extracted from a source access record."""

    model_config = ConfigDict(extra="forbid")

    schema_id: Literal["hisys.source_connector.evidence_item"] = "hisys.source_connector.evidence_item"
    schema_version: Literal["0.1.0"] = "0.1.0"
    evidence_id: str
    access_ref: str
    quoted_text: str
    interpretation: str
    claim_type: Literal["source_evidence", "interpreted_gap", "synthesis_candidate", "validation_scenario"]
    confidence: Literal["low", "medium", "high", "unknown"] = "unknown"
    uncertainty: str | None = None

    @model_validator(mode="after")
    def _validate_evidence_separation(self) -> "SourceEvidenceItem":
        if not self.quoted_text.strip():
            raise ValueError("quoted_text is required before interpretation")
        if not self.interpretation.strip():
            raise ValueError("interpretation is required and must be separate from quoted_text")
        if self.quoted_text.strip() == self.interpretation.strip():
            raise ValueError("quoted_text and interpretation must remain separate")
        return self


__all__ = ["SourceAccessRecord", "SourceEvidenceItem"]
