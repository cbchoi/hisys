# Milestone M21.8-CLI — `hisys evaluate-code-analysis-contract` CLI Wrapper Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development`. This plan is the document-RED/Prepare artifact for the M21.8-CLI thin CLI wrapper that follows the M21.8.1.A..D adapter (`e3e7291 feat: map architecture candidates into code-analysis pass-contract evidence`) and the M21.8.2 fixture registry contracts (`bd89335 feat: add code-analysis pass-contract fixtures`). The pure adapter, writer, and fixture pass-contract entries are already stable; M21.8-CLI only exposes them through `hisys evaluate-code-analysis-contract`.

**Goal:** Add a thin `hisys evaluate-code-analysis-contract --instance <root> --date <YYYYMMDD> --contract-ref <json> --question-type <name> [--coverage-report <json>] [--boundary-report <json>] [--freshness-report <json>] [--benchmark-report <json>] [--change-impact-report <json>] [--architecture-candidates-report <json>] [--human-approval-ref <token>]` CLI subcommand that wires the existing M21.8.1 adapter, the existing `evaluate_pass_contract` evaluator, the existing pass-contract registry loader, and the existing M21.8.1 evaluation writer into a single advisory-only local-only workflow. The CLI must not change adapter mapping rules, must not expand the `CodeAnalysisQuestionType` taxonomy, must not introduce live access, credentials, repair, deletion, approval authority, model calls, `.git/` reads, `date.today()`, or `subprocess`, and must remain advisory-only.

**Architecture:** Reuse the existing surfaces without modification:

- `src/hisys/contracts/pass_registry.load_pass_contract_registry` and `PassContractRegistryEntry`
- `src/hisys/contracts/evaluator.EvidenceSummary` and `evaluate_pass_contract`
- `src/hisys/operations/code_analysis_pass_contract.build_code_analysis_evidence_summary`
- `src/hisys/operations/code_analysis_pass_contract.write_code_analysis_pass_contract_evaluation`
- `tests/fixtures/pass-contracts/code_analysis/*.json` for end-to-end test payloads

The CLI increment adds one argparse subcommand definition and one `_cmd_evaluate_code_analysis_contract` dispatcher in `src/hisys/cli/main.py`. No new dependency. The CLI reads only explicit JSON payload files supplied by the caller. It does not discover report paths automatically, does not scan runtime-boundary directories, does not read raw source, and does not infer the current Git head. Missing report arguments become `None` inputs to the adapter — the adapter raises `ValueError` if its question-type requires a missing payload, and the CLI surfaces that as a non-zero exit code without writing an evaluation artifact.

**Tech Stack:** Python, argparse, pathlib, json, pytest, existing Hisys CLI `main(argv)` tests.

**Context Packet:**
- Current HEAD: `bd89335 feat: add code-analysis pass-contract fixtures`.
- Pure adapter/writer: `src/hisys/operations/code_analysis_pass_contract.py`.
- Existing registry loader: `src/hisys/contracts/pass_registry.py`.
- Existing evaluator: `src/hisys/contracts/evaluator.py`.
- CLI parser/dispatcher precedents: `src/hisys/cli/main.py` `_cmd_evaluate_pass_contract` + `evaluate-pass-contract` parser (registry+evidence shape); `_cmd_architecture_candidates` + `architecture-candidates` parser (M21.7-CLI thin-wrapper shape).
- CLI test precedents: `tests/unit/test_pass_contract_evaluate_cli.py` (evaluation artifact shape); `tests/unit/test_domain_cli.py::test_architecture_candidates_cli_writes_report` (thin-wrapper smoke pattern).
- Fixture pass-contracts: `tests/fixtures/pass-contracts/code_analysis/*.json` (the M21.8.2 candidates).
- Documentation/control: `docs/traceability/README.md` and `ralph.md`.

**Boundary Record:** Local code/test/docs changes and local commit are allowed after validation. Remote push, live external access, credential resolution, publication, repair/deletion of partitions, system clock reads, `.git/` reads, raw source reads, automatic report discovery, model calls, and any `git diff` / `git log` / `subprocess` invocation are not authorized. The CLI does not promote a candidate to active and does not modify any pass-contract registry entry. The exit code reflects only whether the evaluation artifact was successfully written; `failed` / `needs_more_evidence` / `human_approval_required` quality gates do not change the exit code.

---

## Accepted decisions

1. **Thin wrapper:** The CLI calls existing pure functions without reshaping any mapping rule or pass-contract semantic.
2. **Explicit JSON inputs only:** The CLI accepts zero or more explicit JSON report paths. It loads their JSON objects via the same `_load_json_report` helper used by `_cmd_architecture_candidates` (reused, not re-implemented) and passes them into `build_code_analysis_evidence_summary`.
3. **Required arguments:** `--instance`, `--date`, `--contract-ref`, and `--question-type` are required. Optional report arguments depend on the question type; the adapter enforces required-payload presence and raises `ValueError` when missing.
4. **`--question-type` is restricted to the five supported strings.** The CLI validates it against `_SUPPORTED_QUESTION_TYPES` from the adapter module before any payload load, returning a clear error.
5. **`--human-approval-ref` is optional and recorded verbatim.** The CLI never derives or generates it; the caller supplies a fixed token if any.
6. **First contract wins.** Following the existing `_cmd_evaluate_pass_contract` precedent, the CLI uses `entries[0]` from `load_pass_contract_registry`. The M21.8.2 fixtures each contain exactly one contract.
7. **Print bounded summary lines:** `evaluate-code-analysis-contract evaluation: json=<ref>`, `markdown: <ref>`, then `contract_id: <id>`, `question_type: <name>`, `quality_gate: <gate>`, `blockers: <comma-separated or none>`, `advisory_only: true`, `requires_human_review: true`, `external_call_made: false`, `mutation_performed: false`, `raw_source_content_persisted: false`, `allowed_actions: advisory_only`.
8. **Exit code:** Always `0` for a successfully written evaluation artifact regardless of the quality gate. A `ValueError` from the adapter (missing required payload, unknown question type) or from the writer (non-`YYYYMMDD` date) propagates as a non-zero exit and no evaluation artifact is written.
9. **No vocabulary expansion:** The CLI does not add new question types, new minimum-evidence keys, new blocked-if codes, or approval/readiness wording.
10. **No registry mutation:** The CLI never writes back to the `--contract-ref` path. Promotion to `active` continues to require the existing human-approved `promote-pass-contract` flow.
11. **Traceability required:** Update `docs/traceability/README.md` with an `M21.8-CLI` row and append a `ralph.md` Reflection Log entry plus Resume checkpoint in the implementation increment.

---

## Task 0: Reconstruct baseline before editing

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_code_analysis_pass_contract.py tests/unit/test_code_analysis_pass_contract_fixtures.py tests/unit/test_pass_contract_evaluate_cli.py tests/unit/test_domain_cli.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:** branch `dars`, HEAD at or after `bd89335 feat: add code-analysis pass-contract fixtures`; focused gates pass; DARS focused gate 50 passes; traceability validator OK; secret scan hit_count=0; `git diff --check` clean.

---

## Task 1: RED — CLI smoke test

**Files:**
- Modify: `tests/unit/test_domain_cli.py`

**Test sketch (illustrative; precise shape pinned in M21.8-CLI RED iteration):**

```python
def test_evaluate_code_analysis_contract_cli_writes_artifact(tmp_path: Path, capsys) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    contract_path = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "pass-contracts"
        / "code_analysis"
        / "traceability_coverage_review.json"
    )
    coverage_path = tmp_path / "coverage.json"
    coverage_path.write_text(
        json.dumps(
            {
                "schema_id": "hisys.traceability.coverage.v1",
                "requirement_count": 2,
                "covered_requirement_count": 2,
                "coverage_ratio": 1.0,
                "unreferenced_requirements": [],
                "orphan_test_ids": [],
            }
        ),
        encoding="utf-8",
    )

    result = main(
        [
            "evaluate-code-analysis-contract",
            "--instance",
            str(instance_root),
            "--date",
            "20260521",
            "--contract-ref",
            str(contract_path),
            "--question-type",
            "traceability_coverage_review",
            "--coverage-report",
            str(coverage_path),
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "evaluate-code-analysis-contract evaluation" in captured.out
    assert "quality_gate: passed" in captured.out
    assert "external_call_made: false" in captured.out
    assert "allowed_actions: advisory_only" in captured.out

    json_path = (
        instance_root
        / "runtime-boundary"
        / "code-analysis-pass-contracts"
        / "20260521"
        / "code_analysis_traceability_coverage_review_v0_1_candidate-evaluation.json"
    )
    md_path = (
        instance_root
        / "runtime-boundary"
        / "code-analysis-pass-contracts"
        / "20260521"
        / "code_analysis_traceability_coverage_review_v0_1_candidate-evaluation.md"
    )
    assert json_path.exists()
    assert md_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema_id"] == "hisys.code_analysis_pass_contract.evaluation.v1"
    assert data["contract_id"] == "code_analysis_traceability_coverage_review_v0_1_candidate"
    assert data["quality_gate"] == "passed"
    assert data["blockers"] == []
    assert data["advisory_only"] is True
    assert data["requires_human_review"] is True
    assert data["external_call_made"] is False
    assert data["mutation_performed"] is False
    assert data["raw_source_content_persisted"] is False
    assert data["human_approval_ref"] is None
```

**Verify RED:**

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py::test_evaluate_code_analysis_contract_cli_writes_artifact -q
```

**Expected RED:** argparse rejects `evaluate-code-analysis-contract` with `SystemExit: 2`.

---

## Task 2: GREEN — add the smallest CLI wrapper

**Files:**
- Modify: `src/hisys/cli/main.py`

**Step 1: Add imports.** Near the existing `code_analysis_pass_contract` import area or adjacent operations imports:

```python
from ..operations.code_analysis_pass_contract import (
    _SUPPORTED_QUESTION_TYPES,
    build_code_analysis_evidence_summary,
    write_code_analysis_pass_contract_evaluation,
)
```

Reuse the existing `_load_json_report` helper added by `_cmd_architecture_candidates` (it already loads explicit caller-supplied JSON object payloads and rejects non-objects).

**Step 2: Add parser entry next to the `architecture_candidates` block:**

```python
evaluate_code_analysis = sub.add_parser(
    "evaluate-code-analysis-contract",
    help="evaluate a code-analysis pass-contract against M21.1..M21.7 reports",
)
evaluate_code_analysis.add_argument("--instance", required=True, help="Hisys instance root")
evaluate_code_analysis.add_argument("--date", required=True, help="YYYYMMDD evaluation partition")
evaluate_code_analysis.add_argument(
    "--contract-ref",
    required=True,
    help="explicit caller-supplied pass-contract registry JSON path (first contract wins)",
)
evaluate_code_analysis.add_argument(
    "--question-type",
    required=True,
    choices=sorted(_SUPPORTED_QUESTION_TYPES),
    help="code-analysis question type",
)
evaluate_code_analysis.add_argument("--coverage-report", default=None)
evaluate_code_analysis.add_argument("--boundary-report", default=None)
evaluate_code_analysis.add_argument("--freshness-report", default=None)
evaluate_code_analysis.add_argument("--benchmark-report", default=None)
evaluate_code_analysis.add_argument("--change-impact-report", default=None)
evaluate_code_analysis.add_argument("--architecture-candidates-report", default=None)
evaluate_code_analysis.add_argument(
    "--human-approval-ref",
    default=None,
    help="optional caller-supplied human-approval token recorded verbatim",
)
```

**Step 3: Add command function next to `_cmd_architecture_candidates`:**

```python
def _cmd_evaluate_code_analysis_contract(
    *,
    instance_root: Path,
    yyyymmdd: str,
    contract_ref: Path,
    question_type: str,
    coverage_report_path: Path | None,
    boundary_report_path: Path | None,
    freshness_report_path: Path | None,
    benchmark_report_path: Path | None,
    change_impact_report_path: Path | None,
    architecture_candidates_report_path: Path | None,
    human_approval_ref: str | None,
) -> int:
    """Evaluate a code-analysis pass-contract via the CLI."""

    entries = load_pass_contract_registry(contract_ref)
    if not entries:
        raise ValueError("contract registry is empty")
    entry = entries[0]
    summary = build_code_analysis_evidence_summary(
        question_type=question_type,
        coverage_report=_load_json_report(coverage_report_path),
        boundary_report=_load_json_report(boundary_report_path),
        freshness_report=_load_json_report(freshness_report_path),
        benchmark_report=_load_json_report(benchmark_report_path),
        change_impact_report=_load_json_report(change_impact_report_path),
        architecture_candidates_report=_load_json_report(
            architecture_candidates_report_path
        ),
    )
    result = evaluate_pass_contract(entry, summary)
    written = write_code_analysis_pass_contract_evaluation(
        instance_root=instance_root,
        date=yyyymmdd,
        contract_id=entry.contract_id,
        result=result,
        human_approval_ref=human_approval_ref,
    )
    print(f"evaluate-code-analysis-contract evaluation: json={written['json_ref']}")
    print(f"markdown: {written['markdown_ref']}")
    print(f"contract_id: {entry.contract_id}")
    print(f"question_type: {question_type}")
    print(f"quality_gate: {result.quality_gate}")
    blockers_text = ",".join(result.blockers) if result.blockers else "none"
    print(f"blockers: {blockers_text}")
    print("advisory_only: true")
    print("requires_human_review: true")
    print("external_call_made: false")
    print("mutation_performed: false")
    print("raw_source_content_persisted: false")
    print("allowed_actions: advisory_only")
    return 0
```

**Step 4: Add dispatcher branch next to the `architecture-candidates` branch:**

```python
if args.command == "evaluate-code-analysis-contract":
    return _cmd_evaluate_code_analysis_contract(
        instance_root=Path(args.instance),
        yyyymmdd=args.date,
        contract_ref=Path(args.contract_ref),
        question_type=args.question_type,
        coverage_report_path=Path(args.coverage_report) if args.coverage_report else None,
        boundary_report_path=Path(args.boundary_report) if args.boundary_report else None,
        freshness_report_path=Path(args.freshness_report) if args.freshness_report else None,
        benchmark_report_path=Path(args.benchmark_report) if args.benchmark_report else None,
        change_impact_report_path=Path(args.change_impact_report) if args.change_impact_report else None,
        architecture_candidates_report_path=Path(args.architecture_candidates_report) if args.architecture_candidates_report else None,
        human_approval_ref=args.human_approval_ref,
    )
```

**Verify GREEN:**

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py::test_evaluate_code_analysis_contract_cli_writes_artifact -q
PYTHONPATH=src pytest tests/unit/test_code_analysis_pass_contract.py tests/unit/test_code_analysis_pass_contract_fixtures.py tests/unit/test_pass_contract_evaluate_cli.py tests/unit/test_domain_cli.py -q
```

---

## Task 3: Traceability/docs and final gates

**Files:**
- Modify: `docs/traceability/README.md`
- Modify: `ralph.md`

**Traceability row:** add an `M21.8-CLI` row linking:
- this plan;
- `src/hisys/cli/main.py` parser/dispatcher;
- `src/hisys/operations/code_analysis_pass_contract.py` adapter/writer;
- `src/hisys/contracts/{pass_registry.py,evaluator.py}` for registry/evaluator reuse;
- `tests/fixtures/pass-contracts/code_analysis/*.json`;
- `tests/unit/test_domain_cli.py::test_evaluate_code_analysis_contract_cli_writes_artifact`.

**Final validation:**

```bash
PYTHONPATH=src pytest tests/unit/test_code_analysis_pass_contract.py tests/unit/test_code_analysis_pass_contract_fixtures.py tests/unit/test_pass_contract_registry_schema.py tests/unit/test_pass_contract_evaluator.py tests/unit/test_pass_contract_evaluate_cli.py tests/unit/test_pass_contract_promotion.py tests/unit/test_pass_contract_proposal_conversion.py tests/unit/test_pass_contract_improvement_cli.py tests/unit/test_pass_contract_review_package.py tests/unit/test_domain_investigation_pass_contracts.py tests/unit/test_architecture_candidates.py tests/unit/test_change_impact.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_domain_cli.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
git status --short --branch
```

**Commit boundary:** PREP and RED/GREEN ship as separate commits:

- PREP commit (this task plan):

```bash
git add docs/plans/m21-8-cli-evaluate-code-analysis-contract-implementation-tasks.md ralph.md
git commit -m "docs: prepare evaluate-code-analysis-contract cli wrapper"
```

- RED/GREEN commit (next iteration):

```bash
git add src/hisys/cli/main.py tests/unit/test_domain_cli.py docs/traceability/README.md ralph.md
git commit -m "feat: add evaluate-code-analysis-contract cli wrapper"
```

---

## Stop / continue rule

Stop after this Prepare package is committed. The next safe row is `M21.8-CLI` Task 1 RED: add `tests/unit/test_domain_cli.py::test_evaluate_code_analysis_contract_cli_writes_artifact`, observe argparse RED, then implement the minimal CLI wrapper. Do not start GREEN in the same Prepare-only increment unless explicitly authorized by the user.

If a future iteration finds that the adapter's `_SUPPORTED_QUESTION_TYPES` set diverges from the M21.8.2 fixture question types, stop and ask the user before changing either side — the fixture taxonomy is the human-review surface, and adapter changes require a separate Prepare/RED. Do not expand the question-type taxonomy without an explicit Prepare/RED.
