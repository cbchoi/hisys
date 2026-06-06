"""Local smoke entry points for the Hisys MCP gateway.

The default entry points expose deterministic introspection only. The local HTTP
smoke mode is an ephemeral loopback harness: it binds to 127.0.0.1/localhost,
serves deterministic health/tool-list endpoints, performs a local client request
sequence, and shuts down. It is not a production MCP listener and does not cross
live provider, credential, mutation, publication, or external-action boundaries.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import socket
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Sequence

from .config import load_mcp_config
from .tools import list_hisys_mcp_tool_names

LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


def health_payload() -> dict[str, object]:
    cfg = load_mcp_config()
    return {
        "status": "ok",
        "sampling_enabled": cfg.sampling_enabled,
        "allow_live_actions": cfg.allow_live_actions,
        "future_tools_exposed": cfg.expose_future_tools,
    }


def tool_list_payload() -> dict[str, object]:
    cfg = load_mcp_config()
    return {
        "tools": list_hisys_mcp_tool_names(expose_future_tools=cfg.expose_future_tools),
        "future_tools_exposed": cfg.expose_future_tools,
        "sampling_enabled": cfg.sampling_enabled,
    }


def _json_http_handler() -> type[BaseHTTPRequestHandler]:
    class HisysMcpSmokeHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            if self.path == "/health":
                self._write_json(health_payload())
                return
            if self.path == "/tools":
                self._write_json(tool_list_payload())
                return
            self.send_error(404, "unknown local MCP smoke endpoint")

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib signature
            return

        def _write_json(self, payload: dict[str, object]) -> None:
            raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    return HisysMcpSmokeHandler


def _read_local_json(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url, timeout=5) as response:  # noqa: S310 - loopback smoke URL only
        payload = json.loads(response.read().decode("utf-8"))
    return payload if isinstance(payload, dict) else {"value": payload}


def http_local_smoke_payload(*, host: str, port: int) -> dict[str, object]:
    if host not in LOOPBACK_HOSTS:
        raise ValueError("HTTP local smoke requires a loopback host")

    server = ThreadingHTTPServer((host, port), _json_http_handler())
    actual_host, actual_port = server.server_address[:2]
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    thread.start()
    payload: dict[str, object] = {"server_shutdown": False}
    try:
        base_url = f"http://{actual_host}:{actual_port}"
        health = _read_local_json(f"{base_url}/health")
        tools = _read_local_json(f"{base_url}/tools")
        payload.update(
            {
                "schema_id": "hisys.mcp.http_local_smoke.v1",
                "status": "ok" if health.get("status") == "ok" and isinstance(tools.get("tools"), list) else "error",
                "host": actual_host,
                "port": actual_port,
                "health": health,
                "tools": tools,
                "external_call_made": False,
                "mutation_performed": False,
                "publication_performed": False,
                "live_provider_model_call_made": False,
                "credential_lookup_performed": False,
            }
        )
        return payload
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        payload["server_shutdown"] = True


def run_http_local_smoke(*, host: str, port: int) -> dict[str, object]:
    return http_local_smoke_payload(host=host, port=port)


def _reserve_loopback_port(host: str) -> int:
    with socket.socket(socket.AF_INET6 if host == "::1" else socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def build_streamable_http_mcp_server(*, host: str, port: int, path: str = "/mcp") -> Any:
    """Build a FastMCP server for local streamable HTTP smoke only."""
    from mcp.server.fastmcp import FastMCP

    config = load_mcp_config()
    mcp_server = FastMCP(
        "hisys-mcp",
        host=host,
        port=port,
        streamable_http_path=path,
        json_response=True,
        stateless_http=True,
    )

    @mcp_server.tool(name="health_status")
    def health_status() -> dict[str, object]:
        return health_payload()

    @mcp_server.tool(name="environment_status")
    def environment_status() -> dict[str, object]:
        return {"status": "not_run_from_sdk_local_smoke", "environment_config": str(config.environment_config)}

    @mcp_server.tool(name="investigate_domain")
    def investigate_domain() -> dict[str, object]:
        return {"status": "needs_more_evidence", "live_action_rejected_by_default": True}

    @mcp_server.tool(name="list_run_artifacts")
    def list_run_artifacts() -> dict[str, object]:
        return {"status": "not_run_from_sdk_local_smoke", "artifacts": []}

    @mcp_server.tool(name="show_artifact")
    def show_artifact() -> dict[str, object]:
        return {"status": "not_run_from_sdk_local_smoke", "artifact": None}

    @mcp_server.tool(name="release_readiness")
    def release_readiness() -> dict[str, object]:
        return {"status": "needs_more_evidence", "requires_human_review": True}

    return mcp_server


async def _list_streamable_http_tools(url: str) -> list[str]:
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    async with streamablehttp_client(url) as (read_stream, write_stream, _get_session_id):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.list_tools()
    return [tool.name for tool in result.tools]


def streamable_http_sdk_local_smoke_payload(*, host: str, port: int, path: str = "/mcp") -> dict[str, object]:
    if host not in LOOPBACK_HOSTS:
        raise ValueError("streamable HTTP SDK local smoke requires a loopback host")

    actual_port = _reserve_loopback_port(host) if port == 0 else port
    mcp_server = build_streamable_http_mcp_server(host=host, port=actual_port, path=path)

    import uvicorn

    uvicorn_server = uvicorn.Server(
        uvicorn.Config(
            mcp_server.streamable_http_app(),
            host=host,
            port=actual_port,
            log_level="warning",
            access_log=False,
        )
    )
    thread = threading.Thread(target=uvicorn_server.run, daemon=True)
    thread.start()
    payload: dict[str, object] = {"server_shutdown": False}
    try:
        url_host = "[::1]" if host == "::1" else host
        url = f"http://{url_host}:{actual_port}{path}"
        tools: list[str] | None = None
        last_error: Exception | None = None
        for _ in range(40):
            if uvicorn_server.started:
                try:
                    tools = asyncio.run(_list_streamable_http_tools(url))
                    break
                except Exception as exc:  # pragma: no cover - retry path is timing-sensitive
                    last_error = exc
            threading.Event().wait(0.05)
        if tools is None:
            raise RuntimeError(f"streamable HTTP SDK local client could not list tools: {last_error}")
        config = load_mcp_config()
        payload.update(
            {
                "schema_id": "hisys.mcp.streamable_http_sdk_local_smoke.v1",
                "status": "ok" if tools == list_hisys_mcp_tool_names(expose_future_tools=False) else "error",
                "transport_kind": "streamable-http",
                "host": host,
                "port": actual_port,
                "path": path,
                "tools": tools,
                "external_call_made": False,
                "mutation_performed": False,
                "publication_performed": False,
                "live_provider_model_call_made": False,
                "credential_lookup_performed": False,
                "hermes_config_mutated": False,
                "production_listener_started": False,
                "sampling_enabled": config.sampling_enabled,
            }
        )
        return payload
    finally:
        uvicorn_server.should_exit = True
        thread.join(timeout=5)
        payload["server_shutdown"] = not thread.is_alive()


def run_streamable_http_sdk_local_smoke(*, host: str, port: int, path: str = "/mcp") -> dict[str, object]:
    return streamable_http_sdk_local_smoke_payload(host=host, port=port, path=path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hisys MCP sidecar gateway")
    parser.add_argument("--health", action="store_true", help="print fail-closed health JSON and exit")
    parser.add_argument("--stdio", action="store_true", help="select stdio transport mode for smoke/introspection")
    parser.add_argument("--list-tools-json", action="store_true", help="print the deterministic initial tool catalog JSON")
    parser.add_argument("--http-local-smoke", action="store_true", help="run an ephemeral loopback HTTP client/server smoke and exit")
    parser.add_argument(
        "--streamable-http-local-smoke",
        action="store_true",
        help="run an ephemeral loopback MCP SDK streamable HTTP client/server smoke and exit",
    )
    parser.add_argument("--http-host", default="127.0.0.1", help="loopback host for --http-local-smoke")
    parser.add_argument("--http-port", type=int, default=0, help="loopback port for --http-local-smoke; 0 selects an ephemeral port")
    parser.add_argument("--mcp-path", default="/mcp", help="streamable HTTP MCP path for local SDK smoke")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.health:
        print(json.dumps(health_payload(), ensure_ascii=False, sort_keys=True))
        return 0
    if args.stdio and args.list_tools_json:
        print(json.dumps(tool_list_payload(), ensure_ascii=False, sort_keys=True))
        return 0
    if args.http_local_smoke:
        try:
            payload = run_http_local_smoke(host=args.http_host, port=args.http_port)
        except ValueError as exc:
            parser.error(str(exc))
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0
    if args.streamable_http_local_smoke:
        try:
            payload = run_streamable_http_sdk_local_smoke(host=args.http_host, port=args.http_port, path=args.mcp_path)
        except ValueError as exc:
            parser.error(str(exc))
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0
    parser.error(
        "first slices support --health, --stdio --list-tools-json, --http-local-smoke, "
        "or --streamable-http-local-smoke only"
    )
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
