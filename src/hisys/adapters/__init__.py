"""Hisys DataSource adapter framework (mocks only in I0/I1).

Traceability: HISYS-IDD-001 Section 4 (DataSource adapter contract),
HISYS-FR-DS-001..006. Live network use is intentionally absent;
``HISYS-CON-022..023`` and the I0/I1 scope require fixtures only.
"""

from .base import (
    AdapterStatus,
    HealthStatus,
    DataSource,
    RawCollectionResult,
)
from .hardware_mock import HardwareMockSource
from .web_news_mock import WebNewsMockSource
from .agent_system_mock import AgentSystemMockSource
from .hermes_tool_mock import HermesToolMockSource

__all__ = [
    "AdapterStatus",
    "HealthStatus",
    "DataSource",
    "RawCollectionResult",
    "HardwareMockSource",
    "WebNewsMockSource",
    "AgentSystemMockSource",
    "HermesToolMockSource",
]
