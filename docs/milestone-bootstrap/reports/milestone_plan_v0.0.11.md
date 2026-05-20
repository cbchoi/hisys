# Milestone Plan v0.0.11 — M21.5 Regression Benchmark Fixtures Prepare

## Scope

Prepare/document-RED for M21.5 after M21.4 pure checker and CLI wrapper completed. This package plans a local-only regression benchmark fixture surface and does not add production code or fixture files yet.

## Baseline

- Target workspace: `/home/cbchoi/workspaces/develop/repos/hisys`
- Branch: `dars`
- Baseline HEAD: `d992905 feat: add codebase-map-freshness-review cli wrapper`
- Completed M21 through: M21.4-CLI

## Next safe task

`MB-M21-5-RED` — write and observe the failing benchmark operation test:

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_regression_benchmarks.py::test_codebase_regression_benchmarks_report_expected_outcomes -q
```

Expected failure: `ModuleNotFoundError` for `hisys.operations.codebase_regression_benchmarks`.

## Boundary

Local docs/control preparation only. No production code, no fixture repository creation, no remote push, no live clone/network access, no credential lookup, no raw source archival, and no CLI surface are authorized by this package.
