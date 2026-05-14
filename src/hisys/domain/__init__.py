"""Domain-specific Hisys investigation adapters."""

from .adapters import DomainAdapterRegistry, DomainInvestigationAdapter, DomainInvestigationContext
from .translation import (
    DomainUseCaseArtifactPacket,
    DomainUseCaseArtifactTranslator,
    build_domain_investigation_result,
)
from .layers import (
    AggregationLayer,
    AggregationWorkProduct,
    DecisionLayer,
    DecisionWorkProduct,
    DomainUseCase,
    DomainUseCaseContext,
    DomainUseCaseResult,
    InvestigationLayer,
    InvestigationWorkProduct,
    LayerTraceStep,
)

__all__ = [
    "AggregationLayer",
    "AggregationWorkProduct",
    "DecisionLayer",
    "DecisionWorkProduct",
    "DomainAdapterRegistry",
    "DomainInvestigationAdapter",
    "DomainInvestigationContext",
    "DomainUseCase",
    "DomainUseCaseArtifactPacket",
    "DomainUseCaseArtifactTranslator",
    "DomainUseCaseContext",
    "DomainUseCaseResult",
    "InvestigationLayer",
    "InvestigationWorkProduct",
    "LayerTraceStep",
    "build_domain_investigation_result",
]
