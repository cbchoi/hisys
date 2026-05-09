"""Build quote-to-claim evidence ledger records.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .pdf_quote_extractor import SourceQuoteRecord

ClaimEvidenceRelation = Literal["support", "contradict", "needs_evidence"]


class ClaimEvidenceLedgerRecord(BaseModel):
    """Advisory mapping from one source quote to one proposed claim."""

    model_config = ConfigDict(extra="forbid")

    schema_id: Literal["hisys.source_connector.claim_evidence_ledger"] = "hisys.source_connector.claim_evidence_ledger"
    schema_version: Literal["0.1.0"] = "0.1.0"
    ledger_id: str
    request_id: str
    claim_id: str
    claim_text: str
    relation: ClaimEvidenceRelation
    rationale: str
    source_quote_ref: str
    quote_id: str
    quote_text: str
    quote_sha256: str
    quote_text_is_source_evidence: Literal[True] = True
    claim_mapping_is_interpretation: Literal[True] = True
    advisory_only: Literal[True] = True
    external_call_made: bool = False
    mutation_performed: Literal[False] = False
    policy_refs: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class ClaimEvidenceLedgerResult:
    """Result refs for claim-evidence ledger construction."""

    request_id: str
    claim_evidence_ledger_refs: list[str]
    external_call_made: bool = False
    mutation_performed: bool = False


class ClaimEvidenceLedgerBuilder:
    """Build advisory quote-to-claim ledger records from explicit source quotes."""

    valid_relations = {"support", "contradict", "needs_evidence"}

    def __init__(self, *, root: Path) -> None:
        self.root = root

    def build(
        self,
        *,
        request_id: str,
        claim_id: str,
        claim_text: str,
        relation: str,
        rationale: str,
        source_quote_refs: list[str],
        yyyymmdd: str,
    ) -> ClaimEvidenceLedgerResult:
        if relation not in self.valid_relations:
            raise ValueError("relation must be one of support/contradict/needs_evidence")
        if not source_quote_refs:
            raise ValueError("source_quote_refs are required for claim evidence ledger construction")
        output_dir = self.root / "runtime-boundary" / "source-connectors" / yyyymmdd
        output_dir.mkdir(parents=True, exist_ok=True)
        refs: list[str] = []
        for index, quote_ref in enumerate(source_quote_refs, start=1):
            quote = self._load_source_quote(quote_ref)
            ledger = ClaimEvidenceLedgerRecord(
                ledger_id=f"LEDGER-{request_id}-{claim_id}-{index:03d}",
                request_id=request_id,
                claim_id=claim_id,
                claim_text=claim_text,
                relation=relation,  # type: ignore[arg-type]
                rationale=rationale,
                source_quote_ref=quote_ref,
                quote_id=quote.quote_id,
                quote_text=quote.quote_text,
                quote_sha256=quote.quote_sha256,
                policy_refs=["HISYS-T-024", "HISYS-CON-010", "HISYS-CON-011", "HISYS-CON-012"],
            )
            ledger_path = output_dir / f"claim-evidence-ledger-{ledger.ledger_id}.json"
            ledger_path.write_text(ledger.model_dump_json(indent=2) + "\n", encoding="utf-8")
            refs.append(str(ledger_path.relative_to(self.root)))
        return ClaimEvidenceLedgerResult(request_id=request_id, claim_evidence_ledger_refs=refs)

    def _load_source_quote(self, source_quote_ref: str) -> SourceQuoteRecord:
        if not source_quote_ref.startswith("runtime-boundary/source-connectors/"):
            raise ValueError("source_quote_ref must point under runtime-boundary/source-connectors")
        quote = SourceQuoteRecord.model_validate_json((self.root / source_quote_ref).read_text(encoding="utf-8"))
        if quote.claim_type != "source_quote":
            raise ValueError("claim evidence ledger requires source_quote records")
        if quote.interpretation is not None:
            raise ValueError("claim evidence ledger requires quote-only records without interpretation")
        return quote


__all__ = [
    "ClaimEvidenceLedgerBuilder",
    "ClaimEvidenceLedgerRecord",
    "ClaimEvidenceLedgerResult",
    "ClaimEvidenceRelation",
]
