# Milestone M21.3-CLI — Runtime-Boundary Check CLI Wrapper Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for every code-bearing task. This plan is the document-RED/Prepare artifact for the M21.3-CLI thin CLI wrapper that follows the M21.3 GREEN commit (`6a067ed feat: add runtime-boundary consistency checker`). The pure checker is already stable; M21.3-CLI only exposes it through `hisys runtime-boundary-check`.

**Goal:** Add a thin `hisys runtime-boundary-check --instance <root> --date <YYYYMMDD> [--ref <relative-ref>]*` CLI subcommand that wraps the M21.3 pure checker and writer. The CLI must not change consistency-report semantics, must not expand the issue vocabulary, must not introduce live access, credentials, repair, deletion, or approval authority, and must remain advisory-only.

**Architecture:** Reuse the existing M21.3 surfaces:

- `src/hisys/operations/runtime_boundary_consistency.build_runtime_boundary_consistency_report` (pure classifier)
- `src/hisys/operations/runtime_boundary_consistency.write_runtime_boundary_consistency_report` (JSON/Markdown writer)

The CLI increment adds one argparse subcommand definition and one `_cmd_runtime_boundary_check` dispatcher in `src/hisys/cli/main.py`. No new dependency. Refs are accepted only as repeatable `--ref` values; if zero refs are supplied the CLI writes an empty advisory report (useful as an empty-baseline regression artifact and as a structural smoke). A future `--scan` mode that recursively lists `<instance>/runtime-boundary/` entries is intentionally deferred.

**Tech Stack:** Python, argparse, Pydantic v2, pytest, existing Hisys CLI `main(argv)` tests.

**Context Packet:**
- Current HEAD: `6a067ed feat: add runtime-boundary consistency checker`.
- Pure checker/writer module: `src/hisys/operations/runtime_boundary_consistency.py`.
- CLI parser/dispatcher: `src/hisys/cli/main.py` (`_build_parser` traceability-coverage block near line 1901, dispatcher near line 3108).
- M21.2 CLI wrapper precedent: `_cmd_traceability_coverage` and `traceability_coverage` subparser.
- CLI tests: `tests/unit/test_domain_cli.py` (M21.2 test at line 60).
- Existing focused gate suite invocation:
  ```bash
  PYTHONPATH=src pytest tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_cli.py -q
  ```

**Boundary Record:** Local code/test/docs changes and local commit are allowed after validation. Remote push, live external access, credential resolution, publication, repair/deletion of artifacts, and any action-authority expansion are not authorized. The CLI never opens refs that escape the instance root and never adds approval/safe-to-deploy/readiness language.

---

## Accepted decisions

1. **Thin wrapper:** The CLI calls the existing `build_runtime_boundary_consistency_report` and `write_runtime_boundary_consistency_report` without reshaping or wrapping the report record.
2. **Refs are CLI inputs only:** Refs come from repeatable `--ref` flags. If zero refs are supplied, the report is still written and records all-zero issue counts.
3. **No `--scan` flag in this increment:** Recursive scanning of `runtime-boundary/` is deferred.
4. **No issue-vocabulary expansion:** The CLI does not add new issue kinds. Any future kinds must come through a separate RED.
5. **Print bounded summary lines:** The CLI prints `runtime-boundary consistency report: json=<ref>`, `markdown: <ref>`, `ok_ref_count: <n>`, and an `external_call_made: false` / `allowed_actions: advisory_only` pair, mirroring the M21.2 wrapper's output shape.
6. **Exit code:** Always returns `0` for a successfully written report. The presence of issues never raises the exit code (advisory-only); a downstream gate is responsible for interpreting the JSON.
7. **Traceability required:** Update `docs/traceability/README.md` with an `M21.3-CLI` row and append a `ralph.md` Reflection Log entry plus Resume checkpoint in the implementation increment.

---

## Task 0: Reconstruct baseline before editing

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_cli.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:** branch `dars`, HEAD at or after `6a067ed feat: add runtime-boundary consistency checker`; extended focused gate (≥37) passes; DARS focused gate 48 passes; traceability validator OK; secret scan hit_count=0; `git diff --check` clean.

---

## Task 1: RED — CLI smoke test

**Objective:** Add a failing CLI test that proves the `runtime-boundary-check` subcommand does not exist yet.

**Files:**
- Modify: `tests/unit/test_domain_cli.py`

**Test sketch:**

```python
def test_runtime_boundary_check_cli_writes_consistency_report(tmp_path: Path, capsys) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    safe_ref = "runtime-boundary/traceability-coverage/20260520/coverage-report.json"
    safe_md = "runtime-boundary/traceability-coverage/20260520/coverage-report.md"
    (instance_root / safe_ref).parent.mkdir(parents=True, exist_ok=True)
    (instance_root / safe_ref).write_text(
        json.dumps(
            {
                "schema_id": "hisys.traceability.coverage.v1",
                "advisory_only": True,
                "requires_human_review": True,
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (instance_root / safe_md).write_text("# coverage\n- advisory_only: true\n", encoding="utf-8")

    result = main(
        [
            "runtime-boundary-check",
            "--instance",
            str(instance_root),
            "--date",
            "20260520",
            "--ref",
            safe_ref,
            "--ref",
            safe_md,
            "--ref",
            "runtime-boundary/codebase-analysis/20260520/REQ-MISSING/inventory.json",
            "--ref",
            "runtime-boundary/../escape.txt",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "runtime-boundary consistency report" in captured.out
    assert "external_call_made: false" in captured.out
    json_path = instance_root / "runtime-boundary" / "runtime-boundary-consistency" / "20260520" / "consistency-report.json"
    md_path = instance_root / "runtime-boundary" / "runtime-boundary-consistency" / "20260520" / "consistency-report.md"
    assert json_path.exists()
    assert md_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema_id"] == "hisys.runtime_boundary.consistency.v1"
    assert data["advisory_only"] is True
    assert data["requires_human_review"] is True
    assert data["external_call_made"] is False
    assert data["mutation_performed"] is False
    assert data["raw_source_content_persisted"] is False
    assert data["ok_ref_count"] == 2
    assert data["unsafe_refs"] == ["runtime-boundary/../escape.txt"]
    assert data["missing_files"] == [
        "runtime-boundary/codebase-analysis/20260520/REQ-MISSING/inventory.json"
    ]
```

**Verify RED:**

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py::test_runtime_boundary_check_cli_writes_consistency_report -q
```

**Expected RED:** argparse rejects `runtime-boundary-check` with `SystemExit: 2`, or the dispatcher branch is missing.

---

## Task 2: GREEN — add the smallest CLI wrapper

**Objective:** Add the subcommand definition, the `_cmd_runtime_boundary_check` dispatcher, and the dispatcher branch.

**Files:**
- Modify: `src/hisys/cli/main.py`

**Step 1: Import existing pure surfaces**

Add to the existing block of `from hisys.operations.runtime_boundary_consistency import ...`:

```python
from hisys.operations.runtime_boundary_consistency import (
    build_runtime_boundary_consistency_report,
    write_runtime_boundary_consistency_report,
)
```

**Step 2: Add parser entry (place near `traceability_coverage` block):**

```python
runtime_boundary_check = sub.add_parser(
    "runtime-boundary-check",
    help="write local advisory runtime-boundary consistency report artifacts",
)
runtime_boundary_check.add_argument("--instance", required=True, help="Hisys instance root")
runtime_boundary_check.add_argument("--date", required=True, help="YYYYMMDD report partition")
runtime_boundary_check.add_argument(
    "--ref",
    action="append",
    default=[],
    help="relative runtime-boundary ref under <instance>/runtime-boundary/; repeatable",
)
```

**Step 3: Add command function (place near `_cmd_traceability_coverage`):**

```python
def _cmd_runtime_boundary_check(
    *,
    instance_root: Path,
    yyyymmdd: str,
    refs: tuple[str, ...],
) -> int:
    """Write a local advisory runtime-boundary consistency report via the CLI."""

    report = build_runtime_boundary_consistency_report(
        instance_root=instance_root, candidate_refs=refs
    )
    written = write_runtime_boundary_consistency_report(
        instance_root=instance_root, date=yyyymmdd, report=report
    )
    print(f"runtime-boundary consistency report: json={written['json_ref']}")
    print(f"markdown: {written['markdown_ref']}")
    print(f"ok_ref_count: {report.ok_ref_count}")
    print(f"unsafe_refs: {len(report.unsafe_refs)}")
    print(f"missing_files: {len(report.missing_files)}")
    print(f"malformed_json_refs: {len(report.malformed_json_refs)}")
    print(f"missing_markdown_pair_refs: {len(report.missing_markdown_pair_refs)}")
    print(f"missing_advisory_flag_refs: {len(report.missing_advisory_flag_refs)}")
    print(f"outside_runtime_boundary_refs: {len(report.outside_runtime_boundary_refs)}")
    print("external_call_made: false")
    print("allowed_actions: advisory_only")
    return 0
```

**Step 4: Add dispatcher branch (place after `traceability-coverage` branch):**

```python
if args.command == "runtime-boundary-check":
    return _cmd_runtime_boundary_check(
        instance_root=Path(args.instance),
        yyyymmdd=args.date,
        refs=tuple(args.ref),
    )
```

**Verify GREEN:**

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py::test_runtime_boundary_check_cli_writes_consistency_report -q
PYTHONPATH=src pytest tests/unit/test_runtime_boundary_consistency.py tests/unit/test_domain_cli.py -q
```

**Expected GREEN:** focused CLI test passes; consistency and domain CLI suites pass together.

---

## Task 3: Traceability/docs and validation

**Files:**
- Modify: `docs/traceability/README.md` — append/update M21.3 row to mention CLI exposure, or add a separate `M21.3-CLI` row.
- Modify: `ralph.md` — append a Reflection Log entry following the M21.2/M21.3 format with Resume checkpoint.

**Validation:**

```bash
PYTHONPATH=src pytest tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_codebase_domain_artifact_bridge.py tests/unit/test_domain_three_layer_use_cases.py tests/unit/test_structured_domain_adapter.py tests/unit/test_domain_runtime_artifacts.py tests/unit/test_domain_cli.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit:**

```bash
git add tests/unit/test_domain_cli.py src/hisys/cli/main.py docs/traceability/README.md ralph.md
git commit -m "feat: add runtime-boundary-check CLI wrapper"
```

---

## Stop conditions

- Stop if the CLI wrapper requires live/external source access, credential resolution, process spawning, or publication authority.
- Stop if implementation requires changing the M21.3 report semantics rather than merely wrapping them.
- Stop if validation reveals stale bootstrap/package assumptions requiring a new queue-refill decision.
- Stop if the CLI needs a scanning mode beyond repeatable `--ref` (defer to a separate M21.3-SCAN increment).
