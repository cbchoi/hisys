"""Shared pytest fixtures.

Traceability: HISYS-FIXTURE-001 Section 2 (controlled fixture sets), Section
3 (no live credentials, no real web access). All tokens here are explicitly
fake.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from hisys.adapters import (
    AgentSystemMockSource,
    HardwareMockSource,
    HermesToolMockSource,
    WebNewsMockSource,
)
from hisys.adapters.hermes_tool_mock import HermesCollectionInputs
from hisys.schemas import SourceRegistryEntry


@pytest.fixture
def hardware_source() -> SourceRegistryEntry:
    # HISYS-FIXTURE-001: hardware-mock-temperature
    return SourceRegistryEntry(
        source_id="SRC-HW-MOCK-001",
        source_type="hardware_sensor",
        display_name="Mock Temperature Sensor",
        owner="lab-test",
        lifecycle_state="experimental",
        reliability_class="B",
        access_method="device",
        cadence="P1H",
        rate_limit="60/min",
        usage_constraints=["test_only"],
        retention_rule="P7D",
        producer_id="fixture-hw",
    )


@pytest.fixture
def web_news_source() -> SourceRegistryEntry:
    # HISYS-FIXTURE-001: web-news-rss-permitted
    return SourceRegistryEntry(
        source_id="SRC-WEB-RSS-001",
        source_type="web_news",
        display_name="Permitted RSS Feed (fixture)",
        owner="research",
        lifecycle_state="approved",
        reliability_class="B",
        access_method="rss",
        cadence="PT1H",
        rate_limit="6/min",
        usage_constraints=["citation_required", "no_full_text_storage"],
        retention_rule="P30D",
        compliance_review_ref="WEB-COMPL-001",
        approved_by="reviewer-test",
        producer_id="fixture-web",
    )


@pytest.fixture
def agent_source() -> SourceRegistryEntry:
    # HISYS-FIXTURE-001: agent-dars-critique
    return SourceRegistryEntry(
        source_id="SRC-AGT-DARS-001",
        source_type="agent_system",
        display_name="DARS critique fixture",
        owner="qa",
        lifecycle_state="experimental",
        reliability_class="C",
        access_method="agent_handoff",
        cadence="ad_hoc",
        rate_limit="n/a",
        usage_constraints=["advisory_only"],
        retention_rule="P30D",
        producer_id="fixture-agent",
    )


@pytest.fixture
def hermes_source() -> SourceRegistryEntry:
    # HISYS-FIXTURE-001: hermes-tool-hierarchy
    return SourceRegistryEntry(
        source_id="SRC-HERMES-TOOL-001",
        source_type="hermes_tool",
        display_name="Hermes preapproved tool collection",
        owner="hermes-runtime",
        lifecycle_state="experimental",
        reliability_class="C",
        access_method="hermes_tool",
        cadence="PT1H",
        rate_limit="10/min",
        usage_constraints=["preapproved_scope_only"],
        retention_rule="P30D",
        scope_policy_ref="HERMES-SCOPE-001",
        delegated_subagent_preapproval_ref="HERMES-PREAPPROVAL-001",
        producer_id="fixture-hermes",
    )


@pytest.fixture
def hardware_adapter(hardware_source) -> HardwareMockSource:
    return HardwareMockSource(
        hardware_source,
        payload={"temperature_c": 92.4, "unit": "C"},
        device_identity="dev-mock-001",
    )


@pytest.fixture
def web_news_adapter(web_news_source) -> WebNewsMockSource:
    return WebNewsMockSource(
        web_news_source,
        payload={"title": "Lab announces new procedure", "summary": "..."},
        citation_url="https://example.test/feed/item-001",
        citation_title="Lab announces new procedure",
    )


@pytest.fixture
def agent_adapter(agent_source) -> AgentSystemMockSource:
    return AgentSystemMockSource(
        agent_source,
        payload={"critique": "Confidence overstated; cite raw payload."},
        agent_identity="dars-fixture",
    )


@pytest.fixture
def hermes_inputs() -> HermesCollectionInputs:
    # HISYS-IDD-001 Section 6 boundary path convention.
    boundary = (
        "hisys/runtime-boundary/hermes/20260508/CAMP-HERMES-001/"
        "tool_output-HERMES-001.md"
    )
    return HermesCollectionInputs(
        campaign_id="CAMP-HERMES-001",
        hermes_parent_run_id="run-parent-001",
        user_input_ref="hisys/runtime-boundary/hermes/20260508/CAMP-HERMES-001/user_input-001.md",
        prompt_or_query_ref="hisys/runtime-boundary/hermes/20260508/CAMP-HERMES-001/prompt-001.md",
        tool_output_ref="hisys/runtime-boundary/hermes/20260508/CAMP-HERMES-001/tool_output-001.md",
        boundary_record_ref=boundary,
        working_directory="/tmp/hisys-fixture-wd",
        scope_policy_ref="HERMES-SCOPE-001",
        approval_state="preapproved",
        tool_invocation_id="tool-invoke-001",
        tool_name="mock_search",
        enabled_toolsets=("read_only_search",),
        delegated_task_id="task-delegate-001",
        delegated_subagent_preapproval_ref="HERMES-PREAPPROVAL-001",
        source_scope="approved_research_feeds",
    )


@pytest.fixture
def hermes_adapter(hermes_source, hermes_inputs) -> HermesToolMockSource:
    return HermesToolMockSource(
        hermes_source,
        payload={"finding": "Two reliable sources contradict claim X."},
        inputs=hermes_inputs,
    )
