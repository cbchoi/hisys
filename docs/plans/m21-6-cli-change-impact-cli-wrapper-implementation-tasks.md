# Milestone M21.6-CLI — Change-Impact CLI Wrapper Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development`. This plan is the document-RED/Prepare artifact for the M21.6-CLI thin CLI wrapper that follows the M21.6 GREEN commit (`7c4d5d0 feat: add change-impact analyzer`). The pure analyzer is already stable; M21.6-CLI only exposes it through `hisys change-impact`.

**Goal:** Add a thin `hisys change-impact --instance <root> --date <YYYYMMDD> [--repo <repo>] [--changed-ref <relative-ref>]* [--current-head-short <hash>]` CLI subcommand that wraps the M21.6 pure analyzer/writer. The CLI must not change the impact-report semantics, must not expand the impact vocabulary, must not introduce live access, credentials, repair, deletion, or approval authority, must not shell out to `git diff` / `git log` / `subprocess`, and must remain advisory-only.

**Architecture:** Reuse the existing M21.6 surfaces:

- `src/hisys/operations/change_impact.ChangeImpactRequest`
- `src/hisys/operations/change_impact.build_change_impact_report`
- `src/hisys/operations/change_impact.write_change_impact_report`
- `src/hisys/operations/traceability_coverage.load_repo_traceability_anchors` for the anchor set (M21.1 bounded loader; reads only IDs/refs, no source bodies).

The CLI increment adds one argparse subcommand definition and one `_cmd_change_impact` dispatcher in `src/hisys/cli/main.py`. No new dependency. The CLI never calls `date.today()`, never reads `.git/`, never shells out, and never opens changed-file bodies. Changed refs come from repeatable `--changed-ref` flags only; a `--from-git-diff` mode for local diff capture is intentionally deferred to a separate M21.6-DIFFCAP increment.

**Tech Stack:** Python, argparse, pathlib, pytest, existing Hisys CLI `main(argv)` tests.

**Context Packet:**
- Current HEAD: `7c4d5d0 feat: add change-impact analyzer`.
- Pure analyzer/writer: `src/hisys/operations/change_impact.py`.
- CLI parser/dispatcher: `src/hisys/cli/main.py` (nearest precedents: `_cmd_codebase_map_freshness_review` + `codebase-map-freshness-review` subparser from M21.4-CLI; `_cmd_traceability_coverage` + `traceability-coverage` subparser from M21.2).
- CLI tests: `tests/unit/test_domain_cli.py` (M21.4-CLI and M21.2 tests are nearest shape).
- Anchor loader: `src/hisys/operations/traceability_coverage.load_repo_traceability_anchors`.

**Boundary Record:** Local code/test/docs changes and local commit are allowed after validation. Remote push, live external access, credential resolution, publication, repair/deletion of partitions, calls to system clock, `.git/` reads, and any `git diff` / `git log` / `subprocess` invocation are not authorized. The CLI never opens changed-file bodies, never raises the exit code on impact counts (advisory-only), and never adds approval/safe-to-deploy/readiness language.

---

## Accepted decisions

1. **Thin wrapper:** The CLI calls the existing pure functions without reshaping the report.
2. **Caller-supplied refs only:** Changed refs come from repeatable `--changed-ref` flags. A future `--from-git-diff` mode is intentionally deferred; the CLI does not run `git diff` in this increment.
3. **Anchor source:** Anchors are loaded via `load_repo_traceability_anchors(repo_root)` with `--repo` defaulting to the current working directory. The loader reads only IDs and relative refs; no source bodies are persisted.
4. **`--current-head-short` is optional and recorded verbatim.** The CLI never derives it from `.git/`; the caller supplies it.
5. **No impact-vocabulary expansion:** The CLI does not add new impact partition kinds.
6. **Print bounded summary lines:** `change-impact report: json=<ref>`, `markdown: <ref>`, then `changed_ref_count: <n>`, `impacted_requirements: <n>`, `impacted_tests: <n>`, `impacted_design_or_interface_refs: <n>`, `impacted_runtime_boundary_refs: <n>`, `unmapped_changed_refs: <n>`, `unsafe_changed_refs: <n>`, `external_call_made: false`, `allowed_actions: advisory_only`, mirroring the M21.3-CLI/M21.4-CLI shape.
7. **Exit code:** Always `0` for a successfully written report. Counts (including unsafe-ref count) never raise the exit code; raising on issues requires a separate RED.
8. **Traceability required:** Update `docs/traceability/README.md` with an `M21.6-CLI` row and append a `ralph.md` Reflection Log entry plus Resume checkpoint.

---

## Task 0: Reconstruct baseline before editing

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_change_impact.py tests/unit/test_codebase_regression_benchmarks.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_cli.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:** branch `dars`, HEAD at or after `7c4d5d0 feat: add change-impact analyzer`; extended focused gate 51 passes; DARS focused gate 50 passes; traceability validator OK; secret scan hit_count=0; `git diff --check` clean.

---

## Task 1: RED — CLI smoke test

**Files:**
- Modify: `tests/unit/test_domain_cli.py`

**Test sketch:**

```python
def test_change_impact_cli_writes_report(tmp_path: Path, capsys) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    # Use the live repo root so the CLI's bounded anchor loader finds real
    # HISYS-* IDs in docs/traceability/README.md and src/hisys/schemas/*.py.
    repo_root = Path(__file__).resolve().parents[2]

    result = main(
        [
            "change-impact",
            "--instance",
            str(instance_root),
            "--date",
            "20260521",
            "--repo",
            str(repo_root),
            "--changed-ref",
            "docs/traceability/README.md",
            "--changed-ref",
            "src/hisys/agents/unrelated_helper.py",
            "--changed-ref",
            "runtime-boundary/codebase-analysis/20260520/REQ-X/inventory.json",
            "--changed-ref",
            "/etc/passwd",
            "--current-head-short",
            "7c4d5d0",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "change-impact report" in captured.out
    assert "external_call_made: false" in captured.out
    assert "allowed_actions: advisory_only" in captured.out

    json_path = (
        instance_root
        / "runtime-boundary"
        / "change-impact"
        / "20260521"
        / "impact-report.json"
    )
    md_path = (
        instance_root
        / "runtime-boundary"
        / "change-impact"
        / "20260521"
        / "impact-report.md"
    )
    assert json_path.exists()
    assert md_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema_id"] == "hisys.change_impact.v1"
    assert data["advisory_only"] is True
    assert data["external_call_made"] is False
    assert data["mutation_performed"] is False
    assert data["raw_source_content_persisted"] is False
    assert data["current_head_short"] == "7c4d5d0"
    assert data["changed_ref_count"] == 4
    assert "/etc/passwd" in data["unsafe_changed_refs"]
    assert (
        "runtime-boundary/codebase-analysis/20260520/REQ-X/inventory.json"
        in data["impacted_runtime_boundary_refs"]
    )
    assert (
        "docs/traceability/README.md"
        in data["impacted_design_or_interface_refs"]
    )
    assert "src/hisys/agents/unrelated_helper.py" in data["unmapped_changed_refs"]
```

**Verify RED:**

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py::test_change_impact_cli_writes_report -q
```

**Expected RED:** argparse rejects `change-impact` with `SystemExit: 2`.

---

## Task 2: GREEN — add the smallest CLI wrapper

**Files:**
- Modify: `src/hisys/cli/main.py`

**Step 1: Add imports.** Next to the existing `from ..operations.codebase_map_freshness import ...` block:

```python
from ..operations.change_impact import (
    ChangeImpactRequest,
    build_change_impact_report,
    write_change_impact_report,
)
from ..operations.traceability_coverage import load_repo_traceability_anchors
```

(If `load_repo_traceability_anchors` is already imported by the M21.2 `traceability-coverage` block, reuse the existing import line.)

**Step 2: Add parser entry next to the `codebase_map_freshness_review` block:**

```python
change_impact = sub.add_parser(
    "change-impact",
    help="write local advisory change-impact report artifacts",
)
change_impact.add_argument("--instance", required=True, help="Hisys instance root")
change_impact.add_argument("--date", required=True, help="YYYYMMDD report partition")
change_impact.add_argument(
    "--repo",
    default=None,
    help="optional repo root for traceability anchor loading (defaults to CWD)",
)
change_impact.add_argument(
    "--changed-ref",
    action="append",
    default=[],
    help="repeatable relative changed file ref (caller-supplied)",
)
change_impact.add_argument(
    "--current-head-short",
    default=None,
    help="optional caller-supplied git HEAD short hash recorded verbatim",
)
```

**Step 3: Add command function next to `_cmd_codebase_map_freshness_review`:**

```python
def _cmd_change_impact(
    *,
    instance_root: Path,
    yyyymmdd: str,
    repo_root: Path,
    changed_refs: tuple[str, ...],
    current_head_short: str | None,
) -> int:
    """Write a local advisory change-impact report via the CLI."""

    anchors = load_repo_traceability_anchors(repo_root=repo_root)
    request = ChangeImpactRequest(
        instance_root=instance_root,
        repo_root=repo_root,
        changed_file_refs=changed_refs,
        current_head_short=current_head_short,
    )
    report = build_change_impact_report(request=request, anchors=anchors)
    written = write_change_impact_report(
        instance_root=instance_root, date=yyyymmdd, report=report
    )
    print(f"change-impact report: json={written['json_ref']}")
    print(f"markdown: {written['markdown_ref']}")
    print(f"changed_ref_count: {report.changed_ref_count}")
    print(f"impacted_requirements: {len(report.impacted_requirement_ids)}")
    print(f"impacted_tests: {len(report.impacted_test_id_or_refs)}")
    print(
        "impacted_design_or_interface_refs: "
        f"{len(report.impacted_design_or_interface_refs)}"
    )
    print(
        "impacted_runtime_boundary_refs: "
        f"{len(report.impacted_runtime_boundary_refs)}"
    )
    print(f"unmapped_changed_refs: {len(report.unmapped_changed_refs)}")
    print(f"unsafe_changed_refs: {len(report.unsafe_changed_refs)}")
    print("external_call_made: false")
    print("allowed_actions: advisory_only")
    return 0
```

Note: the actual signature of `load_repo_traceability_anchors(repo_root: Path)` is `load_repo_traceability_anchors(repo_root)` — pass `repo_root` positionally if the existing M21.2 call site uses that style.

**Step 4: Add dispatcher branch next to the `codebase-map-freshness-review` branch:**

```python
if args.command == "change-impact":
    repo_root = Path(args.repo) if args.repo else Path.cwd()
    return _cmd_change_impact(
        instance_root=Path(args.instance),
        yyyymmdd=args.date,
        repo_root=repo_root,
        changed_refs=tuple(args.changed_ref),
        current_head_short=args.current_head_short,
    )
```

**Verify GREEN:**

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py::test_change_impact_cli_writes_report -q
PYTHONPATH=src pytest tests/unit/test_change_impact.py tests/unit/test_domain_cli.py -q
```

---

## Task 3: Traceability/docs and validation

**Files:**
- Modify: `docs/traceability/README.md` — prepend an `M21.6-CLI` row linking the plan, CLI/dispatcher, pure module, and CLI test with explicit advisory-only/no-mutation/no-external-call/no-git-shellout invariants.
- Modify: `ralph.md` — append a Reflection Log entry following the existing M21.x-CLI format with Resume checkpoint.

**Validation:**

```bash
PYTHONPATH=src pytest tests/unit/test_change_impact.py tests/unit/test_codebase_regression_benchmarks.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_cli.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit:**

```bash
git add tests/unit/test_domain_cli.py src/hisys/cli/main.py docs/traceability/README.md ralph.md
git commit -m "feat: add change-impact cli wrapper"
```

---

## Stop conditions

- Stop if the CLI wrapper requires live/external access, credential resolution, process spawning, or publication authority.
- Stop if implementation requires changing M21.6 report semantics rather than merely wrapping them.
- Stop if implementation would call `date.today()`, read `.git/`, or shell out to `git diff` / `git log` / `subprocess` inside the CLI (callers must supply changed refs and HEAD short hash).
- Stop if validation reveals stale bootstrap/package assumptions requiring a new queue-refill decision.

## Out of scope for M21.6-CLI (deferred)

- `--from-git-diff` or `--scan` modes that capture changed refs from local Git state (planned separately as M21.6-DIFFCAP).
- Raising the CLI exit code on impact counts or unsafe-ref counts (planned separately under a dedicated RED).
- Cross-branch / base-branch comparison.
- Symbol-level impact (function/class) granularity.

## Next executable action

After this Prepare plan is committed, run the RED command:

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py::test_change_impact_cli_writes_report -q
```

Expected failure: `SystemExit: 2` from argparse rejecting `change-impact` as an unknown subcommand.
