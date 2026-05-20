# Milestone Plan v0.0.12 — DARS live panel configuration Prepare

## Objective

Prepare the implementation path for a controlled live DARS panel that crosses only an approved localhost model boundary at first, using fake-server tests before any real local model smoke.

## Scope

- Document activation packet requirements.
- Define RED tests for live panel config, local model panel adapter bridge, CLI activation rehearsal, and runbook smoke procedure.
- Preserve advisory-only, human-review, no-mutation, no-publication invariants.
- Defer remote/external DARS APIs to a separate policy packet.

## Out of scope

- Production code.
- Test file creation.
- Live model calls.
- Credential lookup.
- Remote API dispatch.
- Runtime config mutation outside docs.
- Remote push.

## Next safe RED

```bash
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_live_config.py::test_live_panel_activation_requires_human_approval_ref -q
```

Expected RED: `ModuleNotFoundError: No module named 'hisys.agents.dars_panel_live_config'`.
