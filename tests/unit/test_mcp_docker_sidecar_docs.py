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
SERVICE_COMPOSE = ROOT / "docker-compose.yml"
DOCKERIGNORE = ROOT / ".dockerignore"
PUBLIC_DOC = ROOT / "docs" / "public" / "hisys-mcp-service.md"
README = ROOT / "README.md"
SETUP_SCRIPT = ROOT / "scripts" / "setup_hisys_mcp_docker.sh"
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
    assert "HISYS_MCP_HOST=0.0.0.0" in text
    assert "HISYS_MCP_PORT=8765" in text
    assert "EXPOSE 8765" in text
    assert "USER hisys" in text
    assert "HEALTHCHECK" in text
    assert "socket.create_connection" in text
    assert "--production-listener" in text
    assert "--mcp-path" in text
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


def test_service_compose_runs_long_lived_loopback_published_mcp_listener() -> None:
    compose = yaml.safe_load(SERVICE_COMPOSE.read_text(encoding="utf-8"))
    service = compose["services"]["hisys-mcp"]

    assert service["build"] == {"context": ".", "dockerfile": "Dockerfile.hisys-mcp"}
    assert service["image"] == "hisys-mcp:local"
    assert service["restart"] == "unless-stopped"
    assert service["environment"]["HISYS_INSTANCE_ROOT"] == "/runtime"
    assert service["environment"]["HISYS_MCP_SAMPLING_ENABLED"] == "false"
    assert service["environment"]["HISYS_ALLOW_LIVE_ACTIONS"] == "false"
    assert service["environment"]["HISYS_MCP_ALLOW_NON_LOOPBACK_BIND"] == "true"
    assert service["environment"]["HISYS_MCP_HOST"] == "0.0.0.0"
    assert service["environment"]["HISYS_MCP_PORT"] == "8765"
    assert service["environment"]["HISYS_MCP_PATH"] == "/mcp"
    assert service["ports"] == ["127.0.0.1:19613:8765"]
    assert service["volumes"] == ["../../runtime/hisys-mcp-instance:/runtime"]
    assert "healthcheck" in service


def test_dockerignore_excludes_runtime_and_development_artifacts() -> None:
    ignored = set(DOCKERIGNORE.read_text(encoding="utf-8").splitlines())

    assert ".git" in ignored
    assert ".codegraph" in ignored
    assert "tmp" in ignored
    assert "reports" in ignored
    assert "runtime-boundary" in ignored


def test_setup_script_wraps_docker_compose_without_public_binding() -> None:
    text = SETUP_SCRIPT.read_text(encoding="utf-8")

    assert text.startswith("#!/usr/bin/env bash")
    assert "set -euo pipefail" in text
    assert "docker compose" in text
    assert "up -d --build" in text
    assert "hermes mcp test hisys" in text
    assert "http://127.0.0.1:19613/mcp" in text
    assert "runtime/hisys-mcp-instance" in text
    assert "--stop-user-service" in text
    assert "systemctl --user stop hisys-mcp.service" in text
    assert "0.0.0.0:19613" not in text


def test_public_docs_include_candidate_config_approval_and_rollback_boundaries() -> None:
    text = PUBLIC_DOC.read_text(encoding="utf-8")

    assert "candidate config" in text.lower()
    assert "do not auto-apply" in text.lower()
    assert "operator approval" in text.lower()
    assert "restart Hermes" in text
    assert "docker compose up -d --build hisys-mcp" in text
    assert "127.0.0.1:19613:8765" in text
    assert "http://127.0.0.1:19613/mcp" in text
    assert "mcp_servers:" in text
    assert "hisys:" in text
    assert 'url: "http://hisys-mcp:8765/mcp"' in text
    assert "timeout: 180" in text
    assert "connect_timeout: 60" in text
    assert "enabled: false" in text
    assert "mcp_servers.hisys" in text
    assert "docker compose -f docker/compose.hisys-mcp-smoke.yaml down" in text
    assert "has no live MCP network listener" in text
    assert "scripts/setup_hisys_mcp_docker.sh up" in text
    assert "scripts/setup_hisys_mcp_docker.sh test" in text
    assert "--stop-user-service" in text


def test_readme_has_operator_quickstart_for_docker_mcp_service() -> None:
    text = README.read_text(encoding="utf-8")

    assert "Quick start: local Hisys MCP Docker service" in text
    assert "scripts/setup_hisys_mcp_docker.sh up" in text
    assert "scripts/setup_hisys_mcp_docker.sh status" in text
    assert "scripts/setup_hisys_mcp_docker.sh test" in text
    assert "http://127.0.0.1:19613/mcp" in text
    assert "../../runtime/hisys-mcp-instance -> /runtime" in text
    assert "127.0.0.1:19613:8765" in text
