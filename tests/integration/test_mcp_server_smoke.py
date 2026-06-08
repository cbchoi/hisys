"""Hisys MCP server smoke tests.

Traceability: docs/plans/hisys-mcp-docker-service-implementation-tasks.md
Tasks 4.1-4.2. These tests stay local/fixture-only and do not require Docker or network.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path


def test_mcp_server_health_check_starts_without_creating_runtime_artifacts(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    env = {**os.environ, "PYTHONPATH": "src", "HISYS_INSTANCE_ROOT": str(runtime), "HISYS_ALLOW_LIVE_ACTIONS": "false"}

    completed = subprocess.run(
        [sys.executable, "-m", "hisys.mcp.server", "--health"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["status"] == "ok"
    assert payload["sampling_enabled"] is False
    assert not runtime.exists(), "server health check must not create runtime artifacts"


def test_mcp_server_stdio_lists_initial_tool_names(tmp_path: Path) -> None:
    # The first transport slice exposes a deterministic local introspection mode so
    # stdio/server wiring can be smoke-tested before Docker HTTP smoke is added.
    env = {**os.environ, "PYTHONPATH": "src", "HISYS_INSTANCE_ROOT": str(tmp_path / "runtime")}

    completed = subprocess.run(
        [sys.executable, "-m", "hisys.mcp.server", "--stdio", "--list-tools-json"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["tools"] == [
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
    assert payload["future_tools_exposed"] is False


def test_mcp_server_stdio_list_tools_excludes_live_tools_by_default(tmp_path: Path) -> None:
    env = {**os.environ, "PYTHONPATH": "src", "HISYS_INSTANCE_ROOT": str(tmp_path / "runtime")}
    env.pop("HISYS_MCP_EXPOSE_LIVE_TOOLS", None)

    completed = subprocess.run(
        [sys.executable, "-m", "hisys.mcp.server", "--stdio", "--list-tools-json"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    tool_names = set(payload["tools"])
    for live_name in ("altas_search_live", "run_dars_panel_live", "judge_advisory_live"):
        assert live_name not in tool_names
    assert payload.get("live_tools_exposed") is False


def test_mcp_server_stdio_list_tools_exposes_live_tools_when_env_set(tmp_path: Path) -> None:
    env = {
        **os.environ,
        "PYTHONPATH": "src",
        "HISYS_INSTANCE_ROOT": str(tmp_path / "runtime"),
        "HISYS_MCP_EXPOSE_LIVE_TOOLS": "1",
    }

    completed = subprocess.run(
        [sys.executable, "-m", "hisys.mcp.server", "--stdio", "--list-tools-json"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    tool_names = payload["tools"]
    for live_name in ("altas_search_live", "run_dars_panel_live", "judge_advisory_live"):
        assert live_name in tool_names
    assert payload.get("live_tools_exposed") is True


def test_build_streamable_http_mcp_server_default_excludes_live_tools() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from hisys.mcp.server import build_streamable_http_mcp_server

    server = build_streamable_http_mcp_server(host="127.0.0.1", port=0)
    tools = asyncio.run(server.list_tools())
    names = {tool.name for tool in tools}
    for live_name in ("altas_search_live", "run_dars_panel_live", "judge_advisory_live"):
        assert live_name not in names


def test_build_streamable_http_mcp_server_exposes_live_tools_when_requested() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from hisys.mcp.server import build_streamable_http_mcp_server

    server = build_streamable_http_mcp_server(host="127.0.0.1", port=0, expose_live_tools=True)
    tools = asyncio.run(server.list_tools())
    names = {tool.name for tool in tools}
    assert {"altas_search_live", "run_dars_panel_live", "judge_advisory_live"} <= names


def test_streamable_http_live_tool_fails_closed_without_provider_injection() -> None:
    """Even when registered on the server, a live tool must fail closed because
    the server-side wiring does not perform credential lookup or provider
    invocation: it only routes to the live-adapter contract with no injected
    transport."""

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from hisys.mcp.server import build_streamable_http_mcp_server

    server = build_streamable_http_mcp_server(host="127.0.0.1", port=0, expose_live_tools=True)
    result = asyncio.run(
        server.call_tool(
            "altas_search_live",
            {
                "instance_root": "/tmp/hisys-mcp-instance-live-smoke",
                "date": "20260608",
                "request_id": "HISYS-REQ-MCP-LIVE-SMOKE-001",
                "topic": "live tool smoke",
            },
        )
    )
    # FastMCP call_tool returns either a tuple (content, structuredContent) or
    # the structured content directly depending on version. Normalize to dict.
    if isinstance(result, tuple) and len(result) >= 2 and isinstance(result[1], dict):
        envelope = result[1]
    elif isinstance(result, dict):
        envelope = result
    else:
        # Fall back: inspect any structuredContent attribute or content payload.
        envelope = getattr(result, "structuredContent", None) or {}
        if not envelope and isinstance(result, list) and result:
            first = result[0]
            text = getattr(first, "text", None)
            if isinstance(text, str):
                try:
                    envelope = json.loads(text)
                except json.JSONDecodeError:
                    envelope = {}
    assert envelope.get("status") == "blocked"
    assert envelope.get("tool_name") == "altas_search_live"
    assert envelope.get("external_call_made") is False
    assert envelope.get("mutation_performed") is False
    assert envelope.get("publication_or_live_action_approved") is False
