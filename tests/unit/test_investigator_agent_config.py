"""Tests for configurable Investigator evidence-agent connector registry.

Traceability: HISYS-T-032, HISYS-INST-INV-001, HISYS-FR-INV-001..006.
"""

from pathlib import Path

import pytest

from hisys.investigator.agent_config import (
    AgentConnectorSafetyError,
    load_investigator_agent_config,
    select_configured_agent_plan,
)


EXAMPLE_CONFIG = Path("examples/instance/config/investigator-agents.yaml")


def test_example_investigator_agent_config_declares_disabled_connectors_and_policy():
    config = load_investigator_agent_config(EXAMPLE_CONFIG)

    assert config.default_mode == "fixture_only"
    assert config.policy.live_network_enabled is False
    assert config.policy.require_human_approval_for_live_network is True
    assert config.policy.require_evidence_package_schema is True
    assert config.policy.allow_raw_payload_in_memo is False
    assert config.policy.allow_external_side_effects is False

    assert config.purpose_agent_plans["research_idea_discovery"].default_agents == ["formalism_gap_analysis"]
    assert "publisher_web_search" in config.purpose_agent_plans["research_idea_discovery"].optional_agents
    assert config.purpose_agent_plans["investment_decision_support"].default_agents == [
        "investment_decision_support"
    ]
    assert "company_filing_search" in config.purpose_agent_plans["investment_decision_support"].optional_agents

    claude = config.agents["claude_research_evidence"]
    assert claude.enabled is False
    assert claude.kind == "claude_code"
    assert claude.mode == "read_only"
    assert claude.output_contract == "EvidencePackage"
    assert claude.external_side_effects_allowed is False
    assert "Edit" in claude.disallowed_tools
    assert "Write" in claude.disallowed_tools

    search = config.agents["publisher_web_search"]
    assert search.enabled is False
    assert search.kind == "web_search"
    assert search.mode == "dry_run"
    assert "arxiv.org" in search.allowed_domains
    assert search.output_contract == "EvidencePackage"


def test_configured_agent_plan_uses_enabled_fixture_agents_and_records_disabled_optionals():
    config = load_investigator_agent_config(EXAMPLE_CONFIG)
    plan = select_configured_agent_plan(config, guideline_profile_id="research_idea_discovery", explicit_agent_types=None)

    assert plan.agent_types == ["formalism_gap_analysis"]
    assert plan.source == "config_default"
    assert "publisher_web_search" in plan.disabled_optional_agents
    assert "claude_research_evidence" in plan.disabled_optional_agents
    assert plan.blocked_agents == []


def test_configured_agent_plan_blocks_disabled_explicit_external_connector():
    config = load_investigator_agent_config(EXAMPLE_CONFIG)

    with pytest.raises(AgentConnectorSafetyError, match="disabled"):
        select_configured_agent_plan(
            config,
            guideline_profile_id="research_idea_discovery",
            explicit_agent_types=["publisher_web_search"],
        )
