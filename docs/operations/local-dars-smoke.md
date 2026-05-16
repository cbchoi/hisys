# Local DARS Smoke Procedure

> Controlled fixture-backed smoke for the openai-compatible Local DARS adapter
> introduced in Hisys Ralph milestones M8..M11. This procedure verifies the
> local-LLM dispatch path against a loopback fake HTTP server. It does not
> install a local LLM runner, download a model, or change a runtime config.

## 1. Purpose

The Local DARS / ByeSys Provenance plan
(`docs/plans/2026-05-16-local-dars-byesys-provenance.md`) requires that an
`openai_compatible` DARS adapter be exercised against a deterministic local
fake HTTP server before any live local-runner deployment. This document
captures the controlled smoke procedure so reviewers can confirm the
end-to-end shape of the local-model boundary without invoking a real model.

Traceability: HISYS-FR-AGT-001..005, HISYS-T-019, HISYS-T-020,
HISYS-CON-010..012, Local DARS plan Milestones 2, 3, 7, and 8.

## 2. Scope and Boundaries

In scope:

- Verify that `DarsRuntime.run_configured_critique` dispatches to the
  loopback fake server at `127.0.0.1:<ephemeral-port>/v1/chat/completions`
  for an `openai_compatible` + `local_network_only` backend.
- Verify that the persisted critique records
  `dars_backend="local_llm_dars"`, `external_call_made=false`,
  `model_boundary_crossed=true`, `local_model_call_made=true`, and
  `endpoint_scope="localhost_only"`.
- Verify that a runtime-boundary artifact
  `runtime-boundary/dars/<yyyymmdd>/dars-local-llm-boundary-<request_id>.json`
  records the approval ref and matching boundary fields.
- Verify that the openai-compatible adapter fails closed on missing
  approval ref, remote endpoint, non-2xx response, malformed JSON,
  missing message content, and timeout (one failure class per check).

Out of scope (Section 4 stop conditions apply):

- Installing `ollama`, `llama.cpp`, vLLM, LM Studio, or any other local
  model runner.
- Downloading any model.
- Replacing the working Claude DARS runtime config with a Local DARS
  config before fake-server tests pass.
- Permitting non-localhost endpoints, live external search, browser
  calls, credential use, or any mutation.

## 3. Smoke Command

The controlled smoke procedure is executed as a pytest run against the
threaded loopback fake server defined under
`tests/unit/helpers/fake_openai_server.py`. The harness binds only to
`127.0.0.1` on an ephemeral port and never reaches the network.

```bash
python3 -m pytest \
  tests/unit/test_dars_runtime.py::test_dars_runtime_calls_local_openai_compatible_backend \
  tests/unit/test_dars_runtime.py::test_dars_runtime_records_local_model_boundary_not_external_call \
  tests/unit/test_dars_runtime.py::test_dars_runtime_rejects_local_backend_without_approval_ref \
  tests/unit/test_dars_runtime.py::test_dars_runtime_rejects_remote_endpoint_before_http_request \
  tests/unit/test_dars_runtime.py::test_dars_runtime_fails_closed_on_non_2xx_local_llm_response \
  tests/unit/test_dars_runtime.py::test_dars_runtime_fails_closed_on_malformed_local_llm_response \
  tests/unit/test_dars_runtime.py::test_dars_runtime_fails_closed_on_missing_message_content \
  tests/unit/test_dars_runtime.py::test_dars_runtime_fails_closed_on_local_llm_timeout \
  tests/unit/test_dars_runtime.py::test_dars_runtime_local_llm_failure_does_not_leak_secrets \
  -q
```

Expected result: all nine cases pass against the fake server, and the
fake server's `contacted` flag is `True` for the success-path and HTTP
failure-class tests, and `False` for the missing-approval-ref and
remote-endpoint pre-HTTP rejection tests.

## 4. Expected Persisted Artifact Shape

When the smoke test runs successfully it persists two artifact families:

```text
data/agent-critiques/<yyyymmdd>/CRITIQUE-DARS-<request-suffix>.json
runtime-boundary/dars/<yyyymmdd>/dars-local-llm-boundary-<request_id>.json
```

The critique JSON includes:

```text
dars_backend: local_llm_dars
external_call_made: false
model_boundary_crossed: true
local_model_call_made: true
endpoint_scope: localhost_only
mutation_performed: false
```

The boundary JSON includes:

```text
endpoint_scope: localhost_only
model_boundary_crossed: true
local_model_call_made: true
external_call_made: false
mutation_performed: false
approval_ref: <APPROVAL-REF-FROM-CALLER>
```

The fake-server happy path also asserts that the request payload contains
the configured model, the DARS advisory/no-mutation instructions, the
provenance instructions for internal sources / external DOI / ByeSys
unsupported synthesis, and **no** tool, search, or browser
authorization fields.

## 5. Stop Conditions

The Local DARS smoke procedure stops and requires user execution for any
of the following:

- Installing or invoking a real local model runner.
- Downloading a model from any registry.
- Replacing the working Claude DARS runtime config with a Local DARS
  config in a controlled runtime instance.
- Permitting any non-localhost endpoint, live external search, browser
  call, credential use, or mutation.

Each of these actions is non-delegable per the Ralph Section 2 safety
boundary and must be performed by the user with the exact command the
loop prepares before continuing.

## 6. Next Step Toward a Live Local Runner

A future controlled task may enable a real local LLM runner once:

1. The full M8..M11 fake-server tests are green on the deploying host
   (covered by this smoke procedure).
2. The user has installed and started the local runner with a
   user-executed command outside the loop.
3. The runtime config is updated with explicit approval and the runner
   binds only to a loopback address.
4. A live smoke run records `external_call_made=false`,
   `model_boundary_crossed=true`, `local_model_call_made=true`, and
   `endpoint_scope=localhost_only` against the real runner.

Until those gates are met, the fake-server smoke described in Section 3
remains the authoritative Local DARS validation.
