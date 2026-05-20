# Milestone M21.4-CLI — Codebase Map Freshness Review CLI Wrapper Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development`. This plan is the document-RED/Prepare artifact for the M21.4-CLI thin CLI wrapper that follows the M21.4 GREEN commit (`1cb2857 feat: add codebase map freshness review`). The pure checker is already stable; M21.4-CLI only exposes it through `hisys codebase-map-freshness-review`.

**Goal:** Add a thin `hisys codebase-map-freshness-review --instance <root> --date <YYYYMMDD> --current-date <YYYY-MM-DD> --max-age-days <int> [--current-head-short <hash>]` CLI subcommand that wraps the M21.4 pure checker/writer. The CLI must not change the freshness-report semantics, must not expand the partition vocabulary, must not introduce live access, credentials, repair, deletion, or approval authority, and must remain advisory-only.

**Architecture:** Reuse the existing M21.4 surfaces:

- `src/hisys/operations/codebase_map_freshness.build_codebase_map_freshness_report`
- `src/hisys/operations/codebase_map_freshness.write_codebase_map_freshness_report`

The CLI increment adds one argparse subcommand definition and one `_cmd_codebase_map_freshness_review` dispatcher in `src/hisys/cli/main.py`. No new dependency. The CLI never calls `date.today()` — `--current-date` is required and `date.fromisoformat` parses it. `--current-head-short` is optional and recorded verbatim. A future `--scan` mode for multi-date drift is intentionally deferred.

**Tech Stack:** Python, argparse, datetime.date, pytest, existing Hisys CLI `main(argv)` tests.

**Context Packet:**
- Current HEAD: `1cb2857 feat: add codebase map freshness review`.
- Pure checker/writer: `src/hisys/operations/codebase_map_freshness.py`.
- CLI parser/dispatcher: `src/hisys/cli/main.py` (`runtime-boundary-check` block from M21.3-CLI as nearest precedent).
- M21.3-CLI precedent: `_cmd_runtime_boundary_check` and `runtime_boundary_check` subparser.
- CLI tests: `tests/unit/test_domain_cli.py` (M21.3-CLI test at top of file).

**Boundary Record:** Local code/test/docs changes and local commit are allowed after validation. Remote push, live external access, credential resolution, publication, repair/deletion of partitions, calls to system clock, and `.git/` reads are not authorized. The CLI never opens artifact bodies, never raises the exit code on stale/incomplete partition counts (advisory-only), and never adds approval/safe-to-deploy/readiness language.

---

## Accepted decisions

1. **Thin wrapper:** The CLI calls the existing pure functions without reshaping the report.
2. **Caller-supplied date:** `--current-date YYYY-MM-DD` is required so output is deterministic. Parsing uses `date.fromisoformat`; bad input raises argparse error.
3. **`max_age_days` is required:** No default — callers must declare freshness policy explicitly.
4. **No `--scan` mode in this increment:** Multi-date drift across instances is deferred.
5. **No partition-vocabulary expansion:** The CLI does not add new partition kinds.
6. **Print bounded summary lines:** `codebase map freshness report: json=<ref>`, `markdown: <ref>`, then `fresh_partitions: <n>` / `stale_partitions: <n>` / `incomplete_partitions: <n>` / `unsafe_partitions: <n>` / `external_call_made: false` / `allowed_actions: advisory_only`, mirroring the M21.3-CLI shape.
7. **Exit code:** Always `0` for a successfully written report. Counts never raise the exit code.
8. **Traceability required:** Update `docs/traceability/README.md` with an `M21.4-CLI` row and append a `ralph.md` Reflection Log entry plus Resume checkpoint.

---

## Task 0: Reconstruct baseline before editing

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_cli.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:** branch `dars`, HEAD at or after `1cb2857 feat: add codebase map freshness review`; extended focused gate (≥43) passes; DARS focused gate 48 passes; traceability validator OK; secret scan hit_count=0; `git diff --check` clean.

---

## Task 1: RED — CLI smoke test

**Files:**
- Modify: `tests/unit/test_domain_cli.py`

**Test sketch:**

```python
def test_codebase_map_freshness_review_cli_writes_report(tmp_path: Path, capsys) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    partition_dir = (
        instance_root
        / "runtime-boundary"
        / "codebase-analysis"
        / "20260518"
        / "REQ-CLI-FRESH"
    )
    partition_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "inventory.json",
        "symbol-index.json",
        "scope-map.json",
        "risk-scan.json",
    ):
        (partition_dir / name).write_text("{}\n", encoding="utf-8")

    result = main(
        [
            "codebase-map-freshness-review",
            "--instance",
            str(instance_root),
            "--date",
            "20260520",
            "--current-date",
            "2026-05-20",
            "--max-age-days",
            "30",
            "--current-head-short",
            "1cb2857",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "codebase map freshness report" in captured.out
    assert "external_call_made: false" in captured.out

    json_path = (
        instance_root
        / "runtime-boundary"
        / "codebase-map-freshness"
        / "20260520"
        / "freshness-report.json"
    )
    md_path = (
        instance_root
        / "runtime-boundary"
        / "codebase-map-freshness"
        / "20260520"
        / "freshness-report.md"
    )
    assert json_path.exists()
    assert md_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema_id"] == "hisys.codebase_map.freshness.v1"
    assert data["advisory_only"] is True
    assert data["current_date"] == "2026-05-20"
    assert data["max_age_days"] == 30
    assert data["current_head_short"] == "1cb2857"
    assert data["fresh_partitions"] == [
        "runtime-boundary/codebase-analysis/20260518/REQ-CLI-FRESH"
    ]
```

**Verify RED:**

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py::test_codebase_map_freshness_review_cli_writes_report -q
```

**Expected RED:** argparse rejects `codebase-map-freshness-review` with `SystemExit: 2`.

---

## Task 2: GREEN — add the smallest CLI wrapper

**Files:**
- Modify: `src/hisys/cli/main.py`

**Step 1: Add imports**

```python
from ..operations.codebase_map_freshness import (
    build_codebase_map_freshness_report,
    write_codebase_map_freshness_report,
)
```

(Place next to the M21.4 module import line. The existing `from ..operations.runtime_boundary_consistency import ...` block is the nearest precedent.)

**Step 2: Add parser entry (next to `runtime_boundary_check` block):**

```python
codebase_map_freshness_review = sub.add_parser(
    "codebase-map-freshness-review",
    help="write local advisory codebase map freshness/drift report artifacts",
)
codebase_map_freshness_review.add_argument("--instance", required=True, help="Hisys instance root")
codebase_map_freshness_review.add_argument("--date", required=True, help="YYYYMMDD report partition")
codebase_map_freshness_review.add_argument(
    "--current-date",
    required=True,
    help="YYYY-MM-DD caller date used for freshness comparison",
)
codebase_map_freshness_review.add_argument(
    "--max-age-days",
    required=True,
    type=int,
    help="freshness threshold in days; partitions older than this are stale",
)
codebase_map_freshness_review.add_argument(
    "--current-head-short",
    default=None,
    help="optional caller-supplied git HEAD short hash recorded verbatim",
)
```

**Step 3: Add command function (next to `_cmd_runtime_boundary_check`):**

```python
def _cmd_codebase_map_freshness_review(
    *,
    instance_root: Path,
    yyyymmdd: str,
    current_date_iso: str,
    max_age_days: int,
    current_head_short: str | None,
) -> int:
    """Write a local advisory codebase map freshness report via the CLI."""

    from datetime import date as _date

    parsed_current = _date.fromisoformat(current_date_iso)
    report = build_codebase_map_freshness_report(
        instance_root=instance_root,
        current_date=parsed_current,
        max_age_days=max_age_days,
        current_head_short=current_head_short,
    )
    written = write_codebase_map_freshness_report(
        instance_root=instance_root, date=yyyymmdd, report=report
    )
    print(f"codebase map freshness report: json={written['json_ref']}")
    print(f"markdown: {written['markdown_ref']}")
    print(f"fresh_partitions: {len(report.fresh_partitions)}")
    print(f"stale_partitions: {len(report.stale_partitions)}")
    print(f"incomplete_partitions: {len(report.incomplete_partitions)}")
    print(f"unsafe_partitions: {len(report.unsafe_partitions)}")
    print("external_call_made: false")
    print("allowed_actions: advisory_only")
    return 0
```

**Step 4: Add dispatcher branch:**

```python
if args.command == "codebase-map-freshness-review":
    return _cmd_codebase_map_freshness_review(
        instance_root=Path(args.instance),
        yyyymmdd=args.date,
        current_date_iso=args.current_date,
        max_age_days=args.max_age_days,
        current_head_short=args.current_head_short,
    )
```

**Verify GREEN:**

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py::test_codebase_map_freshness_review_cli_writes_report -q
PYTHONPATH=src pytest tests/unit/test_codebase_map_freshness.py tests/unit/test_domain_cli.py -q
```

---

## Task 3: Traceability/docs and validation

**Files:**
- Modify: `docs/traceability/README.md` — prepend an `M21.4-CLI` row.
- Modify: `ralph.md` — append a Reflection Log entry with Resume checkpoint.

**Validation:**

```bash
PYTHONPATH=src pytest tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_cli.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit:**

```bash
git add tests/unit/test_domain_cli.py src/hisys/cli/main.py docs/traceability/README.md ralph.md
git commit -m "feat: add codebase-map-freshness-review cli wrapper"
```

---

## Stop conditions

- Stop if the CLI wrapper requires live/external access, credential resolution, process spawning, or publication authority.
- Stop if implementation requires changing M21.4 report semantics rather than merely wrapping them.
- Stop if implementation would call `date.today()` or read `.git/` inside the CLI (callers must supply both).
- Stop if validation reveals stale bootstrap/package assumptions requiring a new queue-refill decision.
