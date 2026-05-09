"""Source connector governance package."""

from .doi_metadata import DoiMetadataConnector, DoiMetadataEvidencePackage
from .fixture_publisher import FixturePublisherConnector, FixturePublisherEvidencePackage
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
    "DoiMetadataConnector",
    "DoiMetadataEvidencePackage",
    "FixturePublisherConnector",
    "FixturePublisherEvidencePackage",
    "LiveSearchPolicy",
    "LiveSourceConnectorSafetyError",
    "SourceAccessRecord",
    "SourceConnectorConfig",
    "SourceConnectorDispatchDecision",
    "SourceConnectorDispatchGate",
    "SourceConnectorRegistry",
    "SourceEvidenceItem",
    "load_source_connector_registry",
]
