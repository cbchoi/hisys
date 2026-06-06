# Hisys MCP Service First Slice

This document records the first local/fixture-only Hisys MCP gateway slice.

## Scope

The first slice exposes transport-independent wrappers and deterministic server introspection modes for a future `hisys-mcp` sidecar service. It is intended to let Hermes or another MCP-capable agent call a small governed Hisys tool surface without loading the full Hisys runtime into the Hermes container.

Implemented surfaces:

- `hisys.mcp.contracts`: fail-closed request, safety, and result envelopes.
- `hisys.mcp.config`: environment-driven configuration loader that does not create runtime directories.
- `hisys.mcp.cli_adapter`: subprocess-safe local CLI adapter with timeout handling and bounded redacted errors.
- `hisys.mcp.tools`: local wrappers for `health_status`, `environment_status`, `investigate_domain`, `list_run_artifacts`, `show_artifact`, and `release_readiness`.
- `hisys.mcp.server`: deterministic `--health` and `--stdio --list-tools-json` smoke entry points.

## Authority boundary

This first slice is local and fixture-only. It does not start a network server, perform a live provider/model call, inspect credentials, perform publication or deployment, run browser/search collection, or mutate external systems. MCP sampling is disabled by default, future Altas/DARS/Judge placeholder tools are hidden by default, and every result envelope defaults to `external_call_made=false`, `mutation_performed=false`, `publication_or_live_action_approved=false`, and `human_approval_required=true`.

## Verification

Focused verification command:

```bash
PYTHONPATH=src:. pytest tests/unit/test_mcp_contracts.py tests/unit/test_mcp_config.py tests/unit/test_mcp_cli_adapter.py tests/unit/test_mcp_tools.py tests/integration/test_mcp_server_smoke.py -q
```

Observed result on 2026-06-06: `20 passed`.

## Next local-safe continuation

The next safe continuation is to add the Docker/Compose and public manual slice around the already-tested local entry points, still without live network exposure or credential handling by default.
