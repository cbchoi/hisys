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
from hisys.schemas.lapidary_governance import EvidenceChainRecord, HisysMode


def _investigation_evidence_package() -> DomainEvidencePackage:
    return DomainEvidencePackage(
        package_id="DEPKG-INV-MODE-001",
        domain="research",
        evidence_type="research_gap_matrix",
        summary="Evidence summary for hisys_mode tests.",
        evidence_refs=["EPKG-TASK-INV-001-FORMALISM"],
        source_refs=["SRC-FORMALISM-001"],
    )


def _investigation_data_package(**overrides) -> InvestigationDataPackage:
    data = {
        "investigation_id": "INV-MODE-001",
        "request_id": "HISYS-REQ-MODE-001",
        "domain": "research",
        "objective": "Confirm hisys_mode default selective governance.",
        "evidence_packages": [_investigation_evidence_package()],
    }
    data.update(overrides)
    return InvestigationDataPackage(**data)


def _claim_chain(**overrides) -> EvidenceChainRecord:
    data = {
        "chain_id": "CHAIN-INV-CLAIM-001",
        "producer_id": "hisys-domain-investigation",
        "status": "active",
        "decision_ref": None,
        "synthesis_refs": [],
        "claim_ledger_refs": ["canonical/claims/LEDGER-INV-001.md#C-INV-001"],
        "evidence_refs": ["canonical/evidence/EVID-INV-001.md"],
        "source_refs": ["canonical/sources/SRC-INV-001.md"],
    }
    data.update(overrides)
    return EvidenceChainRecord(**data)


def _synthesis_chain(**overrides) -> EvidenceChainRecord:
    data = {
        "chain_id": "CHAIN-INV-SYN-001",
        "producer_id": "hisys-domain-investigation",
        "status": "active",
        "decision_ref": None,
        "synthesis_refs": ["canonical/synthesis/SYN-INV-001.md"],
        "claim_ledger_refs": ["canonical/claims/LEDGER-INV-001.md#C-INV-001"],
        "evidence_refs": ["canonical/evidence/EVID-INV-001.md"],
        "source_refs": ["canonical/sources/SRC-INV-001.md"],
    }
    data.update(overrides)
    return EvidenceChainRecord(**data)


def _decision_chain(**overrides) -> EvidenceChainRecord:
    data = {
        "chain_id": "CHAIN-INV-DECISION-001",
        "producer_id": "hisys-domain-investigation",
        "status": "active",
        "decision_ref": "canonical/decisions/DECISION-INV-001.md",
        "synthesis_refs": ["canonical/synthesis/SYN-INV-001.md"],
        "claim_ledger_refs": ["canonical/claims/LEDGER-INV-001.md#C-INV-001"],
        "evidence_refs": ["canonical/evidence/EVID-INV-001.md"],
        "source_refs": ["canonical/sources/SRC-INV-001.md"],
    }
    data.update(overrides)
    return EvidenceChainRecord(**data)


def _stone_chain() -> EvidenceChainRecord:
    return EvidenceChainRecord(
        chain_id="CHAIN-INV-STONE-001",
        producer_id="hisys-domain-investigation",
        status="active",
        decision_ref=None,
        synthesis_refs=[],
        claim_ledger_refs=[],
        evidence_refs=["canonical/evidence/EVID-INV-001.md"],
        source_refs=["canonical/sources/SRC-INV-001.md"],
    )


def test_investigation_data_package_hisys_mode_defaults_to_selective_none() -> None:
    package = _investigation_data_package()

    assert package.hisys_mode.level == "none"
    assert package.hisys_mode.selective_governance is True
    assert package.hisys_mode.applies_to_all_notes is False
    assert package.evidence_chain is None

    dumped = package.model_dump(mode="json")
    assert dumped["hisys_mode"]["level"] == "none"
    assert dumped["evidence_chain"] is None


def test_investigation_data_package_lower_modes_allow_omitted_evidence_chain() -> None:
    for level in ("none", "stone"):
        package = _investigation_data_package(hisys_mode=HisysMode(level=level))
        assert package.hisys_mode.level == level
        assert package.evidence_chain is None


def test_investigation_data_package_claim_mode_requires_claim_level_evidence_chain() -> None:
    with pytest.raises(ValidationError, match="hisys_mode.level='claim'"):
        _investigation_data_package(hisys_mode=HisysMode(level="claim"))


def test_investigation_data_package_claim_mode_rejects_stone_only_evidence_chain() -> None:
    with pytest.raises(ValidationError, match="claim-level EvidenceChainRecord"):
        _investigation_data_package(
            hisys_mode=HisysMode(level="claim"),
            evidence_chain=_stone_chain(),
        )


def test_investigation_data_package_claim_mode_accepts_claim_level_evidence_chain() -> None:
    package = _investigation_data_package(
        hisys_mode=HisysMode(level="claim"),
        evidence_chain=_claim_chain(),
    )

    assert package.hisys_mode.level == "claim"
    assert package.evidence_chain is not None
    assert package.evidence_chain.claim_ledger_refs


def test_investigation_data_package_synthesis_mode_requires_synthesis_level_evidence_chain() -> None:
    with pytest.raises(ValidationError, match="hisys_mode.level='synthesis'"):
        _investigation_data_package(hisys_mode=HisysMode(level="synthesis"))


def test_investigation_data_package_synthesis_mode_rejects_claim_only_evidence_chain() -> None:
    with pytest.raises(ValidationError, match="synthesis-level EvidenceChainRecord"):
        _investigation_data_package(
            hisys_mode=HisysMode(level="synthesis"),
            evidence_chain=_claim_chain(),
        )


def test_investigation_data_package_synthesis_mode_accepts_synthesis_level_evidence_chain() -> None:
    package = _investigation_data_package(
        hisys_mode=HisysMode(level="synthesis"),
        evidence_chain=_synthesis_chain(),
    )

    assert package.hisys_mode.level == "synthesis"
    assert package.evidence_chain is not None
    assert package.evidence_chain.synthesis_refs
    assert package.evidence_chain.claim_ledger_refs
    dumped = package.model_dump(mode="json")
    assert dumped["hisys_mode"]["level"] == "synthesis"
    assert dumped["evidence_chain"]["synthesis_refs"] == [
        "canonical/synthesis/SYN-INV-001.md"
    ]


def test_investigation_data_package_decision_modes_require_decision_level_chain() -> None:
    for level in ("decision", "publication"):
        with pytest.raises(ValidationError, match=f"{level}-level EvidenceChainRecord"):
            _investigation_data_package(
                hisys_mode=HisysMode(level=level),
                evidence_chain=_synthesis_chain(),
            )

        package = _investigation_data_package(
            hisys_mode=HisysMode(level=level),
            evidence_chain=_decision_chain(),
        )
        assert package.hisys_mode.level == level
        assert package.evidence_chain is not None
        assert package.evidence_chain.decision_ref == "canonical/decisions/DECISION-INV-001.md"


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
