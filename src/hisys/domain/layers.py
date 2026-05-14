"""Three-layer domain use-case interfaces and records.

Traceability: HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001,
HISYS-CON-010..012.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Protocol

from hisys.schemas.domain_investigation import DomainInvestigationRequest

LayerName = Literal["investigation", "aggregation", "decision"]


@dataclass(frozen=True)
class DomainUseCaseContext:
    """Runtime context for a domain use case.

    Concrete layers receive this context rather than reading CLI globals. This
    keeps the use-case object testable and preserves the runtime-boundary write
    location chosen by the caller.
    """

    instance_root: Path
    boundary_dir: Path
    yyyymmdd: str


@dataclass(frozen=True)
class LayerTraceStep:
    """A deterministic trace entry for one completed layer."""

    layer: LayerName
    component: str
    output_ref: str


@dataclass(frozen=True)
class InvestigationWorkProduct:
    """Evidence discovered or selected by the investigation layer."""

    work_product_id: str
    scope: str
    local_search_targets: list[str]
    data_source_targets: list[str]
    memo_refs: list[str]
    evidence_refs: list[str]
    domain_subtype: str | None = None
    external_call_made: bool = False
    mutation_performed: bool = False


@dataclass(frozen=True)
class AggregationWorkProduct:
    """Report synthesized from investigation memos and evidence."""

    work_product_id: str
    report_type: str
    input_memo_refs: list[str]
    input_evidence_refs: list[str]
    report_ref: str
    summary: str
    external_call_made: bool = False
    mutation_performed: bool = False


@dataclass(frozen=True)
class DecisionWorkProduct:
    """Decision-layer review result over the aggregated report."""

    work_product_id: str
    decision_engine: str
    decision_type: str
    input_report_ref: str
    decision_ref: str
    recommendation: str
    requires_human_review: bool = True
    governance_flags: dict[str, bool] = field(default_factory=dict)
    external_call_made: bool = False
    mutation_performed: bool = False


@dataclass(frozen=True)
class DomainUseCaseResult:
    """Composed result of investigation -> aggregation -> decision."""

    request_id: str
    domain: str
    investigation: InvestigationWorkProduct
    aggregation: AggregationWorkProduct
    decision: DecisionWorkProduct
    layer_trace: list[LayerTraceStep] = field(default_factory=list)
    domain_subtype: str | None = None
    recommendation_summary: str = ""
    quality_gate: Literal["passed", "needs_more_evidence", "failed"] = "needs_more_evidence"
    requires_human_review: bool = True
    governance_flags: dict[str, bool] = field(default_factory=dict)
    external_call_made: bool = False
    mutation_performed: bool = False


class InvestigationLayer(Protocol):
    """Base interface for domain investigation components."""

    def investigate(
        self,
        request: DomainInvestigationRequest,
        context: DomainUseCaseContext,
    ) -> InvestigationWorkProduct:
        """Collect or select read-only evidence for the request."""


class AggregationLayer(Protocol):
    """Base interface for domain aggregation components."""

    def aggregate(
        self,
        request: DomainInvestigationRequest,
        context: DomainUseCaseContext,
        investigation: InvestigationWorkProduct,
    ) -> AggregationWorkProduct:
        """Aggregate investigation memos/evidence into a report."""


class DecisionLayer(Protocol):
    """Base interface for domain decision components."""

    def decide(
        self,
        request: DomainInvestigationRequest,
        context: DomainUseCaseContext,
        aggregation: AggregationWorkProduct,
    ) -> DecisionWorkProduct:
        """Run DARS or another approved decision review over the report."""


class DomainUseCase:
    """Object-oriented template for three-layer domain use cases."""

    def __init__(
        self,
        *,
        investigation_layer: InvestigationLayer,
        aggregation_layer: AggregationLayer,
        decision_layer: DecisionLayer,
    ) -> None:
        self._investigation_layer = investigation_layer
        self._aggregation_layer = aggregation_layer
        self._decision_layer = decision_layer

    def run(
        self,
        request: DomainInvestigationRequest,
        context: DomainUseCaseContext,
    ) -> DomainUseCaseResult:
        investigation = self._investigation_layer.investigate(request, context)
        aggregation = self._aggregation_layer.aggregate(request, context, investigation)
        decision = self._decision_layer.decide(request, context, aggregation)
        external_call_made = any(
            [investigation.external_call_made, aggregation.external_call_made, decision.external_call_made]
        )
        mutation_performed = any(
            [investigation.mutation_performed, aggregation.mutation_performed, decision.mutation_performed]
        )
        return DomainUseCaseResult(
            request_id=request.request_id,
            domain=request.domain,
            investigation=investigation,
            aggregation=aggregation,
            decision=decision,
            layer_trace=[
                LayerTraceStep(
                    layer="investigation",
                    component=type(self._investigation_layer).__name__,
                    output_ref=investigation.work_product_id,
                ),
                LayerTraceStep(
                    layer="aggregation",
                    component=type(self._aggregation_layer).__name__,
                    output_ref=aggregation.report_ref,
                ),
                LayerTraceStep(
                    layer="decision",
                    component=type(self._decision_layer).__name__,
                    output_ref=decision.decision_ref,
                ),
            ],
            domain_subtype=investigation.domain_subtype,
            recommendation_summary=decision.recommendation,
            quality_gate="needs_more_evidence",
            requires_human_review=decision.requires_human_review,
            governance_flags=dict(decision.governance_flags),
            external_call_made=external_call_made,
            mutation_performed=mutation_performed,
        )


__all__ = [
    "AggregationLayer",
    "AggregationWorkProduct",
    "DecisionLayer",
    "DecisionWorkProduct",
    "DomainUseCase",
    "DomainUseCaseContext",
    "DomainUseCaseResult",
    "InvestigationLayer",
    "InvestigationWorkProduct",
    "LayerTraceStep",
]
