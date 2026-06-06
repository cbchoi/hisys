# Hisys MCP Service First Slice

This document records the first local/fixture-only Hisys MCP gateway slice.

## Scope

The first slice exposes transport-independent wrappers and deterministic server introspection modes for a future `hisys-mcp` sidecar service. It is intended to let Hermes or another MCP-capable agent call a small governed Hisys tool surface without loading the full Hisys runtime into the Hermes container.

Implemented surfaces:

- `hisys.mcp.contracts`: fail-closed request, safety, and result envelopes.
- `hisys.mcp.config`: environment-driven configuration loader that does not create runtime directories.
- `hisys.mcp.cli_adapter`: subprocess-safe local CLI adapter with timeout handling and bounded redacted errors.
- `hisys.mcp.tools`: local wrappers for `health_status`, `environment_status`, `investigate_domain`, `list_run_artifacts`, `show_artifact`, and `release_readiness`.
- `hisys.mcp.server`: deterministic `--health`, `--stdio --list-tools-json`, ephemeral `--http-local-smoke`, and ephemeral MCP SDK `--streamable-http-local-smoke` entry points.

## Authority boundary

This first slice is local and fixture-only. It does not start a network server, perform a live provider/model call, inspect credentials, perform publication or deployment, run browser/search collection, or mutate external systems. MCP sampling is disabled by default, future Altas/DARS/Judge placeholder tools are hidden by default, and every result envelope defaults to `external_call_made=false`, `mutation_performed=false`, `publication_or_live_action_approved=false`, and `human_approval_required=true`.

The Docker/Compose smoke slice is also local and fixture-only. It packages the deterministic introspection entry points, not a live MCP network listener. The compose smoke intentionally publishes no host ports. The HTTP local client smoke starts an ephemeral loopback-only stdlib HTTP server, fetches `/health` and `/tools` with a local client, records fail-closed authority flags, and shuts the server down inside the same command. The MCP SDK streamable HTTP local smoke starts an ephemeral loopback-only FastMCP `streamable-http` server, uses the MCP SDK client session to list the current tool catalog, records fail-closed authority flags, and shuts the server down inside the same command.

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
PYTHONPATH=src:. pytest tests/unit/test_mcp_contracts.py tests/unit/test_mcp_config.py tests/unit/test_mcp_cli_adapter.py tests/unit/test_mcp_tools.py tests/unit/test_mcp_docker_sidecar_docs.py tests/integration/test_mcp_server_smoke.py tests/integration/test_mcp_http_local_client_smoke.py tests/integration/test_mcp_streamable_http_sdk_binding_smoke.py -q
```

Observed result on 2026-06-06 before HTTP local smoke: `20 passed`. HTTP local client smoke focused gate: `2 passed`. MCP SDK streamable HTTP local smoke focused gate on 2026-06-07: `2 passed`; combined MCP focused gate: `28 passed`.

Docker/Compose/doc static verification command:

```bash
PYTHONPATH=src:. pytest tests/unit/test_mcp_docker_sidecar_docs.py -q
```

## Next local-safe continuation

The next safe continuation is `HISYS-MCP-STREAMABLE-HTTP-SDK-BINDING-LOCAL-REVIEW-GATE`: review the local SDK smoke evidence and decide the next bounded local-safe increment. Any production listener activation, Hermes config mutation, persistent sidecar registration, Docker service publication, credential handling, or live external action still requires separate explicit approval.
