"""Investigator runtime package.

Traceability: HISYS-INST-INV-001, HISYS-FR-INV-001..006, HISYS-T-027,
HISYS-T-029, HISYS-T-030.
"""

from .agents import (
    FixtureContradictionAgent,
    FixtureResearchAgent,
    FormalismComparisonAgent,
    FormalismGapAnalysisAgent,
    InvestmentDecisionSupportAgent,
    ResearchAgent,
    SelfOrganizationMechanismAgent,
    create_research_agent,
)
from .delegated import (
    DelegatedAgentConfig,
    DelegatedAgentSafetyError,
    DelegatedLLMResearchAgent,
    parse_delegated_evidence_package,
)
from .evidence import EvidenceValidationError, MergedEvidence, merge_evidence_packages, validate_evidence_package
from .research import AgentType, ClaimRecord, EvidenceItem, EvidencePackage, ResearchTask
from .runtime import CollectionReport, InvestigatorRuntime

__all__ = [
    "AgentType",
    "ClaimRecord",
    "CollectionReport",
    "DelegatedAgentConfig",
    "DelegatedAgentSafetyError",
    "DelegatedLLMResearchAgent",
    "EvidenceItem",
    "EvidencePackage",
    "EvidenceValidationError",
    "FixtureContradictionAgent",
    "FixtureResearchAgent",
    "FormalismComparisonAgent",
    "FormalismGapAnalysisAgent",
    "InvestmentDecisionSupportAgent",
    "InvestigatorRuntime",
    "MergedEvidence",
    "ResearchAgent",
    "ResearchTask",
    "SelfOrganizationMechanismAgent",
    "create_research_agent",
    "merge_evidence_packages",
    "parse_delegated_evidence_package",
    "validate_evidence_package",
]
