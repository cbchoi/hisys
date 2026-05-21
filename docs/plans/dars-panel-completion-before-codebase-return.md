# DARS Panel Completion Before Codebase Return Implementation Plan

> **For Hermes/Ralph:** Complete the DARS panel productization closure queue before returning to the M21.6 codebase-analysis Prepare queue. Execute each implementation row with strict RED--GREEN--validate--commit discipline.

**Goal:** Finish the local/fixture/localhost-controlled DARS critic panel productization line so the branch can return to `MB-CODEBASE-M21-6-PREP` without leaving DARS panel UX/reporting/readiness gaps.

**Architecture:** Treat the DARS panel as complete only for local, fixture, localhost-controlled, advisory-only use. Closure consists of a golden scenario fixture, an operator UX wrapper/runbook, a readiness/completion status surface, and a final closure gate that explicitly returns the Ralph queue to M21.6. Remote provider execution remains outside this completion line unless a separate operator-approved live external dispatch plan is created.

**Tech Stack:** Python 3.11, argparse in `src/hisys/cli/main.py`, pytest, local runtime artifacts under a selected Hisys instance root, Markdown/JSON docs and traceability.

**Context Packet:**
- Current branch/head at planning: `dars` / `5ea9620 feat: add dars panel operator report`.
- Completed DARS surfaces: fixture panel runtime, external fail-closed registry, local activation packet, fake localhost adapter, activation-gated CLI rehearsal, local smoke runbook, remote subscription policy/injected-executor harness with fake executor only, and operator report writer.
- Key files: `src/hisys/cli/main.py`, `src/hisys/agents/dars_panel.py`, `src/hisys/agents/dars_panel_live_config.py`, `src/hisys/agents/dars_panel_live_adapter.py`, `src/hisys/agents/dars_remote_subscription_dispatch.py`, `tests/unit/test_dars_critic_panel_cli.py`, `docs/traceability/dars-critic-panel-runtime-traceability.md`, `ralph.md`.
- Omitted context: old M19 codebase-analysis tail in `ralph.md` and raw full source listings; retrieve specific files only when executing a row.

**Boundary Record:**
- Authorized now: local docs/control planning, local fixture/test data, local pytest execution, local runtime report artifacts under explicit temp/fixture instance roots, traceability updates, local commits, normal push to existing `origin/dars` after validation.
- Not authorized in this plan: real remote provider calls, credential lookup, raw secret capture, browser/search/tool execution by critics, publication/deployment, schema/data migrations, force push, new remote configuration, or claims that live provider execution has been smoked.
- Completion claim boundary: `DARS panel complete` means **local/fixture/localhost-controlled advisory panel complete**, not live external provider dispatch complete.

---

## Decision table

| Candidate | Scope | Benefit | Risk | Decision |
|---|---|---|---|---|
| Return immediately to M21.6 | Stop after operator report | Fastest return | Leaves DARS panel with no golden end-to-end fixture or closure gate | Reject for now |
| Finish local productization closure | Golden fixture + UX wrapper + readiness status + closure gate | Makes DARS panel resumable and demonstrable before returning | Small additional local-only work | Select |
| Add live external/provider execution | Real provider smoke | Would prove live remote dispatch | Requires credentials, operator approval, egress policy, live-smoke record | Defer to separate governed line |

## Completion criteria

The DARS panel line is ready to close when all are true:

1. A checked-in golden scenario fixture can run `hisys run-dars-panel --write-report` in fixture mode and assert JSON/Markdown report contents.
2. An operator-facing UX command or runbook gives one copy-pasteable local-safe path for fixture mode and one human-gated localhost rehearsal path.
3. A readiness/completion status command or static report distinguishes:
   - fixture/local panel complete;
   - localhost rehearsal path available but human-gated;
   - remote subscription dispatch harness present only through injected executor/fake tests;
   - live provider execution not proven.
4. Traceability and `ralph.md` record the closure boundary and next queue pointer back to `MB-CODEBASE-M21-6-PREP`.
5. Focused DARS tests, full suite, traceability, secret scan, and diff check pass.

---

## Task 1 — Golden fixture scenario for operator report

**Objective:** Add a deterministic golden scenario that proves a fixture-local DARS panel round produces the advisory operator report without live actions.

**Files:**
- Create: `tests/fixtures/dars_panel/golden_basic/candidate-001.json`
- Create: `tests/fixtures/dars_panel/golden_basic/evidence-001.json`
- Create: `tests/fixtures/dars_panel/golden_basic/rubric-001.md`
- Create: `tests/fixtures/dars_panel/golden_basic/panel-config.json`
- Modify/Test: `tests/unit/test_dars_critic_panel_cli.py`

**RED test:**

Add a test named:

```python
def test_run_dars_panel_cli_golden_fixture_writes_stable_operator_report(tmp_path: Path, capsys):
    ...
```

The test should copy or reference the checked-in golden fixture, run:

```text
hisys run-dars-panel --instance <tmp_path> --date 20260521 --request-id REQ-DARS-GOLDEN-BASIC --panel-config <fixture>/panel-config.json --candidate-ref data/dars-panel-fixtures/20260521/candidate-001.json --evidence-ref data/dars-panel-fixtures/20260521/evidence-001.json --write-report --format json
```

Expected RED before fixture/implementation wiring:

```text
FileNotFoundError or assertion failure for missing checked-in golden fixture/report contract
```

**GREEN implementation:**

Create tiny fixture files and assert:

- `payload["report_ref"] == "reports/run-summaries/20260521/dars-panel-round-report.json"`;
- report `schema_id == "hisys.dars_panel.round_report"`;
- report has one completed task;
- `advisory_only=true`, `requires_human_review=true`, `external_call_made=false`, `mutation_performed=false`, `publication_performed=false`, `live_external_action_authorized=false`;
- Markdown companion includes the request id and safety fields.

**Validation:**

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_critic_panel_cli.py::test_run_dars_panel_cli_golden_fixture_writes_stable_operator_report -q
PYTHONPATH=src:. pytest tests/unit/test_dars_critic_panel_cli.py -q
```

**Commit:**

```bash
git add tests/fixtures/dars_panel/golden_basic tests/unit/test_dars_critic_panel_cli.py
git commit -m "test: add dars panel golden report fixture"
```

---

## Task 2 — Operator UX wrapper for fixture-local panel run

**Objective:** Provide a low-friction operator command that runs the golden fixture path without requiring the user to assemble all flags manually.

**Files:**
- Modify: `src/hisys/cli/main.py`
- Modify/Test: `tests/unit/test_dars_critic_panel_cli.py`
- Create or modify docs: `docs/runbooks/dars-panel-fixture-operator-run.md`

**RED test:**

Add a test named:

```python
def test_dars_panel_golden_run_cli_uses_fixture_and_writes_report(tmp_path: Path, capsys):
    ...
```

Proposed CLI surface:

```bash
hisys run-dars-panel-golden --instance <tmp_path> --date 20260521 --request-id REQ-DARS-GOLDEN-UX --format json
```

Expected RED:

```text
argparse rejects unknown command run-dars-panel-golden
```

**GREEN implementation:**

Add a narrow wrapper that:

- resolves checked-in golden fixture paths;
- copies only necessary fixture files into the selected instance root or uses instance-relative fixture refs in a deterministic way;
- calls the same underlying `_cmd_run_dars_panel(..., write_report=True)` path;
- does not expose local model endpoint or activation flags;
- prints the same bounded JSON/text summary with `report_ref`.

**Validation:**

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_critic_panel_cli.py::test_dars_panel_golden_run_cli_uses_fixture_and_writes_report -q
PYTHONPATH=src:. pytest tests/unit/test_dars_critic_panel_cli.py -q
python3 scripts/scan_secrets.py
```

**Commit:**

```bash
git add src/hisys/cli/main.py tests/unit/test_dars_critic_panel_cli.py docs/runbooks/dars-panel-fixture-operator-run.md
git commit -m "feat: add dars panel golden run wrapper"
```

---

## Task 3 — DARS panel completion/readiness status surface

**Objective:** Add a local status surface that reports which DARS panel modes are complete and which remain gated or unproven.

**Files:**
- Modify: `src/hisys/cli/main.py` or create `src/hisys/operations/dars_panel_readiness.py`
- Create/Test: `tests/unit/test_dars_panel_readiness.py` or extend `tests/unit/test_dars_critic_panel_cli.py`
- Modify: `docs/traceability/dars-critic-panel-runtime-traceability.md`

**RED test:**

Add a test named:

```python
def test_dars_panel_readiness_status_distinguishes_local_and_live_boundaries(tmp_path: Path, capsys):
    ...
```

Proposed CLI:

```bash
hisys dars-panel-readiness --instance <tmp_path> --date 20260521 --format json
```

Expected RED:

```text
argparse rejects unknown command dars-panel-readiness
```

**GREEN implementation:**

The JSON output should include:

```json
{
  "schema_id": "hisys.dars_panel.readiness_status",
  "fixture_panel_complete": true,
  "operator_report_available": true,
  "golden_fixture_available": true,
  "localhost_rehearsal_available": true,
  "localhost_rehearsal_human_gated": true,
  "remote_subscription_policy_exists": true,
  "remote_subscription_injected_executor_harness_available": true,
  "live_provider_execution_smoked": false,
  "completion_claim": "local_fixture_localhost_controlled_advisory_complete",
  "next_queue_after_closure": "MB-CODEBASE-M21-6-PREP"
}
```

**Validation:**

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_panel_readiness.py -q
PYTHONPATH=src:. pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_remote_subscription_dispatch.py -q
```

**Commit:**

```bash
git add src/hisys/cli/main.py src/hisys/operations/dars_panel_readiness.py tests/unit/test_dars_panel_readiness.py docs/traceability/dars-critic-panel-runtime-traceability.md
git commit -m "feat: add dars panel readiness status"
```

---

## Task 4 — Closure gate and queue return to M21.6

**Objective:** Close the DARS panel productization line and set the next Ralph queue target back to M21.6 codebase-analysis Prepare.

**Files:**
- Modify: `ralph.md`
- Modify: `docs/milestone-bootstrap/profile.yaml` if the current bootstrap status needs to name the returned next task
- Modify: `tests/unit/test_governance_docs_current_state.py` if profile/current-state expectations are changed
- Modify: `docs/traceability/dars-critic-panel-runtime-traceability.md`

**RED/control check:**

Run a governance/current-state check before editing:

```bash
PYTHONPATH=src:. pytest tests/unit/test_governance_docs_current_state.py::test_governance_profile_and_ralph_checkpoint_match_current_head -q
```

If it fails due to stale head/profile pointers, treat that as the RED for current-state sync.

**GREEN docs/control update:**

Record in `ralph.md`:

- completed DARS closure tasks and commit hashes;
- exact completion claim boundary: local/fixture/localhost-controlled advisory complete;
- live provider execution still not proven;
- next safe task restored to `MB-CODEBASE-M21-6-PREP`;
- stop condition: DARS line closed; resume codebase-analysis queue on next `go`.

Update `docs/milestone-bootstrap/profile.yaml` only if needed to preserve current-state tests. Do not invent a new bootstrap package unless governance tests or current docs require it.

**Validation:**

```bash
PYTHONPATH=src:. pytest tests/unit/test_governance_docs_current_state.py -q
PYTHONPATH=src:. pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_panel_readiness.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
PYTHONPATH=src:. pytest -q
```

**Commit and push:**

```bash
git add ralph.md docs/milestone-bootstrap/profile.yaml tests/unit/test_governance_docs_current_state.py docs/traceability/dars-critic-panel-runtime-traceability.md
git commit -m "docs: close dars panel productization queue"
git push origin dars
```

---

## Final handoff after Task 4

Report:

```text
DARS panel completion status: local/fixture/localhost-controlled advisory complete.
Live external provider dispatch: not implemented/smoked; deferred to separate approval.
Next queue: MB-CODEBASE-M21-6-PREP.
Branch: dars synced with origin/dars.
Validation: focused DARS, readiness, governance, full suite, traceability, secret scan, diff-check all green.
```

Then resume the original queue with `docs/plans/m21-6-change-impact-analyzer-implementation-tasks.md` as the next Prepare artifact.
