"""Deterministic needs-more-evidence reason taxonomy.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NeedsMoreEvidenceReason(str, Enum):
    ADAPTER_MISSING = "adapter_missing"
    DOMAIN_CONTRACT_MISSING = "domain_contract_missing"
    SOURCE_COUNT_INSUFFICIENT = "source_count_insufficient"
    INDEPENDENT_CORROBORATION_MISSING = "independent_corroboration_missing"
    CONTRADICTION_UNCHECKED = "contradiction_unchecked"
    CLAIM_COVERAGE_INCOMPLETE = "claim_coverage_incomplete"
    CONFIDENCE_BELOW_THRESHOLD = "confidence_below_threshold"
    HUMAN_APPROVAL_REQUIRED = "human_approval_required"


@dataclass(frozen=True)
class NeedsMoreEvidenceClassification:
    code: str
    blocks_passing: bool = True


def reason_codes() -> list[str]:
    return [reason.value for reason in NeedsMoreEvidenceReason]


def classify_reason(
    *,
    adapter_found: bool,
    contract_found: bool,
    source_count: int = 0,
    independent_corroboration: bool = True,
    contradiction_checked: bool = True,
    claims_covered: bool = True,
    confidence_ok: bool = True,
    human_approval_required: bool = False,
) -> NeedsMoreEvidenceClassification:
    if not adapter_found:
        return NeedsMoreEvidenceClassification(NeedsMoreEvidenceReason.ADAPTER_MISSING.value)
    if not contract_found:
        return NeedsMoreEvidenceClassification(NeedsMoreEvidenceReason.DOMAIN_CONTRACT_MISSING.value)
    if source_count < 1:
        return NeedsMoreEvidenceClassification(NeedsMoreEvidenceReason.SOURCE_COUNT_INSUFFICIENT.value)
    if not independent_corroboration:
        return NeedsMoreEvidenceClassification(NeedsMoreEvidenceReason.INDEPENDENT_CORROBORATION_MISSING.value)
    if not contradiction_checked:
        return NeedsMoreEvidenceClassification(NeedsMoreEvidenceReason.CONTRADICTION_UNCHECKED.value)
    if not claims_covered:
        return NeedsMoreEvidenceClassification(NeedsMoreEvidenceReason.CLAIM_COVERAGE_INCOMPLETE.value)
    if not confidence_ok:
        return NeedsMoreEvidenceClassification(NeedsMoreEvidenceReason.CONFIDENCE_BELOW_THRESHOLD.value)
    if human_approval_required:
        return NeedsMoreEvidenceClassification(NeedsMoreEvidenceReason.HUMAN_APPROVAL_REQUIRED.value)
    return NeedsMoreEvidenceClassification(NeedsMoreEvidenceReason.HUMAN_APPROVAL_REQUIRED.value, blocks_passing=False)
