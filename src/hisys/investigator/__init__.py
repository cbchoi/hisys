"""Investigator runtime package.

Traceability: HISYS-INST-INV-001, HISYS-FR-INV-001..006, HISYS-T-027.
"""

from .agents import FixtureContradictionAgent, FixtureResearchAgent, ResearchAgent, create_research_agent
from .research import AgentType, ClaimRecord, EvidenceItem, EvidencePackage, ResearchTask
from .runtime import CollectionReport, InvestigatorRuntime

__all__ = [
    "AgentType",
    "ClaimRecord",
    "CollectionReport",
    "EvidenceItem",
    "EvidencePackage",
    "FixtureContradictionAgent",
    "FixtureResearchAgent",
    "InvestigatorRuntime",
    "ResearchAgent",
    "ResearchTask",
    "create_research_agent",
]
