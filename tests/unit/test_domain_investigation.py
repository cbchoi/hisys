"""Domain-general Hisys investigation schemas.

Traceability: HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001, HISYS-T-024,
HISYS-CON-010..012.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from hisys.schemas.domain_investigation import (
    AlternativeDecisionSet,
    CandidateRecord,
    DomainEvidencePackage,
    DomainInvestigationRequest,
    DomainInvestigationResult,
    HisysToolResult,
    InvestigationDataPackage,
)


def test_domain_investigation_request_is_read_only_by_default() -> None:
    request = DomainInvestigationRequest(
        request_id="HISYS-REQ-001",
        producer_id="hermes",
        status="submitted",
        domain="research",
        objective="Find research gap among formalisms for self-organizing structure.",
        sources=[
            {
                "source_id": "SRC-FORMALISM-001",
                "source_type": "current_artifact",
                "ref": "fixture://formalism-literature",
                "access_mode": "read_only",
            }
        ],
    )

    assert request.constraints.external_calls_allowed is False
    assert request.constraints.mutation_allowed is False
    assert request.constraints.credential_use_allowed is False
    assert request.output_contract.include_runtime_boundary_refs is True
    assert request.sources[0].access_mode == "read_only"


def test_domain_investigation_request_rejects_mutating_source_access() -> None:
    with pytest.raises(ValidationError, match="read_only"):
        DomainInvestigationRequest(
            request_id="HISYS-REQ-002",
            producer_id="hermes",
            status="submitted",
            domain="research",
            objective="Find research gap.",
            sources=[
                {
                    "source_id": "SRC-BAD-001",
                    "source_type": "current_artifact",
                    "ref": "fixture://bad",
                    "access_mode": "write",
                }
            ],
        )


def test_domain_result_links_evidence_alternatives_and_tool_result() -> None:
    evidence = DomainEvidencePackage(
        package_id="DEPKG-001",
        domain="research",
        evidence_type="research_gap_matrix",
        summary="DSDEVS, graph rewriting, and ABM cover complementary pieces.",
        evidence_refs=["EPKG-TASK-INV-001-FORMALISM"],
        source_refs=["SRC-FORMALISM-001"],
        limitations=["Fixture evidence only."],
    )
    data_package = InvestigationDataPackage(
        investigation_id="INV-001",
        request_id="HISYS-REQ-001",
        domain="research",
        objective="Find research gap among formalisms for self-organizing structure.",
        evidence_packages=[evidence],
        source_governance_refs=["runtime-boundary/domain-investigation/research/20260509/source-governance-HISYS-REQ-001.json"],
    )
    candidate = CandidateRecord(
        candidate_id="CAND-001",
        candidate_type="research_direction",
        claim="Self-organizing Dynamic Structure DEVS with graph-rewrite transitions.",
        evidence_refs=["DEPKG-001"],
        value="Unifies executable topology change with local structure rewrite semantics.",
        risks=["Requires source validation beyond fixtures."],
    )
    alternatives = AlternativeDecisionSet(
        alternative_set_id="ALTSET-001",
        request_id="HISYS-REQ-001",
        candidates=[candidate],
        baseline_option="request_more_evidence",
        recommended_candidate_id="CAND-001",
    )
    result = DomainInvestigationResult(
        result_id="DRESULT-001",
        request_id="HISYS-REQ-001",
        domain="research",
        investigation_data=data_package,
        alternative_decision_set=alternatives,
        recommendation_summary="Proceed as research direction with more publisher evidence.",
        dars_refs=["runtime-boundary/dars/20260509/dars-trace-DARS-TRACE-001.json"],
        runtime_boundary_refs=["runtime-boundary/domain-investigation/research/20260509/hisys-tool-result-HISYS-REQ-001.json"],
    )
    tool_result = HisysToolResult.from_domain_result(result)

    assert result.recommended_alternative_id == "CAND-001"
    assert tool_result.status == "completed"
    assert tool_result.domain == "research"
    assert tool_result.recommended_alternative_id == "CAND-001"
    assert tool_result.external_call_made is False
    assert tool_result.mutation_performed is False
    assert tool_result.requires_human_review is True
