# DARS live backend — localhost smoke runbook (M-DARS-BE-4)

> **Status:** human-gated rehearsal. Do not run this procedure unless the operator has already started the model runner outside Hisys and is willing to take responsibility for the local model boundary crossing.

This runbook documents how to exercise the local `openai_compatible` DARS
backend through `DarsRuntime.run_configured_critique(...)` against an
operator-supplied localhost endpoint. It assumes the M-DARS-BE-1 activation
packet validator, M-DARS-BE-2 runtime enforcement, and M-DARS-BE-3
backend-boundary decision record are in place.

Remote providers are not covered. The Codex/Claude subscription policy
packet is fail-closed preparation only and waits for a later explicit
implementation approval.

## Preconditions

The smoke runbook MUST stop and ask before continuing on any of these
signals: non-loopback endpoint, missing activation packet, credential
requirement, tool/search/browser permission, mutation request, failed
secret scan, or human uncertainty.

- The operator owns an **already-running localhost-only model endpoint**.
  Hisys never installs, downloads, starts, or selects a model runner.
- The endpoint is a loopback URL of the form
  `http://127.0.0.1:<port>/v1/chat/completions` and never points at a
  non-loopback address. Reject any **non-loopback endpoint** before any
  HTTP call.
- A signed activation packet exists on disk and matches the M-DARS-BE-1
  schema. The packet must declare `endpoint_scope=localhost_only`,
  `allowed_actions=advisory_only`, and `human_approved=true`. Reject a
  **missing activation packet** before the runtime is called.
- The operator confirms the local model runner does not demand any
  Authorization header, API key, or credential. Reject any
  **credential requirement** at this gate.
- The operator confirms the local model runner has no
  **tool/search/browser permission** for this rehearsal.
- No **mutation request** is in scope. The runbook stops on any mutation
  request from either the operator or the local model output.
- `python3 scripts/scan_secrets.py` must pass. Stop on a
  **failed secret scan**.
- The operator is decisive about each gate. Stop on
  **human uncertainty** rather than proceeding.

## Inputs

The operator supplies two values out of band:

- `HISYS_DARS_LOCAL_ENDPOINT` — the operator-supplied localhost endpoint
  (must resolve to a loopback address).
- `HISYS_INSTANCE` — the Hisys instance root that owns the DARS config.

The activation packet path is supplied through
`--backend-activation-packet`. A starter packet is committed at
`docs/examples/dars/backend-activation-localhost.example.json`; copy and
update it for the operator's `approval_ref` and `expires_at` window
before rehearsal.

## Rehearsal commands

The runtime is the enforcement boundary. The CLI only passes
`--backend-activation-packet` through. Operators must not skip the CLI in
this rehearsal, but direct Python calls to
`DarsRuntime.run_configured_critique(...)` still cannot bypass activation —
the M-DARS-BE-2 helper fails closed without the packet.

1. Confirm the CLI parser accepts the new pass-through (no model call):

   ```bash
   PYTHONPATH=src:. python3 -m hisys.cli.main request-dars-critique --help
   ```

2. Rehearse the no-op fixture path first (no model call):

   ```bash
   PYTHONPATH=src:. python3 -m hisys.cli.main request-dars-critique \
     --instance "$HISYS_INSTANCE" \
     --date 20260521 \
     --source-execution-id EXEC-LOCAL-SMOKE-001 \
     --critique-text "fixture critique for smoke rehearsal" \
     --producer-id dars-local-smoke-rehearsal
   ```

3. Only after every precondition above is green, rehearse the configured
   `openai_compatible` path against the operator's already-running
   endpoint. The runbook does **not** authorize starting a model runner.

   ```bash
   PYTHONPATH=src:. python3 -m hisys.cli.main request-dars-critique \
     --instance "$HISYS_INSTANCE" \
     --date 20260521 \
     --source-execution-id EXEC-LOCAL-SMOKE-001 \
     --producer-id dars-local-smoke-rehearsal \
     --backend configured \
     --approval-ref APPROVAL-DARS-BE-LOCALHOST-EXAMPLE \
     --backend-activation-packet docs/examples/dars/backend-activation-localhost.example.json
   ```

   The DARS config under `$HISYS_INSTANCE/config/dars.json` must declare
   `local_llm_dars` as the default backend with
   `endpoint: $HISYS_DARS_LOCAL_ENDPOINT` and
   `mode: local_network_only`.

## Expected boundary record

After a successful run, the M-DARS-BE-3 record exists at
`$HISYS_INSTANCE/runtime-boundary/dars-backends/20260521/EXEC-LOCAL-SMOKE-001/local_llm_dars.{json,md}`
and carries:

- `external_call_made=false`
- `mutation_performed=false`
- `publication_performed=false`
- `allowed_actions=advisory_only`
- `model_boundary_crossed=true`
- `local_model_call_made=true`
- `endpoint_scope=localhost_only`

No credential lookup, No remote API, No Authorization header — the
localhost endpoint must accept the request without any credential.

## Stop conditions

The runbook stops, the operator is notified, and no further command runs
on any of these signals:

- non-loopback endpoint
- missing activation packet
- credential requirement
- tool/search/browser permission
- mutation request
- failed secret scan
- human uncertainty
- the operator pauses for any reason

## Traceability

- M-DARS-BE-1 — `tests/unit/test_dars_backend_activation.py`
- M-DARS-BE-2 — `tests/unit/test_dars_runtime.py`
- M-DARS-BE-3 — `tests/unit/test_dars_backend_boundary.py`
- M-DARS-BE-4 — this runbook and `tests/unit/test_dars_live_backend_runbook.py`

Remote providers are not covered. Future Codex/Claude subscription
backends remain fail-closed preparation only until M-DARS-BE-5 lands and
is separately approved.
