"""Hisys Lapidary governance schema tests.

Traceability: HISYS-SCHEMA-001, HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001,
HISYS-CON-010..012, HISYS-T-024.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from hisys.schemas.lapidary_governance import (
    AppraiserSeparationPolicy,
    EvidenceChainRecord,
    EvidenceOriginWeight,
    HisysMode,
    LapidaryRoleAssignment,
    TemporalArchivePolicy,
    WeightedDecisionAlternative,
)


def test_hisys_mode_defaults_to_selective_none() -> None:
    mode = HisysMode()

    assert mode.level == "none"
    assert mode.upgrade_triggers == []
    assert mode.selective_governance is True
    assert mode.applies_to_all_notes is False


def test_hisys_mode_rejects_apply_to_all_notes() -> None:
    with pytest.raises(ValidationError, match="selective governance"):
        HisysMode(applies_to_all_notes=True)


def test_evidence_chain_requires_decision_to_synthesis_to_claim_to_stone_path() -> None:
    chain = EvidenceChainRecord(
        chain_id="CHAIN-DEVS-DT-001",
        producer_id="test",
        status="active",
        decision_ref="canonical/decisions/DECISION-DEVS-DT-001.md",
        synthesis_refs=["canonical/synthesis/SYN-DEVS-DT-001.md"],
        claim_ledger_refs=["canonical/claims/LEDGER-DEVS-DT-001.md#C-DEVS-DT-001"],
        evidence_refs=["canonical/evidence/EVID-DEVS-DT-001.md"],
        source_refs=["canonical/sources/SRC-DEVS-DT-001.md"],
        attachment_refs=["canonical/attachments/blobs/ab/cd/source.pdf"],
        structured_links_source_of_truth=True,
        wikilinks_are_projection=True,
    )

    assert chain.path_summary == (
        "decision/Jewel -> synthesis/Gem -> claim ledger -> evidence/Stone -> attachment/source"
    )


def test_evidence_chain_rejects_decision_without_synthesis_or_claim_ledger() -> None:
    with pytest.raises(ValidationError, match="synthesis_refs"):
        EvidenceChainRecord(
            chain_id="CHAIN-BAD-001",
            producer_id="test",
            status="active",
            decision_ref="canonical/decisions/DECISION-BAD-001.md",
            synthesis_refs=[],
            claim_ledger_refs=["canonical/claims/LEDGER-BAD-001.md#C-BAD-001"],
            evidence_refs=["canonical/evidence/EVID-BAD-001.md"],
            source_refs=["canonical/sources/SRC-BAD-001.md"],
        )

    with pytest.raises(ValidationError, match="claim_ledger_refs"):
        EvidenceChainRecord(
            chain_id="CHAIN-BAD-002",
            producer_id="test",
            status="active",
            decision_ref="canonical/decisions/DECISION-BAD-002.md",
            synthesis_refs=["canonical/synthesis/SYN-BAD-001.md"],
            claim_ledger_refs=[],
            evidence_refs=["canonical/evidence/EVID-BAD-001.md"],
            source_refs=["canonical/sources/SRC-BAD-001.md"],
        )


def test_evidence_chain_rejects_decision_without_source_refs() -> None:
    with pytest.raises(ValidationError, match="source_refs"):
        EvidenceChainRecord(
            chain_id="CHAIN-BAD-003",
            producer_id="test",
            status="active",
            decision_ref="canonical/decisions/DECISION-BAD-003.md",
            synthesis_refs=["canonical/synthesis/SYN-BAD-003.md"],
            claim_ledger_refs=["canonical/claims/LEDGER-BAD-003.md#C-BAD-003"],
            evidence_refs=["canonical/evidence/EVID-BAD-003.md"],
            source_refs=[],
        )


def test_evidence_chain_allows_stone_level_without_decision() -> None:
    chain = EvidenceChainRecord(
        chain_id="CHAIN-STONE-001",
        producer_id="test",
        status="active",
        decision_ref=None,
        synthesis_refs=[],
        claim_ledger_refs=[],
        evidence_refs=["canonical/evidence/EVID-STONE-001.md"],
        source_refs=["canonical/sources/SRC-STONE-001.md"],
    )

    assert chain.decision_ref is None
    assert chain.synthesis_refs == []
    assert chain.claim_ledger_refs == []


def test_evidence_chain_stone_level_still_requires_evidence_and_source() -> None:
    with pytest.raises(ValidationError, match="evidence_refs"):
        EvidenceChainRecord(
            chain_id="CHAIN-STONE-BAD-001",
            producer_id="test",
            status="active",
            decision_ref=None,
            synthesis_refs=[],
            claim_ledger_refs=[],
            evidence_refs=[],
            source_refs=["canonical/sources/SRC-STONE-001.md"],
        )

    with pytest.raises(ValidationError, match="source_refs"):
        EvidenceChainRecord(
            chain_id="CHAIN-STONE-BAD-002",
            producer_id="test",
            status="active",
            decision_ref=None,
            synthesis_refs=[],
            claim_ledger_refs=[],
            evidence_refs=["canonical/evidence/EVID-STONE-001.md"],
            source_refs=[],
        )


def test_evidence_chain_rejects_blank_refs() -> None:
    with pytest.raises(ValidationError, match="blank"):
        EvidenceChainRecord(
            chain_id="CHAIN-BLANK-001",
            producer_id="test",
            status="active",
            decision_ref="   ",
            synthesis_refs=["canonical/synthesis/SYN-BLANK-001.md"],
            claim_ledger_refs=["canonical/claims/LEDGER-BLANK-001.md#C-BLANK-001"],
            evidence_refs=["canonical/evidence/EVID-BLANK-001.md"],
            source_refs=["canonical/sources/SRC-BLANK-001.md"],
        )

    with pytest.raises(ValidationError, match="blank"):
        EvidenceChainRecord(
            chain_id="CHAIN-BLANK-002",
            producer_id="test",
            status="active",
            decision_ref=None,
            synthesis_refs=[],
            claim_ledger_refs=[],
            evidence_refs=["canonical/evidence/EVID-BLANK-001.md"],
            source_refs=["   "],
        )


def test_lapidary_role_assignment_keeps_metaphor_out_of_function() -> None:
    assignment = LapidaryRoleAssignment(
        role_id="ROLE-APPRAISER-001",
        producer_id="test",
        status="active",
        agent_role="dars_adversarial_auditor",
        function="adversarial_audit",
        display_metaphor="Appraiser",
        technical_type="hisys/advisory-review",
    )

    assert assignment.display_metaphor == "Appraiser"
    assert assignment.function == "adversarial_audit"


def test_temporal_policy_archives_instead_of_deleting_time_sensitive_evidence() -> None:
    policy = TemporalArchivePolicy(
        policy_id="ARCHIVE-POLICY-001",
        producer_id="test",
        status="active",
        temporal_class="company_market_product_news",
        current_stage="stale",
        next_stage="archive_candidate",
        delete_allowed=False,
        preserve_historical_evidence=True,
        review_due="2026-06-01",
    )

    assert policy.next_stage == "archive_candidate"

    with pytest.raises(ValidationError, match="delete_allowed=false"):
        TemporalArchivePolicy(
            policy_id="ARCHIVE-POLICY-BAD",
            producer_id="test",
            status="active",
            temporal_class="company_market_product_news",
            current_stage="stale",
            next_stage="archive",
            delete_allowed=True,
            preserve_historical_evidence=True,
            review_due="2026-06-01",
        )


def test_temporal_policy_rejects_deleted_next_stage_at_literal_level() -> None:
    with pytest.raises(ValidationError, match="next_stage"):
        TemporalArchivePolicy(
            policy_id="ARCHIVE-POLICY-DELETED",
            producer_id="test",
            status="active",
            temporal_class="company_market_product_news",
            current_stage="archive_candidate",
            next_stage="deleted",  # type: ignore[arg-type]
            delete_allowed=False,
            preserve_historical_evidence=True,
            review_due="2026-06-01",
        )


def test_weighted_alternative_preserves_internal_external_origin_distinction() -> None:
    alternative = WeightedDecisionAlternative(
        alternative_id="ALT-HYBRID-001",
        producer_id="test",
        status="active",
        label="Hybrid option",
        claim="Use internal prior as a hypothesis and verify with external evidence.",
        origin_weights=[
            EvidenceOriginWeight(
                evidence_origin="internal_prior",
                ref="canonical/synthesis/SYN-PRIOR-001.md",
                origin_weight=0.5,
                source_quality=0.5,
                verification_status=0.4,
                recency=0.6,
                independence=0.3,
                contradiction_status=0.7,
                domain_fit=0.9,
            ),
            EvidenceOriginWeight(
                evidence_origin="external_source",
                ref="canonical/sources/SRC-PAPER-001.md",
                origin_weight=0.5,
                source_quality=0.9,
                verification_status=0.8,
                recency=0.7,
                independence=0.9,
                contradiction_status=0.8,
                domain_fit=0.8,
            ),
        ],
        recommended_use="conditional_decision",
    )

    assert alternative.origin_summary == ["internal_prior", "external_source"]
    assert alternative.weighted_score > 0


def test_weighted_alternative_applies_origin_weight_weighted_average() -> None:
    alternative = WeightedDecisionAlternative(
        alternative_id="ALT-WEIGHTED-001",
        producer_id="test",
        status="active",
        label="External-heavy",
        claim="External source weighted more heavily than internal prior.",
        origin_weights=[
            EvidenceOriginWeight(
                evidence_origin="internal_prior",
                ref="canonical/synthesis/SYN-PRIOR-002.md",
                origin_weight=0.3,
                source_quality=0.5,
                verification_status=0.4,
                recency=0.6,
                independence=0.3,
                contradiction_status=0.7,
                domain_fit=0.9,
            ),
            EvidenceOriginWeight(
                evidence_origin="external_source",
                ref="canonical/sources/SRC-PAPER-002.md",
                origin_weight=0.7,
                source_quality=0.9,
                verification_status=0.8,
                recency=0.7,
                independence=0.9,
                contradiction_status=0.8,
                domain_fit=0.8,
            ),
        ],
        recommended_use="hybrid",
    )

    internal_score = round((0.5 + 0.4 + 0.6 + 0.3 + 0.7 + 0.9) / 6, 4)
    external_score = round((0.9 + 0.8 + 0.7 + 0.9 + 0.8 + 0.8) / 6, 4)
    expected = round((0.3 * internal_score + 0.7 * external_score) / (0.3 + 0.7), 4)

    assert alternative.weighted_score == expected
    naive_average = round((internal_score + external_score) / 2, 4)
    assert alternative.weighted_score != naive_average


def test_origin_weight_must_be_between_zero_and_one() -> None:
    with pytest.raises(ValidationError):
        EvidenceOriginWeight(
            evidence_origin="internal_prior",
            ref="canonical/synthesis/SYN-OOR-001.md",
            origin_weight=1.5,
            source_quality=0.5,
            verification_status=0.5,
            recency=0.5,
            independence=0.5,
            contradiction_status=0.5,
            domain_fit=0.5,
        )


def test_weighted_alternative_rejects_zero_total_origin_weight() -> None:
    with pytest.raises(ValidationError, match="positive total origin_weight"):
        WeightedDecisionAlternative(
            alternative_id="ALT-ZERO-WEIGHT-001",
            producer_id="test",
            status="active",
            label="Zero-weight invalid alternative",
            claim="Origin weights must be positive in aggregate.",
            origin_weights=[
                EvidenceOriginWeight(
                    evidence_origin="internal_prior",
                    ref="canonical/synthesis/SYN-ZERO-001.md",
                    origin_weight=0.0,
                    source_quality=0.5,
                    verification_status=0.5,
                    recency=0.5,
                    independence=0.5,
                    contradiction_status=0.5,
                    domain_fit=0.5,
                ),
                EvidenceOriginWeight(
                    evidence_origin="external_source",
                    ref="canonical/sources/SRC-ZERO-001.md",
                    origin_weight=0.0,
                    source_quality=0.5,
                    verification_status=0.5,
                    recency=0.5,
                    independence=0.5,
                    contradiction_status=0.5,
                    domain_fit=0.5,
                ),
            ],
            recommended_use="request_more_evidence",
        )


def test_appraiser_policy_keeps_dars_advisory_and_separate_from_decision_authority() -> None:
    policy = AppraiserSeparationPolicy(
        policy_id="APPRAISER-POLICY-001",
        producer_id="test",
        status="active",
        appraiser_role="DARS/Devil",
        separate_from_roles=["Chief Editor", "Jeweler", "Hisys Core Synthesizer"],
        advisory_only=True,
        may_approve_decision=False,
        may_execute_action=False,
        checks=["confirmation_bias", "stale_evidence", "weak_evidence"],
    )

    assert policy.advisory_only is True

    with pytest.raises(ValidationError, match="advisory only"):
        AppraiserSeparationPolicy(
            policy_id="APPRAISER-POLICY-BAD",
            producer_id="test",
            status="active",
            appraiser_role="DARS/Devil",
            separate_from_roles=["Chief Editor"],
            advisory_only=False,
            may_approve_decision=True,
            may_execute_action=False,
            checks=["confirmation_bias"],
        )
