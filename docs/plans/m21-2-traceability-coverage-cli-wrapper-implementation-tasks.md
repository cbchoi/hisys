# M21.2 Traceability Coverage CLI Wrapper Implementation Plan

> **For Hermes:** Use test-driven-development and writing-plans. Implement task-by-task; do not start production CLI wiring until the RED test in Task 1 is observed.

**Goal:** Add a controlled `hisys traceability-coverage` CLI wrapper around the M21.1 local advisory reporter.

**Architecture:** Reuse the existing M21.1 pure reporter and standalone repo-anchor loader. The CLI increment adds one argparse subcommand and one `_cmd_traceability_coverage` dispatcher in `src/hisys/cli/main.py`; it must not broaden the reporter into live parsing, external calls, raw source persistence, or approval authority.

**Tech Stack:** Python, argparse, Pydantic, pytest, existing Hisys CLI `main(argv)` tests.

**Context Packet:**
- Current HEAD: `6e5a1ce feat: add traceability coverage report`.
- Existing reporter: `src/hisys/operations/traceability_coverage.py`.
- Existing standalone wrapper/loader: `scripts/report_traceability_coverage.py`.
- CLI parser/dispatcher: `src/hisys/cli/main.py` (`_build_parser` near line 1693, `main` near line 2876).
- CLI tests: `tests/unit/test_domain_cli.py`.
- M21.1 plan: `docs/plans/m21-1-traceability-coverage-report-implementation-tasks.md`.
- M21.1 constraints: local-only, advisory-only, human-review-required, no external calls, no raw source text persistence, no mutation beyond runtime-boundary report writes.

**Boundary Record:** Local code/test/docs changes and local commit are allowed after validation. Remote push, live external access, credential resolution, publication, and any action-authority expansion are not authorized.
---

## Design choice

Recommended M21.2 approach: **thin CLI wrapper over the M21.1 script/report seam**.

Alternatives considered:

1. **Thin CLI wrapper** — lowest risk, reuses existing `load_repo_traceability_anchors`, writes the same runtime-boundary artifacts, easy focused CLI smoke. Chosen.
2. **Move loader into operations module first** — cleaner architecture, but broadens M21.2 beyond wrapper behavior and risks mixing refactor with CLI acceptance.
3. **Add richer SRS/SDD/IDD/STD scanning** — useful later, but it changes coverage semantics and should be a separate RED/GREEN increment after the CLI surface exists.

## Task 1: RED — pin CLI wrapper behavior

**Objective:** Add a failing CLI test that proves the `traceability-coverage` subcommand does not exist yet.

**Files:**
- Modify: `tests/unit/test_domain_cli.py`

**Step 1: Add failing test**

Append a focused test similar to:

```python
def test_traceability_coverage_cli_writes_runtime_boundary_report(tmp_path: Path, capsys) -> None:
    result = main([
        "traceability-coverage",
        "--instance",
        str(tmp_path),
        "--date",
        "20260520",
    ])

    captured = capsys.readouterr()
    assert result == 0
    assert "traceability coverage report" in captured.out
    assert "external_call_made: false" in captured.out
    json_path = tmp_path / "runtime-boundary" / "traceability-coverage" / "20260520" / "coverage-report.json"
    md_path = tmp_path / "runtime-boundary" / "traceability-coverage" / "20260520" / "coverage-report.md"
    assert json_path.exists()
    assert md_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema_id"] == "hisys.traceability.coverage.v1"
    assert data["advisory_only"] is True
    assert data["requires_human_review"] is True
    assert data["external_call_made"] is False
    assert data["mutation_performed"] is False
    assert data["raw_source_content_persisted"] is False
```

**Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py::test_traceability_coverage_cli_writes_runtime_boundary_report -q
```

Expected: fail because argparse rejects `traceability-coverage` as an unknown subcommand, or because the dispatcher does not yet handle it.

## Task 2: GREEN — add the smallest CLI wrapper

**Objective:** Add the subcommand and dispatcher without changing coverage semantics.

**Files:**
- Modify: `src/hisys/cli/main.py`

**Step 1: Import the existing reporter/loader**

Either import from `scripts.report_traceability_coverage` only for `load_repo_traceability_anchors`, or move that loader into a small operations helper if the import boundary becomes brittle. Prefer minimal wrapper for this increment.

**Step 2: Add parser entry**

Add near other runtime report commands:

```python
traceability_coverage = sub.add_parser(
    "traceability-coverage",
    help="write local advisory traceability coverage report artifacts",
)
traceability_coverage.add_argument("--instance", required=True, help="Hisys instance root")
traceability_coverage.add_argument("--date", required=True, help="YYYYMMDD report partition")
traceability_coverage.add_argument("--repo", type=Path, default=Path.cwd(), help="repo root to scan; defaults to cwd")
```

**Step 3: Add command function**

```python
def _cmd_traceability_coverage(*, instance_root: Path, yyyymmdd: str, repo_root: Path) -> int:
    anchors = load_repo_traceability_anchors(repo_root)
    report = build_traceability_coverage_report(anchors)
    refs = write_traceability_coverage_report(instance_root=instance_root, date=yyyymmdd, report=report)
    print(f"traceability coverage report: json={refs['json_ref']}")
    print(f"markdown: {refs['markdown_ref']}")
    print(f"coverage_ratio: {report.coverage_ratio}")
    print(f"unreferenced_requirements: {len(report.unreferenced_requirements)}")
    print(f"orphan_test_ids: {len(report.orphan_test_ids)}")
    print("external_call_made: false")
    print("allowed_actions: advisory_only")
    return 0
```

**Step 4: Add dispatcher branch**

```python
if args.command == "traceability-coverage":
    return _cmd_traceability_coverage(
        instance_root=Path(args.instance),
        yyyymmdd=args.date,
        repo_root=args.repo,
    )
```

**Step 5: Verify GREEN**

Run:

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py::test_traceability_coverage_cli_writes_runtime_boundary_report -q
PYTHONPATH=src pytest tests/unit/test_traceability_coverage.py tests/unit/test_domain_cli.py -q
```

Expected: focused CLI test passes; traceability coverage unit tests and full domain CLI file pass.

## Task 3: Traceability/docs and validation

**Objective:** Record M21.2 implementation evidence and keep governance boundaries explicit.

**Files:**
- Modify: `docs/traceability/README.md`
- Modify: `ralph.md`

**Validation commands:**

```bash
PYTHONPATH=src pytest tests/unit/test_traceability_coverage.py tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_cli.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit after validation:**

```bash
git add tests/unit/test_domain_cli.py src/hisys/cli/main.py docs/traceability/README.md ralph.md
git commit -m "feat: add traceability coverage CLI wrapper"
```

## Stop conditions

- Stop if the CLI wrapper requires live/external source access, credentials, process spawning, or publication authority.
- Stop if implementation requires changing M21.1 report semantics rather than merely wrapping them.
- Stop if validation reveals stale bootstrap/package assumptions requiring a new queue-refill decision.
