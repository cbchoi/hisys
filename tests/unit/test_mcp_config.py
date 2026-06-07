"""MCP Docker service configuration tests.

Traceability: docs/plans/hisys-mcp-docker-service-implementation-tasks.md
Task 1.3 and Claude review required revisions for safe runtime defaults.
"""

from __future__ import annotations

import importlib
from pathlib import Path


def _config_module():
    return importlib.import_module("hisys.mcp.config")


def test_mcp_config_defaults_are_safe_and_do_not_create_runtime_dirs(monkeypatch, tmp_path: Path) -> None:
    config_mod = _config_module()
    runtime = tmp_path / "runtime-not-created"
    env_config = tmp_path / "env.yaml"

    monkeypatch.delenv("HISYS_INSTANCE_ROOT", raising=False)
    monkeypatch.delenv("HISYS_ENVIRONMENT_CONFIG", raising=False)
    monkeypatch.delenv("HISYS_STORE_CONFIG", raising=False)
    monkeypatch.delenv("HISYS_ALLOW_LIVE_ACTIONS", raising=False)
    monkeypatch.delenv("HISYS_MCP_SAMPLING_ENABLED", raising=False)
    monkeypatch.delenv("HISYS_MCP_SUBPROCESS_TIMEOUT_SECONDS", raising=False)

    # The loader accepts explicit env for tests so it can be exercised without mutating os.environ.
    cfg = config_mod.load_mcp_config(env={"HISYS_INSTANCE_ROOT": str(runtime), "HISYS_ENVIRONMENT_CONFIG": str(env_config)})

    assert cfg.instance_root == runtime
    assert cfg.environment_config == env_config
    assert cfg.store_config is None
    assert cfg.allow_live_actions is False
    assert cfg.sampling_enabled is False
    assert cfg.subprocess_timeout_seconds == 180
    assert not runtime.exists()
    assert not env_config.exists()


def test_mcp_config_boolean_flags_enable_only_on_explicit_true(tmp_path: Path) -> None:
    config_mod = _config_module()

    cfg = config_mod.load_mcp_config(
        env={
            "HISYS_INSTANCE_ROOT": str(tmp_path / "runtime"),
            "HISYS_ALLOW_LIVE_ACTIONS": "1",
            "HISYS_MCP_SAMPLING_ENABLED": "true",
            "HISYS_MCP_SUBPROCESS_TIMEOUT_SECONDS": "42",
        }
    )

    assert cfg.allow_live_actions is True
    assert cfg.sampling_enabled is True
    assert cfg.subprocess_timeout_seconds == 42


def test_mcp_config_rejects_invalid_timeout_without_creating_dirs(tmp_path: Path) -> None:
    config_mod = _config_module()
    runtime = tmp_path / "runtime"

    try:
        config_mod.load_mcp_config(
            env={
                "HISYS_INSTANCE_ROOT": str(runtime),
                "HISYS_MCP_SUBPROCESS_TIMEOUT_SECONDS": "not-an-int",
            }
        )
    except ValueError as exc:
        assert "HISYS_MCP_SUBPROCESS_TIMEOUT_SECONDS" in str(exc)
    else:
        raise AssertionError("invalid MCP timeout must fail closed")

    assert not runtime.exists()
