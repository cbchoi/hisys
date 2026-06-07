# Hisys MCP Subsystem Extraction Decision Packet v0.0.137

Date: 2026-06-07
Task: `HISYS-MCP-SUBSYSTEM-EXTRACTION-DECISION-PACKET`

## Request context

The operator instructed `go with drloo claude` after the DRLOO parallel-write lane execution checkpoint. This packet records a Claude-backed DRLOO decision pass for the Hisys MCP subsystem extraction question. Three Claude Code read-only mapper lanes inspected the local repository only:

```text
claude_read_only_mapper_lane_a=altas
claude_read_only_mapper_lane_b=dars_judge
claude_read_only_mapper_lane_c=gateway_sidecar
claude_lane_a_session=cc6bbd0a-615e-48f4-911f-258d24727071
claude_lane_b_session=f01c9987-0902-41b1-b81e-77f957618961
claude_lane_c_session=7dfed6a3-aaa7-4c20-b7f9-d76e9947843c
claude_lane_c_max_turns_recovered=true
```

The Claude lanes were advisory evidence only. The parent controller preserved the decision boundary, wrote this packet, and remains responsible for validation and commit.

## Accepted claim

```text
task_id=HISYS-MCP-SUBSYSTEM-EXTRACTION-DECISION-PACKET
accepted_claim=hisys_mcp_subsystem_extraction_decision_recorded
gateway_should_remain_lightweight=true
first_extraction_candidate=altas
altas_split_decision=defer
dars_split_decision=defer
judge_split_decision=no
actual_subsystem_split_performed=false
next_safe_task=HISYS-MCP-SUBSYSTEM-STATUS-READINESS-WRAPPER-PREFLIGHT
requires_human_review=true
```

## Decision

Keep the current `hisys-mcp` gateway lightweight and do not split any subsystem in this increment. Altas is recorded as the first extraction candidate only if later evidence shows that index/cache dependencies materially bloat or destabilize the gateway. The current repository state does not support an immediate Altas split because the `src/hisys/altas/ package is not present`; only a pure service-contract placeholder exists in `src/hisys/services/altas.py`.

DARS should be deferred because its actual runtime surface is heavier and more failure-prone, but its MCP exposure is still placeholder-only and its live/provider-related paths remain gated. Judge should not be split now because it is governance-sensitive, local, deterministic, and must retain the `requires_human_review=true` boundary. The gateway must not expose `judge_decide` as a final-authority tool; in short, do not expose judge_decide.

## Evidence scope

- `docs/plans/hisys-mcp-docker-service-implementation-tasks.md` Phase 6.3 default recommendation and open questions.
- `docs/public/hisys-mcp-service.md` lightweight-sidecar and candidate Hermes registration boundary.
- `Dockerfile.hisys-mcp` non-root, MCP extra only, browser dependency exclusion.
- `docker/compose.hisys-mcp-smoke.yaml` no host-port publication and local introspection behavior.
- `src/hisys/mcp/server.py` loopback-only local smoke and server entry points.
- `src/hisys/mcp/tools.py` six base tools, hidden future status tools, fail-closed placeholders.
- `src/hisys/services/altas.py`, `src/hisys/services/dars.py`, and `src/hisys/services/judge.py` pure service contracts.
- `tests/unit/test_service_contracts.py`, `tests/unit/test_mcp_tools.py`, and `tests/integration/test_mcp_streamable_http_sdk_binding_smoke.py` boundary tests.
- Claude Code read-only mapper outputs for Altas, DARS/Judge, and gateway/sidecar constraints.

## Local-safe next slice

The next safe slice is `HISYS-MCP-SUBSYSTEM-STATUS-READINESS-WRAPPER-PREFLIGHT`. It may prepare RED tests and a local-only design for fail-closed status/readiness wrappers, especially around `dars_status` and `judge_status`, without activating a production listener or live provider/model path. It must keep future tools gated behind explicit exposure and must preserve `judge_decide` as non-exposed.

## Boundary flags

```text
production_listener_started=false
hermes_config_mutated=false
live_external_action_authorized=false
live_model_call_authorized=false
raw_provider_api_call_by_hisys=false
credential_lookup_by_hisys=false
docker_build_authorized=false
docker_run_authorized=false
subsystem_service_split_authorized=false
actual_subsystem_split_performed=false
altas_runtime_created=false
dars_runtime_created=false
judge_runtime_created=false
judge_decide_exposed=false
deployment_authorized=false
deployment_performed=false
publication_authorized=false
publication_performed=false
external_notification_authorized=false
external_notification_performed=false
remote_push_authorized=false
force_push_authorized=false
branch_rewrite_authorized=false
human_review_removal_authorized=false
requires_human_review=true
```

## Stop conditions

Stop before any production MCP listener activation, Hermes config mutation, live provider/model call, raw provider API use, credential lookup, Docker build/run, subsystem runtime split, release tag/package/upload/deploy/publication, external notification, remote push, branch rewrite, force push, destructive Git, `judge_decide` exposure, or human-review removal.
