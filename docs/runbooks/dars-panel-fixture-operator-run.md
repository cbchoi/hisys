# DARS Panel Fixture Operator Run Runbook

Traceability: DARS-CLOSE-1, DARS-CLOSE-2 in
`docs/plans/dars-panel-completion-before-codebase-return.md`.

This runbook is the low-friction copy-pasteable operator path for the
fixture-local DARS critic panel. It runs entirely against the checked-in
golden fixture and never enables live model dispatch, remote providers,
credentials, browser/search/tool execution, mutation, publication, or
external networking.

## 1. Scope

Use this runbook when an operator wants to demonstrate or regress-check the
fixture-local advisory DARS panel without manually assembling candidate,
evidence, rubric, and panel-config files. The procedure runs the same
``run-dars-panel --write-report`` code path that
`test_run_dars_panel_cli_golden_fixture_writes_stable_operator_report` pins
as the golden contract.

This is the **fixture-local advisory** path only:

- no live external provider call;
- no remote model dispatch;
- no credential lookup;
- no browser/search/tool execution by critics;
- no mutation, publication, deployment, or push beyond the operator-selected
  instance root.

A human-gated localhost rehearsal path is documented separately in
`docs/runbooks/dars-live-panel-localhost-smoke.md` and is **not** part of
this runbook.

## 2. Prerequisites

Confirm before running:

1. The repository is checked out at the desired branch (default for this
   line: `dars`).
2. Python and pytest are available in the shell.
3. An operator-selected instance root is available as a temporary or
   sandbox directory; do not use a production or publication target.

## 3. Copy-pasteable fixture-local run

Set a shell variable for the instance root, then run the golden wrapper:

```bash
export HISYS_DARS_PANEL_GOLDEN_INSTANCE="$(mktemp -d -t hisys-dars-panel-golden-XXXX)"

PYTHONPATH=src:. python3 -m hisys.cli.main run-dars-panel-golden \
  --instance "$HISYS_DARS_PANEL_GOLDEN_INSTANCE" \
  --date 20260521 \
  --request-id REQ-DARS-GOLDEN-UX \
  --format json
```

Expected output (formatted JSON) includes:

```json
{
  "request_id": "REQ-DARS-GOLDEN-UX",
  "panel_id": "PANEL-DARS-GOLDEN-BASIC",
  "execution_mode": "serial",
  "task_statuses": {"TASK-REQ-DARS-GOLDEN-UX-00-logical-devil": "completed"},
  "report_ref": "reports/run-summaries/20260521/dars-panel-round-report.json"
}
```

The wrapper writes:

- `data/dars-panel-fixtures/20260521/candidate-001.json`
- `data/dars-panel-fixtures/20260521/evidence-001.json`
- `data/dars-panel-fixtures/20260521/rubric-001.md`
- `panel-config.json`
- the operator report under `reports/run-summaries/20260521/dars-panel-round-report.{json,md}`
- the critique/synthesis/round-trace/execution-boundary refs under the
  instance root

All output is advisory-only: `advisory_only`, `requires_human_review`,
`external_call_made=false`, `mutation_performed=false`,
`publication_performed=false`,
`live_external_action_authorized=false`.

## 4. Manual long-form run

When more granular control is needed, run the underlying
`run-dars-panel --write-report` command directly. The checked-in golden
fixture lives at `tests/fixtures/dars_panel/golden_basic/`. The
`run-dars-panel-golden` wrapper is just convenience; copying the fixture
files manually into `<instance>/data/dars-panel-fixtures/<date>/` and
running `run-dars-panel ... --write-report ...` produces an equivalent
report.

## 5. Stop conditions

Stop and report instead of proceeding when:

- the wrapper reports a missing checked-in golden fixture;
- the operator-selected instance root is a production or publication target;
- the run is being asked to use a remote endpoint, credential, browser,
  search tool, deployment surface, mutation authority, or live provider;
- the operator wants to claim live external provider dispatch has been
  smoked — this runbook does **not** cover that claim.

For live external provider execution, open a separate operator-approved
governed line. The DARS panel productization closure boundary is
"local/fixture/localhost-controlled advisory complete"; live provider
execution remains unimplemented/unproven unless that separate line is
opened.

## 6. Cleanup

The instance root created by `mktemp -d` may be removed once the operator
has captured the advisory report content they need:

```bash
rm -rf "$HISYS_DARS_PANEL_GOLDEN_INSTANCE"
unset HISYS_DARS_PANEL_GOLDEN_INSTANCE
```

Do not commit the temporary instance root or its artifacts to the
repository.
