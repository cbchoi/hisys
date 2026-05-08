"""Configurable Investigator evidence-agent connector registry.

Traceability: HISYS-T-032, HISYS-T-031, HISYS-T-030, HISYS-INST-INV-001,
HISYS-FR-INV-001..006, HISYS-DATA-005.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator


class AgentConnectorSafetyError(ValueError):
    """Raised when a configured Investigator connector violates safety policy."""


class InvestigatorAgentPolicy(BaseModel):
    """Global safety policy for optional Investigator connectors."""

    live_network_enabled: bool = False
    require_human_approval_for_live_network: bool = True
    require_evidence_package_schema: bool = True
    allow_raw_payload_in_memo: bool = False
    allow_external_side_effects: bool = False
    max_agent_runtime_seconds: int = 300
    max_sources_per_task: int = 10


class PurposeAgentPlan(BaseModel):
    """Default and optional agent names for a purpose guideline profile."""

    default_agents: list[str] = Field(default_factory=list)
    optional_agents: list[str] = Field(default_factory=list)


class AgentConnectorConfig(BaseModel):
    """Configured optional evidence connector.

    Connectors remain disabled until an explicit future task implements and
    approves their adapter. Even enabled connectors must return EvidencePackage.
    """

    enabled: bool = False
    kind: str
    mode: str = "dry_run"
    output_contract: Literal["EvidencePackage"] = "EvidencePackage"
    external_side_effects_allowed: bool = False
    allowed_domains: list[str] = Field(default_factory=list)
    disallowed_domains: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    disallowed_tools: list[str] = Field(default_factory=list)
    command: str | None = None
    endpoint: str | None = None
    model: str | None = None
    max_turns: int | None = None

    @model_validator(mode="after")
    def _validate_disabled_live_safety(self) -> "AgentConnectorConfig":
        if self.external_side_effects_allowed:
            raise ValueError("Investigator connectors must not allow external side effects")
        if self.output_contract != "EvidencePackage":
            raise ValueError("Investigator connectors must output EvidencePackage")
        return self


class InvestigatorAgentConfig(BaseModel):
    """Root config for Investigator purpose plans and optional connectors."""

    default_mode: str = "fixture_only"
    policy: InvestigatorAgentPolicy = Field(default_factory=InvestigatorAgentPolicy)
    purpose_agent_plans: dict[str, PurposeAgentPlan] = Field(default_factory=dict)
    agents: dict[str, AgentConnectorConfig] = Field(default_factory=dict)


class SelectedAgentPlan(BaseModel):
    """Resolved runtime agent plan after config and explicit CLI handling."""

    agent_types: list[str]
    source: str
    disabled_optional_agents: list[str] = Field(default_factory=list)
    blocked_agents: list[str] = Field(default_factory=list)


def load_investigator_agent_config(path: str | Path) -> InvestigatorAgentConfig:
    """Load and validate Investigator agent connector config from YAML."""

    config_path = Path(path)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return InvestigatorAgentConfig.model_validate(raw)


def select_configured_agent_plan(
    config: InvestigatorAgentConfig,
    *,
    guideline_profile_id: str,
    explicit_agent_types: list[str] | None,
) -> SelectedAgentPlan:
    """Resolve explicit or purpose-default agent plan from config.

    Built-in fixture agents may execute directly. Optional external connectors
    must be enabled before they can be selected, and live-network policy remains
    enforced by separate future adapters.
    """

    if explicit_agent_types:
        blocked = [agent for agent in explicit_agent_types if _is_disabled_connector(config, agent)]
        if blocked:
            raise AgentConnectorSafetyError(f"configured connector is disabled: {', '.join(blocked)}")
        return SelectedAgentPlan(agent_types=list(explicit_agent_types), source="explicit")

    purpose_plan = config.purpose_agent_plans.get(guideline_profile_id, PurposeAgentPlan())
    blocked_defaults = [agent for agent in purpose_plan.default_agents if _is_disabled_connector(config, agent)]
    if blocked_defaults:
        raise AgentConnectorSafetyError(f"default connector is disabled: {', '.join(blocked_defaults)}")
    disabled_optional = [agent for agent in purpose_plan.optional_agents if _is_disabled_connector(config, agent)]
    return SelectedAgentPlan(
        agent_types=list(purpose_plan.default_agents),
        source="config_default",
        disabled_optional_agents=disabled_optional,
    )


def _is_disabled_connector(config: InvestigatorAgentConfig, agent_name: str) -> bool:
    connector = config.agents.get(agent_name)
    return connector is not None and not connector.enabled
