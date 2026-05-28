# Hisys Hermes DARS panel readiness smoke — 2026-05-28

## Request context

The operator instructed Hermes to proceed through the actual Hermes-call smoke test for the Hisys DARS panel. The bounded test used a child Hermes CLI session to call the Hisys DARS panel readiness surface and return the observed state.

## Bounded Hermes invocation

```bash
hermes chat -Q -t terminal -q '<bounded smoke prompt>'
```

Child Hermes session:

```text
session_id=20260528_205103_8880e6
source=cli
model=gpt-5.5
```

The child Hermes prompt required exactly one terminal call, prohibited file edits, network/browser/search actions, credential inspection, push, release, and publication, and requested this read-only command:

```bash
PYTHONPATH=src:. python3 -m hisys.cli.main dars-panel-readiness --instance /home/cbchoi/workspaces/develop/repos/hisys --date 20260528 --format json
```

Session-store verification shows the child Hermes assistant issued the terminal tool call with that command and `workdir=/home/cbchoi/workspaces/develop/repos/hisys`.

## Observed result

The parent shell command returned exit code 0. The child Hermes final response reported:

```text
종료 코드: 0
schema_id: hisys.dars_panel.readiness_status
schema_version: 0.1.0
advisory_only: true
completion_claim: local_fixture_localhost_controlled_advisory_complete
external_call_made: false
mutation_performed: false
publication_performed: false
live_external_action_authorized: false
live_provider_execution_smoked: false
requires_human_review: true
fixture_panel_complete: true
golden_fixture_available: true
localhost_rehearsal_available: true
localhost_rehearsal_human_gated: true
remote_subscription_policy_exists: true
remote_subscription_injected_executor_harness_available: true
operator_report_available: true
next_queue_after_closure: MB-CODEBASE-M21-6-PREP
```

## Boundary interpretation

This smoke confirms that a live Hermes child session can call the Hisys DARS panel readiness surface through the terminal tool and return the expected readiness fields. It does not upgrade DARS completion, raw provider API readiness, adapter-native readiness, bounded unattended operation, controlled advisory release, live external action, credential lookup, release execution, publication, deployment, remote push, or human-review removal.

The Hermes child session itself crossed the Hermes model boundary. The Hisys command executed by that child reported `external_call_made=false`, `mutation_performed=false`, `publication_performed=false`, `live_external_action_authorized=false`, and `requires_human_review=true`.

## Accepted claim boundary

```text
accepted_claim=hermes_dars_panel_readiness_smoke_completed
hermes_child_session_id=20260528_205103_8880e6
hermes_terminal_tool_call_verified=true
hisys_command_exit_code=0
hisys_dars_readiness_schema=hisys.dars_panel.readiness_status
hisys_command_external_call_made=false
hisys_command_mutation_performed=false
hisys_command_publication_performed=false
hisys_command_live_external_action_authorized=false
requires_human_review=true
next_safe_task=MB-CODEBASE-M21-6-PREP
```
