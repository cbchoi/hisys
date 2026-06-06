"""Local smoke entry points for the Hisys MCP gateway.

This first slice deliberately exposes deterministic introspection modes only;
it does not open a network listener or require the MCP SDK. A later transport
increment can bind these tool wrappers to stdio/streamable HTTP.
"""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from .config import load_mcp_config
from .tools import list_hisys_mcp_tool_names


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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hisys MCP sidecar gateway")
    parser.add_argument("--health", action="store_true", help="print fail-closed health JSON and exit")
    parser.add_argument("--stdio", action="store_true", help="select stdio transport mode for smoke/introspection")
    parser.add_argument("--list-tools-json", action="store_true", help="print the deterministic initial tool catalog JSON")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.health:
        print(json.dumps(health_payload(), ensure_ascii=False, sort_keys=True))
        return 0
    if args.stdio and args.list_tools_json:
        print(json.dumps(tool_list_payload(), ensure_ascii=False, sort_keys=True))
        return 0
    parser.error("first slice supports --health or --stdio --list-tools-json only")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
