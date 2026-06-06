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
from pathlib import Path


EXPECTED_TOOLS = [
    "health_status",
    "environment_status",
    "investigate_domain",
    "list_run_artifacts",
    "show_artifact",
    "release_readiness",
]


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
