"""Domain-specific Hisys investigation adapters."""

from .adapters import DomainAdapterRegistry, DomainInvestigationAdapter, DomainInvestigationContext
from .domain_adapters import DomainAdapterSpec, StructuredDomainAdapter, build_use_case_context
from .runtime import DomainRuntimeArtifactRefs, DomainRuntimeArtifactWriter
from .specs import codebase_spec, investment_spec, research_spec
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
    "DomainAdapterSpec",
    "DomainInvestigationAdapter",
    "DomainInvestigationContext",
    "DomainRuntimeArtifactRefs",
    "DomainRuntimeArtifactWriter",
    "DomainUseCase",
    "DomainUseCaseArtifactPacket",
    "DomainUseCaseArtifactTranslator",
    "DomainUseCaseContext",
    "DomainUseCaseResult",
    "InvestigationLayer",
    "InvestigationWorkProduct",
    "LayerTraceStep",
    "StructuredDomainAdapter",
    "build_domain_investigation_result",
    "build_use_case_context",
    "codebase_spec",
    "investment_spec",
    "research_spec",
]
