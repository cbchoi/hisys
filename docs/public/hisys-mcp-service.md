# Hisys MCP Service First Slice

This document records the first local/fixture-only Hisys MCP gateway slice.

## Scope

The first slice exposes transport-independent wrappers and deterministic server introspection modes for a future `hisys-mcp` sidecar service. It is intended to let Hermes or another MCP-capable agent call a small governed Hisys tool surface without loading the full Hisys runtime into the Hermes container.

Implemented surfaces:

- `hisys.mcp.contracts`: fail-closed request, safety, and result envelopes.
- `hisys.mcp.config`: environment-driven configuration loader that does not create runtime directories.
- `hisys.mcp.cli_adapter`: subprocess-safe local CLI adapter with timeout handling and bounded redacted errors.
- `hisys.mcp.tools`: local wrappers for `health_status`, `environment_status`, `investigate_domain`, `list_run_artifacts`, `show_artifact`, and `release_readiness`.
- `hisys.mcp.server`: deterministic `--health`, `--stdio --list-tools-json`, ephemeral `--http-local-smoke`, ephemeral MCP SDK `--streamable-http-local-smoke`, and guarded long-lived `--production-listener` entry points.

## Authority boundary

This slice is local and fail-closed. The default entry points do not start a persistent network server, perform a live provider/model call, inspect credentials, perform publication or deployment, run browser/search collection, or mutate external systems. The guarded production listener starts a long-lived streamable-http server only when the explicit `--production-listener` flag is passed, binds to loopback by default, and rejects non-loopback binds unless `HISYS_MCP_ALLOW_NON_LOOPBACK_BIND=true` is present in the launcher environment. MCP sampling is disabled by default, future Altas/DARS/Judge placeholder tools are hidden by default, and every result envelope defaults to `external_call_made=false`, `mutation_performed=false`, `publication_or_live_action_approved=false`, and `human_approval_required=true`.

The Docker/Compose service slice is local and fixture-only by default. It packages the guarded production MCP listener as a container-managed sidecar. The compose service publishes only `127.0.0.1:19613` on the host, mounts a repo-external runtime instance directory into `/runtime`, keeps MCP sampling and live actions disabled, and requires the explicit non-loopback bind approval only for the container-internal `0.0.0.0:8765` bind needed by Docker port publishing. The HTTP local client smoke starts an ephemeral loopback-only stdlib HTTP server, fetches `/health` and `/tools` with a local client, records fail-closed authority flags, and shuts the server down inside the same command. The MCP SDK streamable HTTP local smoke starts an ephemeral loopback-only FastMCP `streamable-http` server, uses the MCP SDK client session to list the current tool catalog, records fail-closed authority flags, and shuts the server down inside the same command.

## Local sidecar smoke

The local Docker sidecar smoke files are:

- `Dockerfile.hisys-mcp`
- `docker/compose.hisys-mcp-smoke.yaml`

The image installs `.[mcp]`, keeps browser dependencies out of the first image, runs as the non-root `hisys` user, sets `HISYS_INSTANCE_ROOT=/runtime`, and keeps both `HISYS_MCP_SAMPLING_ENABLED=false` and `HISYS_ALLOW_LIVE_ACTIONS=false` by default.

The compose smoke runs the deterministic tool-list entry point:

```bash
docker compose -f docker/compose.hisys-mcp-smoke.yaml run --rm hisys-mcp
```

This command is a packaging/introspection smoke only. It should print the deterministic local tool catalog and exit. It has no live MCP network listener, does not publish port `8765`, and does not call live providers or external sources.

## Container-managed MCP service

The easiest operator path is the checked-in setup script:

```bash
cd /home/cbchoi/workspaces/develop/repos/hisys
scripts/setup_hisys_mcp_docker.sh up
scripts/setup_hisys_mcp_docker.sh status
scripts/setup_hisys_mcp_docker.sh test
```

The script creates the required repo-external runtime directories, builds the
image, starts the compose service, and prints the local MCP endpoint. If a
legacy `systemd --user` service is still active and may occupy the same port,
the script warns by default. Stopping/disabling that legacy service remains an
explicit operator action:

```bash
scripts/setup_hisys_mcp_docker.sh up --stop-user-service
```

The script also supports:

```bash
scripts/setup_hisys_mcp_docker.sh restart
scripts/setup_hisys_mcp_docker.sh logs
scripts/setup_hisys_mcp_docker.sh down
scripts/setup_hisys_mcp_docker.sh doctor
```

The underlying compose service is still directly runnable:

```bash
mkdir -p /home/cbchoi/workspaces/develop/runtime/hisys-mcp-instance/{config,data,reports,runtime-boundary}
docker compose up -d --build hisys-mcp
```

It runs the guarded production listener in the container and publishes the MCP
endpoint on the host loopback interface only:

```text
http://127.0.0.1:19613/mcp
```

The service uses these boundaries:

- source image: `Dockerfile.hisys-mcp`
- persistent instance root: `../../runtime/hisys-mcp-instance:/runtime`
- container listener: `0.0.0.0:8765` so Docker can publish the port
- host publication: `127.0.0.1:19613:8765`, not a public interface
- `HISYS_MCP_ALLOW_NON_LOOPBACK_BIND=true` only inside the compose service to
  approve the container-internal bind required by port publishing
- `HISYS_MCP_SAMPLING_ENABLED=false`
- `HISYS_ALLOW_LIVE_ACTIONS=false`

Verify after startup:

```bash
docker compose ps
hermes mcp test hisys
```

Then call `health_status`; it should report `overall_status: ok` when the
mounted runtime root contains `config/`, `data/`, `reports/`, and
`runtime-boundary/`.

### Hermes MCP registration

After the Docker service is running, register the host-loopback endpoint in the
Hermes profile that should use Hisys:

```bash
hermes mcp add hisys --url http://127.0.0.1:19613/mcp
hermes mcp test hisys
```

If `hisys` is already present, do not add a duplicate. Inspect and test the
existing entry instead:

```bash
hermes mcp list
hermes mcp test hisys
```

The expected registration URL from the host is
`http://127.0.0.1:19613/mcp`. Use the container-internal
`http://hisys-mcp:8765/mcp` URL only for a Hermes process that runs inside the
same Docker Compose network as the `hisys-mcp` service.

Hermes may need a new session or restart to load newly added MCP tools.

### Runtime and local-folder configuration

There are two separate configuration layers:

1. **Hermes MCP registration**: maps the server name `hisys` to
   `http://127.0.0.1:19613/mcp`.
2. **Hisys runtime/source configuration**: decides what files the Hisys process
   can read and where it writes evidence.

For Docker, host folders are invisible until they are mounted into the
container. The checked-in compose file mounts only the persistent Hisys runtime:

```text
../../runtime/hisys-mcp-instance -> /runtime
```

To inspect a local folder such as `ai.mind`, add a local override file:

```yaml
# docker-compose.override.yml
services:
  hisys-mcp:
    volumes:
      - ../../runtime/hisys-mcp-instance:/runtime
      - /home/cbchoi/ai.mind:/knowledge/ai.mind:ro
```

Use the actual host path. For example, on this host the personal AI-system
workspace may be `/home/cbchoi/ai.sapientia`, so the override would be:

```yaml
services:
  hisys-mcp:
    volumes:
      - ../../runtime/hisys-mcp-instance:/runtime
      - /home/cbchoi/ai.sapientia:/knowledge/ai.sapientia:ro
```

Restart after changing mounts:

```bash
scripts/setup_hisys_mcp_docker.sh restart
scripts/setup_hisys_mcp_docker.sh test
```

Then refer to the **container path**, not the host path, in an MCP request. A
bounded local codebase/current-artifact inspection uses `domain: codebase` and a
`current_artifact` source:

```json
{
  "request_id": "HISYS-REQ-AIMIND-001",
  "domain": "codebase",
  "objective": "Inspect the mounted ai.mind folder as read-only current artifact evidence.",
  "sources": [
    {
      "source_id": "SRC-AIMIND-REPO-001",
      "source_type": "current_artifact",
      "ref": "/knowledge/ai.mind",
      "access_mode": "read_only"
    }
  ]
}
```

The current `codebase` adapter can produce bounded source-inspection artifacts
from a mounted local directory and write them under `/runtime`. General full-text
search over arbitrary vault folders is not controlled by `hermes mcp add`; it
requires a Hisys adapter/tool path that reads the mounted folder and records the
evidence boundary.

## HTTP local client smoke

The local HTTP smoke command is:

```bash
PYTHONPATH=src:. python -m hisys.mcp.server --http-local-smoke --http-host 127.0.0.1 --http-port 0
```

This command binds only to loopback, selects an ephemeral port when `--http-port 0` is used, serves deterministic `/health` and `/tools` responses, performs the local client requests, and then shuts down. It rejects non-loopback hosts such as `0.0.0.0`. The payload records `external_call_made=false`, `mutation_performed=false`, `publication_performed=false`, `live_provider_model_call_made=false`, and `credential_lookup_performed=false`.

This is not production Hermes registration and not a persistent MCP listener.

## MCP SDK streamable HTTP local smoke

The local MCP SDK streamable HTTP smoke command is:

```bash
PYTHONPATH=src:. python -m hisys.mcp.server --streamable-http-local-smoke --http-host 127.0.0.1 --http-port 0
```

This command binds only to loopback, selects an ephemeral port when `--http-port 0` is used, builds a FastMCP server with `transport_kind=streamable-http` at `/mcp`, uses `mcp.client.streamable_http.streamablehttp_client` plus `mcp.ClientSession` to initialize and list tools, and then shuts the server down. It rejects non-loopback hosts such as `0.0.0.0`. The payload records `external_call_made=false`, `mutation_performed=false`, `publication_performed=false`, `live_provider_model_call_made=false`, `credential_lookup_performed=false`, `hermes_config_mutated=false`, `production_listener_started=false`, and `sampling_enabled=false`.

This is a local SDK binding smoke only. It is not production Hermes registration, not a persistent MCP listener, and not permission to mutate Hermes config or publish a network service.

## Guarded production MCP listener (loopback by default)

The guarded production listener is the first long-lived MCP streamable-http
mode for Hisys. It remains opt-in and fail-closed:

- It does not start unless the explicit `--production-listener` CLI flag is
  passed; without the flag the server module exits non-zero by default.
- It binds only to a loopback host (`127.0.0.1`, `localhost`, or `::1`) unless
  the operator sets `HISYS_MCP_ALLOW_NON_LOOPBACK_BIND=true` in the
  environment of the process that launches the listener.
- It never mutates Hermes configuration (`~/.hermes` is never read or
  written), never inspects credentials, never calls live providers/models,
  never performs publication, and never performs any other external action.
- It exposes the same six base tools as the local SDK smoke
  (`health_status`, `environment_status`, `investigate_domain`,
  `list_run_artifacts`, `show_artifact`, `release_readiness`) with MCP
  sampling disabled by default.
- It prints a single deterministic JSON ready packet
  (`schema_id: hisys.mcp.production_listener_ready.v1`) to stdout once the
  server is started, then serves until it receives `SIGINT` or `SIGTERM`.

### Preflight (deterministic, never starts a server)

Use the preflight to confirm the safety envelope without binding any socket:

```bash
PYTHONPATH=src:. python -m hisys.mcp.server \
    --production-listener-preflight \
    --http-host 127.0.0.1 \
    --http-port 8765
```

The preflight prints JSON with
`schema_id: hisys.mcp.production_listener_preflight.v1`. The payload records
`status` (`ok` for loopback or for an explicitly approved non-loopback bind,
`blocked` otherwise), `loopback_only`, `non_loopback_bind_requested`,
`non_loopback_approval_present`, `approval_env`, `production_listener_started`
(always `false` in preflight), `hermes_config_mutated=false`,
`sampling_enabled`, plus the standard fail-closed flags
(`external_call_made=false`, `mutation_performed=false`,
`publication_performed=false`, `live_provider_model_call_made=false`,
`credential_lookup_performed=false`, `human_approval_required=true`).

### Long-lived listener (loopback)

The default safe launch binds only to loopback and uses an ephemeral port so
multiple operators can smoke-test in parallel without colliding on `8765`:

```bash
PYTHONPATH=src:. python -m hisys.mcp.server \
    --production-listener \
    --http-host 127.0.0.1 \
    --http-port 0
```

The first line of stdout is the JSON ready packet. The `host`, `port`, and
`path` fields in the packet are the URL components for an MCP SDK
streamable-http client (e.g. `mcp.client.streamable_http.streamable_http_client`
on `http://<host>:<port>/mcp`). Send `SIGINT` (Ctrl-C) or `SIGTERM` to stop
the listener; the process exits cleanly without mutating any runtime state.

### Explicit non-loopback approval (operator-gated)

A non-loopback bind is rejected by default. To bind on a non-loopback host the
operator must set the explicit approval environment variable in the launching
shell:

```bash
HISYS_MCP_ALLOW_NON_LOOPBACK_BIND=true \
PYTHONPATH=src:. python -m hisys.mcp.server \
    --production-listener \
    --http-host 0.0.0.0 \
    --http-port 8765
```

This approval applies to the listener process only. It is not a standing
policy, it does not register the listener with Hermes, it does not authorize
publication, credential lookup, live provider/model calls, or any external
action, and it does not remove `human_approval_required=true` from the
response envelope.

### Hermes registration boundary

The guarded production listener is a Hisys process. It does not edit, create,
or delete any file under `~/.hermes/`, does not restart Hermes, and does not
register itself as an MCP server in any Hermes profile. Registration with
Hermes still requires the separate operator-approved "Candidate config for
future Hermes registration" workflow documented below: review the candidate
YAML, apply it manually to the appropriate Hermes profile, restart Hermes,
and confirm the boundary in the next review packet.

## Candidate config for future Hermes registration

The following is a candidate config only; do not auto-apply it. It requires explicit operator approval, a completed MCP SDK streamable HTTP transport smoke, and a Hermes restart before it becomes active.

```yaml
mcp_servers:
  hisys:
    url: "http://hisys-mcp:8765/mcp"
    timeout: 180
    connect_timeout: 60
    sampling:
      enabled: false
```

This candidate keeps sampling disabled. It is not permission to mutate Hermes profiles, register the server in production config, start a live connector, inspect credentials, publish, deploy, or remove human review.

## Rollback

If the candidate registration is tested later and must be reverted:

1. Remove the `mcp_servers.hisys` entry from the Hermes config.
2. restart Hermes so the registration is no longer loaded.
3. Stop the local sidecar stack:

   ```bash
   docker compose -f docker/compose.hisys-mcp-smoke.yaml down
   ```

4. Preserve runtime evidence until reviewed; delete generated smoke runtime directories only after confirming they contain no needed evidence.
5. Keep the existing Hisys CLI and Hermes snapshot path as the fallback.

## Verification

Focused verification command:

```bash
PYTHONPATH=src:. pytest tests/unit/test_mcp_contracts.py tests/unit/test_mcp_config.py tests/unit/test_mcp_cli_adapter.py tests/unit/test_mcp_tools.py tests/unit/test_mcp_docker_sidecar_docs.py tests/integration/test_mcp_server_smoke.py tests/integration/test_mcp_http_local_client_smoke.py tests/integration/test_mcp_streamable_http_sdk_binding_smoke.py tests/integration/test_mcp_production_listener_guarded.py -q
```

Observed result on 2026-06-06 before HTTP local smoke: `20 passed`. HTTP local client smoke focused gate: `2 passed`. MCP SDK streamable HTTP local smoke focused gate on 2026-06-07: `2 passed`; combined MCP focused gate before the guarded production listener lane: `28 passed`. Guarded production listener focused gate on 2026-06-07: `6 passed`; combined MCP focused gate after the guarded production listener lane: `36 passed`.

Docker/Compose/doc static verification command:

```bash
PYTHONPATH=src:. pytest tests/unit/test_mcp_docker_sidecar_docs.py -q
```

## Next local-safe continuation

The next safe continuation is `HISYS-MCP-PRODUCTION-LISTENER-GUARDED-CLI-LOCAL-REVIEW-GATE`: review the local guarded production listener evidence (preflight payload, loopback-only ready packet, non-loopback rejection, explicit-approval acknowledgement) and decide the next bounded local-safe increment. Hermes config mutation, persistent sidecar registration, Docker service publication on a public port, credential handling, live provider/model calls, or any other external action still require separate explicit operator approval.
