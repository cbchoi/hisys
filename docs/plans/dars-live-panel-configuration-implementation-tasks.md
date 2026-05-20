# DARS live panel configuration — implementation tasks

> **For Ralph/Hermes:** This is a Prepare/document-RED artifact for the live DARS panel configuration line. Use the `test-driven-development` skill before writing tests or production code. This plan authorizes documentation and bootstrap artifacts only. It does not authorize a live model call, credential lookup, network access beyond future localhost fake-server tests, remote push, publication, or external API dispatch.

## Decision context

- Date: `2026-05-20`.
- Repository: `/home/cbchoi/workspaces/develop/repos/hisys`.
- Baseline HEAD at planning: `6cbef3a docs: prepare regression benchmark fixtures`.
- Branch: `dars`, tracking `origin/dars`, ahead locally.
- Current local/advisory DARS panel status: fixture-local `hisys run-dars-panel` CLI, `DarsCriticPanelRuntime`, `CriticAdapterRegistry`, per-task `ExecutionBoundaryRecord`, `ExecutionGraphPlan`, duration records, blocked external-style backend invariant, and DARS focused regression are already present.
- Relevant existing surfaces:
  - `src/hisys/agents/dars_panel.py` — panel runtime, adapter registry, execution-boundary writer, CLI-backed fixture panel.
  - `src/hisys/agents/dars.py` — existing `openai_compatible` local-loopback DARS runtime surface with model-boundary metadata.
  - `src/hisys/agents/dars_config.py` — loopback endpoint validation and backend config schema.
  - `src/hisys/agents/dars_dispatch.py` — approval-gated dispatch decision records.
  - `docs/plans/2026-05-16-local-dars-byesys-provenance.md` — local DARS / ByeSys provenance plan.
  - `docs/traceability/dars-critic-panel-runtime-traceability.md` — current panel traceability matrix.

## Goal

Define the safe implementation path for a **controlled live DARS panel**: multiple DARS critic roles are configured to call an approved local model boundary through the existing loopback-only `openai_compatible` DARS runtime contract, while preserving panel-level advisory-only semantics, per-task boundary records, human approval references, and no mutation authority.

In this plan, **live** means a runtime model boundary is crossed. The first authorized live target class is **localhost-only local model** with fake-server tests first. Remote external API DARS is a later, separately approved line.

## Non-goals and hard boundaries

This Prepare increment does not authorize:

- live model calls or any network call;
- credential resolution, secret lookup, token persistence, or environment-variable capture;
- remote OpenAI/Anthropic/Gemini/external API calls;
- browser/search/tool execution by a critic;
- publication, alert delivery, repository push, or downstream state mutation;
- changing the current fixture-local panel behavior;
- enabling bounded-parallel execution by default;
- storing raw prompts, secrets, or full model transcripts outside runtime-boundary artifacts.

All future runtime artifacts must continue to preserve:

```text
advisory_only=true
requires_human_review=true
action_authorized=false
mutation_performed=false
allowed_actions=advisory_only
```

For localhost model calls only, the model-boundary fields should be:

```text
model_boundary_crossed=true
local_model_call_made=true
endpoint_scope=localhost_only
external_call_made=false
```

## Architecture target

```text
DarsCriticPanelConfig
  + LiveDarsPanelActivationPacket (human approval, endpoint scope, run intent)
        |
        v
DarsRoundPlan / ExecutionGraphPlan
        |
        v
PanelLiveAdapterRegistry
        |
        v
LocalModelPanelCriticAdapter
        |
        v
DarsRuntime.run_configured_critique / openai_compatible local-loopback adapter
        |
        v
ExecutionBoundaryRecord + LocalModelBoundaryRecord + DarsCritiqueRecord
```

The bridge should reuse existing validated surfaces instead of adding a second HTTP client inside `dars_panel.py`. The panel runtime stays responsible for critic scheduling and synthesis. The DARS runtime stays responsible for local model request construction, loopback endpoint defense-in-depth, and critique record persistence.

## Proposed increments

### M-CP-LIVE-1 — Live panel activation packet and config validation

Objective: define a checked, machine-readable activation packet required before any panel critic can resolve to a local model adapter.

Files to create or modify in the future:

- `src/hisys/agents/dars_panel_live_config.py`
- `tests/unit/test_dars_critic_panel_live_config.py`
- `docs/traceability/dars-critic-panel-runtime-traceability.md`

RED command:

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_live_config.py::test_live_panel_activation_requires_human_approval_ref -q
```

Expected RED:

```text
ModuleNotFoundError: No module named 'hisys.agents.dars_panel_live_config'
```

Acceptance:

- `LiveDarsPanelActivationPacket` requires `approval_ref`, `operator_id`, `approved_endpoint_scope="localhost_only"`, `allowed_actions="advisory_only"`, and `expires_at` or equivalent review timestamp.
- It rejects `external_api`, remote endpoint scope, mutation authority, missing approval, or raw credential fields.
- It records `human_approved=true` only for the activation packet, while panel output still records `requires_human_review=true` and no downstream authority.

### M-CP-LIVE-2 — Fake-server local model panel adapter bridge

Objective: prove the panel can route each critic through the existing local-loopback DARS runtime contract using a fake OpenAI-compatible server.

Files to create or modify in the future:

- `src/hisys/agents/dars_panel_live_adapter.py` or a small bridge module imported by `dars_panel.py`.
- `tests/unit/test_dars_critic_panel_live_adapter.py`.
- Test helper fake server under `tests/unit/helpers/` if not already reusable.

RED command:

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_live_adapter.py::test_live_panel_adapter_calls_fake_local_model_and_records_model_boundary -q
```

Acceptance:

- The fake server listens only on `127.0.0.1` with an ephemeral port.
- Each critic call includes advisory/no-mutation instructions, configured role/rubric/evidence refs, and no browser/search/tool authorization.
- Persisted per-task boundary records include `approval_ref`, `adapter_class="local_model"` or an equivalent explicit class, `model_boundary_crossed=true`, `local_model_call_made=true`, `endpoint_scope="localhost_only"`, `external_call_made=false`, `mutation_performed=false`, and `duration_ms`.
- Remote, deceptive, missing-host, unsupported-scheme, and missing-approval cases fail before any HTTP request is attempted.
- Model failures are isolated per critic; synthesis remains partial and advisory.

### M-CP-LIVE-3 — Read-only CLI activation rehearsal

Objective: add an explicit CLI rehearsal path that loads a disabled-by-default local model panel config and proves that live mode remains blocked unless the activation packet is supplied.

Files to create or modify in the future:

- `src/hisys/cli/main.py`
- `tests/unit/test_dars_critic_panel_cli.py`
- `docs/examples/dars/live-panel-localhost-config.example.json` or equivalent checked-in example with no secrets.

RED command:

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py::test_run_dars_panel_live_mode_requires_activation_packet -q
```

Acceptance:

- `hisys run-dars-panel` fixture mode behavior remains unchanged.
- Live/local model mode is opt-in through a named flag such as `--activation-packet` and rejects operation without it.
- Example config contains only localhost endpoint placeholders and no credentials.
- CLI output clearly reports `model_boundary_crossed` and `local_model_call_made` for approved localhost fake-server tests.
- Exit code `0` remains reserved for completed advisory round persistence; policy rejections are explicit and bounded.

### M-CP-LIVE-4 — Human-gated local smoke procedure

Objective: document the manual local smoke procedure after fake-server tests and CLI activation rehearsal pass.

Files to create or modify in the future:

- `docs/runbooks/dars-live-panel-localhost-smoke.md`
- `docs/traceability/dars-critic-panel-runtime-traceability.md`
- `ralph.md`

Acceptance:

- Smoke uses an already-running localhost-only model endpoint supplied by the operator.
- No credential lookup is performed by Hisys.
- The command is copy-pasteable and writes only under a chosen runtime instance root.
- The runbook states stop conditions: non-loopback endpoint, missing approval packet, credential requirement, tool/search permission, mutation request, failed secret scan, or human uncertainty.

### M-CP-LIVE-5 — Remote/external DARS policy packet (deferred)

Objective: define a separate approval and security packet for remote APIs. This is deferred and not part of the first live panel implementation.

Exit criteria before any future remote API work:

- explicit human approval for a remote provider and endpoint;
- credential reference policy that never stores raw secrets;
- egress scope and audit policy;
- redaction rules for prompts, outputs, and error traces;
- separate RED tests proving default rejection of remote dispatch;
- decision packet before live execution.

## Validation plan for this Prepare increment

Run after writing this plan and bootstrap artifacts:

```bash
python3 - <<'PY'
from pathlib import Path
import json, yaml
root = Path('/home/cbchoi/workspaces/develop/repos/hisys')
for rel in [
  'docs/milestone-bootstrap/profile.yaml',
  'docs/milestone-bootstrap/tasks/milestone_tasks_v0.0.12.yaml',
  'docs/milestone-bootstrap/testcases/milestone_testcases_v0.0.12.yaml',
  'docs/milestone-bootstrap/hisys/request_v0.0.12.json',
]:
    path = root / rel
    assert path.exists(), rel
    if path.suffix in {'.yaml', '.yml'}:
        yaml.safe_load(path.read_text())
    if path.suffix == '.json':
        json.loads(path.read_text())
assert (root / 'docs/plans/dars-live-panel-configuration-implementation-tasks.md').exists()
print('live DARS panel Prepare structural check: pass')
PY

PYTHONPATH=src pytest   tests/unit/test_dars_runtime.py   tests/unit/test_dars_config.py   tests/unit/test_dars_dispatch.py   tests/unit/test_dars_critic_panel_cli.py   tests/unit/test_dars_critic_panel_adapters.py   tests/unit/test_dars_critic_panel_runtime.py   tests/unit/test_dars_critic_panel_tool_execution_runtime.py   tests/unit/test_dars_critic_panel_execution_graph_plan.py -q

python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

## Next safe task after this Prepare commit

If approved, start M-CP-LIVE-1 with the RED command above. Do not call a model or start a server during M-CP-LIVE-1. The first expected failure is a missing module for `hisys.agents.dars_panel_live_config`.
