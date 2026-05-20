# DARS Live Panel Localhost Smoke Runbook

Traceability: M-CP-LIVE-1, M-CP-LIVE-2, M-CP-LIVE-3, M-CP-LIVE-4.

This runbook is the human-gated local smoke procedure for the DARS live panel. It is for an operator-supplied localhost endpoint only. It does not install, start, download, configure, or select a model runner.

## 1. Scope

Use this procedure only after these prerequisite gates are green:

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_live_config.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_live_adapter.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py -q
```

The smoke uses an already-running localhost-only model endpoint supplied by the operator. The expected endpoint shape is:

```text
http://127.0.0.1:<port>/v1/chat/completions
```

`localhost` or `::1` may also be acceptable when the runtime parser classifies the parsed authority as loopback. Do not use substring matching or a remote alias.

## 2. Non-delegable operator prerequisites

Do not run this procedure unless the operator has already started the model runner and has confirmed all of the following:

1. The model runner is already bound to loopback only.
2. The endpoint URL is an operator-supplied localhost endpoint, not a remote API endpoint.
3. No credential, API key, password, bearer token, or Authorization header is required.
4. A M-CP-LIVE-1 activation packet exists and authorizes only `localhost_only` / `advisory_only` operation.
5. The runtime instance root is a chosen smoke instance root, not a production or publication target.

Hermes/Hisys must not install a runner, download a model, edit a system service, fetch credentials, or start a remote provider for this smoke.

## 3. Environment variables

Set these values explicitly for the smoke shell:

```bash
export HISYS_INSTANCE="/tmp/hisys-dars-live-localhost-smoke"
export HISYS_YYYYMMDD="20260520"
export HISYS_REQUEST_ID="REQ-DARS-LIVE-SMOKE-001"
export HISYS_DARS_LOCAL_ENDPOINT="http://127.0.0.1:<port>/v1/chat/completions"
export HISYS_DARS_LOCAL_MODEL="operator-local-model"
export HISYS_DARS_ACTIVATION_PACKET="/absolute/path/to/activation-packet.json"
export HISYS_DARS_PANEL_CONFIG="docs/examples/dars/live-panel-localhost-config.example.json"
```

`HISYS_DARS_LOCAL_ENDPOINT` must be the operator-supplied localhost endpoint. Replace `<port>` only with the loopback port opened by the operator-owned runner.

## 4. Copy-paste smoke command

```bash
PYTHONPATH=src python3 -m hisys.cli.main run-dars-panel \
  --instance "$HISYS_INSTANCE" \
  --date "$HISYS_YYYYMMDD" \
  --request-id "$HISYS_REQUEST_ID" \
  --panel-config "$HISYS_DARS_PANEL_CONFIG" \
  --candidate-ref "artifact://operator/local-smoke/candidate" \
  --evidence-ref "artifact://operator/local-smoke/evidence" \
  --local-model-endpoint "$HISYS_DARS_LOCAL_ENDPOINT" \
  --local-model "$HISYS_DARS_LOCAL_MODEL" \
  --activation-packet "$HISYS_DARS_ACTIVATION_PACKET" \
  --format json
```

Expected successful boundary semantics:

```text
execution_mode=local_model_rehearsal
endpoint_scope=localhost_only
model_boundary_crossed=true
local_model_call_made=true
external_call_made=false
mutation_performed=false
publication_performed=false
allowed_actions=advisory_only
```

The command writes only under the selected `$HISYS_INSTANCE` runtime root. It should produce local model boundary refs under:

```text
runtime-boundary/dars-panel-live/<YYYYMMDD>/<REQUEST_ID>/<TASK_ID>.json
```

## 5. Stop conditions

Stop immediately and do not run the smoke command if any of these conditions appears:

- non-loopback endpoint
- missing activation packet
- credential requirement
- tool/search/browser permission
- mutation request
- failed secret scan
- human uncertainty
- request to install, start, or download a model runner
- request to use a remote API provider
- request to persist secrets or Authorization headers
- request to publish, deploy, push, upload, or otherwise act outside the chosen runtime instance root

Boundary commitments:

- No credential lookup
- No remote API
- No Authorization header
- No browser/search/tool authorization
- No mutation authority
- No publication authority

## 6. Review after execution

After the operator-run smoke completes, review the JSON output and boundary refs before making any follow-up claim. The smoke is acceptable only if every persisted boundary record preserves:

```text
external_call_made=false
mutation_performed=false
publication_performed=false
allowed_actions=advisory_only
endpoint_scope=localhost_only
```

Any failed local model response is a task-level failure, not approval for synthesis, publication, mutation, or remote/external DARS.

## 7. Next governed line

M-CP-LIVE-5, if approved later, must be a separate remote/external DARS policy packet with credential-reference, egress, redaction, and decision-packet controls. This runbook does not authorize M-CP-LIVE-5.
