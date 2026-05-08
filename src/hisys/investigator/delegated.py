"""Disabled delegated LLM/Hermes research-agent contract.

Traceability: HISYS-T-027, HISYS-FR-AGT-001..005, HISYS-DATA-005.
"""

from __future__ import annotations

import json

from pydantic import BaseModel

from .evidence import EvidenceValidationError, validate_evidence_package
from .research import EvidencePackage, ResearchTask


class DelegatedAgentSafetyError(ValueError):
    """Raised when delegated research output violates the HISYS contract."""


class DelegatedAgentConfig(BaseModel):
    """Configuration for delegated LLM/Hermes research adapters."""

    enabled: bool = False
    require_evidence_package: bool = True
    allowed_tools: list[str] = []


class DelegatedLLMResearchAgent:
    """Contract stub for future external LLM/Hermes subagents.

    The adapter is disabled by default. A future implementation may dispatch a
    Hermes/LLM subagent, but the only accepted runtime output remains
    EvidencePackage JSON; subagents must not write final memos directly.
    """

    agent_id = "delegated-llm-research-agent"
    agent_type = "delegated_llm"
    output_schema = "EvidencePackage"

    def __init__(self, config: DelegatedAgentConfig | None = None) -> None:
        self.config = config or DelegatedAgentConfig()

    def run(self, task: ResearchTask) -> EvidencePackage:
        if not self.config.enabled:
            raise DelegatedAgentSafetyError("delegated_llm research agent is disabled")
        raise DelegatedAgentSafetyError("live delegated LLM/Hermes dispatch is not implemented")


def parse_delegated_evidence_package(payload: str) -> EvidencePackage:
    """Parse and validate delegated-agent EvidencePackage JSON."""

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise DelegatedAgentSafetyError("delegated agent output must be EvidencePackage JSON") from exc
    try:
        package = EvidencePackage.model_validate(data)
    except Exception as exc:  # pydantic validation error type varies by version
        raise DelegatedAgentSafetyError("delegated agent output failed EvidencePackage schema validation") from exc
    try:
        validate_evidence_package(package)
    except EvidenceValidationError as exc:
        raise DelegatedAgentSafetyError(str(exc)) from exc
    if package.agent_type != "delegated_llm":
        raise DelegatedAgentSafetyError("delegated agent output must use agent_type=delegated_llm")
    return package
