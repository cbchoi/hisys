"""Local loopback MCP SDK streamable HTTP smoke tests.

Traceability: HISYS-MCP-STREAMABLE-HTTP-SDK-BINDING-PREFLIGHT.
This remains fixture/local only: the SDK server binds to a loopback ephemeral
port, an SDK client initializes and lists tools, and the server shuts down
without credentials, live provider/model calls, Hermes config mutation, or
production listener activation.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path


EXPECTED_TOOLS = [
    "health_status",
    "environment_status",
    "investigate_domain",
    "list_run_artifacts",
    "show_artifact",
    "release_readiness",
    "altas_search",
    "dars_panel_readiness",
    "run_dars_panel_golden",
    "judge_advisory",
]


def _write_domain_request(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "producer_id": "hermes",
                "status": "submitted",
                "request_id": "HISYS-REQ-RESEARCH-GAP-001",
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
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def test_mcp_streamable_http_sdk_client_lists_tools_without_runtime_mutation(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    env = {
        **os.environ,
        "PYTHONPATH": "src",
        "HISYS_INSTANCE_ROOT": str(runtime),
        "HISYS_ALLOW_LIVE_ACTIONS": "false",
        "HISYS_MCP_SAMPLING_ENABLED": "false",
    }

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hisys.mcp.server",
            "--streamable-http-local-smoke",
            "--http-host",
            "127.0.0.1",
            "--http-port",
            "0",
        ],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["schema_id"] == "hisys.mcp.streamable_http_sdk_local_smoke.v1"
    assert payload["status"] == "ok"
    assert payload["transport_kind"] == "streamable-http"
    assert payload["path"] == "/mcp"
    assert payload["host"] == "127.0.0.1"
    assert payload["port"] > 0
    assert payload["tools"] == EXPECTED_TOOLS
    assert payload["external_call_made"] is False
    assert payload["mutation_performed"] is False
    assert payload["publication_performed"] is False
    assert payload["live_provider_model_call_made"] is False
    assert payload["credential_lookup_performed"] is False
    assert payload["hermes_config_mutated"] is False
    assert payload["production_listener_started"] is False
    assert payload["sampling_enabled"] is False
    assert payload["server_shutdown"] is True
    assert not runtime.exists(), "SDK list-tools smoke must not create runtime artifacts"


def test_mcp_streamable_http_sdk_call_tool_creates_health_artifacts(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    env = {
        **os.environ,
        "PYTHONPATH": "src",
        "HISYS_INSTANCE_ROOT": str(runtime),
        "HISYS_ALLOW_LIVE_ACTIONS": "false",
        "HISYS_MCP_SAMPLING_ENABLED": "false",
    }

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hisys.mcp.server",
            "--streamable-http-local-call-tool-smoke",
            "--http-host",
            "127.0.0.1",
            "--http-port",
            "0",
            "--tool-name",
            "health_status",
            "--tool-args-json",
            json.dumps({"instance_root": str(runtime), "date": "20260605"}),
        ],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["schema_id"] == "hisys.mcp.streamable_http_sdk_call_tool_smoke.v1"
    assert payload["status"] == "ok"
    assert payload["tool_name"] == "health_status"
    assert payload["external_call_made"] is False
    assert payload["mutation_performed"] is False
    assert payload["publication_performed"] is False
    assert payload["hermes_config_mutated"] is False
    assert payload["production_listener_started"] is False
    result = payload["tool_result"]
    assert result["tool_name"] == "health_status"
    assert "reports/run-summaries/20260605/hisys-health-status.json" in result["artifact_refs"]
    assert "reports/run-summaries/20260605/hisys-health-status.md" in result["artifact_refs"]
    assert (runtime / "reports/run-summaries/20260605/hisys-health-status.json").is_file()
    assert (runtime / "reports/run-summaries/20260605/hisys-health-status.md").is_file()


def test_mcp_streamable_http_sdk_call_tool_no_args_uses_config_root_and_today(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    today = date.today().strftime("%Y%m%d")
    env = {
        **os.environ,
        "PYTHONPATH": "src",
        "HISYS_INSTANCE_ROOT": str(runtime),
        "HISYS_ALLOW_LIVE_ACTIONS": "false",
        "HISYS_MCP_SAMPLING_ENABLED": "false",
    }

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hisys.mcp.server",
            "--streamable-http-local-call-tool-smoke",
            "--http-host",
            "127.0.0.1",
            "--http-port",
            "0",
            "--tool-name",
            "health_status",
        ],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["status"] == "ok"
    result = payload["tool_result"]
    assert result["tool_name"] == "health_status"
    assert f"reports/run-summaries/{today}/hisys-health-status.json" in result["artifact_refs"]
    assert (runtime / f"reports/run-summaries/{today}/hisys-health-status.json").is_file()


def test_mcp_streamable_http_sdk_call_tool_investigate_domain_creates_runtime_boundary_artifacts(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    request_path = runtime / "requests" / "domain-request.json"
    _write_domain_request(request_path)
    env = {
        **os.environ,
        "PYTHONPATH": "src",
        "HISYS_INSTANCE_ROOT": str(runtime),
        "HISYS_ALLOW_LIVE_ACTIONS": "false",
        "HISYS_MCP_SAMPLING_ENABLED": "false",
    }

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hisys.mcp.server",
            "--streamable-http-local-call-tool-smoke",
            "--http-host",
            "127.0.0.1",
            "--http-port",
            "0",
            "--tool-name",
            "investigate_domain",
            "--tool-args-json",
            json.dumps(
                {
                    "instance_root": str(runtime),
                    "date": "20260509",
                    "request_path": "requests/domain-request.json",
                }
            ),
        ],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["schema_id"] == "hisys.mcp.streamable_http_sdk_call_tool_smoke.v1"
    assert payload["status"] == "ok"
    assert payload["tool_name"] == "investigate_domain"
    assert payload["external_call_made"] is False
    assert payload["mutation_performed"] is False
    assert payload["publication_performed"] is False
    assert payload["hermes_config_mutated"] is False
    assert payload["production_listener_started"] is False
    result = payload["tool_result"]
    assert result["tool_name"] == "investigate_domain"
    assert result["status"] == "ok"
    result_ref = "runtime-boundary/domain-investigation/research/20260509/hisys-tool-result-HISYS-REQ-RESEARCH-GAP-001.json"
    report_ref = "reports/run-summaries/20260509/domain-investigation-report.json"
    assert result_ref in result["artifact_refs"]
    assert report_ref in result["artifact_refs"]
    assert (runtime / result_ref).is_file()
    assert (runtime / report_ref).is_file()
    tool_result = json.loads((runtime / result_ref).read_text(encoding="utf-8"))
    assert tool_result["status"] == "completed"
    assert tool_result["external_call_made"] is False
    assert tool_result["mutation_performed"] is False


def test_mcp_streamable_http_sdk_call_tool_investigate_domain_inline_request_materializes_request_artifact(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    env = {
        **os.environ,
        "PYTHONPATH": "src",
        "HISYS_INSTANCE_ROOT": str(runtime),
        "HISYS_ALLOW_LIVE_ACTIONS": "false",
        "HISYS_MCP_SAMPLING_ENABLED": "false",
    }

    inline_request = {
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

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hisys.mcp.server",
            "--streamable-http-local-call-tool-smoke",
            "--http-host",
            "127.0.0.1",
            "--http-port",
            "0",
            "--tool-name",
            "investigate_domain",
            "--tool-args-json",
            json.dumps(
                {
                    "instance_root": str(runtime),
                    "date": "20260509",
                    "request": inline_request,
                }
            ),
        ],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["schema_id"] == "hisys.mcp.streamable_http_sdk_call_tool_smoke.v1"
    assert payload["status"] == "ok"
    assert payload["tool_name"] == "investigate_domain"
    assert payload["external_call_made"] is False
    assert payload["mutation_performed"] is False
    assert payload["publication_performed"] is False
    assert payload["hermes_config_mutated"] is False
    assert payload["production_listener_started"] is False
    result = payload["tool_result"]
    assert result["tool_name"] == "investigate_domain"
    assert result["status"] == "ok"
    inline_request_ref = "reports/run-summaries/20260509/mcp-investigate-domain-request-HISYS-REQ-INLINE-001.json"
    assert inline_request_ref in result["artifact_refs"]
    assert (runtime / inline_request_ref).is_file()


def test_mcp_streamable_http_sdk_call_tool_altas_search_writes_fixture_search_report(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    env = {
        **os.environ,
        "PYTHONPATH": "src",
        "HISYS_INSTANCE_ROOT": str(runtime),
        "HISYS_ALLOW_LIVE_ACTIONS": "false",
        "HISYS_MCP_SAMPLING_ENABLED": "false",
    }
    env.pop("HISYS_ALLOW_LIVE_SEARCH_SMOKE", None)

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hisys.mcp.server",
            "--streamable-http-local-call-tool-smoke",
            "--http-host",
            "127.0.0.1",
            "--http-port",
            "0",
            "--tool-name",
            "altas_search",
            "--tool-args-json",
            json.dumps(
                {
                    "instance_root": str(runtime),
                    "date": "20260607",
                    "request_id": "HISYS-REQ-MCP-ALTAS-SDK-001",
                    "topic": "self-organizing executable digital twin governance",
                }
            ),
        ],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["schema_id"] == "hisys.mcp.streamable_http_sdk_call_tool_smoke.v1"
    assert payload["status"] == "ok"
    assert payload["tool_name"] == "altas_search"
    assert payload["external_call_made"] is False
    assert payload["mutation_performed"] is False
    assert payload["publication_performed"] is False
    assert payload["hermes_config_mutated"] is False
    assert payload["production_listener_started"] is False
    result = payload["tool_result"]
    assert result["tool_name"] == "altas_search"
    assert "reports/run-summaries/20260607/search-topic-report.json" in result["artifact_refs"]
    report = json.loads((runtime / "reports/run-summaries/20260607/search-topic-report.json").read_text(encoding="utf-8"))
    assert report["status"] == "completed"
    assert report["transport_kind"] == "fixture_injected"
    assert report["external_call_made"] is False


def test_mcp_streamable_http_sdk_call_tool_run_dars_panel_golden_creates_round_report(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    env = {
        **os.environ,
        "PYTHONPATH": "src",
        "HISYS_INSTANCE_ROOT": str(runtime),
        "HISYS_ALLOW_LIVE_ACTIONS": "false",
        "HISYS_MCP_SAMPLING_ENABLED": "false",
    }

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hisys.mcp.server",
            "--streamable-http-local-call-tool-smoke",
            "--http-host",
            "127.0.0.1",
            "--http-port",
            "0",
            "--tool-name",
            "run_dars_panel_golden",
            "--tool-args-json",
            json.dumps(
                {
                    "instance_root": str(runtime),
                    "date": "20260607",
                    "request_id": "HISYS-REQ-MCP-DARS-GOLDEN-SDK-001",
                }
            ),
        ],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["schema_id"] == "hisys.mcp.streamable_http_sdk_call_tool_smoke.v1"
    assert payload["status"] == "ok"
    assert payload["tool_name"] == "run_dars_panel_golden"
    assert payload["external_call_made"] is False
    assert payload["mutation_performed"] is False
    assert payload["publication_performed"] is False
    assert payload["hermes_config_mutated"] is False
    assert payload["production_listener_started"] is False
    result = payload["tool_result"]
    assert result["tool_name"] == "run_dars_panel_golden"
    report_ref = "reports/run-summaries/20260607/dars-panel-round-report.json"
    assert report_ref in result["artifact_refs"]
    report = json.loads((runtime / report_ref).read_text(encoding="utf-8"))
    assert report["advisory_only"] is True
    assert report["requires_human_review"] is True
    assert report["external_call_made"] is False
    assert report["live_external_action_authorized"] is False


def test_mcp_streamable_http_sdk_smoke_rejects_non_loopback_host(tmp_path: Path) -> None:
    env = {**os.environ, "PYTHONPATH": "src", "HISYS_INSTANCE_ROOT": str(tmp_path / "runtime")}

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hisys.mcp.server",
            "--streamable-http-local-smoke",
            "--http-host",
            "0.0.0.0",
            "--http-port",
            "0",
        ],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )

    assert completed.returncode == 2
    assert "loopback" in completed.stderr.lower()
