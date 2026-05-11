"""Hisys record schemas (Pydantic v2).

Implements HISYS-SCHEMA-001 v0.2.2. Each module declares the SRS/IDD/STD
IDs it covers in its module docstring; ``REQUIREMENTS`` constants make
the same trace machine-readable for ``scripts/validate_traceability.py``.
"""

from .base import BaseRecord, SCHEMA_VERSION
from .source import SourceRegistryEntry
from .compliance import WebComplianceReview
from .observation import RawObservation, ProvenanceBundle, DataQuality
from .signal import ExtractedSignal
from .perspective import PerspectiveProfile
from .memo import ZettelMemo
from .alert import AlertDecisionRecord
from .investment import (
    HumanApprovalGate,
    InvestmentDecisionPacket,
    InvestmentSignal,
    OrderTicketDraft,
    ScenarioAssessment,
)
from .lapidary_governance import (
    AppraiserSeparationPolicy,
    EvidenceChainRecord,
    EvidenceOriginWeight,
    HisysMode,
    LapidaryRoleAssignment,
    TemporalArchivePolicy,
    WeightedDecisionAlternative,
)
from .handoff import AgentHandoffPackage
from .hermes_trace import HermesCollectionTrace
from .audit import AuditEvent
from .browser_acceptance import (
    BrowserDarsCorroborationMappingRow,
    BrowserDarsRevisionResolution,
    BrowserDarsRevisionResolutionReport,
    BrowserDarsSegmentNormalizationRow,
    FinalBrowserAcceptanceReview,
    FinalBrowserAcceptanceReviewReport,
)
from .domain_investigation import (
    AlternativeDecisionSet,
    CandidateRecord,
    DomainEvidencePackage,
    DomainInvestigationConstraints,
    DomainInvestigationRequest,
    DomainInvestigationResult,
    DomainOutputContract,
    DomainSourceRef,
    HisysToolResult,
    InvestigationDataPackage,
)

__all__ = [
    "BaseRecord",
    "SCHEMA_VERSION",
    "SourceRegistryEntry",
    "WebComplianceReview",
    "RawObservation",
    "ProvenanceBundle",
    "DataQuality",
    "ExtractedSignal",
    "PerspectiveProfile",
    "ZettelMemo",
    "AlertDecisionRecord",
    "HumanApprovalGate",
    "InvestmentDecisionPacket",
    "InvestmentSignal",
    "OrderTicketDraft",
    "ScenarioAssessment",
    "AppraiserSeparationPolicy",
    "EvidenceChainRecord",
    "EvidenceOriginWeight",
    "HisysMode",
    "LapidaryRoleAssignment",
    "TemporalArchivePolicy",
    "WeightedDecisionAlternative",
    "AgentHandoffPackage",
    "HermesCollectionTrace",
    "AuditEvent",
    "BrowserDarsCorroborationMappingRow",
    "BrowserDarsRevisionResolution",
    "BrowserDarsRevisionResolutionReport",
    "BrowserDarsSegmentNormalizationRow",
    "FinalBrowserAcceptanceReview",
    "FinalBrowserAcceptanceReviewReport",
    "AlternativeDecisionSet",
    "CandidateRecord",
    "DomainEvidencePackage",
    "DomainInvestigationConstraints",
    "DomainInvestigationRequest",
    "DomainInvestigationResult",
    "DomainOutputContract",
    "DomainSourceRef",
    "HisysToolResult",
    "InvestigationDataPackage",
]
