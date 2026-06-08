"""Safe runtime configuration loader for the Hisys MCP gateway."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

from pydantic import BaseModel

_TRUE_VALUES = {"1", "true", "yes", "on"}


class McpConfig(BaseModel):
    instance_root: Path
    environment_config: Path | None = None
    store_config: Path | None = None
    allow_live_actions: bool = False
    sampling_enabled: bool = False
    subprocess_timeout_seconds: int = 180
    expose_future_tools: bool = False
    expose_live_tools: bool = False


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in _TRUE_VALUES


def _optional_path(value: str | None) -> Path | None:
    return Path(value).expanduser() if value else None


def load_mcp_config(env: Mapping[str, str] | None = None) -> McpConfig:
    """Load MCP config from environment-like values without filesystem writes."""

    values = dict(os.environ if env is None else env)
    timeout_raw = values.get("HISYS_MCP_SUBPROCESS_TIMEOUT_SECONDS", "180")
    try:
        timeout = int(timeout_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("HISYS_MCP_SUBPROCESS_TIMEOUT_SECONDS must be an integer") from exc
    if timeout <= 0:
        raise ValueError("HISYS_MCP_SUBPROCESS_TIMEOUT_SECONDS must be positive")

    return McpConfig(
        instance_root=Path(values.get("HISYS_INSTANCE_ROOT", "/tmp/hisys-mcp-instance")).expanduser(),
        environment_config=_optional_path(values.get("HISYS_ENVIRONMENT_CONFIG")),
        store_config=_optional_path(values.get("HISYS_STORE_CONFIG")),
        allow_live_actions=_truthy(values.get("HISYS_ALLOW_LIVE_ACTIONS")),
        sampling_enabled=_truthy(values.get("HISYS_MCP_SAMPLING_ENABLED")),
        subprocess_timeout_seconds=timeout,
        expose_future_tools=_truthy(values.get("HISYS_MCP_EXPOSE_FUTURE_TOOLS")),
        expose_live_tools=_truthy(values.get("HISYS_MCP_EXPOSE_LIVE_TOOLS")),
    )


__all__ = ["McpConfig", "load_mcp_config"]
