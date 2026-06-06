"""Local smoke entry points for the Hisys MCP gateway.

The default entry points expose deterministic introspection only. The local HTTP
smoke mode is an ephemeral loopback harness: it binds to 127.0.0.1/localhost,
serves deterministic health/tool-list endpoints, performs a local client request
sequence, and shuts down. It is not a production MCP listener and does not cross
live provider, credential, mutation, publication, or external-action boundaries.
"""

from __future__ import annotations

import argparse
import json
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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hisys MCP sidecar gateway")
    parser.add_argument("--health", action="store_true", help="print fail-closed health JSON and exit")
    parser.add_argument("--stdio", action="store_true", help="select stdio transport mode for smoke/introspection")
    parser.add_argument("--list-tools-json", action="store_true", help="print the deterministic initial tool catalog JSON")
    parser.add_argument("--http-local-smoke", action="store_true", help="run an ephemeral loopback HTTP client/server smoke and exit")
    parser.add_argument("--http-host", default="127.0.0.1", help="loopback host for --http-local-smoke")
    parser.add_argument("--http-port", type=int, default=0, help="loopback port for --http-local-smoke; 0 selects an ephemeral port")
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
    parser.error("first slices support --health, --stdio --list-tools-json, or --http-local-smoke only")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
