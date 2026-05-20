# Current Code and Document Weakness Analysis Improvement Plan

## Decision context

- Date: `2026-05-20`.
- Repository: `/home/cbchoi/workspaces/develop/repos/hisys`.
- Branch: `dars`.
- Baseline HEAD for this analysis: `ff89b1b docs: prepare live dars panel configuration`.
- Request: analyze weaknesses from current code and documents, derive improvements, and establish an implementation plan.
- Evidence scope: local repository only. This plan used current source files, tests, plans, traceability documents, milestone-bootstrap artifacts, and Ralph reflection state. No live model call, external API, credential lookup, browser/search action, mutation outside repository docs, publication, or remote push is authorized.

## Executive conclusion

The main weakness is not a missing single feature. The current codebase has two simultaneous risk fronts:

1. **Live DARS panel transition risk** — fixture/advisory DARS panel behavior and local-loopback DARS model behavior both exist, but the controlled bridge between them is still only planned. The next implementation should start with activation-packet validation before any adapter or CLI live mode is added.
2. **Governance-state drift risk** — `ralph.md`, milestone-bootstrap profile/task status, plan lifecycle state, and traceability rows do not yet consistently encode the current HEAD and next task. This can cause a resumed agent loop to repeat an already committed step or select the wrong branch/path.

A secondary but important front is **M21 codebase-analysis readiness**. M21.5 benchmark fixtures and M21.6 change-impact analysis remain planned or absent, so advanced code-analysis decisions lack a stable regression surface.

## Weakness inventory

### W1 — Live DARS activation packet missing

Evidence handles:

- `docs/plans/dars-live-panel-configuration-implementation-tasks.md`
- `src/hisys/agents/dars_panel.py`
- `src/hisys/agents/dars.py`
- `src/hisys/agents/dars_config.py`
- `src/hisys/agents/dars_dispatch.py`

Current weakness:

- `LiveDarsPanelActivationPacket` and `src/hisys/agents/dars_panel_live_config.py` do not exist yet.
- Current panel configuration uses local fixture policies and an `approval_ref` string, but does not structurally require `operator_id`, `approved_endpoint_scope=localhost_only`, `allowed_actions=advisory_only`, activation expiry/review timestamp, or raw credential rejection.

Improvement:

- Implement activation-packet schema and validation first, before adding local model panel adapters.
- Preserve the distinction between approval to cross a local model boundary and downstream authority. Even when an activation packet is human-approved, panel outputs must continue to record `requires_human_review=true`, `action_authorized=false`, and `publication_or_live_action_approved=false`.

### W2 — DARS panel boundary record cannot yet express local model crossing

Evidence handles:

- `src/hisys/agents/dars_panel.py`
- `src/hisys/agents/dars.py`
- `docs/operations/local-dars-smoke.md`

Current weakness:

- Panel `ExecutionBoundaryRecord` locks advisory/no-mutation/external-call fields, but does not yet carry `model_boundary_crossed`, `local_model_call_made`, `endpoint_scope`, or a link to the existing local DARS boundary artifact.
- The existing local-loopback DARS runtime writes model-boundary evidence, but the critic panel task boundary is not connected to it.

Improvement:

- Add model-boundary fields to panel task boundary records with safe defaults.
- Add a local model boundary ref field only after activation-packet validation exists.
- Preserve `external_call_made=false` for localhost-only fake/local model calls and avoid conflating local model boundary with external API access.

### W3 — Panel adapter bridge is absent

Evidence handles:

- `src/hisys/agents/dars_panel.py`
- `src/hisys/agents/dars.py`
- `tests/unit/helpers/fake_openai_server.py`

Current weakness:

- Panel adapters are still fixture declarations rather than call-capable critic adapters.
- `DarsRuntime.run_configured_critique` can call local OpenAI-compatible loopback endpoints, but its prompt/context shape is connector-execution oriented, not panel critic-role/rubric/candidate oriented.

Improvement:

- Add a `LocalModelPanelCriticAdapter` only after activation-packet validation is GREEN.
- Use the fake OpenAI server harness before any real local runner smoke.
- Test that critic role, rubric ref, candidate ref, and evidence refs are represented in the local-model request payload without persisting raw source content.

### W4 — CLI live rehearsal is not pinned

Evidence handles:

- `src/hisys/cli/main.py`
- `tests/unit/test_dars_critic_panel_cli.py`

Current weakness:

- `hisys run-dars-panel` is fixture-only and has no `--activation-packet` or equivalent controlled live/local mode flag.
- There is no test proving that a live/local panel mode is rejected without an activation packet.

Improvement:

- Add a future CLI mode only after W1/W2/W3 are GREEN.
- Initial CLI test should prove fail-closed behavior, not successful model use.

### W5 — Governance-state drift in Ralph/bootstrap

Evidence handles:

- `ralph.md`
- `docs/milestone-bootstrap/profile.yaml`
- `docs/milestone-bootstrap/tasks/milestone_tasks_v0.0.12.yaml`

Current weakness:

- `ralph.md` still contains stale current-state checkpoint text from before commit `ff89b1b` and older top-level metadata from earlier branches.
- `profile.yaml` has `baseline_head` but no `current_head`, so planning baseline and post-commit state are ambiguous.
- `milestone_tasks_v0.0.12.yaml` leaves validation as `pending_validation` even though validation passed and the package was committed.

Improvement:

- Create a governance sync increment before or alongside the first live DARS implementation.
- Separate `planning_baseline_head` from `current_head`.
- Update task status and Ralph checkpoint to the committed state.

### W6 — Plan lifecycle and traceability coverage are incomplete for current active lines

Evidence handles:

- `docs/plans/*.md`
- `docs/traceability/README.md`
- `docs/traceability/dars-critic-panel-runtime-traceability.md`

Current weakness:

- Completed plans remain active-looking because there is no plan lifecycle index.
- DARS live `M-CP-LIVE-*` rows are not yet represented in DARS panel traceability as planned/future anchors.
- M21.5 Prepare is committed but not clearly reflected as a prepared/queued row in global traceability.

Improvement:

- Add a plan lifecycle index in a future docs increment.
- Add planned traceability rows for DARS live activation and panel bridge before implementation GREEN claims are made.
- Add prepared/queued rows for M21.5 without overstating implementation.

### W7 — M21.5 benchmark fixture surface absent

Evidence handles:

- `docs/plans/m21-5-regression-benchmark-fixture-repositories-implementation-tasks.md`
- `docs/plans/m21-roadmap-implementation-plan.md`

Current weakness:

- `src/hisys/operations/codebase_regression_benchmarks.py`, `tests/unit/test_codebase_regression_benchmarks.py`, and `tests/fixtures/codebase_repos/benchmark_manifest.json` are absent.
- This leaves later change-impact and architecture-candidate work without a stable regression benchmark surface.

Improvement:

- Resume M21.5 after the live-DARS governance sync or after explicit user prioritization.
- Start with the already planned RED test and keep the implementation local-only and manifest-driven.

### W8 — M21.3/M21.4 hardening gaps

Evidence handles:

- `src/hisys/operations/runtime_boundary_consistency.py`
- `src/hisys/operations/codebase_map_freshness.py`
- `tests/unit/test_runtime_boundary_consistency.py`
- `tests/unit/test_codebase_map_freshness.py`

Current weakness:

- Runtime-boundary consistency checks advisory flag presence more than boolean correctness.
- Codebase-map freshness reports directory/file presence and stale partitions, but invalid calendar dates and deeper metadata drift are not fully pinned.

Improvement:

- Add hardening RED tests for invalid advisory flag values, unexpected JSON top-level shape, invalid date partitions, and freshness/consistency bridge references.

## Prioritized implementation plan

### Phase A — Governance sync before live behavior

Goal: reduce resume/automation drift before live panel behavior is implemented.

Tasks:

1. Update `ralph.md` with a committed current-state checkpoint for `ff89b1b` and this weakness-analysis plan.
2. Update milestone-bootstrap `v0.0.13` package for this analysis and next safe task.
3. Record v0.0.12 validation as completed in a follow-on governance sync, or explicitly list it as a known drift to repair before M-CP-LIVE-1 GREEN.

Acceptance:

- Current HEAD and next task are unambiguous.
- No code behavior changes.
- Validation passes: structural parse, focused DARS regression, traceability validator, secret scan, diff-check.

### Phase B — M-CP-LIVE-1 activation packet

Goal: make the local/live DARS panel transition fail closed before any model call bridge exists.

RED command:

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_critic_panel_live_config.py::test_live_panel_activation_requires_human_approval_ref -q
```

Expected RED:

```text
ModuleNotFoundError: No module named 'hisys.agents.dars_panel_live_config'
```

Future files:

- `src/hisys/agents/dars_panel_live_config.py`
- `tests/unit/test_dars_critic_panel_live_config.py`
- `docs/traceability/dars-critic-panel-runtime-traceability.md`

Acceptance:

- Missing approval/operator/scope/actions fails validation.
- `external_api`, remote endpoint scope, raw credential fields, and mutation/publication authority fail validation.
- Successful activation authorizes only localhost-only advisory local-model boundary rehearsal, not downstream decisions.

### Phase C — M-CP-LIVE-2 local fake-server panel adapter bridge

Goal: connect panel critic tasks to a fake localhost OpenAI-compatible adapter while preserving boundary records.

Future files:

- `src/hisys/agents/dars_panel_live_adapter.py`
- `tests/unit/test_dars_critic_panel_live_adapter.py`

Acceptance:

- Fake server receives critic role/rubric/candidate/evidence context.
- Boundary records include model-boundary fields and linked local boundary refs.
- Remote endpoints are rejected before any HTTP request.
- Failed local model responses produce task-level `failed` or `blocked` outcomes without authorizing synthesis as final approval.

### Phase D — CLI activation rehearsal

Goal: expose controlled rehearsal only after config and adapter are GREEN.

Future files:

- `src/hisys/cli/main.py`
- `tests/unit/test_dars_critic_panel_cli.py`

Acceptance:

- Existing fixture mode remains unchanged.
- Live/local mode requires an activation packet and remains blocked otherwise.
- CLI output includes model-boundary summary fields and advisory/no-authority flags.

### Phase E — M21 codebase-analysis continuation

Goal: restore the M21 queue after live-DARS activation safety is established or explicitly deferred.

Next task:

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_regression_benchmarks.py::test_codebase_regression_benchmarks_report_expected_outcomes -q
```

Expected RED:

```text
ModuleNotFoundError: No module named 'hisys.operations.codebase_regression_benchmarks'
```

Acceptance:

- Local fixture manifest and benchmark report exist.
- Reports preserve `external_call_made=false`, `mutation_performed=false`, `raw_source_content_persisted=false`, and `requires_human_review=true`.

## Validation plan for this planning increment

```bash
python3 - <<'PY'
from pathlib import Path
import json, yaml
root = Path('/home/cbchoi/workspaces/develop/repos/hisys')
for rel in [
  'docs/milestone-bootstrap/profile.yaml',
  'docs/milestone-bootstrap/tasks/milestone_tasks_v0.0.13.yaml',
  'docs/milestone-bootstrap/testcases/milestone_testcases_v0.0.13.yaml',
  'docs/milestone-bootstrap/hisys/request_v0.0.13.json',
]:
    p = root / rel
    if p.suffix in {'.yaml', '.yml'}:
        yaml.safe_load(p.read_text())
    elif p.suffix == '.json':
        json.loads(p.read_text())
print('weakness-analysis bootstrap parse ok')
PY
PYTHONPATH=src:. pytest tests/unit/test_dars_runtime.py tests/unit/test_dars_config.py tests/unit/test_dars_dispatch.py tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

## Boundary

This plan does not authorize live model calls, external API calls, credential lookup, non-localhost endpoints, raw source archival, destructive Git, publication, deployment, or remote push. It authorizes only local documentation/control artifacts and a later RED-first implementation sequence.
