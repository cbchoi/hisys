# Milestone Plan v0.0.7 — Current-Session Bootstrap Refresh for M20.3

## Objective

Refresh the milestone-bootstrap package in the current Hermes session, with omitted `/bootstrap` arguments inferred from this Discord Hisys thread. The target is the existing Hisys develop repository and the current safe next task is M20.3 Task 1 RED.

## Current baseline

- Branch: `dars`
- Baseline HEAD: `a6d310b docs: prepare codebase bundle enrichment increment`
- Working tree before bootstrap writes: clean
- Existing M20.3 Prepare plan: `docs/plans/m20-codebase-domain-artifact-bridge-m20-3-implementation-tasks.md`
- Prior bootstrap: `v0.0.6`, committed in `a6d310b`

## Next safe task

`MB-M20-3-T001`: write and observe the RED test for complete local bundle enrichment:

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_domain_artifact_bridge.py::test_codebase_domain_result_enriches_complete_local_bundle -q
```

Expected initial RED: missing result-enrichment seam/helper or assertion failure because no `codebase_analysis_bundle` evidence package exists yet.

## Boundaries

- Current bootstrap is docs/readiness-only.
- No production code or RED tests are written in this bootstrap.
- No tmux or background agent was spawned.
- No remote push, live external action, credential use, browser/network/model call, publication, destructive Git, or action authorization.
- M20.3 implementation must load local artifacts only through `load_codebase_review_bundle` / `resolve_instance_runtime_ref`.
