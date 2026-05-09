"""Gate manuscript-facing claim language on explicit claim evidence summaries.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .claim_evidence_summary import ClaimEvidenceSummaryRecord

CoverageStatus = Literal["complete_conditional", "needs_more_claim_evidence"]
ManuscriptLanguageGate = Literal["conditional_only"]


class ClaimCoverageGateRecord(BaseModel):
    """Conditional gate over required claims and explicit evidence summaries."""

    model_config = ConfigDict(extra="forbid")

    schema_id: Literal["hisys.source_connector.claim_coverage_gate"] = "hisys.source_connector.claim_coverage_gate"
    schema_version: Literal["0.1.0"] = "0.1.0"
    gate_id: str
    request_id: str
    required_claim_ids: list[str]
    claim_evidence_summary_refs: list[str]
    covered_claim_ids: list[str]
    uncovered_claim_ids: list[str]
    coverage_status: CoverageStatus
    manuscript_language_gate: ManuscriptLanguageGate = "conditional_only"
    conditional_manuscript_language_only: Literal[True] = True
    does_not_approve_publication_ready_claims: Literal[True] = True
    does_not_prove_novelty: Literal[True] = True
    gate_summary: str
    external_call_made: bool = False
    mutation_performed: Literal[False] = False
    policy_refs: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class ClaimCoverageGateResult:
    """Result refs for claim coverage gate construction."""

    request_id: str
    claim_coverage_gate_refs: list[str]
    external_call_made: bool = False
    mutation_performed: bool = False


class ClaimCoverageGateBuilder:
    """Build conditional manuscript-language coverage gates from summary refs."""

    def __init__(self, *, root: Path) -> None:
        self.root = root

    def build(
        self,
        *,
        request_id: str,
        required_claim_ids: list[str],
        claim_evidence_summary_refs: list[str],
        yyyymmdd: str,
    ) -> ClaimCoverageGateResult:
        if not required_claim_ids:
            raise ValueError("required_claim_ids are required for claim coverage gates")
        if not claim_evidence_summary_refs:
            raise ValueError("claim_evidence_summary_refs are required for claim coverage gates")
        summaries = [self._load_summary(ref) for ref in claim_evidence_summary_refs]
        for summary in summaries:
            if summary.request_id != request_id:
                raise ValueError("claim coverage gate requires summary request_id to match")
            if not summary.advisory_confidence_only or not summary.does_not_prove_novelty:
                raise ValueError("claim coverage gate requires advisory, non-novelty-proof summaries")
            if summary.external_call_made or summary.mutation_performed:
                raise ValueError("claim coverage gate requires non-mutating summaries")

        available_claim_ids = {summary.claim_id for summary in summaries}
        covered = [claim_id for claim_id in required_claim_ids if claim_id in available_claim_ids]
        uncovered = [claim_id for claim_id in required_claim_ids if claim_id not in available_claim_ids]
        status: CoverageStatus = "complete_conditional" if not uncovered else "needs_more_claim_evidence"
        gate = ClaimCoverageGateRecord(
            gate_id=f"GATE-{request_id}-CLAIM-COVERAGE",
            request_id=request_id,
            required_claim_ids=required_claim_ids,
            claim_evidence_summary_refs=claim_evidence_summary_refs,
            covered_claim_ids=covered,
            uncovered_claim_ids=uncovered,
            coverage_status=status,
            gate_summary=(
                f"Claim coverage gate for {request_id}: covered={len(covered)}, uncovered={len(uncovered)}. "
                "Manuscript-facing language remains conditional only and this gate does not approve publication-ready claims."
            ),
            policy_refs=["HISYS-T-024", "HISYS-CON-010", "HISYS-CON-011", "HISYS-CON-012"],
        )
        output_dir = self.root / "runtime-boundary" / "source-connectors" / yyyymmdd
        output_dir.mkdir(parents=True, exist_ok=True)
        gate_path = output_dir / f"claim-coverage-gate-{gate.gate_id}.json"
        gate_path.write_text(gate.model_dump_json(indent=2) + "\n", encoding="utf-8")
        return ClaimCoverageGateResult(
            request_id=request_id,
            claim_coverage_gate_refs=[str(gate_path.relative_to(self.root))],
        )

    def _load_summary(self, summary_ref: str) -> ClaimEvidenceSummaryRecord:
        if not summary_ref.startswith("runtime-boundary/source-connectors/") or "/claim-evidence-summary-" not in summary_ref:
            raise ValueError("claim_evidence_summary_ref must point to a runtime-boundary/source-connectors claim summary")
        return ClaimEvidenceSummaryRecord.model_validate_json((self.root / summary_ref).read_text(encoding="utf-8"))


__all__ = [
    "ClaimCoverageGateBuilder",
    "ClaimCoverageGateRecord",
    "ClaimCoverageGateResult",
    "CoverageStatus",
    "ManuscriptLanguageGate",
]
