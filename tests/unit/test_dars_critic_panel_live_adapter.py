import json
from pathlib import Path

import pytest

from helpers.fake_openai_server import FakeOpenAIServer
from hisys.agents.dars_panel_live_adapter import (
    LocalModelCriticRequest,
    LocalModelPanelAdapter,
)
from hisys.agents.dars_panel_live_config import LiveDarsPanelActivationPacket
from hisys.config.instance import InstanceRoot


def _activation_packet() -> LiveDarsPanelActivationPacket:
    return LiveDarsPanelActivationPacket(
        activation_id="ACT-DARS-LIVE-2",
        approval_ref="APPROVAL-DARS-LIVE-LOCALHOST-ONLY",
        operator_id="operator-professor",
        expires_at="2026-05-21T00:00:00Z",
        requested_backend_id="local-fake-openai",
    )


def _critic_request(endpoint: str) -> LocalModelCriticRequest:
    return LocalModelCriticRequest(
        yyyymmdd="20260520",
        request_id="REQ-DARS-LIVE-2",
        task_id="TASK-DARS-LIVE-2-00-logical-devil",
        critic_id="logical-devil",
        critic_role="logical_devil",
        backend_id="local-fake-openai",
        model="fake-local-dars",
        endpoint=endpoint,
        candidate_ref="data/dars-panel-fixtures/20260520/candidate-001.json",
        evidence_refs=["data/dars-panel-fixtures/20260520/evidence-001.json"],
        rubric_ref="data/dars-panel-fixtures/20260520/rubric-001.json",
        critique_dimensions=["logical_validity", "missing_evidence"],
    )


def test_live_panel_adapter_calls_fake_local_model_and_records_model_boundary(tmp_path: Path):
    with FakeOpenAIServer(response_content="local fake critique: check unsupported claims") as server:
        server_host = server.host
        adapter = LocalModelPanelAdapter(instance=InstanceRoot(tmp_path))
        result = adapter.run_critic(
            activation_packet=_activation_packet(),
            critic_request=_critic_request(server.endpoint),
        )

    assert server_host == "127.0.0.1"
    assert server.contacted is True
    assert len(server.requests) == 1
    sent = server.requests[0].json
    assert sent["model"] == "fake-local-dars"
    rendered_messages = "\n".join(message["content"] for message in sent["messages"])
    assert "logical_devil" in rendered_messages
    assert "data/dars-panel-fixtures/20260520/candidate-001.json" in rendered_messages
    assert "data/dars-panel-fixtures/20260520/evidence-001.json" in rendered_messages
    assert "data/dars-panel-fixtures/20260520/rubric-001.json" in rendered_messages
    assert "advisory_only" in rendered_messages
    assert "no browser" in rendered_messages
    assert "no search" in rendered_messages
    assert "no tool authorization" in rendered_messages

    assert result.status == "completed"
    assert result.critique_text == "local fake critique: check unsupported claims"
    assert result.external_call_made is False
    assert result.local_model_call_made is True
    assert result.model_boundary_crossed is True
    assert result.endpoint_scope == "localhost_only"

    boundary = json.loads((tmp_path / result.boundary_ref).read_text(encoding="utf-8"))
    assert boundary["approval_ref"] == "APPROVAL-DARS-LIVE-LOCALHOST-ONLY"
    assert boundary["adapter_class"] == "local_model"
    assert boundary["endpoint_scope"] == "localhost_only"
    assert boundary["model_boundary_crossed"] is True
    assert boundary["local_model_call_made"] is True
    assert boundary["external_call_made"] is False
    assert boundary["mutation_performed"] is False
    assert boundary["allowed_actions"] == "advisory_only"
    assert isinstance(boundary["duration_ms"], int)
    assert boundary["duration_ms"] >= 0


def test_live_panel_adapter_rejects_remote_endpoint_before_http_request(tmp_path: Path):
    with FakeOpenAIServer() as server:
        adapter = LocalModelPanelAdapter(instance=InstanceRoot(tmp_path))
        request = _critic_request("https://api.example.com/v1/chat/completions")
        with pytest.raises(ValueError, match="localhost_only"):
            adapter.run_critic(
                activation_packet=_activation_packet(),
                critic_request=request,
            )

    assert server.contacted is False


def test_live_panel_adapter_rejects_missing_activation_approval_before_http_request(tmp_path: Path):
    with FakeOpenAIServer() as server:
        adapter = LocalModelPanelAdapter(instance=InstanceRoot(tmp_path))
        packet = _activation_packet().model_copy(update={"approval_ref": ""})
        with pytest.raises(ValueError, match="activation packet"):
            adapter.run_critic(
                activation_packet=packet,
                critic_request=_critic_request(server.endpoint),
            )

    assert server.contacted is False


def test_live_panel_adapter_isolates_local_model_failure_as_failed_task(tmp_path: Path):
    with FakeOpenAIServer(mode="non_2xx") as server:
        adapter = LocalModelPanelAdapter(instance=InstanceRoot(tmp_path))
        result = adapter.run_critic(
            activation_packet=_activation_packet(),
            critic_request=_critic_request(server.endpoint),
        )

    assert server.contacted is True
    assert result.status == "failed"
    assert result.critique_text is None
    assert result.external_call_made is False
    assert result.mutation_performed is False
    assert "non-2xx" in (result.error_message or "")
    boundary = json.loads((tmp_path / result.boundary_ref).read_text(encoding="utf-8"))
    assert boundary["dispatch_decision"] == "allowed"
    assert boundary["task_status"] == "failed"
    assert boundary["external_call_made"] is False
    assert boundary["mutation_performed"] is False
