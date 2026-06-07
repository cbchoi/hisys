#!/usr/bin/env bash
# Manage the local Hisys MCP Docker Compose sidecar.
#
# This script keeps the MCP service local by using the checked-in compose file,
# which publishes only 127.0.0.1:19613 on the host.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RUNTIME_ROOT="$(cd "${REPO_ROOT}/../.." && pwd)/runtime/hisys-mcp-instance"
SERVICE_NAME="hisys-mcp"
MCP_URL="http://127.0.0.1:19613/mcp"

usage() {
  cat <<'USAGE'
Usage: scripts/setup_hisys_mcp_docker.sh <command> [--stop-user-service]

Commands:
  up        Create runtime directories, build, and start the Docker service.
  restart   Rebuild and restart the Docker service.
  status    Show compose/container health and configured MCP URL.
  test      Run local Docker/Hermes connectivity checks.
  logs      Follow container logs.
  down      Stop and remove the compose service container.
  doctor    Check prerequisites and render docker compose config.
  help      Show this help.

Options:
  --stop-user-service
            Before up/restart, stop and disable the legacy systemd --user
            hisys-mcp.service if it exists. Without this flag the script only
            warns, so service-manager changes stay operator-approved.

Local endpoint after startup:
  http://127.0.0.1:19613/mcp

Runtime root mounted into the container:
  ../../runtime/hisys-mcp-instance -> /runtime
USAGE
}

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "ERROR: required command not found: $1" >&2
    exit 1
  fi
}

docker_compose() {
  docker compose "$@"
}

ensure_prereqs() {
  need_cmd docker
  if ! docker compose version >/dev/null 2>&1; then
    echo "ERROR: 'docker compose' plugin is not available." >&2
    exit 1
  fi
}

ensure_runtime_dirs() {
  mkdir -p \
    "${RUNTIME_ROOT}/config" \
    "${RUNTIME_ROOT}/data" \
    "${RUNTIME_ROOT}/reports" \
    "${RUNTIME_ROOT}/runtime-boundary"
}

legacy_user_service_active() {
  command -v systemctl >/dev/null 2>&1 \
    && systemctl --user list-unit-files hisys-mcp.service >/dev/null 2>&1
}

handle_legacy_user_service() {
  local stop_user_service="$1"
  if ! legacy_user_service_active; then
    return 0
  fi

  if [[ "${stop_user_service}" == "true" ]]; then
    echo "Stopping/disabling legacy systemd --user hisys-mcp.service..."
    systemctl --user stop hisys-mcp.service || true
    systemctl --user disable hisys-mcp.service || true
    return 0
  fi

  local state
  state="$(systemctl --user is-active hisys-mcp.service 2>/dev/null || true)"
  if [[ "${state}" == "active" ]]; then
    cat >&2 <<'WARN'
WARNING: legacy systemd --user hisys-mcp.service is active and may conflict
with Docker's 127.0.0.1:19613 port binding.

Re-run with --stop-user-service if you want this script to stop/disable it:
  scripts/setup_hisys_mcp_docker.sh up --stop-user-service
WARN
  fi
}

compose_up() {
  local stop_user_service="$1"
  ensure_prereqs
  ensure_runtime_dirs
  handle_legacy_user_service "${stop_user_service}"
  echo "Runtime root: ${RUNTIME_ROOT}"
  echo "Starting ${SERVICE_NAME} via Docker Compose..."
  (cd "${REPO_ROOT}" && docker_compose up -d --build "${SERVICE_NAME}")
  (cd "${REPO_ROOT}" && docker_compose ps "${SERVICE_NAME}")
  echo "MCP URL: ${MCP_URL}"
}

compose_down() {
  ensure_prereqs
  echo "Stopping ${SERVICE_NAME}..."
  (cd "${REPO_ROOT}" && docker_compose down)
}

compose_status() {
  ensure_prereqs
  echo "Repository: ${REPO_ROOT}"
  echo "Runtime root: ${RUNTIME_ROOT}"
  echo "MCP URL: ${MCP_URL}"
  (cd "${REPO_ROOT}" && docker_compose ps "${SERVICE_NAME}")
  if docker inspect "${SERVICE_NAME}" >/dev/null 2>&1; then
    docker inspect \
      --format 'health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} status={{.State.Status}} started={{.State.StartedAt}}' \
      "${SERVICE_NAME}"
  fi
}

compose_test() {
  ensure_prereqs
  (cd "${REPO_ROOT}" && docker_compose ps "${SERVICE_NAME}")
  if docker inspect "${SERVICE_NAME}" >/dev/null 2>&1; then
    docker inspect \
      --format 'health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} status={{.State.Status}}' \
      "${SERVICE_NAME}"
  else
    echo "ERROR: container ${SERVICE_NAME} is not present. Run 'up' first." >&2
    exit 1
  fi

  if command -v hermes >/dev/null 2>&1; then
    echo "Testing Hermes MCP registration: hermes mcp test hisys"
    hermes mcp test hisys
  else
    echo "SKIP: hermes CLI is not on PATH; container health check was still inspected."
  fi
}

compose_doctor() {
  ensure_prereqs
  ensure_runtime_dirs
  echo "docker: $(docker --version)"
  echo "docker compose: $(docker compose version)"
  echo "Repository: ${REPO_ROOT}"
  echo "Runtime root: ${RUNTIME_ROOT}"
  echo "Rendering compose config..."
  (cd "${REPO_ROOT}" && docker_compose config)
}

main() {
  local command="${1:-help}"
  local stop_user_service="false"
  if [[ $# -gt 0 ]]; then
    shift || true
  fi
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --stop-user-service)
        stop_user_service="true"
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "ERROR: unknown option: $1" >&2
        usage >&2
        exit 2
        ;;
    esac
    shift
  done

  case "${command}" in
    up)
      compose_up "${stop_user_service}"
      ;;
    restart)
      compose_down
      compose_up "${stop_user_service}"
      ;;
    status)
      compose_status
      ;;
    test)
      compose_test
      ;;
    logs)
      ensure_prereqs
      (cd "${REPO_ROOT}" && docker_compose logs -f "${SERVICE_NAME}")
      ;;
    down)
      compose_down
      ;;
    doctor)
      compose_doctor
      ;;
    help|-h|--help)
      usage
      ;;
    *)
      echo "ERROR: unknown command: ${command}" >&2
      usage >&2
      exit 2
      ;;
  esac
}

main "$@"
