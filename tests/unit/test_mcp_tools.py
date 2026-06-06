"""Transport-independent MCP tool wrapper tests.

Traceability: docs/plans/hisys-mcp-docker-service-implementation-tasks.md
Tasks 3.1-3.5 plus Claude review S0/Top-10 safety revisions.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path


def _tools_module():
    return importlib.import_module("hisys.mcp.tools")


def _to_dict(model_or_mapping: object) -> dict:
    if isinstance(model_or_mapping, dict):
        return model_or_mapping
    if hasattr(model_or_mapping, "model_dump"):
        return model_or_mapping.model_dump(mode="json")  # type: ignore[attr-defined]
    raise AssertionError(f"tool result is not a dict/model envelope: {type(model_or_mapping)!r}")


def _make_healthy_instance(root: Path) -> None:
    for name in ["config", "data", "reports", "runtime-boundary"]:
        (root / name).mkdir(parents=True, exist_ok=True)
    (root / "config" / "source-registry.yaml").write_text("sources: []\n", encoding="utf-8")


def test_health_status_tool_returns_fail_closed_envelope_and_artifact_refs(tmp_path: Path) -> None:
    tools = _tools_module()
    instance = tmp_path / "instance"
    _make_healthy_instance(instance)

    result = tools.hisys_health_status(instance_root=instance, date="20260605")
    envelope = _to_dict(result)

    assert envelope["status"] == "ok"
    assert envelope["tool_name"] == "health_status"
    assert envelope["external_call_made"] is False
    assert envelope["mutation_performed"] is False
    assert envelope["publication_or_live_action_approved"] is False
    assert all(not ref.startswith("/") and ".." not in ref for ref in envelope["artifact_refs"])
    assert "reports/run-summaries/20260605/hisys-health-status.json" in envelope["artifact_refs"]
    assert "reports/run-summaries/20260605/hisys-health-status.md" in envelope["artifact_refs"]


def test_show_artifact_rejects_absolute_path_and_dotdot_before_cli_call(tmp_path: Path, monkeypatch) -> None:
    tools = _tools_module()

    def _forbidden_call(*args, **kwargs):  # pragma: no cover - failure path only
        raise AssertionError("unsafe artifact ref must be rejected before invoking the CLI adapter")

    monkeypatch.setattr(tools, "run_hisys_cli", _forbidden_call, raising=False)

    for unsafe_ref in ["../secret.json", "/tmp/secret.json", "reports/../../secret.md", "reports/run.txt"]:
        envelope = _to_dict(tools.hisys_show_artifact(instance_root=tmp_path, artifact_ref=unsafe_ref))
        assert envelope["status"] == "blocked"
        assert envelope["external_call_made"] is False
        assert envelope["mutation_performed"] is False
        assert "unsafe" in envelope["error"].lower() or "unsupported" in envelope["error"].lower()


def test_list_run_artifacts_returns_safe_relative_refs(tmp_path: Path) -> None:
    tools = _tools_module()
    refs = [
        "reports/run-summaries/20260605/hisys-health-status.json",
        "reports/run-summaries/20260605/hisys-health-status.md",
        "data/evidence-packages/20260605/HISYS-REQ-MCP-001.json",
    ]
    for ref in refs:
        path = tmp_path / ref
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"ok": True}) + "\n", encoding="utf-8")

    result = tools.hisys_list_run_artifacts(instance_root=tmp_path, date="20260605", request_id="HISYS-REQ-MCP-001")
    envelope = _to_dict(result)

    assert envelope["status"] == "ok"
    assert envelope["tool_name"] == "list_run_artifacts"
    assert envelope["external_call_made"] is False
    assert all(not ref.startswith("/") and ".." not in ref for ref in envelope["artifact_refs"])
    assert "data/evidence-packages/20260605/HISYS-REQ-MCP-001.json" in envelope["artifact_refs"]


def test_environment_status_tool_uses_config_path_not_instance_argument(tmp_path: Path) -> None:
    tools = _tools_module()
    config_path = tmp_path / "environment.yaml"
    config_path.write_text(
        "schema_id: hisys.environment_config\n"
        "schema_version: 0.1.0\n"
        "host_id: test-host\n"
        "paths: {}\n"
        "stores: {}\n"
        "vaults: {}\n"
        "projection_targets: {}\n",
        encoding="utf-8",
    )

    result = tools.hisys_environment_status(environment_config=config_path)
    envelope = _to_dict(result)

    assert envelope["tool_name"] == "environment_status"
    assert envelope["external_call_made"] is False
    assert envelope["mutation_performed"] is False
    assert "instance" not in envelope.get("payload", {}).get("command_args", [])


def test_investigate_domain_rejects_live_request_fields_without_approval(tmp_path: Path) -> None:
    tools = _tools_module()
    request = {
        "producer_id": "hermes",
        "status": "submitted",
        "request_id": "HISYS-REQ-MCP-LIVE-001",
        "domain": "research",
        "objective": "collect current public web evidence",
        "sources": [{"source_id": "SRC-LIVE-WEB", "source_type": "web", "ref": "https://example.com"}],
        "allow_live_actions": True,
    }

    result = tools.hisys_investigate_domain(instance_root=tmp_path, request=request, date="20260605")
    envelope = _to_dict(result)

    assert envelope["status"] == "blocked"
    assert envelope["external_call_made"] is False
    assert envelope["mutation_performed"] is False
    assert envelope["publication_or_live_action_approved"] is False
    assert "live" in envelope["error"].lower()


def test_release_readiness_missing_quality_gates_does_not_invent_pass(tmp_path: Path) -> None:
    tools = _tools_module()

    result = tools.hisys_release_readiness(
        instance_root=tmp_path,
        date="20260605",
        quality_gates=[],
        trace_refs=["SourceRegistryEntry"],
        known_gaps=[],
    )
    envelope = _to_dict(result)

    assert envelope["status"] in {"blocked", "needs_more_evidence", "error"}
    assert envelope["external_call_made"] is False
    assert envelope["mutation_performed"] is False
    assert envelope["payload"].get("release_decision") != "human_review_ready"


def test_future_altas_dars_judge_tools_are_not_exposed_by_default() -> None:
    tools = _tools_module()

    names = set(tools.list_hisys_mcp_tool_names(expose_future_tools=False))

    assert {"health_status", "environment_status", "investigate_domain", "list_run_artifacts", "show_artifact", "release_readiness"} <= names
    assert "altas_status" not in names
    assert "dars_status" not in names
    assert "judge_status" not in names
