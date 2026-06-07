"""Local loopback HTTP smoke tests for the Hisys MCP sidecar.

Traceability: HISYS-MCP-HTTP-TRANSPORT-LOCAL-CLIENT-SMOKE-CONTINUATION.
This stays fixture/local only: the server binds to 127.0.0.1 on an ephemeral
port, serves deterministic smoke endpoints, performs one local client request
sequence, and shuts down without live provider/model calls or credentials.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_mcp_server_http_local_client_smoke_lists_tools_without_runtime_mutation(tmp_path: Path) -> None:
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
            "--http-local-smoke",
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
        timeout=10,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["schema_id"] == "hisys.mcp.http_local_smoke.v1"
    assert payload["status"] == "ok"
    assert payload["host"] == "127.0.0.1"
    assert payload["port"] > 0
    assert payload["external_call_made"] is False
    assert payload["mutation_performed"] is False
    assert payload["publication_performed"] is False
    assert payload["live_provider_model_call_made"] is False
    assert payload["credential_lookup_performed"] is False
    assert payload["server_shutdown"] is True
    assert payload["health"]["status"] == "ok"
    assert payload["tools"]["tools"] == [
        "health_status",
        "environment_status",
        "investigate_domain",
        "list_run_artifacts",
        "show_artifact",
        "release_readiness",
    ]
    assert not runtime.exists(), "local HTTP smoke must not create runtime artifacts"


def test_mcp_server_http_local_smoke_rejects_non_loopback_host(tmp_path: Path) -> None:
    env = {**os.environ, "PYTHONPATH": "src", "HISYS_INSTANCE_ROOT": str(tmp_path / "runtime")}

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hisys.mcp.server",
            "--http-local-smoke",
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
