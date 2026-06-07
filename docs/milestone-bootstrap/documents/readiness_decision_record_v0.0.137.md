# Readiness Decision Record v0.0.137

Date: 2026-06-07
Task: `HISYS-MCP-SUBSYSTEM-EXTRACTION-DECISION-PACKET`

## Decision

The operator instruction `go with drloo claude` is accepted as authorization to use Claude Code as a bounded read-only DRLOO mapper for the Hisys MCP subsystem extraction decision. The resulting decision is local docs/control only: keep the gateway lightweight, do not split any subsystem now, record Altas as the first extraction candidate only if later cache/index evidence requires it, defer DARS splitting, and keep Judge inside the gateway.

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
requires_human_review=true
next_safe_task=HISYS-MCP-SUBSYSTEM-STATUS-READINESS-WRAPPER-PREFLIGHT
```

## Boundary flags

```yaml
gateway_should_remain_lightweight: true
actual_subsystem_split_performed: false
```

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

## Evidence scope

- `docs/release/hisys-mcp-subsystem-extraction-decision-packet-v0.0.137.md`
- `docs/release/hisys-mcp-release-notes-v0.0.137.md`
- `docs/plans/hisys-mcp-docker-service-implementation-tasks.md`
- `src/hisys/mcp/tools.py`
- `src/hisys/services/altas.py`
- `src/hisys/services/dars.py`
- `src/hisys/services/judge.py`
- Claude Code read-only mapper lanes A/B/C
- `tests/unit/test_hisys_mcp_subsystem_extraction_decision_packet.py`
- `docs/milestone-bootstrap/profile.yaml`
- `docs/traceability/README.md`
- `ralph.md`

## Next safe task

```text
next_safe_task=HISYS-MCP-SUBSYSTEM-STATUS-READINESS-WRAPPER-PREFLIGHT
```
