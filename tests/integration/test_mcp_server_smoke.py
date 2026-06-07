"""Hisys MCP server smoke tests.

Traceability: docs/plans/hisys-mcp-docker-service-implementation-tasks.md
Tasks 4.1-4.2. These tests stay local/fixture-only and do not require Docker or network.
"""

from __future__ import annotations

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
