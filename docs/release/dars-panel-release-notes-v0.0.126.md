# DARS Panel Release Notes v0.0.126

Hisys Hermes DARS panel readiness smoke gate is recorded.

```text
accepted_claim=hermes_dars_panel_readiness_smoke_completed
hermes_child_session_id=20260528_205103_8880e6
hermes_terminal_tool_call_verified=true
hisys_command_exit_code=0
evidence_ref=docs/reports/hisys-hermes-dars-panel-readiness-smoke-2026-05-28.md
next_safe_task=MB-CODEBASE-M21-6-PREP
```

The smoke confirms that a child Hermes CLI session can invoke the local Hisys DARS panel readiness command and return the expected advisory status fields. It does not authorize raw provider API use, adapter-native real-provider readiness, unattended operation, release execution, credential lookup, deployment, publication, external notification, repository synchronization, or human-review removal.
