# Milestone M21.7-CLI — Architecture Candidates CLI Wrapper Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development`. This plan is the document-RED/Prepare artifact for the M21.7-CLI thin CLI wrapper that follows the M21.7 GREEN commit (`50b7263 feat: add architecture candidate generator`). The pure generator is already stable; M21.7-CLI only exposes it through `hisys architecture-candidates`.

**Goal:** Add a thin `hisys architecture-candidates --instance <root> --date <YYYYMMDD> [--coverage-report <json>] [--freshness-report <json>] [--change-impact-report <json>] [--current-head-short <hash>]` CLI subcommand that wraps the M21.7 pure generator/writer. The CLI must not change candidate semantics, must not expand the candidate-kind or recommendation-strength vocabulary, must not introduce live access, credentials, repair, deletion, approval authority, model calls, `.git/` reads, `date.today()`, or `subprocess`, and must remain advisory-only.

**Architecture:** Reuse the existing M21.7 surfaces:

- `src/hisys/operations/architecture_candidates.ArchitectureCandidateInputs`
- `src/hisys/operations/architecture_candidates.build_architecture_candidate_report`
- `src/hisys/operations/architecture_candidates.write_architecture_candidate_report`

The CLI increment adds one argparse subcommand definition and one `_cmd_architecture_candidates` dispatcher in `src/hisys/cli/main.py`. No new dependency. The CLI reads only explicit JSON payload files supplied by the caller. It does not discover report paths automatically, does not scan runtime-boundary directories, does not read raw source, and does not infer the current Git head. Missing report arguments become `None` inputs to the pure generator.

**Tech Stack:** Python, argparse, pathlib, json, pytest, existing Hisys CLI `main(argv)` tests.

**Context Packet:**
- Current HEAD: `c4c7b96 test: exclude fixture repositories from collection`.
- Pure generator/writer: `src/hisys/operations/architecture_candidates.py`.
- CLI parser/dispatcher: `src/hisys/cli/main.py` (nearest precedents: `_cmd_change_impact` + `change-impact` subparser from M21.6-CLI; `_cmd_codebase_map_freshness_review` + `codebase-map-freshness-review` subparser from M21.4-CLI).
- CLI tests: `tests/unit/test_domain_cli.py` (M21.6-CLI, M21.4-CLI, and M21.2 tests are nearest shape).
- Pure tests: `tests/unit/test_architecture_candidates.py`.
- Documentation/control: `docs/traceability/README.md` and `ralph.md`.

**Boundary Record:** Local code/test/docs changes and local commit are allowed after validation. Remote push, live external access, credential resolution, publication, repair/deletion of partitions, calls to system clock, `.git/` reads, raw source reads, automatic report discovery, model calls, and any `git diff` / `git log` / `subprocess` invocation are not authorized. The CLI never raises the exit code merely because the candidate count is non-zero; candidate records are advisory-only and require human review.

---

## Accepted decisions

1. **Thin wrapper:** The CLI calls the existing pure functions without reshaping candidate semantics.
2. **Explicit JSON inputs only:** The CLI accepts zero or more explicit JSON report paths. It loads their JSON objects and passes them into `ArchitectureCandidateInputs`; it does not crawl runtime-boundary directories or infer latest artifacts.
3. **Missing inputs allowed:** If any report argument is omitted, the corresponding input is `None`, matching the pure generator's missing-input behavior.
4. **`--current-head-short` is optional and recorded verbatim.** The CLI never derives it from `.git/`; the caller supplies it.
5. **No vocabulary expansion:** The CLI does not add new candidate kinds, recommendation-strength values, or approval/readiness wording.
6. **Print bounded summary lines:** `architecture-candidates report: json=<ref>`, `markdown: <ref>`, then `candidate_count: <n>`, `advisory_only: true`, `requires_human_review: true`, `external_call_made: false`, `mutation_performed: false`, `raw_source_content_persisted: false`, `allowed_actions: advisory_only`.
7. **Exit code:** Always `0` for a successfully written report. Candidate counts never imply approval, readiness, or failure.
8. **Traceability required:** Update `docs/traceability/README.md` with an `M21.7-CLI` row and append a `ralph.md` Reflection Log entry plus Resume checkpoint in the implementation increment.

---

## Task 0: Reconstruct baseline before editing

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_architecture_candidates.py tests/unit/test_domain_cli.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:** branch `dars`, HEAD at or after `50b7263 feat: add architecture candidate generator`; focused architecture/domain CLI gate passes; DARS focused gate 50 passes; traceability validator OK; secret scan hit_count=0; `git diff --check` clean.

---

## Task 1: RED — CLI smoke test

**Files:**
- Modify: `tests/unit/test_domain_cli.py`

**Test sketch:**

```python
def test_architecture_candidates_cli_writes_report(tmp_path: Path, capsys) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    coverage_path = tmp_path / "coverage.json"
    freshness_path = tmp_path / "freshness.json"
    impact_path = tmp_path / "impact.json"
    coverage_path.write_text(json.dumps(_architecture_coverage_payload()), encoding="utf-8")
    freshness_path.write_text(json.dumps(_architecture_freshness_payload()), encoding="utf-8")
    impact_path.write_text(json.dumps(_architecture_impact_payload()), encoding="utf-8")

    result = main(
        [
            "architecture-candidates",
            "--instance",
            str(instance_root),
            "--date",
            "20260521",
            "--coverage-report",
            str(coverage_path),
            "--freshness-report",
            str(freshness_path),
            "--change-impact-report",
            str(impact_path),
            "--current-head-short",
            "50b7263",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "architecture-candidates report" in captured.out
    assert "candidate_count:" in captured.out
    assert "external_call_made: false" in captured.out
    assert "allowed_actions: advisory_only" in captured.out

    json_path = (
        instance_root
        / "runtime-boundary"
        / "architecture-candidates"
        / "20260521"
        / "architecture-candidates-report.json"
    )
    md_path = (
        instance_root
        / "runtime-boundary"
        / "architecture-candidates"
        / "20260521"
        / "architecture-candidates-report.md"
    )
    assert json_path.exists()
    assert md_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema_id"] == "hisys.architecture_candidates.v1"
    assert data["advisory_only"] is True
    assert data["requires_human_review"] is True
    assert data["external_call_made"] is False
    assert data["mutation_performed"] is False
    assert data["raw_source_content_persisted"] is False
    assert data["current_head_short"] == "50b7263"
    assert data["candidate_count"] > 0
    for candidate in data["candidates"]:
        assert candidate["recommendation_strength"] in (
            "advisory_candidate",
            "advisory_candidate_low_evidence",
        )
```

**Verify RED:**

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py::test_architecture_candidates_cli_writes_report -q
```

**Expected RED:** argparse rejects `architecture-candidates` with `SystemExit: 2`.

---

## Task 2: GREEN — add the smallest CLI wrapper

**Files:**
- Modify: `src/hisys/cli/main.py`

**Step 1: Add imports.** Near the existing `architecture_candidates` import area or adjacent operations imports:

```python
from ..operations.architecture_candidates import (
    ArchitectureCandidateInputs,
    build_architecture_candidate_report,
    write_architecture_candidate_report,
)
```

**Step 2: Add a JSON loader helper near the CLI command helpers:**

```python
def _load_json_report(path: Path | None) -> dict[str, object] | None:
    if path is None:
        return None
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object report at {path}")
    return payload
```

This helper loads only explicit caller-supplied JSON paths. It does not discover files.

**Step 3: Add parser entry next to the `change_impact` block:**

```python
architecture_candidates = sub.add_parser(
    "architecture-candidates",
    help="write local advisory architecture-candidate report artifacts",
)
architecture_candidates.add_argument("--instance", required=True, help="Hisys instance root")
architecture_candidates.add_argument("--date", required=True, help="YYYYMMDD report partition")
architecture_candidates.add_argument(
    "--coverage-report",
    default=None,
    help="optional explicit hisys.traceability.coverage.v1 JSON report path",
)
architecture_candidates.add_argument(
    "--freshness-report",
    default=None,
    help="optional explicit hisys.codebase_map.freshness.v1 JSON report path",
)
architecture_candidates.add_argument(
    "--change-impact-report",
    default=None,
    help="optional explicit hisys.change_impact.v1 JSON report path",
)
architecture_candidates.add_argument(
    "--current-head-short",
    default=None,
    help="optional caller-supplied git HEAD short hash recorded verbatim",
)
```

**Step 4: Add command function next to `_cmd_change_impact`:**

```python
def _cmd_architecture_candidates(
    *,
    instance_root: Path,
    yyyymmdd: str,
    coverage_report_path: Path | None,
    freshness_report_path: Path | None,
    change_impact_report_path: Path | None,
    current_head_short: str | None,
) -> int:
    """Write a local advisory architecture-candidate report via the CLI."""

    inputs = ArchitectureCandidateInputs(
        instance_root=instance_root,
        coverage_report=_load_json_report(coverage_report_path),
        freshness_report=_load_json_report(freshness_report_path),
        change_impact_report=_load_json_report(change_impact_report_path),
        current_head_short=current_head_short,
    )
    report = build_architecture_candidate_report(inputs=inputs)
    written = write_architecture_candidate_report(
        instance_root=instance_root, date=yyyymmdd, report=report
    )
    print(f"architecture-candidates report: json={written['json_ref']}")
    print(f"markdown: {written['markdown_ref']}")
    print(f"candidate_count: {report.candidate_count}")
    print("advisory_only: true")
    print("requires_human_review: true")
    print("external_call_made: false")
    print("mutation_performed: false")
    print("raw_source_content_persisted: false")
    print("allowed_actions: advisory_only")
    return 0
```

**Step 5: Add dispatcher branch next to the `change-impact` branch:**

```python
if args.command == "architecture-candidates":
    return _cmd_architecture_candidates(
        instance_root=Path(args.instance),
        yyyymmdd=args.date,
        coverage_report_path=(
            Path(args.coverage_report) if args.coverage_report else None
        ),
        freshness_report_path=(
            Path(args.freshness_report) if args.freshness_report else None
        ),
        change_impact_report_path=(
            Path(args.change_impact_report) if args.change_impact_report else None
        ),
        current_head_short=args.current_head_short,
    )
```

**Verify GREEN:**

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py::test_architecture_candidates_cli_writes_report -q
PYTHONPATH=src pytest tests/unit/test_architecture_candidates.py tests/unit/test_domain_cli.py -q
```

---

## Task 3: Traceability/docs and final gates

**Files:**
- Modify: `docs/traceability/README.md`
- Modify: `ralph.md`

**Traceability row:** add an `M21.7-CLI` row linking:
- this plan;
- `src/hisys/cli/main.py` parser/dispatcher;
- `src/hisys/operations/architecture_candidates.py` pure module;
- `tests/unit/test_domain_cli.py::test_architecture_candidates_cli_writes_report`.

**Final validation:**

```bash
PYTHONPATH=src pytest tests/unit/test_architecture_candidates.py tests/unit/test_domain_cli.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
git status --short --branch
```

**Commit boundary:** If all gates pass and the working tree contains only M21.7-CLI files, commit locally as:

```bash
git add docs/plans/m21-7-cli-architecture-candidates-cli-wrapper-implementation-tasks.md ralph.md
git commit -m "docs: prepare architecture candidates cli wrapper"
```

Later implementation should use a separate RED -> GREEN commit such as `feat: add architecture candidates cli wrapper`.

---

## Stop / continue rule

Stop after this Prepare package is committed. The next safe row is `M21.7-CLI` Task 1 RED: add `tests/unit/test_domain_cli.py::test_architecture_candidates_cli_writes_report`, observe argparse RED, then implement the minimal CLI wrapper. Do not start GREEN in the same Prepare-only increment unless explicitly authorized by the user.
