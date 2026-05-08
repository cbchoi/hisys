"""Adapter contract tests for mocks.

Traceability: HISYS-FR-DS-001..006, HISYS-T-003 (hardware), HISYS-T-004
(web/news), HISYS-T-005 (agent), HISYS-T-005A (Hermes hierarchical).
"""

from __future__ import annotations

from hisys.adapters import (
    AdapterStatus,
    AgentSystemMockSource,
    HardwareMockSource,
    HermesToolMockSource,
    WebNewsMockSource,
)
from hisys.schemas import RawObservation


def test_hardware_adapter_initialize_and_collect(hardware_adapter):
    status = hardware_adapter.initialize()
    assert isinstance(status, AdapterStatus) and status.initialized is True
    result = hardware_adapter.collect()
    assert result.provenance_bundle.collector_kind == "hardware_sensor"
    assert "over_threshold" in result.data_quality.anomaly_flags


def test_web_news_adapter_records_citation(web_news_adapter):
    result = web_news_adapter.collect()
    pb = result.provenance_bundle
    assert pb.collector_kind == "web_news"
    assert pb.citation_url == "https://example.test/feed/item-001"
    assert pb.fetch_method == "mock_rss"


def test_agent_adapter_advisory_label(agent_adapter):
    result = agent_adapter.collect()
    pb = result.provenance_bundle
    assert pb.collector_kind == "agent_system"
    assert pb.agent_advisory_label == "advisory_only"


def test_hermes_adapter_full_provenance(hermes_adapter, hermes_inputs):
    result = hermes_adapter.collect()
    pb = result.provenance_bundle
    assert pb.collector_kind == "hermes_tool"
    assert pb.campaign_id == hermes_inputs.campaign_id
    assert pb.hermes_parent_run_id == hermes_inputs.hermes_parent_run_id
    assert pb.user_input_ref == hermes_inputs.user_input_ref
    assert pb.delegated_task_id == hermes_inputs.delegated_task_id
    assert pb.tool_invocation_id == hermes_inputs.tool_invocation_id
    assert pb.boundary_record_ref == hermes_inputs.boundary_record_ref
    assert pb.scope_policy_ref == hermes_inputs.scope_policy_ref
    assert pb.approval_state == "preapproved"

    obs = hermes_adapter.to_observation(result, producer_id="hermes-test")
    assert isinstance(obs, RawObservation)
    trace = hermes_adapter.build_trace(producer_id="hermes-test", observation_refs=[obs.observation_id])
    assert trace.raw_observation_refs == [obs.observation_id]
    assert trace.status == "completed"
