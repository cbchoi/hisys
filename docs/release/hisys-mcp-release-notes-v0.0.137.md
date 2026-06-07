---
doc_id: HISYS-MCP-RELEASE-NOTES-V0-0-137
title: Hisys MCP Release Notes v0.0.137
version: v0.0.137
status: subsystem-extraction-decision-recorded
created: 2026-06-07
---

# Hisys MCP Release Notes v0.0.137

## Accepted claim

```text
accepted_claim=hisys_mcp_subsystem_extraction_decision_recorded
next_safe_task=HISYS-MCP-SUBSYSTEM-STATUS-READINESS-WRAPPER-PREFLIGHT
```

## Change

This increment records the Claude-backed DRLOO subsystem extraction decision for the Hisys MCP sidecar. The decision keeps the gateway lightweight, records Altas as the first extraction candidate only under later index/cache dependency evidence, defers DARS splitting, and keeps Judge in the gateway because Judge remains local, deterministic, and human-review-gated.

```text
gateway_should_remain_lightweight=true
first_extraction_candidate=altas
altas_split_decision=defer
dars_split_decision=defer
judge_split_decision=no
actual_subsystem_split_performed=false
requires_human_review=true
```

## Boundary

This release note does not authorize production listener activation, Hermes configuration mutation, Docker build/run, subsystem runtime split, live provider/model calls, raw provider API calls, credential lookup, deployment, publication, external notification, remote push, branch rewrite, force push, `judge_decide` exposure, or removal of human review.
