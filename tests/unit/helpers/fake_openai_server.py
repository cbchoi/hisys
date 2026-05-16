"""Loopback fake OpenAI-compatible HTTP server for DARS adapter tests.

The fake server binds only to ``127.0.0.1`` on an ephemeral port and accepts a
single ``POST /v1/chat/completions`` request shape. Each context manager
instance exposes the request that the adapter sent plus a ``contacted`` flag,
which allows tests to assert that pre-HTTP rejection paths (remote endpoint,
missing approval ref, scheme rejection) never reach the network.

The harness is intentionally minimal: it does not implement OpenAI semantics
beyond echoing a fixed response shape. Failure modes (``non_2xx``,
``malformed_json``, ``missing_content``, ``timeout``) are selected by the
``mode`` argument so tests can pin the exact failure class under test.

Traceability: Local DARS / ByeSys Provenance plan Milestone 2; Hisys Ralph M9.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Literal

FakeServerMode = Literal[
    "success",
    "non_2xx",
    "malformed_json",
    "missing_content",
    "timeout",
]


@dataclass
class FakeServerRequest:
    path: str
    method: str
    headers: dict[str, str]
    body: str

    @property
    def json(self) -> dict[str, Any]:
        return json.loads(self.body) if self.body else {}


@dataclass
class FakeOpenAIServer:
    """Threaded loopback HTTP server emulating an OpenAI chat completion endpoint."""

    mode: FakeServerMode = "success"
    response_content: str = "fake local DARS critique with provenance sections"
    non_2xx_status: int = 500
    timeout_delay_seconds: float = 1.0
    requests: list[FakeServerRequest] = field(default_factory=list)
    contacted: bool = False
    _server: ThreadingHTTPServer | None = field(default=None, init=False, repr=False)
    _thread: threading.Thread | None = field(default=None, init=False, repr=False)

    @property
    def endpoint(self) -> str:
        if self._server is None:
            raise RuntimeError("FakeOpenAIServer is not started; use it as a context manager")
        host, port = self._server.server_address[0], self._server.server_address[1]
        return f"http://{host}:{port}/v1/chat/completions"

    @property
    def host(self) -> str:
        if self._server is None:
            raise RuntimeError("FakeOpenAIServer is not started; use it as a context manager")
        return self._server.server_address[0]

    @property
    def port(self) -> int:
        if self._server is None:
            raise RuntimeError("FakeOpenAIServer is not started; use it as a context manager")
        return self._server.server_address[1]

    def __enter__(self) -> "FakeOpenAIServer":
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802 — http.server contract
                outer.contacted = True
                length = int(self.headers.get("content-length", "0") or "0")
                raw = self.rfile.read(length).decode("utf-8") if length else ""
                outer.requests.append(
                    FakeServerRequest(
                        path=self.path,
                        method="POST",
                        headers={key.lower(): value for key, value in self.headers.items()},
                        body=raw,
                    )
                )
                if outer.mode == "timeout":
                    time.sleep(outer.timeout_delay_seconds)
                    return  # never reply
                if outer.mode == "non_2xx":
                    payload = json.dumps({"error": "server_error"}).encode("utf-8")
                    self.send_response(outer.non_2xx_status)
                    self.send_header("content-type", "application/json")
                    self.send_header("content-length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                    return
                if outer.mode == "malformed_json":
                    payload = b"<<<not-json>>>"
                    self.send_response(200)
                    self.send_header("content-type", "application/json")
                    self.send_header("content-length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                    return
                if outer.mode == "missing_content":
                    payload = json.dumps({"choices": [{"message": {}}]}).encode("utf-8")
                    self.send_response(200)
                    self.send_header("content-type", "application/json")
                    self.send_header("content-length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                    return
                payload = json.dumps(
                    {"choices": [{"message": {"content": outer.response_content}}]}
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, format: str, *args: Any) -> None:  # noqa: D401, A002 — silence
                return

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self._server = None
        self._thread = None


__all__ = ["FakeOpenAIServer", "FakeServerMode", "FakeServerRequest"]
