import pytest
from pydantic import ValidationError

from hisys.schemas.investment import (
    HumanApprovalGate,
    InvestmentDecisionPacket,
    InvestmentSignal,
    InvestmentWeightPolicy,
    OrderTicketDraft,
    ScenarioAssessment,
)
from hisys.schemas.lapidary_governance import (
    EvidenceChainRecord,
    EvidenceOriginWeight,
    HisysMode,
    WeightedDecisionAlternative,
)


def _signal(signal_id: str = "SIG-SP500-GDP-001") -> InvestmentSignal:
    return InvestmentSignal(
        signal_id=signal_id,
        name="Real GDP growth",
        direction="bullish",
        strength=0.68,
        evidence_refs=["EV-SP500-GDP-001"],
        interpretation="Positive real GDP growth supports risk assets over the stated horizon.",
    )


def _packet(**overrides) -> InvestmentDecisionPacket:
    data = {
        "packet_id": "IDP-SP500-001",
        "producer_id": "hisys-investment-decision-support",
        "status": "draft",
        "asset": "S&P 500",
        "instrument_refs": ["SPY", "VOO"],
        "time_horizon": "6-12 months",
        "proposed_action": "staged_buy",
        "weight_policy_ref": "IW-POLICY-SP500-BALANCED-001",
        "recommendation_summary": "Conditional staged exposure only if the human accepts valuation risk.",
        "confidence": 0.58,
        "evidence_score": 0.72,
        "risk_score": 0.61,
        "contradiction_score": 0.54,
        "signals": [_signal()],
        "bull_case": ScenarioAssessment(
            case_id="CASE-BULL-001",
            summary="Growth and liquidity conditions improve.",
            probability=0.35,
            evidence_refs=["EV-SP500-GDP-001"],
        ),
        "base_case": ScenarioAssessment(
            case_id="CASE-BASE-001",
            summary="Index grinds higher with valuation volatility.",
            probability=0.45,
            evidence_refs=["EV-SP500-GDP-001"],
        ),
        "bear_case": ScenarioAssessment(
            case_id="CASE-BEAR-001",
            summary="Valuation compresses if inflation/rates reaccelerate.",
            probability=0.20,
            evidence_refs=["EV-SP500-PE-001"],
        ),
        "decision_boundary": ["Do not full-size while valuation risk remains elevated."],
        "risk_register": ["High trailing P/E makes downside asymmetry material."],
        "contradicting_evidence_refs": ["EV-SP500-PE-001"],
        "chief_editor_status": "accepted_for_human_reviewed_use",
        "devil_review_status": "completed",
        "human_insight_refs": ["HUMAN-THESIS-AI-PRODUCTIVITY-001"],
        "human_approval": HumanApprovalGate(
            required=True,
            status="pending",
            approver_ref="human:professor",
            responsibility_statement="Human accepts responsibility before any consequential use.",
        ),
        "disclaimers": ["not financial advice", "no autonomous execution"],
    }
    data.update(overrides)
    return InvestmentDecisionPacket(**data)


def test_investment_decision_packet_serializes_human_gated_recommendation():
    packet = _packet()

    dumped = packet.model_dump(mode="json")

    assert dumped["schema_id"] == "hisys.investment_decision_packet"
    assert dumped["packet_id"] == "IDP-SP500-001"
    assert dumped["proposed_action"] == "staged_buy"
    assert dumped["weight_policy_ref"] == "IW-POLICY-SP500-BALANCED-001"
    assert dumped["human_approval"]["required"] is True
    assert dumped["human_approval"]["status"] == "pending"
    assert dumped["publication_or_live_action_approved"] is False
    assert dumped["execution_authorized"] is False
    assert dumped["order_ticket_draft"] is None
    assert "not financial advice" in dumped["disclaimers"]


def test_investment_decision_packet_blocks_execution_without_approved_human_gate():
    with pytest.raises(ValidationError, match="execution_authorized requires human_approval.status='approved'"):
        _packet(execution_authorized=True)


def test_investment_weight_policy_serializes_product_profile():
    policy = InvestmentWeightPolicy(
        policy_id="IW-POLICY-SP500-BALANCED-001",
        producer_id="hisys-investment-decision-support",
        status="active",
        profile_name="Balanced 6-12 month index decision support",
        risk_tolerance="balanced",
        time_horizon_profile="6-12 months",
        evidence_weight=0.40,
        risk_weight=0.25,
        contradiction_weight=0.20,
        confidence_weight=0.15,
        contradiction_handling="require_human_review",
        contradiction_threshold=0.60,
    )

    dumped = policy.model_dump(mode="json")

    assert dumped["schema_id"] == "hisys.investment_weight_policy"
    assert dumped["policy_id"] == "IW-POLICY-SP500-BALANCED-001"
    assert dumped["risk_tolerance"] == "balanced"
    assert dumped["contradiction_handling"] == "require_human_review"


def test_investment_weight_policy_rejects_zero_total_weight():
    with pytest.raises(ValidationError, match="InvestmentWeightPolicy requires positive total decision weight"):
        InvestmentWeightPolicy(
            policy_id="IW-POLICY-ZERO-001",
            producer_id="hisys-investment-decision-support",
            status="active",
            profile_name="Invalid zero policy",
            risk_tolerance="balanced",
            time_horizon_profile="6-12 months",
            evidence_weight=0.0,
            risk_weight=0.0,
            contradiction_weight=0.0,
            confidence_weight=0.0,
            contradiction_handling="require_human_review",
        )


def test_investment_decision_packet_blocks_order_draft_without_approval_and_dry_run():
    order = OrderTicketDraft(
        ticket_id="ORD-SPY-001",
        instrument="SPY",
        side="buy",
        quantity_expression="human_defined_notional",
        order_type="market",
        dry_run=False,
    )

    with pytest.raises(ValidationError, match="live order_ticket_draft requires approved human approval"):
        _packet(order_ticket_draft=order)


def test_human_approval_gate_serializes_requested_and_approved_scopes():
    gate = HumanApprovalGate(
        required=True,
        status="approved",
        approver_ref="human:professor",
        approved_at="2026-05-12T00:00:00Z",
        requested_scopes=["human_reviewed_use", "publication"],
        approved_scopes=["human_reviewed_use"],
        responsibility_statement="Human accepts responsibility for the approved scope only.",
    )

    dumped = gate.model_dump(mode="json")

    assert dumped["requested_scopes"] == ["human_reviewed_use", "publication"]
    assert dumped["approved_scopes"] == ["human_reviewed_use"]


def test_human_approval_gate_rejects_approved_status_without_approved_scope():
    with pytest.raises(ValidationError, match="approved human approval requires approved_scopes"):
        HumanApprovalGate(
            required=True,
            status="approved",
            approver_ref="human:professor",
            responsibility_statement="Human accepts responsibility before any consequential use.",
        )


def test_investment_decision_packet_blocks_execution_without_execution_approval_scope():
    approval = HumanApprovalGate(
        required=True,
        status="approved",
        approver_ref="human:professor",
        requested_scopes=["human_reviewed_use", "manual_execution"],
        approved_scopes=["human_reviewed_use"],
        responsibility_statement="Human accepts responsibility for review but not execution.",
    )

    with pytest.raises(ValidationError, match="execution_authorized requires approved manual_execution or live_connector_execution scope"):
        _packet(human_approval=approval, execution_authorized=True)


def test_investment_decision_packet_allows_manual_execution_only_with_explicit_scope():
    approval = HumanApprovalGate(
        required=True,
        status="approved",
        approver_ref="human:professor",
        requested_scopes=["human_reviewed_use", "manual_execution"],
        approved_scopes=["human_reviewed_use", "manual_execution"],
        responsibility_statement="Human accepts responsibility for manual execution outside Hisys.",
    )

    packet = _packet(human_approval=approval, execution_authorized=True)

    assert packet.execution_authorized is True
    assert "manual_execution" in packet.human_approval.approved_scopes


def test_investment_decision_packet_requires_evidence_for_signals_and_scenarios():
    with pytest.raises(ValidationError, match="signals require evidence_refs"):
        _packet(signals=[_signal().model_copy(update={"evidence_refs": []})])

    with pytest.raises(ValidationError, match="scenario assessments require evidence_refs"):
        _packet(
            bull_case=ScenarioAssessment(
                case_id="CASE-BULL-EMPTY",
                summary="Unsupported bull case.",
                probability=0.3,
                evidence_refs=[],
            )
        )


def _decision_chain(**overrides) -> EvidenceChainRecord:
    data = {
        "chain_id": "CHAIN-IDP-SP500-001",
        "producer_id": "hisys-investment-decision-support",
        "status": "active",
        "decision_ref": "canonical/decisions/DECISION-IDP-SP500-001.md",
        "synthesis_refs": ["canonical/synthesis/SYN-IDP-SP500-001.md"],
        "claim_ledger_refs": ["canonical/claims/LEDGER-IDP-SP500-001.md#C-IDP-SP500-001"],
        "evidence_refs": ["canonical/evidence/EVID-SP500-GDP-001.md"],
        "source_refs": ["canonical/sources/SRC-SP500-GDP-001.md"],
    }
    data.update(overrides)
    return EvidenceChainRecord(**data)


def test_investment_decision_packet_hisys_mode_defaults_to_selective_none():
    packet = _packet()

    assert packet.hisys_mode.level == "none"
    assert packet.hisys_mode.selective_governance is True
    assert packet.hisys_mode.applies_to_all_notes is False
    assert packet.evidence_chain is None

    dumped = packet.model_dump(mode="json")
    assert dumped["hisys_mode"]["level"] == "none"
    assert dumped["evidence_chain"] is None


def test_investment_decision_packet_decision_mode_requires_decision_level_evidence_chain():
    with pytest.raises(ValidationError, match="hisys_mode.level='decision'"):
        _packet(hisys_mode=HisysMode(level="decision"))


def test_investment_decision_packet_publication_mode_requires_decision_level_evidence_chain():
    with pytest.raises(ValidationError, match="hisys_mode.level='publication'"):
        _packet(hisys_mode=HisysMode(level="publication"))


def test_investment_decision_packet_decision_mode_rejects_stone_only_evidence_chain():
    stone_chain = EvidenceChainRecord(
        chain_id="CHAIN-IDP-SP500-STONE-001",
        producer_id="hisys-investment-decision-support",
        status="active",
        decision_ref=None,
        synthesis_refs=[],
        claim_ledger_refs=[],
        evidence_refs=["canonical/evidence/EVID-SP500-GDP-001.md"],
        source_refs=["canonical/sources/SRC-SP500-GDP-001.md"],
    )

    with pytest.raises(ValidationError, match="decision-level EvidenceChainRecord"):
        _packet(hisys_mode=HisysMode(level="decision"), evidence_chain=stone_chain)


def test_investment_decision_packet_decision_mode_accepts_decision_level_evidence_chain():
    packet = _packet(
        hisys_mode=HisysMode(level="decision"),
        evidence_chain=_decision_chain(),
        weighted_alternatives=[_weighted_alternative()],
    )

    assert packet.hisys_mode.level == "decision"
    assert packet.evidence_chain is not None
    assert packet.evidence_chain.decision_ref is not None
    dumped = packet.model_dump(mode="json")
    assert dumped["hisys_mode"]["level"] == "decision"
    assert dumped["evidence_chain"]["decision_ref"] == (
        "canonical/decisions/DECISION-IDP-SP500-001.md"
    )


def test_investment_decision_packet_lower_modes_allow_omitted_evidence_chain():
    for level in ("none", "stone", "claim", "synthesis"):
        packet = _packet(hisys_mode=HisysMode(level=level))
        assert packet.hisys_mode.level == level
        assert packet.evidence_chain is None


def _weighted_alternative(
    alternative_id: str = "ALT-IDP-SP500-001",
    *,
    origin_weight: float = 0.6,
) -> WeightedDecisionAlternative:
    return WeightedDecisionAlternative(
        alternative_id=alternative_id,
        producer_id="hisys-investment-decision-support",
        status="active",
        label="Staged buy under valuation guardrails",
        claim="Stagger exposure while contradiction risk remains elevated.",
        origin_weights=[
            EvidenceOriginWeight(
                evidence_origin="external_source",
                ref="canonical/evidence/EVID-SP500-GDP-001.md",
                origin_weight=origin_weight,
                source_quality=0.8,
                verification_status=0.7,
                recency=0.9,
                independence=0.6,
                contradiction_status=0.5,
                domain_fit=0.8,
            ),
        ],
        recommended_use="hybrid",
    )


def test_investment_decision_packet_decision_mode_requires_weighted_alternatives():
    with pytest.raises(ValidationError, match="weighted_alternatives"):
        _packet(
            hisys_mode=HisysMode(level="decision"),
            evidence_chain=_decision_chain(),
        )


def test_investment_decision_packet_publication_mode_requires_weighted_alternatives():
    with pytest.raises(ValidationError, match="weighted_alternatives"):
        _packet(
            hisys_mode=HisysMode(level="publication"),
            evidence_chain=_decision_chain(),
        )


def test_investment_decision_packet_decision_mode_rejects_empty_weighted_alternatives():
    with pytest.raises(ValidationError, match="weighted_alternatives"):
        _packet(
            hisys_mode=HisysMode(level="decision"),
            evidence_chain=_decision_chain(),
            weighted_alternatives=[],
        )


def test_investment_decision_packet_decision_mode_accepts_non_empty_weighted_alternatives():
    packet = _packet(
        hisys_mode=HisysMode(level="decision"),
        evidence_chain=_decision_chain(),
        weighted_alternatives=[_weighted_alternative()],
    )

    assert packet.hisys_mode.level == "decision"
    assert len(packet.weighted_alternatives) == 1
    alternative = packet.weighted_alternatives[0]
    assert alternative.alternative_id == "ALT-IDP-SP500-001"
    assert sum(w.origin_weight for w in alternative.origin_weights) > 0
    dumped = packet.model_dump(mode="json")
    assert dumped["weighted_alternatives"][0]["alternative_id"] == "ALT-IDP-SP500-001"


def test_investment_decision_packet_publication_mode_accepts_non_empty_weighted_alternatives():
    packet = _packet(
        hisys_mode=HisysMode(level="publication"),
        evidence_chain=_decision_chain(),
        weighted_alternatives=[_weighted_alternative()],
    )

    assert packet.hisys_mode.level == "publication"
    assert len(packet.weighted_alternatives) == 1


def test_investment_decision_packet_lower_modes_allow_empty_weighted_alternatives():
    for level in ("none", "stone", "claim", "synthesis"):
        packet = _packet(hisys_mode=HisysMode(level=level))
        assert packet.hisys_mode.level == level
        assert packet.weighted_alternatives == []
