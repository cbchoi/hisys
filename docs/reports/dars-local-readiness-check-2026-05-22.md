# DARS local readiness check — 2026-05-22

## Request context

User instruction: if local is ready, proceed with A; if local is not ready, proceed with C, subscription path.

## Checked evidence

Commands/checks performed from `/home/cbchoi/workspaces/develop/repos/hisys`:

- `HISYS_DARS_LOCAL_ENDPOINT` environment variable: unset.
- `HISYS_INSTANCE` environment variable: unset.
- Listening localhost ports inspected with `ss -ltnp`: no declared OpenAI-compatible `/v1/chat/completions` DARS endpoint was provided or identified.
- DARS config search found only `examples/instance/config/dars.json`, not an operator-provided live instance root.
- Activation packet search found only `docs/examples/dars/backend-activation-localhost.example.json`, not a fresh operator-supplied packet with current approval/expiry.

## Decision result

Local path A is **not ready**. The non-delegable prerequisites required by `DARS-LIVE-EXECUTION-AUTH-EXECUTE-OPERATOR-PREREQUISITES` are missing.

Per the user conditional instruction, switch to C: prepare the governed remote subscription path.

## Boundary

This check did not start a model runner, select a port, synthesize a Hisys instance, create an activation packet, resolve credentials, call a local model, call a remote provider, or mutate runtime-boundary artifacts.
