"""DARS handoff loop runtime tests.

Traceability: HISYS-FR-AGT-001..005, HISYS-DARS-CONTRACT-001,
HISYS-D-015, HISYS-T-023, HISYS-T-024.

Local DARS adapter tests trace to the Local DARS / ByeSys Provenance plan
Milestones 2 and 3 (`docs/plans/2026-05-16-local-dars-byesys-provenance.md`).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from hisys.agents.dars import DarsRuntime
from hisys.config.instance import InstanceRoot

from helpers.fake_openai_server import FakeOpenAIServer


def test_dars_runtime_loopback_placeholder_returns_without_implemented_dars(tmp_path: Path):
    execution_dir = tmp_path / "data" / "alert-connector-executions" / "20260508"
    execution_dir.mkdir(parents=True)
    (execution_dir / "EXEC-LOOPBACK-001.json").write_text(
        json.dumps(
            {
                "execution_id": "EXEC-LOOPBACK-001",
                "action_plan_ref": "PLAN-LOOPBACK-001",
                "alert_decision_ref": "ALERT-LOOPBACK-001",
                "connector_id": "disabled-fixture-connector",
                "target_channel": "discord:#ops",
                "would_send": True,
                "live_delivery_permitted": False,
                "execution_status": "blocked",
                "blocked_reason": "live_delivery_disabled",
                "action_taken": "none",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    report = DarsRuntime(instance=InstanceRoot(tmp_path)).run_loopback_placeholder(
        yyyymmdd="20260508",
        source_execution_id="EXEC-LOOPBACK-001",
        producer_id="dars-loopback-test",
    )

    assert report.handoff_refs == ["HANDOFF-DARS-LOOPBACK-001"]
    assert report.critique_refs == ["CRITIQUE-DARS-LOOPBACK-001"]
    handoff = json.loads((tmp_path / "data" / "agent-handoffs" / "20260508" / "HANDOFF-DARS-LOOPBACK-001.json").read_text(encoding="utf-8"))
    critique = json.loads((tmp_path / "data" / "agent-critiques" / "20260508" / "CRITIQUE-DARS-LOOPBACK-001.json").read_text(encoding="utf-8"))
    assert handoff["allowed_actions"] == "advisory_only"
    assert handoff["status"] == "linked"
    assert "dars_backend=loopback_placeholder" in handoff["constraints"]
    assert critique["critique_text"].startswith("DARS is not implemented yet")
    assert critique["dars_backend"] == "loopback_placeholder"
    assert critique["external_call_made"] is False
    assert critique["action_taken"] == "none"



def test_dars_runtime_prepares_advisory_handoff_and_ingests_fixture_critique(tmp_path: Path):
    execution_dir = tmp_path / "data" / "alert-connector-executions" / "20260508"
    execution_dir.mkdir(parents=True)
    execution_path = execution_dir / "EXEC-DARS-001.json"
    execution_path.write_text(
        json.dumps(
            {
                "execution_id": "EXEC-DARS-001",
                "action_plan_ref": "PLAN-DARS-001",
                "alert_decision_ref": "ALERT-DARS-001",
                "connector_id": "disabled-fixture-connector",
                "target_channel": "discord:#ops",
                "would_send": True,
                "live_delivery_permitted": False,
                "execution_status": "blocked",
                "blocked_reason": "live_delivery_disabled",
                "action_taken": "none",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    report = DarsRuntime(instance=InstanceRoot(tmp_path)).run_fixture_critique(
        yyyymmdd="20260508",
        source_execution_id="EXEC-DARS-001",
        critique_text="Confidence overstated; cite raw payload.",
        producer_id="dars-fixture-test",
    )

    assert report.handoff_refs == ["HANDOFF-DARS-001"]
    assert report.critique_refs == ["CRITIQUE-DARS-001"]
    assert report.linked_execution_refs == ["EXEC-DARS-001"]

    handoff_path = tmp_path / "data" / "agent-handoffs" / "20260508" / "HANDOFF-DARS-001.json"
    critique_path = tmp_path / "data" / "agent-critiques" / "20260508" / "CRITIQUE-DARS-001.json"
    handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
    critique = json.loads(critique_path.read_text(encoding="utf-8"))

    assert handoff["target_agent_system"] == "DARS"
    assert handoff["allowed_actions"] == "advisory_only"
    assert handoff["approval_state"] == "not_required"
    assert handoff["status"] == "linked"
    assert handoff["evidence_bundle"] == ["EXEC-DARS-001"]
    assert "no live external action" in handoff["constraints"]

    assert critique["critique_id"] == "CRITIQUE-DARS-001"
    assert critique["handoff_ref"] == "HANDOFF-DARS-001"
    assert critique["source_execution_ref"] == "EXEC-DARS-001"
    assert critique["allowed_actions"] == "advisory_only"
    assert critique["action_taken"] == "none"
    assert critique["status"] == "received"
    assert "Confidence overstated" in critique["critique_text"]
    assert (tmp_path / "reports" / "run-summaries" / "20260508" / "dars-critique-report.md").exists()


def test_dars_runtime_uses_configured_cli_agent_backend(tmp_path: Path):
    execution_dir = tmp_path / "data" / "alert-connector-executions" / "20260508"
    execution_dir.mkdir(parents=True)
    (execution_dir / "EXEC-CLAUDE-001.json").write_text(
        json.dumps(
            {
                "execution_id": "EXEC-CLAUDE-001",
                "action_plan_ref": "PLAN-CLAUDE-001",
                "alert_decision_ref": "ALERT-CLAUDE-001",
                "connector_id": "disabled-fixture-connector",
                "target_channel": "discord:#ops",
                "would_send": True,
                "live_delivery_permitted": False,
                "execution_status": "blocked",
                "blocked_reason": "live_delivery_disabled",
                "action_taken": "none",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    fake_agent = tmp_path / "fake_claude.py"
    fake_agent.write_text(
        "import sys\n"
        "print('configured Claude DARS critique ran; argv=' + ' '.join(sys.argv[1:]))\n",
        encoding="utf-8",
    )
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "dars.json").write_text(
        json.dumps(
            {
                "schema_id": "hisys.dars.config",
                "schema_version": "0.1.0",
                "config_id": "dars-claude-runtime",
                "config_version": "0.1.0",
                "owner": "sysailab",
                "status": "active",
                "classification": "runtime_config",
                "traceability": {
                    "requirements": ["HISYS-FR-AGT-001", "HISYS-T-019", "HISYS-T-020"],
                    "constraints": ["HISYS-CON-010", "HISYS-CON-011", "HISYS-CON-012"],
                },
                "spec": {
                    "default_backend": "claude_dars",
                    "policy": {
                        "enabled": True,
                        "allowed_actions": "advisory_only",
                        "require_human_approval_for_external_call": True,
                        "require_structured_output_schema": "DarsCritiqueRecord",
                        "allow_external_side_effects": False,
                        "max_runtime_seconds": 30,
                        "redact_markdown_outputs": True,
                    },
                    "roles": {
                        "default_devil_advocate": {
                            "kind": "devil_advocate",
                            "profession": "systems_safety_reviewer",
                            "stance": "skeptical_but_constructive",
                            "strictness": "high",
                            "creativity": "medium",
                            "verbosity": "concise_structured",
                            "critique_dimensions": ["unsupported_claims", "risk_findings"],
                            "prompt": {"objective": "Challenge unsupported claims."},
                            "sampling": {"temperature": 0.2, "top_p": 0.9, "max_output_tokens": 2000},
                            "output_contract": "DarsCritiqueRecord",
                        }
                    },
                    "backends": {
                        "claude_dars": {
                            "kind": "cli_agent",
                            "enabled": True,
                            "mode": "read_only",
                            "command": sys.executable,
                            "args": [str(fake_agent)],
                            "allowed_tools": ["Read"],
                            "disallowed_tools": ["Edit", "Write", "WebSearch", "WebFetch"],
                            "external_call_allowed": False,
                            "model": "sonnet",
                            "output_contract": "DarsCritiqueRecord",
                        }
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    report = DarsRuntime(instance=InstanceRoot(tmp_path)).run_configured_critique(
        yyyymmdd="20260508",
        source_execution_id="EXEC-CLAUDE-001",
        producer_id="dars-cli-agent-test",
        approval_ref="APPROVAL-DARS-LOCAL-001",
    )

    assert report.handoff_refs == ["HANDOFF-DARS-CLAUDE-001"]
    critique = json.loads((tmp_path / "data" / "agent-critiques" / "20260508" / "CRITIQUE-DARS-CLAUDE-001.json").read_text(encoding="utf-8"))
    dispatch = json.loads((tmp_path / "runtime-boundary" / "dars" / "20260508" / "dars-dispatch-decision-EXEC-CLAUDE-001.json").read_text(encoding="utf-8"))
    assert critique["dars_backend"] == "claude_dars"
    assert critique["external_call_made"] is False
    assert "configured Claude DARS critique ran" in critique["critique_text"]
    assert "--model sonnet" in critique["critique_text"]
    assert dispatch["decision"] == "allowed"
    assert dispatch["backend_id"] == "claude_dars"


# ---------------------------------------------------------------------------
# Local DARS / ByeSys provenance plan — Milestones 2 and 3 (Ralph M9.1, M9.2)
# openai_compatible local-network adapter behavior against a fake loopback
# HTTP server. Each test uses an ephemeral 127.0.0.1 port and asserts the
# pre-HTTP rejection paths never contact the server.
# ---------------------------------------------------------------------------


def _seed_local_llm_instance(
    tmp_path: Path,
    *,
    endpoint: str,
    model: str = "qwen2.5:14b-instruct",
    max_runtime_seconds: int = 30,
) -> tuple[InstanceRoot, str]:
    """Create an instance whose configured DARS backend is a local LLM endpoint."""
    execution_dir = tmp_path / "data" / "alert-connector-executions" / "20260516"
    execution_dir.mkdir(parents=True)
    source_execution_id = "EXEC-LOCAL-LLM-001"
    (execution_dir / f"{source_execution_id}.json").write_text(
        json.dumps(
            {
                "execution_id": source_execution_id,
                "action_plan_ref": "PLAN-LOCAL-LLM-001",
                "alert_decision_ref": "ALERT-LOCAL-LLM-001",
                "connector_id": "disabled-fixture-connector",
                "target_channel": "discord:#ops",
                "would_send": True,
                "live_delivery_permitted": False,
                "execution_status": "blocked",
                "blocked_reason": "live_delivery_disabled",
                "action_taken": "none",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "dars.json").write_text(
        json.dumps(
            {
                "schema_id": "hisys.dars.config",
                "schema_version": "0.1.0",
                "config_id": "dars-local-llm-runtime",
                "config_version": "0.1.0",
                "owner": "sysailab",
                "status": "active",
                "classification": "runtime_config",
                "traceability": {
                    "requirements": ["HISYS-FR-AGT-001", "HISYS-T-019", "HISYS-T-020"],
                    "constraints": ["HISYS-CON-010", "HISYS-CON-011", "HISYS-CON-012"],
                },
                "spec": {
                    "default_backend": "local_llm_dars",
                    "policy": {
                        "enabled": True,
                        "allowed_actions": "advisory_only",
                        "require_human_approval_for_external_call": True,
                        "require_structured_output_schema": "DarsCritiqueRecord",
                        "allow_external_side_effects": False,
                        "max_runtime_seconds": max_runtime_seconds,
                        "redact_markdown_outputs": True,
                    },
                    "roles": {
                        "default_devil_advocate": {
                            "kind": "devil_advocate",
                            "profession": "systems_safety_reviewer",
                            "stance": "skeptical_but_constructive",
                            "strictness": "high",
                            "creativity": "medium",
                            "verbosity": "concise_structured",
                            "critique_dimensions": ["unsupported_claims", "risk_findings"],
                            "prompt": {"objective": "Challenge unsupported claims."},
                            "sampling": {"temperature": 0.2, "top_p": 0.9, "max_output_tokens": 2000},
                            "output_contract": "DarsCritiqueRecord",
                        }
                    },
                    "backends": {
                        "local_llm_dars": {
                            "kind": "openai_compatible",
                            "enabled": True,
                            "mode": "local_network_only",
                            "endpoint": endpoint,
                            "model": model,
                            "external_call_allowed": False,
                            "output_contract": "DarsCritiqueRecord",
                        }
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return InstanceRoot(tmp_path), source_execution_id


def _read_critique(tmp_path: Path, source_execution_id: str) -> dict:
    suffix = source_execution_id.removeprefix("EXEC-")
    path = tmp_path / "data" / "agent-critiques" / "20260516" / f"CRITIQUE-DARS-{suffix}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _read_local_llm_boundary(tmp_path: Path, source_execution_id: str) -> dict:
    path = (
        tmp_path
        / "runtime-boundary"
        / "dars"
        / "20260516"
        / f"dars-local-llm-boundary-{source_execution_id}.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _write_backend_activation_packet(
    tmp_path: Path,
    *,
    approval_ref: str = "APPROVAL-DARS-LOCAL-LLM-001",
    backend_id: str = "local_llm_dars",
    backend_kind: str = "openai_compatible",
    endpoint_scope: str = "localhost_only",
) -> Path:
    path = tmp_path / "backend-activation-packet.json"
    path.write_text(
        json.dumps(
            {
                "activation_id": "DARS-BE-ACT-20260521-LOCAL-001",
                "backend_id": backend_id,
                "backend_kind": backend_kind,
                "endpoint_scope": endpoint_scope,
                "allowed_actions": "advisory_only",
                "human_approved": True,
                "approval_ref": approval_ref,
                "expires_at": "2026-05-22T00:00:00Z",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def test_dars_runtime_requires_backend_activation_packet_before_local_model_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    contacted_adapter = False

    def fail_if_called(*args, **kwargs):
        nonlocal contacted_adapter
        contacted_adapter = True
        raise AssertionError("openai_compatible backend must not be contacted without backend activation")

    with FakeOpenAIServer() as server:
        instance, source_execution_id = _seed_local_llm_instance(tmp_path, endpoint=server.endpoint)
        monkeypatch.setattr(DarsRuntime, "_run_openai_compatible_backend", fail_if_called)

        with pytest.raises(ValueError) as exc_info:
            DarsRuntime(instance=instance).run_configured_critique(
                yyyymmdd="20260516",
                source_execution_id=source_execution_id,
                producer_id="dars-local-llm-missing-backend-activation",
                approval_ref="APPROVAL-DARS-LOCAL-LLM-001",
            )

    assert "backend_activation_packet_required" in str(exc_info.value)
    assert contacted_adapter is False
    assert server.contacted is False


def test_dars_runtime_rejects_backend_activation_approval_ref_mismatch(
    tmp_path: Path,
):
    activation_packet = _write_backend_activation_packet(
        tmp_path,
        approval_ref="APPROVAL-DARS-BE-DIFFERENT",
    )

    with FakeOpenAIServer() as server:
        instance, source_execution_id = _seed_local_llm_instance(tmp_path, endpoint=server.endpoint)
        with pytest.raises(ValueError) as exc_info:
            DarsRuntime(instance=instance).run_configured_critique(
                yyyymmdd="20260516",
                source_execution_id=source_execution_id,
                producer_id="dars-local-llm-activation-mismatch",
                approval_ref="APPROVAL-DARS-LOCAL-LLM-001",
                backend_activation_packet_ref=str(activation_packet),
            )

    assert "activation_approval_ref_mismatch" in str(exc_info.value)
    assert server.contacted is False


def test_dars_runtime_records_authorized_backend_activation_boundary(
    tmp_path: Path,
):
    activation_packet = _write_backend_activation_packet(
        tmp_path,
        approval_ref="APPROVAL-DARS-LOCAL-LLM-001",
    )

    with FakeOpenAIServer() as server:
        instance, source_execution_id = _seed_local_llm_instance(tmp_path, endpoint=server.endpoint)
        DarsRuntime(instance=instance).run_configured_critique(
            yyyymmdd="20260516",
            source_execution_id=source_execution_id,
            producer_id="dars-local-llm-authorized-backend-activation",
            approval_ref="APPROVAL-DARS-LOCAL-LLM-001",
            backend_activation_packet_ref=str(activation_packet),
        )

    boundary = _read_local_llm_boundary(tmp_path, source_execution_id)
    assert server.contacted is True
    assert boundary["approval_ref"] == "APPROVAL-DARS-LOCAL-LLM-001"
    assert boundary["backend_activation_packet_ref"] == str(activation_packet)
    assert boundary["model_boundary_crossed"] is True
    assert boundary["local_model_call_made"] is True
    assert boundary["external_call_made"] is False


def test_dars_runtime_calls_local_openai_compatible_backend(tmp_path: Path):
    activation_packet = _write_backend_activation_packet(tmp_path)
    with FakeOpenAIServer() as server:
        instance, source_execution_id = _seed_local_llm_instance(tmp_path, endpoint=server.endpoint)
        report = DarsRuntime(instance=instance).run_configured_critique(
            yyyymmdd="20260516",
            source_execution_id=source_execution_id,
            producer_id="dars-local-llm-test",
            approval_ref="APPROVAL-DARS-LOCAL-LLM-001",
            backend_activation_packet_ref=str(activation_packet),
        )

    assert server.contacted is True
    assert len(server.requests) == 1
    request = server.requests[0]
    assert request.path == "/v1/chat/completions"
    assert request.method == "POST"
    payload = request.json
    assert payload["model"] == "qwen2.5:14b-instruct"
    messages = payload.get("messages", [])
    assert messages and messages[0]["role"] == "system"
    combined_prompt = "\n".join(msg.get("content", "") for msg in messages)
    assert "advisory" in combined_prompt.lower()
    assert "no mutation" in combined_prompt.lower() or "do not mutate" in combined_prompt.lower()
    # Provenance instructions must be present in the prompt.
    assert "internal source" in combined_prompt.lower() or "internal knowledge" in combined_prompt.lower()
    assert "byesys" in combined_prompt.lower()
    # The adapter must not authorize tools, search, or browser actions.
    assert "tool_choice" not in payload
    assert "tools" not in payload
    assert report.critique_refs

    critique = _read_critique(tmp_path, source_execution_id)
    assert critique["dars_backend"] == "local_llm_dars"
    assert critique["external_call_made"] is False
    assert critique["model_boundary_crossed"] is True
    assert critique["local_model_call_made"] is True
    assert critique["endpoint_scope"] == "localhost_only"


def test_dars_runtime_records_local_model_boundary_not_external_call(tmp_path: Path):
    activation_packet = _write_backend_activation_packet(
        tmp_path,
        approval_ref="APPROVAL-DARS-LOCAL-LLM-002",
    )
    with FakeOpenAIServer() as server:
        instance, source_execution_id = _seed_local_llm_instance(tmp_path, endpoint=server.endpoint)
        DarsRuntime(instance=instance).run_configured_critique(
            yyyymmdd="20260516",
            source_execution_id=source_execution_id,
            producer_id="dars-local-llm-boundary",
            approval_ref="APPROVAL-DARS-LOCAL-LLM-002",
            backend_activation_packet_ref=str(activation_packet),
        )

    boundary = _read_local_llm_boundary(tmp_path, source_execution_id)
    assert boundary["approval_ref"] == "APPROVAL-DARS-LOCAL-LLM-002"
    assert boundary["endpoint_scope"] == "localhost_only"
    assert boundary["model_boundary_crossed"] is True
    assert boundary["local_model_call_made"] is True
    assert boundary["external_call_made"] is False
    assert boundary["mutation_performed"] is False


def test_dars_runtime_rejects_local_backend_without_approval_ref(tmp_path: Path):
    with FakeOpenAIServer() as server:
        instance, source_execution_id = _seed_local_llm_instance(tmp_path, endpoint=server.endpoint)
        with pytest.raises(ValueError) as exc_info:
            DarsRuntime(instance=instance).run_configured_critique(
                yyyymmdd="20260516",
                source_execution_id=source_execution_id,
                producer_id="dars-local-llm-missing-approval",
                approval_ref=None,
            )

    assert "approval" in str(exc_info.value).lower()
    assert server.contacted is False, "must fail closed before contacting the local server"


def test_dars_runtime_rejects_remote_endpoint_before_http_request(tmp_path: Path):
    # Seed a config whose endpoint config validation would fail; reuse a stand-in
    # remote host that the fake server never binds to so the test fails closed
    # purely from URL classification.
    with FakeOpenAIServer() as server:
        instance, source_execution_id = _seed_local_llm_instance(
            tmp_path,
            endpoint="http://203.0.113.5:11434/v1/chat/completions",
        )
        with pytest.raises(Exception) as exc_info:
            DarsRuntime(instance=instance).run_configured_critique(
                yyyymmdd="20260516",
                source_execution_id=source_execution_id,
                producer_id="dars-local-llm-remote",
                approval_ref="APPROVAL-DARS-LOCAL-LLM-REMOTE",
            )
        assert server.contacted is False
    text = str(exc_info.value).lower()
    assert "local" in text or "endpoint" in text or "non_local" in text


def test_dars_runtime_fails_closed_on_non_2xx_local_llm_response(tmp_path: Path):
    activation_packet = _write_backend_activation_packet(
        tmp_path,
        approval_ref="APPROVAL-DARS-LOCAL-LLM-503",
    )
    with FakeOpenAIServer(mode="non_2xx", non_2xx_status=503) as server:
        instance, source_execution_id = _seed_local_llm_instance(tmp_path, endpoint=server.endpoint)
        with pytest.raises(ValueError) as exc_info:
            DarsRuntime(instance=instance).run_configured_critique(
                yyyymmdd="20260516",
                source_execution_id=source_execution_id,
                producer_id="dars-local-llm-non2xx",
                approval_ref="APPROVAL-DARS-LOCAL-LLM-503",
                backend_activation_packet_ref=str(activation_packet),
            )

    assert server.contacted is True
    message = str(exc_info.value).lower()
    assert "non-2xx" in message or "503" in message or "http" in message


def test_dars_runtime_fails_closed_on_malformed_local_llm_response(tmp_path: Path):
    activation_packet = _write_backend_activation_packet(
        tmp_path,
        approval_ref="APPROVAL-DARS-LOCAL-LLM-MALFORMED",
    )
    with FakeOpenAIServer(mode="malformed_json") as server:
        instance, source_execution_id = _seed_local_llm_instance(tmp_path, endpoint=server.endpoint)
        with pytest.raises(ValueError) as exc_info:
            DarsRuntime(instance=instance).run_configured_critique(
                yyyymmdd="20260516",
                source_execution_id=source_execution_id,
                producer_id="dars-local-llm-malformed",
                approval_ref="APPROVAL-DARS-LOCAL-LLM-MALFORMED",
                backend_activation_packet_ref=str(activation_packet),
            )

    assert server.contacted is True
    assert "malformed" in str(exc_info.value).lower() or "json" in str(exc_info.value).lower()


def test_dars_runtime_fails_closed_on_missing_message_content(tmp_path: Path):
    activation_packet = _write_backend_activation_packet(
        tmp_path,
        approval_ref="APPROVAL-DARS-LOCAL-LLM-MISSING",
    )
    with FakeOpenAIServer(mode="missing_content") as server:
        instance, source_execution_id = _seed_local_llm_instance(tmp_path, endpoint=server.endpoint)
        with pytest.raises(ValueError) as exc_info:
            DarsRuntime(instance=instance).run_configured_critique(
                yyyymmdd="20260516",
                source_execution_id=source_execution_id,
                producer_id="dars-local-llm-missing-content",
                approval_ref="APPROVAL-DARS-LOCAL-LLM-MISSING",
                backend_activation_packet_ref=str(activation_packet),
            )

    assert server.contacted is True
    assert "content" in str(exc_info.value).lower() or "missing" in str(exc_info.value).lower()


def test_dars_runtime_fails_closed_on_local_llm_timeout(tmp_path: Path):
    activation_packet = _write_backend_activation_packet(
        tmp_path,
        approval_ref="APPROVAL-DARS-LOCAL-LLM-TIMEOUT",
    )
    with FakeOpenAIServer(mode="timeout", timeout_delay_seconds=2.0) as server:
        instance, source_execution_id = _seed_local_llm_instance(
            tmp_path,
            endpoint=server.endpoint,
            max_runtime_seconds=1,
        )
        with pytest.raises(ValueError) as exc_info:
            DarsRuntime(instance=instance).run_configured_critique(
                yyyymmdd="20260516",
                source_execution_id=source_execution_id,
                producer_id="dars-local-llm-timeout",
                approval_ref="APPROVAL-DARS-LOCAL-LLM-TIMEOUT",
                backend_activation_packet_ref=str(activation_packet),
            )

    assert server.contacted is True
    message = str(exc_info.value).lower()
    assert "timeout" in message or "timed out" in message


def test_dars_critique_record_normalizes_byesys_weight_to_zero():
    # M11.1: a DarsCritiqueRecord persisted with a ByeSys source entry must
    # always read back with evidential_weight=0.0 regardless of the configured
    # weight, so Jeweler review cannot accidentally treat ByeSys as
    # corroboration.
    from hisys.agents.dars import DarsCritiqueRecord

    record = DarsCritiqueRecord(
        critique_id="CRITIQUE-WEIGHTS-001",
        handoff_ref="HANDOFF-WEIGHTS-001",
        source_execution_ref="EXEC-WEIGHTS-001",
        critique_text="weighted advisory critique",
        producer_id="weights-test",
        source_weights=[
            {"source_id": "internal:obsidian:claim-001", "evidential_weight": 0.6, "kind": "internal"},
            {"source_id": "ByeSys", "evidential_weight": 0.9, "kind": "byesys"},
        ],
    )

    weights_by_source = {entry.source_id: entry.evidential_weight for entry in record.source_weights}
    assert weights_by_source["internal:obsidian:claim-001"] == 0.6
    assert weights_by_source["ByeSys"] == 0.0


def test_dars_critique_record_byesys_kind_is_recorded_when_byesys_source_id_given():
    # M11.1: even if the caller forgets to set `kind="byesys"`, the persisted
    # record should still classify ByeSys entries deterministically so Jeweler
    # review can recognize them without prose parsing.
    from hisys.agents.dars import DarsCritiqueRecord

    record = DarsCritiqueRecord(
        critique_id="CRITIQUE-WEIGHTS-002",
        handoff_ref="HANDOFF-WEIGHTS-002",
        source_execution_ref="EXEC-WEIGHTS-002",
        critique_text="weighted advisory critique",
        producer_id="weights-test",
        source_weights=[
            {"source_id": "ByeSys", "evidential_weight": 0.5},
        ],
    )

    assert record.source_weights[0].kind == "byesys"
    assert record.source_weights[0].evidential_weight == 0.0


def test_dars_runtime_local_llm_failure_does_not_leak_secrets(tmp_path: Path):
    with FakeOpenAIServer(mode="non_2xx") as server:
        instance, source_execution_id = _seed_local_llm_instance(tmp_path, endpoint=server.endpoint)
        with pytest.raises(ValueError) as exc_info:
            DarsRuntime(instance=instance).run_configured_critique(
                yyyymmdd="20260516",
                source_execution_id=source_execution_id,
                producer_id="dars-local-llm-leak-check",
                approval_ref="APPROVAL-DARS-LOCAL-LLM-LEAK-secret-do-not-log",
            )

    message = str(exc_info.value)
    # The error must not echo the approval ref, prompts, or response body verbatim.
    assert "secret-do-not-log" not in message
    assert "server_error" not in message
