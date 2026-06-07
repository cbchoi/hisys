# Hisys MCP production listener final-check record v0.0.138

Traceability: HISYS-MCP-PRODUCTION-LISTENER-GUARDED-CLI-PREFLIGHT

## Request context

Professor Choi asked to advance the Hisys MCP work to the production MCP listener stage using a DRLOO Claude lane.

## Evidence scope

This record covers local repository changes only:

- `src/hisys/mcp/server.py`
- `tests/integration/test_mcp_production_listener_guarded.py`
- `docs/public/hisys-mcp-service.md`

Claude Code produced the initial implementation in a write-capable local lane. Hermes then inspected the diff, patched a deprecated MCP SDK client import, clarified the public service document, and ran validation locally.

## Validation status

Validated locally with:

```bash
PYTHONPATH=src:. pytest tests/integration/test_mcp_production_listener_guarded.py tests/integration/test_mcp_streamable_http_sdk_binding_smoke.py tests/unit/test_mcp_docker_sidecar_docs.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
PYTHONPATH=src:. pytest -q
```

Observed results:

- `12 passed` for the focused listener/SDK/doc gate after Hermes patches.
- Traceability check: `OK: schemas, trace test, and Hermes boundary convention pass traceability checks`.
- Secret scan: `secret_scan: scanned_files=1123 skipped_files=0 hit_count=0`.
- Full suite: `1819 passed, 1 skipped`.

## Claim boundary

The increment provides a guarded long-lived streamable-http listener entry point:

- `--production-listener-preflight` emits deterministic JSON and starts no server.
- `--production-listener` starts a long-lived listener only when explicitly requested.
- Loopback binding is the default safe path.
- Non-loopback binding is rejected unless `HISYS_MCP_ALLOW_NON_LOOPBACK_BIND=true` is present in the listener process environment.
- The ready packet records `hermes_config_mutated=false`, no external call, no mutation, no publication, no live provider/model call, no credential lookup, and `human_approval_required=true`.

This increment does not register the listener in Hermes, does not mutate `~/.hermes`, does not publish a network service, does not deploy Docker, does not read credentials, and does not authorize live provider/model calls or external actions.

## Blockers

No local validation blocker remains. Hermes registration, persistent sidecar activation, non-loopback service exposure, Docker service publication, and live tool expansion remain separate operator-approved gates.

## Next action

Proceed to `HISYS-MCP-PRODUCTION-LISTENER-GUARDED-CLI-LOCAL-REVIEW-GATE`: review the production listener evidence and decide whether to prepare a candidate Hermes MCP registration without applying it automatically.

## Human approval state

The user approved advancing to the production MCP listener stage with DRLOO Claude. This approval covers local code/docs/tests and local validation only, not Hermes profile mutation, deployment, publication, or external actions.
