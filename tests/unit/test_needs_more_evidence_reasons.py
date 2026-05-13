"""Needs-more-evidence reason taxonomy tests.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024.
"""

from hisys.contracts.evidence_reasons import NeedsMoreEvidenceReason, classify_reason, reason_codes


def test_classifies_adapter_missing():
    reason = classify_reason(adapter_found=False, contract_found=False, source_count=0, contradiction_checked=False)
    assert reason.code == NeedsMoreEvidenceReason.ADAPTER_MISSING.value
    assert reason.blocks_passing is True


def test_classifies_independent_corroboration_missing_after_sources_exist():
    reason = classify_reason(
        adapter_found=True,
        contract_found=True,
        source_count=3,
        independent_corroboration=False,
        contradiction_checked=True,
    )
    assert reason.code == NeedsMoreEvidenceReason.INDEPENDENT_CORROBORATION_MISSING.value


def test_reason_codes_are_stable_for_cli_contracts():
    assert "adapter_missing" in reason_codes()
    assert "human_approval_required" in reason_codes()
