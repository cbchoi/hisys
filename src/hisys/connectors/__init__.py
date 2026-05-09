"""Source connector governance package."""

from .doi_metadata import DoiMetadataConnector, DoiMetadataEvidencePackage
from .claim_evidence_ledger import ClaimEvidenceLedgerBuilder, ClaimEvidenceLedgerRecord, ClaimEvidenceLedgerResult
from .fixture_publisher import FixturePublisherConnector, FixturePublisherEvidencePackage
from .open_access_pdf import OpenAccessPdfConnector, OpenAccessPdfEvidencePackage
from .pdf_candidate_planner import PdfCandidatePlan, PdfCandidatePlanner
from .pdf_evidence_promotion import PdfEvidencePromotionLoader, PromotedPdfEvidence
from .pdf_quote_extractor import PdfQuoteExtractionResult, PdfQuoteExtractor, SourceQuoteRecord
from .live_source_config import (
    LiveSearchPolicy,
    LiveSourceConnectorSafetyError,
    SourceConnectorConfig,
    SourceConnectorRegistry,
    load_source_connector_registry,
)
from .live_source_dispatch import SourceConnectorDispatchDecision, SourceConnectorDispatchGate
from .live_source_evidence import SourceAccessRecord, SourceEvidenceItem

__all__ = [
    "ClaimEvidenceLedgerBuilder",
    "ClaimEvidenceLedgerRecord",
    "ClaimEvidenceLedgerResult",
    "DoiMetadataConnector",
    "DoiMetadataEvidencePackage",
    "FixturePublisherConnector",
    "FixturePublisherEvidencePackage",
    "OpenAccessPdfConnector",
    "OpenAccessPdfEvidencePackage",
    "PdfCandidatePlan",
    "PdfCandidatePlanner",
    "PdfEvidencePromotionLoader",
    "PdfQuoteExtractionResult",
    "PdfQuoteExtractor",
    "PromotedPdfEvidence",
    "LiveSearchPolicy",
    "LiveSourceConnectorSafetyError",
    "SourceAccessRecord",
    "SourceConnectorConfig",
    "SourceConnectorDispatchDecision",
    "SourceConnectorDispatchGate",
    "SourceQuoteRecord",
    "SourceConnectorRegistry",
    "SourceEvidenceItem",
    "load_source_connector_registry",
]
