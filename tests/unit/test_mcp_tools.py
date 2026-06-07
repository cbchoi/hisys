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


def _write_domain_request(path: Path, *, live: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    source_type = "web" if live else "fixture"
    payload = {
        "producer_id": "hermes",
        "status": "submitted",
        "request_id": "HISYS-REQ-RESEARCH-GAP-001",
        "domain": "research",
        "objective": "find research gap among formalisms for self-organizing structure",
        "sources": [
            {
                "source_id": "SRC-FORMALISM-FIXTURE-001",
                "source_type": source_type,
                "ref": "https://example.com/live" if live else "fixture://formalism-gap",
                "access_mode": "read_only",
            }
        ],
        "user_focus": "Separate source evidence from interpreted gap statements.",
    }
    if live:
        payload["allow_live_actions"] = True
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


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
        "data/source-access/20260605/HISYS-REQ-MCP-001-source.json",
        "data/investigation-memos/20260605/HISYS-REQ-MCP-001-memo.md",
        "data/chief-editor-reviews/20260605/HISYS-REQ-MCP-001-review.json",
        "data/dars-browser-reviews/20260605/HISYS-REQ-MCP-001-dars.md",
        "data/browser-dars-revision-resolutions/20260605/HISYS-REQ-MCP-001-resolution.json",
        "data/chief-editor-final-browser-reviews/20260605/HISYS-REQ-MCP-001-final.md",
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
    assert "data/source-access/20260605/HISYS-REQ-MCP-001-source.json" in envelope["artifact_refs"]
    assert "data/investigation-memos/20260605/HISYS-REQ-MCP-001-memo.md" in envelope["artifact_refs"]
    assert all("kind" in artifact for artifact in envelope["payload"]["artifacts"])


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


def test_environment_status_missing_config_maps_to_needs_more_evidence(tmp_path: Path) -> None:
    tools = _tools_module()

    result = tools.hisys_environment_status(environment_config=tmp_path / "missing-environment.yaml")
    envelope = _to_dict(result)

    assert envelope["status"] == "needs_more_evidence"
    assert envelope["external_call_made"] is False
    assert envelope["mutation_performed"] is False
    assert envelope["payload"]["exists"] is False
    assert envelope["payload"]["safe_to_use"] is False


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


def test_investigate_domain_with_request_path_writes_canonical_boundary_artifacts(tmp_path: Path) -> None:
    tools = _tools_module()
    instance = tmp_path / "instance"
    request_path = instance / "requests" / "domain-request.json"
    _write_domain_request(request_path)

    result = tools.hisys_investigate_domain(
        instance_root=instance,
        date="20260509",
        request_path="requests/domain-request.json",
    )
    envelope = _to_dict(result)

    assert envelope["status"] == "ok"
    assert envelope["external_call_made"] is False
    assert envelope["mutation_performed"] is False
    assert envelope["payload"]["request_id"] == "HISYS-REQ-RESEARCH-GAP-001"
    result_ref = "runtime-boundary/domain-investigation/research/20260509/hisys-tool-result-HISYS-REQ-RESEARCH-GAP-001.json"
    result_md_ref = "runtime-boundary/domain-investigation/research/20260509/hisys-tool-result-HISYS-REQ-RESEARCH-GAP-001.md"
    report_ref = "reports/run-summaries/20260509/domain-investigation-report.json"
    assert result_ref in envelope["artifact_refs"]
    assert result_md_ref in envelope["artifact_refs"]
    assert report_ref in envelope["artifact_refs"]
    assert (instance / result_ref).is_file()
    assert (instance / result_md_ref).is_file()
    assert (instance / report_ref).is_file()
    tool_result = json.loads((instance / result_ref).read_text(encoding="utf-8"))
    assert tool_result["status"] == "completed"
    assert tool_result["external_call_made"] is False
    assert tool_result["mutation_performed"] is False


def test_investigate_domain_inline_request_materializes_request_artifact_ref(tmp_path: Path) -> None:
    tools = _tools_module()
    instance = tmp_path / "instance"
    request = {
        "producer_id": "hermes",
        "status": "submitted",
        "request_id": "HISYS-REQ-INLINE-001",
        "domain": "research",
        "objective": "find research gap among formalisms for self-organizing structure",
        "sources": [
            {
                "source_id": "SRC-FORMALISM-FIXTURE-001",
                "source_type": "fixture",
                "ref": "fixture://formalism-gap",
                "access_mode": "read_only",
            }
        ],
        "user_focus": "Separate source evidence from interpreted gap statements.",
    }

    result = tools.hisys_investigate_domain(
        instance_root=instance,
        date="20260509",
        request=request,
    )
    envelope = _to_dict(result)

    inline_request_ref = "reports/run-summaries/20260509/mcp-investigate-domain-request-HISYS-REQ-INLINE-001.json"
    assert (instance / inline_request_ref).is_file()
    assert inline_request_ref in envelope["artifact_refs"]
    assert envelope["external_call_made"] is False
    assert envelope["mutation_performed"] is False
    assert envelope["publication_or_live_action_approved"] is False


def test_investigate_domain_inline_request_sanitizes_traversal_request_id(tmp_path: Path) -> None:
    tools = _tools_module()
    instance = tmp_path / "instance"
    request = {
        "producer_id": "hermes",
        "status": "submitted",
        "request_id": "../../escape?x=1",
        "domain": "research",
        "objective": "find research gap among formalisms for self-organizing structure",
        "sources": [
            {
                "source_id": "SRC-FORMALISM-FIXTURE-001",
                "source_type": "fixture",
                "ref": "fixture://formalism-gap",
                "access_mode": "read_only",
            }
        ],
    }

    result = tools.hisys_investigate_domain(instance_root=instance, date="20260509", request=request)
    envelope = _to_dict(result)

    sanitized_ref = "reports/run-summaries/20260509/mcp-investigate-domain-request-------escape-x-1.json"
    assert envelope["status"] == "ok"
    assert envelope["payload"]["request_id"] == "------escape-x-1"
    assert sanitized_ref in envelope["artifact_refs"]
    assert "runtime-boundary/domain-investigation/research/20260509/hisys-tool-request-------escape-x-1.json" in envelope["artifact_refs"]
    assert (instance / sanitized_ref).is_file()
    assert all(not ref.startswith("/") and ".." not in ref for ref in envelope["artifact_refs"])
    escaped_candidates = list(tmp_path.glob("**/escape?x=1*"))
    assert escaped_candidates == []


def test_investigate_domain_rejects_unsafe_request_path_without_cli_call(tmp_path: Path, monkeypatch) -> None:
    tools = _tools_module()

    def _forbidden_call(*args, **kwargs):  # pragma: no cover - failure path only
        raise AssertionError("unsafe request paths must be blocked before CLI execution")

    monkeypatch.setattr(tools, "run_hisys_cli", _forbidden_call, raising=False)

    for request_path in ["../escape.json", "/tmp/escape.json", "requests/domain-request.txt"]:
        result = tools.hisys_investigate_domain(instance_root=tmp_path, date="20260509", request_path=request_path)
        envelope = _to_dict(result)
        assert envelope["status"] == "blocked"
        assert envelope["external_call_made"] is False
        assert envelope["mutation_performed"] is False


def test_investigate_domain_preserves_live_action_block_with_request_path(tmp_path: Path) -> None:
    tools = _tools_module()
    instance = tmp_path / "instance"
    request_path = instance / "requests" / "live-request.json"
    _write_domain_request(request_path, live=True)

    result = tools.hisys_investigate_domain(
        instance_root=instance,
        date="20260509",
        request_path="requests/live-request.json",
    )
    envelope = _to_dict(result)

    assert envelope["status"] == "blocked"
    assert envelope["external_call_made"] is False
    assert envelope["mutation_performed"] is False
    assert "live" in envelope["error"].lower()


def test_investigate_domain_cli_validation_failure_returns_safe_error_envelope(tmp_path: Path) -> None:
    tools = _tools_module()
    instance = tmp_path / "instance"
    request_path = instance / "requests" / "invalid-request.json"
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text(
        json.dumps(
            {
                "producer_id": "hermes",
                "status": "submitted",
                "request_id": "HISYS-REQ-INVALID-001",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    result = tools.hisys_investigate_domain(
        instance_root=instance,
        date="20260509",
        request_path="requests/invalid-request.json",
    )
    envelope = _to_dict(result)

    assert envelope["status"] == "error"
    assert envelope["tool_name"] == "investigate_domain"
    assert envelope["external_call_made"] is False
    assert envelope["mutation_performed"] is False
    assert envelope["publication_or_live_action_approved"] is False
    payload = envelope["payload"]
    assert "returncode" in payload
    assert payload["timed_out"] is False
    assert isinstance(payload["command_args"], list) and payload["command_args"]
    assert "stdout" in payload
    assert "stderr" in payload
    assert envelope["error"]


def test_investigate_domain_rejects_inline_request_and_request_path_together(tmp_path: Path) -> None:
    tools = _tools_module()
    request_path = tmp_path / "requests" / "domain-request.json"
    _write_domain_request(request_path)

    result = tools.hisys_investigate_domain(
        instance_root=tmp_path,
        date="20260509",
        request={"request_id": "HISYS-REQ-INLINE-001"},
        request_path="requests/domain-request.json",
    )
    envelope = _to_dict(result)

    assert envelope["status"] == "blocked"
    assert "either request or request_path" in envelope["error"].lower()


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
    assert "reports/run-summaries/20260605/hisys-release-readiness.json" in envelope["artifact_refs"]
    assert "reports/run-summaries/20260605/hisys-release-readiness.md" in envelope["artifact_refs"]
    assert (tmp_path / "reports/run-summaries/20260605/hisys-release-readiness.md").is_file()


def test_future_altas_dars_judge_tools_are_not_exposed_by_default() -> None:
    tools = _tools_module()

    names = set(tools.list_hisys_mcp_tool_names(expose_future_tools=False))

    assert {"health_status", "environment_status", "investigate_domain", "list_run_artifacts", "show_artifact", "release_readiness"} <= names
    assert "altas_status" not in names
    assert "dars_status" not in names
    assert "judge_status" not in names
    assert "judge_decide" not in names


def test_future_status_tools_are_exposed_only_when_requested() -> None:
    tools = _tools_module()

    names = set(tools.list_hisys_mcp_tool_names(expose_future_tools=True))

    assert {"altas_status", "dars_status", "judge_status"} <= names
    assert "judge_decide" not in names


def test_subsystem_status_placeholders_fail_closed_without_subprocesses(monkeypatch) -> None:
    tools = _tools_module()

    def _forbidden_call(*args, **kwargs):  # pragma: no cover - failure path only
        raise AssertionError("gateway placeholders must not execute subprocesses in this lane")

    monkeypatch.setattr(tools, "run_hisys_cli", _forbidden_call, raising=False)

    for func_name, tool_name in [
        ("hisys_altas_status", "altas_status"),
        ("hisys_dars_status", "dars_status"),
        ("hisys_judge_status", "judge_status"),
    ]:
        result = getattr(tools, func_name)()
        envelope = _to_dict(result)
        assert envelope["status"] in {"blocked", "error"}
        assert envelope["tool_name"] == tool_name
        assert envelope["external_call_made"] is False
        assert envelope["mutation_performed"] is False
        assert envelope["publication_or_live_action_approved"] is False
        assert envelope["human_approval_required"] is True
        assert envelope["error"]
        assert "unimplemented" in envelope["error"].lower() or "placeholder" in envelope["error"].lower()
