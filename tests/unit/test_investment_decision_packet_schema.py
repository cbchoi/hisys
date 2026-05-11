import pytest
from pydantic import ValidationError

from hisys.schemas.investment import (
    HumanApprovalGate,
    InvestmentDecisionPacket,
    InvestmentSignal,
    OrderTicketDraft,
    ScenarioAssessment,
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
    assert dumped["human_approval"]["required"] is True
    assert dumped["human_approval"]["status"] == "pending"
    assert dumped["publication_or_live_action_approved"] is False
    assert dumped["execution_authorized"] is False
    assert dumped["order_ticket_draft"] is None
    assert "not financial advice" in dumped["disclaimers"]


def test_investment_decision_packet_blocks_execution_without_approved_human_gate():
    with pytest.raises(ValidationError, match="execution_authorized requires human_approval.status='approved'"):
        _packet(execution_authorized=True)


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
