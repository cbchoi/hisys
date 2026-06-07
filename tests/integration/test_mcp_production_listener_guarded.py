"""Guarded production MCP listener tests.

Traceability: HISYS-MCP-PRODUCTION-LISTENER-GUARDED-CLI-PREFLIGHT.
This lane keeps the production listener bounded to explicit CLI opt-in plus
loopback-by-default safety. The listener may bind a non-loopback host only when
an explicit environment approval variable is present. The harness never
mutates the Hermes config, never calls live providers/models, never inspects
credentials, never publishes, and never performs external actions; preflight
returns deterministic JSON so the tests never hang on a long-lived listener.
"""

from __future__ import annotations

import asyncio
import json
import os
import queue
import signal
import subprocess
import sys
import threading
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

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

NON_LOOPBACK_APPROVAL_ENV = "HISYS_MCP_ALLOW_NON_LOOPBACK_BIND"


def _base_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k != NON_LOOPBACK_APPROVAL_ENV}
    env["PYTHONPATH"] = "src"
    if extra:
        env.update(extra)
    return env


def _spawn_listener(args: list[str], env: dict[str, str]) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [sys.executable, "-m", "hisys.mcp.server", *args],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )


def _read_first_json_line(proc: subprocess.Popen[str], timeout: float = 20.0) -> str:
    result_q: queue.Queue[tuple[str, object]] = queue.Queue()

    def _reader() -> None:
        try:
            line = proc.stdout.readline() if proc.stdout else ""
            result_q.put(("ok", line))
        except Exception as exc:  # pragma: no cover - defensive
            result_q.put(("err", exc))

    reader = threading.Thread(target=_reader, daemon=True)
    reader.start()
    try:
        kind, value = result_q.get(timeout=timeout)
    except queue.Empty as exc:
        raise TimeoutError("production listener did not print a ready packet in time") from exc
    if kind == "err":
        raise value  # type: ignore[misc]
    return str(value).strip()


def _terminate(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is None:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


async def _list_tools_via_sdk(url: str) -> list[str]:
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    async with streamable_http_client(url) as (read_stream, write_stream, _get_session_id):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.list_tools()
    return [tool.name for tool in result.tools]


def test_production_listener_requires_explicit_cli_flag(tmp_path: Path) -> None:
    """Without --production-listener, the gateway must NOT start a long-lived listener."""

    runtime = tmp_path / "runtime"
    env = _base_env({"HISYS_INSTANCE_ROOT": str(runtime)})

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hisys.mcp.server",
            "--http-host",
            "127.0.0.1",
            "--http-port",
            "0",
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )

    assert completed.returncode == 2, completed.stdout
    assert not runtime.exists(), "fail-closed default must not create runtime artifacts"


def test_production_listener_preflight_returns_deterministic_loopback_payload(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    env = _base_env({"HISYS_INSTANCE_ROOT": str(runtime)})

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hisys.mcp.server",
            "--production-listener-preflight",
            "--http-host",
            "127.0.0.1",
            "--http-port",
            "8765",
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["schema_id"] == "hisys.mcp.production_listener_preflight.v1"
    assert payload["status"] == "ok"
    assert payload["host"] == "127.0.0.1"
    assert payload["port"] == 8765
    assert payload["path"] == "/mcp"
    assert payload["loopback_only"] is True
    assert payload["non_loopback_bind_requested"] is False
    assert payload["non_loopback_approval_present"] is False
    assert payload["production_listener_started"] is False
    assert payload["hermes_config_mutated"] is False
    assert payload["sampling_enabled"] is False
    assert payload["external_call_made"] is False
    assert payload["mutation_performed"] is False
    assert payload["publication_performed"] is False
    assert payload["live_provider_model_call_made"] is False
    assert payload["credential_lookup_performed"] is False
    assert payload["human_approval_required"] is True
    assert not runtime.exists(), "preflight must not create runtime artifacts"


def test_production_listener_preflight_blocks_non_loopback_without_approval(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    env = _base_env({"HISYS_INSTANCE_ROOT": str(runtime)})

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hisys.mcp.server",
            "--production-listener-preflight",
            "--http-host",
            "0.0.0.0",
            "--http-port",
            "8765",
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["schema_id"] == "hisys.mcp.production_listener_preflight.v1"
    assert payload["status"] == "blocked"
    assert payload["loopback_only"] is False
    assert payload["non_loopback_bind_requested"] is True
    assert payload["non_loopback_approval_present"] is False
    assert payload["production_listener_started"] is False
    assert payload["hermes_config_mutated"] is False
    reason = str(payload.get("reason", "")).lower()
    assert "approval" in reason or "loopback" in reason
    assert not runtime.exists()


def test_production_listener_preflight_records_explicit_non_loopback_approval(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    env = _base_env(
        {
            "HISYS_INSTANCE_ROOT": str(runtime),
            NON_LOOPBACK_APPROVAL_ENV: "true",
        }
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hisys.mcp.server",
            "--production-listener-preflight",
            "--http-host",
            "0.0.0.0",
            "--http-port",
            "8765",
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["schema_id"] == "hisys.mcp.production_listener_preflight.v1"
    assert payload["status"] == "ok"
    assert payload["host"] == "0.0.0.0"
    assert payload["loopback_only"] is False
    assert payload["non_loopback_bind_requested"] is True
    assert payload["non_loopback_approval_present"] is True
    assert payload["production_listener_started"] is False
    assert payload["hermes_config_mutated"] is False
    assert not runtime.exists()


def test_production_listener_rejects_non_loopback_host_without_approval(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    env = _base_env({"HISYS_INSTANCE_ROOT": str(runtime)})

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hisys.mcp.server",
            "--production-listener",
            "--http-host",
            "0.0.0.0",
            "--http-port",
            "8765",
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )

    assert completed.returncode == 2
    combined = (completed.stderr + completed.stdout).lower()
    assert "approval" in combined or "loopback" in combined
    assert not runtime.exists(), "rejected production listener must not create runtime artifacts"


def test_production_listener_long_lived_lists_tools_via_sdk_then_terminates(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    env = _base_env(
        {
            "HISYS_INSTANCE_ROOT": str(runtime),
            "HISYS_ALLOW_LIVE_ACTIONS": "false",
            "HISYS_MCP_SAMPLING_ENABLED": "false",
        }
    )

    proc = _spawn_listener(
        [
            "--production-listener",
            "--http-host",
            "127.0.0.1",
            "--http-port",
            "0",
        ],
        env=env,
    )
    try:
        ready_line = _read_first_json_line(proc, timeout=25.0)
        payload = json.loads(ready_line)
        assert payload["schema_id"] == "hisys.mcp.production_listener_ready.v1"
        assert payload["status"] == "ready"
        assert payload["transport_kind"] == "streamable-http"
        assert payload["host"] == "127.0.0.1"
        assert payload["port"] > 0
        assert payload["path"] == "/mcp"
        assert payload["production_listener_started"] is True
        assert payload["non_loopback_approval_present"] is False
        assert payload["hermes_config_mutated"] is False
        assert payload["sampling_enabled"] is False
        assert payload["external_call_made"] is False
        assert payload["mutation_performed"] is False
        assert payload["publication_performed"] is False
        assert payload["live_provider_model_call_made"] is False
        assert payload["credential_lookup_performed"] is False
        assert payload["human_approval_required"] is True

        url = f"http://{payload['host']}:{payload['port']}{payload['path']}"
        tools = asyncio.run(_list_tools_via_sdk(url))
        assert tools == EXPECTED_TOOLS
    finally:
        _terminate(proc)

    assert proc.returncode == 0, proc.stderr.read() if proc.stderr else ""
    assert not runtime.exists(), "production listener must not create runtime artifacts in the loopback smoke"
