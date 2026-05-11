"""Investment decision packet schema.

Traceability:
- HISYS-SCHEMA-001 extension for governed investment decision support packets.
- HISYS-NFR-SEC-004 boundary preservation: consequential actions require
  explicit human approval and remain non-executing by default.
- HISYS-FR-CE-002..006 review-gate discipline: Chief Editor/Devil/DARS status
  is recorded separately from final human approval and any order draft.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from ..core.ids import validate_id
from .base import BaseRecord

InvestmentDirection = Literal["bullish", "neutral", "bearish", "mixed", "unknown"]
InvestmentAction = Literal["buy", "staged_buy", "hold", "reduce", "sell", "watch", "no_action"]
ReviewStatus = Literal[
    "not_started",
    "blocked",
    "completed",
    "accepted_for_human_reviewed_use",
    "rejected",
]
HumanApprovalStatus = Literal["pending", "approved", "rejected", "not_required"]
OrderSide = Literal["buy", "sell"]
OrderType = Literal["market", "limit", "stop", "stop_limit"]


class InvestmentSignal(BaseModel):
    """One evidence-backed market/investment signal."""

    signal_id: str
    name: str
    direction: InvestmentDirection
    strength: float = Field(ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    interpretation: str
    limitations: list[str] = Field(default_factory=list)

    @field_validator("signal_id")
    @classmethod
    def _signal_id(cls, value: str) -> str:
        validate_id(value)
        if not value.startswith("SIG-"):
            raise ValueError(f"signal_id must start with 'SIG-': {value!r}")
        return value


class ScenarioAssessment(BaseModel):
    """Bull/base/bear scenario with explicit evidence references."""

    case_id: str
    summary: str
    probability: float = Field(ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    trigger_conditions: list[str] = Field(default_factory=list)

    @field_validator("case_id")
    @classmethod
    def _case_id(cls, value: str) -> str:
        validate_id(value)
        if not value.startswith("CASE-"):
            raise ValueError(f"case_id must start with 'CASE-': {value!r}")
        return value


class HumanApprovalGate(BaseModel):
    """Human approval and responsibility gate for consequential use."""

    required: bool = True
    status: HumanApprovalStatus = "pending"
    approver_ref: str | None = None
    approved_at: str | None = None
    responsibility_statement: str

    @model_validator(mode="after")
    def _approval_fields(self) -> "HumanApprovalGate":
        if self.status == "approved" and not self.approver_ref:
            raise ValueError("approved human approval requires approver_ref")
        if self.required and self.status == "not_required":
            raise ValueError("required human approval cannot have status='not_required'")
        return self


class OrderTicketDraft(BaseModel):
    """Non-executing order ticket draft; live use requires separate human approval."""

    ticket_id: str
    instrument: str
    side: OrderSide
    quantity_expression: str
    order_type: OrderType
    limit_price_expression: str | None = None
    dry_run: bool = True
    broker_ref: str | None = None
    execution_endpoint_ref: str | None = None

    @field_validator("ticket_id")
    @classmethod
    def _ticket_id(cls, value: str) -> str:
        validate_id(value)
        if not value.startswith("ORD-"):
            raise ValueError(f"ticket_id must start with 'ORD-': {value!r}")
        return value

    @model_validator(mode="after")
    def _no_live_endpoint_in_draft(self) -> "OrderTicketDraft":
        if self.execution_endpoint_ref:
            raise ValueError("OrderTicketDraft must not include execution_endpoint_ref")
        if self.order_type in ("limit", "stop_limit") and not self.limit_price_expression:
            raise ValueError(f"{self.order_type} order draft requires limit_price_expression")
        return self


class InvestmentDecisionPacket(BaseRecord):
    """Evidence-bounded buy/hold/sell decision-support packet.

    The packet may recommend and draft; it must not execute by default. Any
    consequential use requires explicit human approval and a separate execution
    control outside this schema.
    """

    REQUIREMENTS: ClassVar[tuple[str, ...]] = (
        "HISYS-NFR-SEC-004",
        "HISYS-FR-CE-002",
        "HISYS-FR-CE-003",
        "HISYS-FR-CE-004",
        "HISYS-FR-CE-005",
        "HISYS-FR-CE-006",
    )

    schema_id: str = "hisys.investment_decision_packet"
    packet_id: str
    asset: str
    instrument_refs: list[str] = Field(default_factory=list)
    time_horizon: str
    proposed_action: InvestmentAction
    recommendation_summary: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_score: float = Field(ge=0.0, le=1.0)
    risk_score: float = Field(ge=0.0, le=1.0)
    contradiction_score: float = Field(ge=0.0, le=1.0)
    signals: list[InvestmentSignal] = Field(default_factory=list)
    bull_case: ScenarioAssessment
    base_case: ScenarioAssessment
    bear_case: ScenarioAssessment
    decision_boundary: list[str] = Field(default_factory=list)
    risk_register: list[str] = Field(default_factory=list)
    contradicting_evidence_refs: list[str] = Field(default_factory=list)
    chief_editor_status: ReviewStatus = "not_started"
    devil_review_status: ReviewStatus = "not_started"
    dars_review_status: ReviewStatus = "not_started"
    human_insight_refs: list[str] = Field(default_factory=list)
    human_approval: HumanApprovalGate
    order_ticket_draft: OrderTicketDraft | None = None
    execution_authorized: bool = False
    publication_or_live_action_approved: bool = False
    disclaimers: list[str] = Field(default_factory=lambda: ["not financial advice", "no autonomous execution"])

    @field_validator("packet_id")
    @classmethod
    def _packet_id(cls, value: str) -> str:
        validate_id(value)
        if not value.startswith("IDP-"):
            raise ValueError(f"packet_id must start with 'IDP-': {value!r}")
        return value

    @model_validator(mode="after")
    def _decision_boundaries(self) -> "InvestmentDecisionPacket":
        if not self.signals:
            raise ValueError("InvestmentDecisionPacket requires at least one signal")
        if any(not signal.evidence_refs for signal in self.signals):
            raise ValueError("signals require evidence_refs")
        if any(
            not scenario.evidence_refs
            for scenario in (self.bull_case, self.base_case, self.bear_case)
        ):
            raise ValueError("scenario assessments require evidence_refs")
        if self.execution_authorized and self.human_approval.status != "approved":
            raise ValueError("execution_authorized requires human_approval.status='approved'")
        if self.publication_or_live_action_approved and self.human_approval.status != "approved":
            raise ValueError(
                "publication_or_live_action_approved requires human_approval.status='approved'"
            )
        if self.order_ticket_draft and not self.order_ticket_draft.dry_run and self.human_approval.status != "approved":
            raise ValueError("live order_ticket_draft requires approved human approval")
        if "not financial advice" not in {item.lower() for item in self.disclaimers}:
            raise ValueError("InvestmentDecisionPacket disclaimers must include 'not financial advice'")
        if "no autonomous execution" not in {item.lower() for item in self.disclaimers}:
            raise ValueError("InvestmentDecisionPacket disclaimers must include 'no autonomous execution'")
        return self
