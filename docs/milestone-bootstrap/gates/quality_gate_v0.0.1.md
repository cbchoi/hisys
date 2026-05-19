# Quality Gate v0.0.1 — Hisys Develop Bootstrap

## Gate result

Local advisory result: `RALPH_START_READY_WITH_CONTROLS`.

Formal Hisys result: `not_run_in_this_bootstrap`.

## Required controls

- Execute only in the local workspace `/home/cbchoi/workspaces/develop/repos/hisys`.
- Do not spawn tmux or background agents for this bootstrap package.
- Do not enable live DARS backends, remote DARS calls, browser/network connectors, credential resolution, publication, or deployment.
- Keep DARS outputs advisory-only; DARS does not approve, block, mutate, publish, or execute actions.
- Start implementation with the existing RED tests in `tests/unit/test_dars_critic_panel_runtime.py`.
- Stop before remote push unless the user explicitly authorizes synchronization after validation.

## Validation commands

Focused GREEN command for the next implementation increment:

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_runtime.py -q
```

Adjacent DARS regression after focused GREEN:

```bash
PYTHONPATH=src pytest tests/unit/test_dars_runtime.py tests/unit/test_dars_config.py tests/unit/test_dars_dispatch.py -q
```

General local safety checks:

```bash
git diff --check
PYTHONPATH=src python scripts/validate_traceability.py
```

## Stop conditions

Stop and report instead of continuing if:

- implementation would require a live external DARS/backend call;
- artifact writing would escape the runtime instance root or repo scope;
- a credential value would be read or persisted;
- tests fail for reasons unrelated to the current DARS panel increment;
- Git requires reset, force push, credential change, or destructive cleanup.
