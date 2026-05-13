"""Pass-contract evaluator tests.

Traceability: HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001, HISYS-T-024.
"""

from hisys.contracts.evaluator import EvidenceSummary, evaluate_pass_contract
from hisys.contracts.pass_registry import PassContractRegistryEntry


def _entry() -> PassContractRegistryEntry:
    return PassContractRegistryEntry(
        contract_id="product_architecture_architecture_choice_v0_1_candidate",
        domain="product_architecture",
        question_type="architecture_choice",
        status="candidate",
        version="0.1.0",
        minimum_evidence={
            "artifact_refs_required": True,
            "alternative_set_required": True,
            "claim_coverage_required": True,
            "contradiction_check_required": True,
            "dars_critique_required": True,
        },
        blocked_if=["no_traceable_artifact_refs", "boundary_violation_detected"],
        promotion_gate="human_reviewed_traceable_change",
    )


def test_missing_artifact_refs_blocks_passing():
    result = evaluate_pass_contract(_entry(), EvidenceSummary(artifact_refs=[], alternative_count=2, claims_covered=True, contradiction_checked=True, dars_critique_refs=["review/1"]))
    assert result.quality_gate == "needs_more_evidence"
    assert "no_traceable_artifact_refs" in result.blockers


def test_full_candidate_evidence_passes_for_human_reviewed_use():
    result = evaluate_pass_contract(_entry(), EvidenceSummary(artifact_refs=["evidence/1"], alternative_count=2, claims_covered=True, contradiction_checked=True, dars_critique_refs=["review/1"]))
    assert result.quality_gate == "passed"
    assert result.human_reviewed_use_only is True


def test_consequential_evidence_requires_human_approval():
    result = evaluate_pass_contract(_entry(), EvidenceSummary(artifact_refs=["evidence/1"], alternative_count=2, claims_covered=True, contradiction_checked=True, dars_critique_refs=["review/1"], consequential_use=True))
    assert result.quality_gate == "human_approval_required"
    assert "human_approval_required" in result.blockers


def test_boundary_violation_fails_closed():
    result = evaluate_pass_contract(_entry(), EvidenceSummary(artifact_refs=["evidence/1"], alternative_count=2, claims_covered=True, contradiction_checked=True, dars_critique_refs=["review/1"], boundary_violation_detected=True))
    assert result.quality_gate == "failed"
    assert "boundary_violation_detected" in result.blockers
