"""Static safety checks for the Hisys MCP Docker/Compose/doc slice.

Traceability: docs/plans/hisys-mcp-docker-service-implementation-tasks.md
Phase 5 local-safe continuation. These checks do not build images, start
containers, mutate Hermes config, or expose a network listener.
"""

from __future__ import annotations

from pathlib import Path

import tomllib
import yaml

ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = ROOT / "Dockerfile.hisys-mcp"
COMPOSE = ROOT / "docker" / "compose.hisys-mcp-smoke.yaml"
PUBLIC_DOC = ROOT / "docs" / "public" / "hisys-mcp-service.md"
PYPROJECT = ROOT / "pyproject.toml"


def test_pyproject_declares_mcp_optional_extra_without_browser_dependency() -> None:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    extras = data["project"]["optional-dependencies"]

    assert "mcp" in extras
    assert any(dep.startswith("mcp") for dep in extras["mcp"])
    assert not any("playwright" in dep.lower() for dep in extras["mcp"])


def test_hisys_mcp_dockerfile_is_lightweight_fail_closed_sidecar() -> None:
    text = DOCKERFILE.read_text(encoding="utf-8")
    lowered = text.lower()

    assert "python:3.11" in lowered or "python:3.12" in lowered
    assert "pip install" in lowered
    assert ".[mcp]" in text
    assert "HISYS_INSTANCE_ROOT=/runtime" in text
    assert "HISYS_MCP_SAMPLING_ENABLED=false" in text
    assert "HISYS_ALLOW_LIVE_ACTIONS=false" in text
    assert "EXPOSE 8765" not in text, "local smoke slice must not expose a listener yet"
    assert "USER hisys" in text
    assert "HEALTHCHECK" in text
    assert "python -m hisys.mcp.server --health" in text
    assert "hisys.mcp.server" in text
    assert "playwright install" not in lowered
    assert ".[browser]" not in lowered
    assert "hermes" not in lowered


def test_compose_smoke_is_one_shot_local_and_does_not_publish_ports() -> None:
    compose = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    service = compose["services"]["hisys-mcp"]

    assert service["build"] == {"context": "..", "dockerfile": "Dockerfile.hisys-mcp"}
    assert service["environment"]["HISYS_INSTANCE_ROOT"] == "/runtime"
    assert service["environment"]["HISYS_MCP_SAMPLING_ENABLED"] == "false"
    assert service["environment"]["HISYS_ALLOW_LIVE_ACTIONS"] == "false"
    assert service["volumes"] == ["../tmp/hisys-runtime:/runtime"]
    assert "ports" not in service
    assert service["command"] == ["python", "-m", "hisys.mcp.server", "--stdio", "--list-tools-json"]


def test_public_docs_include_candidate_config_approval_and_rollback_boundaries() -> None:
    text = PUBLIC_DOC.read_text(encoding="utf-8")

    assert "candidate config" in text.lower()
    assert "do not auto-apply" in text.lower()
    assert "operator approval" in text.lower()
    assert "restart Hermes" in text
    assert "mcp_servers:" in text
    assert "hisys:" in text
    assert 'url: "http://hisys-mcp:8765/mcp"' in text
    assert "timeout: 180" in text
    assert "connect_timeout: 60" in text
    assert "enabled: false" in text
    assert "mcp_servers.hisys" in text
    assert "docker compose -f docker/compose.hisys-mcp-smoke.yaml down" in text
    assert "no live MCP network listener" in text
