"""Aggregate claim evidence ledgers into advisory evidence balance summaries.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .claim_evidence_ledger import ClaimEvidenceLedgerRecord

EvidenceBalance = Literal["supported", "contradicted", "mixed_needs_more_evidence", "needs_more_evidence"]
AdvisoryConfidence = Literal["none", "low", "medium"]


class ClaimEvidenceSummaryRecord(BaseModel):
    """Advisory per-claim balance over explicit claim-evidence ledger records."""

    model_config = ConfigDict(extra="forbid")

    schema_id: Literal["hisys.source_connector.claim_evidence_summary"] = "hisys.source_connector.claim_evidence_summary"
    schema_version: Literal["0.1.0"] = "0.1.0"
    summary_id: str
    request_id: str
    claim_id: str
    claim_text: str
    claim_evidence_ledger_refs: list[str]
    support_count: int = Field(ge=0)
    contradict_count: int = Field(ge=0)
    needs_evidence_count: int = Field(ge=0)
    evidence_balance: EvidenceBalance
    advisory_confidence: AdvisoryConfidence
    advisory_confidence_only: Literal[True] = True
    does_not_prove_novelty: Literal[True] = True
    interpretation_summary: str
    external_call_made: bool = False
    mutation_performed: Literal[False] = False
    policy_refs: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class ClaimEvidenceSummaryResult:
    """Result refs for claim evidence summary construction."""

    request_id: str
    claim_evidence_summary_refs: list[str]
    external_call_made: bool = False
    mutation_performed: bool = False


class ClaimEvidenceSummaryBuilder:
    """Build advisory evidence-balance summaries from explicit ledger refs."""

    def __init__(self, *, root: Path) -> None:
        self.root = root

    def build(
        self,
        *,
        request_id: str,
        claim_id: str,
        claim_evidence_ledger_refs: list[str],
        yyyymmdd: str,
    ) -> ClaimEvidenceSummaryResult:
        if not claim_evidence_ledger_refs:
            raise ValueError("claim_evidence_ledger_refs are required for claim evidence summaries")
        ledgers = [self._load_ledger(ref) for ref in claim_evidence_ledger_refs]
        for ledger in ledgers:
            if ledger.claim_id != claim_id:
                raise ValueError("claim evidence summary requires all ledgers to have the same claim_id")
            if ledger.request_id != request_id:
                raise ValueError("claim evidence summary requires ledger request_id to match")
            if not ledger.advisory_only or not ledger.claim_mapping_is_interpretation:
                raise ValueError("claim evidence summary requires advisory interpretation ledger records")
            if ledger.external_call_made or ledger.mutation_performed:
                raise ValueError("claim evidence summary requires non-mutating ledger records")

        support_count = sum(1 for ledger in ledgers if ledger.relation == "support")
        contradict_count = sum(1 for ledger in ledgers if ledger.relation == "contradict")
        needs_count = sum(1 for ledger in ledgers if ledger.relation == "needs_evidence")
        balance, confidence = self._balance_and_confidence(support_count, contradict_count, needs_count)
        claim_text = ledgers[0].claim_text
        summary = ClaimEvidenceSummaryRecord(
            summary_id=f"SUMMARY-{request_id}-{claim_id}",
            request_id=request_id,
            claim_id=claim_id,
            claim_text=claim_text,
            claim_evidence_ledger_refs=claim_evidence_ledger_refs,
            support_count=support_count,
            contradict_count=contradict_count,
            needs_evidence_count=needs_count,
            evidence_balance=balance,
            advisory_confidence=confidence,
            interpretation_summary=(
                f"Advisory evidence balance for {claim_id}: support={support_count}, "
                f"contradict={contradict_count}, needs_evidence={needs_count}. "
                "This summary does not prove novelty or publication readiness."
            ),
            policy_refs=["HISYS-T-024", "HISYS-CON-010", "HISYS-CON-011", "HISYS-CON-012"],
        )
        output_dir = self.root / "runtime-boundary" / "source-connectors" / yyyymmdd
        output_dir.mkdir(parents=True, exist_ok=True)
        summary_path = output_dir / f"claim-evidence-summary-{summary.summary_id}.json"
        summary_path.write_text(summary.model_dump_json(indent=2) + "\n", encoding="utf-8")
        return ClaimEvidenceSummaryResult(
            request_id=request_id,
            claim_evidence_summary_refs=[str(summary_path.relative_to(self.root))],
        )

    def _load_ledger(self, ledger_ref: str) -> ClaimEvidenceLedgerRecord:
        if not ledger_ref.startswith("runtime-boundary/source-connectors/") or "/claim-evidence-ledger-" not in ledger_ref:
            raise ValueError("claim_evidence_ledger_ref must point to a runtime-boundary/source-connectors claim ledger")
        return ClaimEvidenceLedgerRecord.model_validate_json((self.root / ledger_ref).read_text(encoding="utf-8"))

    @staticmethod
    def _balance_and_confidence(
        support_count: int, contradict_count: int, needs_evidence_count: int
    ) -> tuple[EvidenceBalance, AdvisoryConfidence]:
        if contradict_count:
            return "contradicted", "low"
        if needs_evidence_count:
            return "mixed_needs_more_evidence", "low"
        if support_count:
            return "supported", "medium"
        return "needs_more_evidence", "none"


__all__ = [
    "AdvisoryConfidence",
    "ClaimEvidenceSummaryBuilder",
    "ClaimEvidenceSummaryRecord",
    "ClaimEvidenceSummaryResult",
    "EvidenceBalance",
]
