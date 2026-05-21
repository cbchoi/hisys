# Milestone M22 — Codebase Evidence Portfolio CLI Wrapper Implementation Task Plan

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for every code-bearing task. This file is the document-RED/Prepare artifact for Milestone M22 Task `M22-PORTFOLIO-CLI` — a thin `hisys codebase-evidence-portfolio` argparse wrapper around the pure `src/hisys/operations/codebase_evidence_portfolio.py` builder/writer landed by `M22-PORTFOLIO-RED-GREEN` (commit `86684f4 feat: add codebase evidence portfolio`). The CLI is a fixture-local read-only operator surface; it never crosses live-provider, credential, subagent, LSP, network, or raw-source boundaries.

**Goal:** Add a thin `hisys codebase-evidence-portfolio` subcommand that consumes a caller-supplied JSON bundle of evidence-line refs and produces the same `runtime-boundary/codebase-evidence-portfolio/<YYYYMMDD>/portfolio-report.{json,md}` artifacts that the pure builder already emits. The CLI is a routing/printing surface only; the M22-PORTFOLIO-RED-GREEN module remains the single source of truth for portfolio semantics, ref safety, label safety, and date validation.

**Architecture:** Reuse the M22-PORTFOLIO-RED-GREEN module. The CLI:

1. Parses a single `--line-bundle <json>` file describing `line_refs: [EvidenceLineRef, ...]`. This matches the rest of the Hisys CLI surface, which accepts complex inputs only via explicit caller-supplied JSON files (pass-contract, change-impact, architecture-candidates reports).
2. Validates the JSON shape minimally (top-level object containing a `line_refs` list of objects with required fields) and delegates to the existing Pydantic models — no shape duplication.
3. Builds `EvidenceLineRef` records and a `CodebaseEvidencePortfolioRequest` with `instance_root: Path`, `date: str`, `line_refs`, and `current_head_short`.
4. Calls `build_codebase_evidence_portfolio_report(request=request)` and `write_codebase_evidence_portfolio_report(...)` without reshaping report semantics.
5. Prints bounded `portfolio-report` JSON/Markdown refs, `source_line_count`, `artifact_ref_count`, `schema_id_count`, `quality_gate_ref_count`, `implemented_surface_count`, `human_gated_surface_count`, `unsafe_ref_count`, `unsafe_line_label_count`, `advisory_only: true`, `requires_human_review: true`, `external_call_made: false`, `mutation_performed: false`, `raw_source_content_persisted: false`, and `allowed_actions: advisory_only` summary lines. Returns exit code `0` on success; any `ValueError` from the loader/builder/writer propagates non-zero.

The CLI must not call `date.today()`, must not read `.git/`, must not call `subprocess`, must not crawl `runtime-boundary/`, must not infer latest artifacts, must not auto-discover bundle files, must not auto-open artifact refs to verify file existence, and must not expand the line-label or ref vocabulary.

**Tech Stack:** Python 3.11, argparse, Pydantic v2 (already imported through the M22 module), pytest. No new dependency.

**Context Packet:** Required source handles:

- `src/hisys/cli/main.py` (`_load_json_report` helper, `change-impact`/`architecture-candidates`/`codebase-map-freshness-review`/`evaluate-code-analysis-contract` subparser/dispatcher patterns).
- `src/hisys/operations/codebase_evidence_portfolio.py` (M22 builder/writer — single source of truth; do not change its shape).
- `tests/unit/test_domain_cli.py` (CLI test layout for `change-impact`, `architecture-candidates`, `codebase-map-freshness-review`).
- `docs/plans/m22-codebase-evidence-portfolio-implementation-plan.md` and `docs/plans/m22-codebase-evidence-portfolio-implementation-tasks.md`.
- `docs/traceability/README.md` (M22 row already added; M22-CLI row will be prepended in Task 4).
- `ralph.md` for the Reflection Log update.

**Boundary Record:** Local docs/control, test, and CLI dispatcher edits only. Local commits and normal push to existing `origin/dars` are allowed after focused gates pass. Remote configuration change, force push, credential lookup, live external call, network clone/fetch/search, local LSP subprocess spawning, subagent execution, publication, deployment, destructive Git history, schema/data migrations against non-fixture data, and raw source-content archival are not authorized. The CLI is advisory only and never implies repair, deletion, retry, approval, or readiness for live action.

---

## Accepted decisions

1. **JSON bundle over argparse grouping.** The CLI accepts one `--line-bundle <json>` path. The bundle is `{"line_refs": [...]}` where each list element matches `EvidenceLineRef`. This deviates from the original "Proposed CLI" sketch in the parent plan (which proposed repeated `--line-label`/`--artifact-ref` flags) because the Hisys CLI surface consistently uses caller-supplied JSON files for complex inputs (pass-contract, change-impact, architecture-candidates payloads). Operator UX gains nothing from custom argparse grouping; tests gain a lot from the simpler shape.
2. **Bundle file passes through `_load_json_report`-style chokepoint.** The CLI opens the bundle as a JSON object only; non-object payloads raise `ValueError`. The Pydantic `EvidenceLineRef` and `CodebaseEvidencePortfolioRequest` constructors then enforce field shape — no field-by-field reimplementation in the CLI.
3. **No shape extension.** The CLI does not add fields to `EvidenceLineRef` or the report. If a future field is needed, it must be added under a separate M22 RED on the pure module first.
4. **No auto-discovery.** The CLI never globs `runtime-boundary/` for latest artifacts, never opens artifact refs to check existence, never reads `.git/`, never calls `subprocess`, never calls `date.today()`. The caller supplies everything verbatim.
5. **Exit code 0 on success only.** Loader/builder/writer `ValueError` propagates non-zero. The CLI does not catch `ValueError` to print a friendly message; it lets argparse/pytest see the failure.
6. **Bounded summary output.** Counts and the advisory-flag echo are sufficient; the CLI does not echo `artifact_refs`, `schema_ids`, or other full ref lists to stdout to avoid accidental leakage of long ref strings into terminal/log capture.
7. **Documentation in lockstep.** `docs/traceability/README.md` gains an `M22-CLI` row in the same commit as the CLI dispatcher. `ralph.md` gains a Reflection Log entry + Resume checkpoint. The governance profile and current-state test roll forward to `next_safe_task: M22-PORTFOLIO-GOLDEN`.

---

## Task 0: Reconstruct baseline before any edit

**Objective:** Confirm the M22-PORTFOLIO-RED-GREEN commit is current, working tree is clean, and the M21/M22/DARS focused gates remain green.

**Commands:**

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_codebase_evidence_portfolio.py tests/unit/test_change_impact.py tests/unit/test_architecture_candidates.py tests/unit/test_code_analysis_pass_contract.py tests/unit/test_subagent_evidence_collector_protocol.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
PYTHONPATH=src pytest tests/unit/test_governance_docs_current_state.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:** branch `dars`, HEAD at or after `86684f4 feat: add codebase evidence portfolio`; combined M21+M22 focused gate passes (65 expected); DARS critic-panel focused regression passes (55 expected); governance current-state test passes (v0.0.17, next_safe_task=M22-PORTFOLIO-CLI); traceability validator OK; secret scan `hit_count=0`; `git diff --check` clean.

---

## Task 1: RED — CLI invocation writes portfolio artifacts and prints advisory summary

**Objective:** Add a failing pytest that invokes `hisys codebase-evidence-portfolio` end-to-end through `main([...])` with a JSON line bundle, asserts the JSON/Markdown artifacts land under the expected `runtime-boundary/codebase-evidence-portfolio/<date>/` path, and asserts the bounded summary lines appear on stdout. The test must fail before the CLI subparser/dispatcher exists.

**Files:**

- Modify: `tests/unit/test_domain_cli.py`

**Test sketch:**

```python
def _portfolio_bundle_payload() -> dict[str, object]:
    return {
        "line_refs": [
            {
                "line_label": "M21",
                "artifact_refs": [
                    "docs/plans/m21-1-traceability-coverage-report-implementation-tasks.md",
                    "docs/plans/m21-6-change-impact-analyzer-implementation-tasks.md",
                ],
                "schema_ids": [
                    "hisys.traceability.coverage.v1",
                    "hisys.change_impact.v1",
                ],
                "quality_gate_refs": [
                    "tests/unit/test_traceability_coverage.py",
                    "tests/unit/test_change_impact.py",
                ],
                "implemented_surface_count": 9,
                "human_gated_surface_count": 2,
            },
            {
                "line_label": "DARS_PANEL_LOCAL_COMPLETION",
                "artifact_refs": [
                    "docs/reports/dars-panel-local-completion-audit.md",
                ],
                "schema_ids": ["hisys.dars_panel_readiness.v1"],
                "quality_gate_refs": [
                    "tests/unit/test_dars_critic_panel_runtime.py",
                ],
                "implemented_surface_count": 5,
                "human_gated_surface_count": 0,
            },
        ]
    }


def test_codebase_evidence_portfolio_cli_writes_report(tmp_path: Path, capsys) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(
        json.dumps(_portfolio_bundle_payload()), encoding="utf-8"
    )

    result = main(
        [
            "codebase-evidence-portfolio",
            "--instance",
            str(instance_root),
            "--date",
            "20260521",
            "--line-bundle",
            str(bundle_path),
            "--current-head-short",
            "86684f4",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "codebase-evidence-portfolio report" in captured.out
    assert "advisory_only: true" in captured.out
    assert "requires_human_review: true" in captured.out
    assert "external_call_made: false" in captured.out
    assert "mutation_performed: false" in captured.out
    assert "raw_source_content_persisted: false" in captured.out
    assert "allowed_actions: advisory_only" in captured.out
    assert "source_line_count: 2" in captured.out
    assert "implemented_surface_count: 14" in captured.out
    assert "human_gated_surface_count: 2" in captured.out

    json_path = (
        instance_root
        / "runtime-boundary"
        / "codebase-evidence-portfolio"
        / "20260521"
        / "portfolio-report.json"
    )
    md_path = (
        instance_root
        / "runtime-boundary"
        / "codebase-evidence-portfolio"
        / "20260521"
        / "portfolio-report.md"
    )
    assert json_path.exists()
    assert md_path.exists()

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema_id"] == "hisys.codebase_evidence_portfolio.v1"
    assert data["current_head_short"] == "86684f4"
    assert data["source_lines"] == ["DARS_PANEL_LOCAL_COMPLETION", "M21"]
    assert data["implemented_surface_count"] == 14
    assert data["human_gated_surface_count"] == 2
    assert "hisys.change_impact.v1" in data["schema_ids"]
    assert data["advisory_only"] is True
```

**Verify RED:**

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py::test_codebase_evidence_portfolio_cli_writes_report -q
```

**Expected RED:** `argparse.ArgumentError` / `SystemExit: 2` (argparse rejects the unknown subcommand `codebase-evidence-portfolio`) — pytest reports the failure as a `SystemExit(2)`.

---

## Task 2: GREEN — implement the thin CLI subparser + dispatcher

**Objective:** Add the smallest CLI plumbing that satisfies the RED.

**Files:**

- Modify: `src/hisys/cli/main.py`

**Shape:**

1. Import the M22 module at the top of `main.py`:

   ```python
   from ..operations.codebase_evidence_portfolio import (
       CodebaseEvidencePortfolioRequest,
       EvidenceLineRef,
       build_codebase_evidence_portfolio_report,
       write_codebase_evidence_portfolio_report,
   )
   ```

2. Add a private loader that parses the bundle file into a tuple of `EvidenceLineRef`:

   ```python
   def _load_portfolio_line_bundle(path: Path) -> tuple[EvidenceLineRef, ...]:
       payload = _load_json_report(path)
       if payload is None:
           raise ValueError(f"portfolio bundle is required at {path}")
       refs = payload.get("line_refs")
       if not isinstance(refs, list):
           raise ValueError(
               f"portfolio bundle must contain a 'line_refs' list, got {type(refs).__name__}"
           )
       line_refs: list[EvidenceLineRef] = []
       for raw in refs:
           if not isinstance(raw, dict):
               raise ValueError("each portfolio bundle line_ref must be an object")
           line_refs.append(EvidenceLineRef(**raw))
       return tuple(line_refs)
   ```

3. Add a private dispatcher:

   ```python
   def _cmd_codebase_evidence_portfolio(
       *,
       instance_root: Path,
       yyyymmdd: str,
       line_bundle_path: Path,
       current_head_short: str | None,
   ) -> int:
       line_refs = _load_portfolio_line_bundle(line_bundle_path)
       request = CodebaseEvidencePortfolioRequest(
           instance_root=instance_root,
           date=yyyymmdd,
           line_refs=line_refs,
           current_head_short=current_head_short,
       )
       report = build_codebase_evidence_portfolio_report(request=request)
       written = write_codebase_evidence_portfolio_report(
           instance_root=instance_root, date=yyyymmdd, report=report
       )
       print(f"codebase-evidence-portfolio report: json={written['json_ref']}")
       print(f"markdown: {written['markdown_ref']}")
       print(f"source_line_count: {len(report.source_lines)}")
       print(f"artifact_ref_count: {len(report.artifact_refs)}")
       print(f"schema_id_count: {len(report.schema_ids)}")
       print(f"quality_gate_ref_count: {len(report.quality_gate_refs)}")
       print(f"implemented_surface_count: {report.implemented_surface_count}")
       print(f"human_gated_surface_count: {report.human_gated_surface_count}")
       print(f"unsafe_ref_count: {len(report.unsafe_refs)}")
       print(f"unsafe_line_label_count: {len(report.unsafe_line_labels)}")
       print("advisory_only: true")
       print("requires_human_review: true")
       print("external_call_made: false")
       print("mutation_performed: false")
       print("raw_source_content_persisted: false")
       print("allowed_actions: advisory_only")
       return 0
   ```

4. Register the subparser alongside `architecture-candidates`:

   ```python
   codebase_portfolio = sub.add_parser(
       "codebase-evidence-portfolio",
       help="write local advisory codebase evidence portfolio report artifacts",
   )
   codebase_portfolio.add_argument(
       "--instance", required=True, help="Hisys instance root"
   )
   codebase_portfolio.add_argument(
       "--date", required=True, help="YYYYMMDD report partition"
   )
   codebase_portfolio.add_argument(
       "--line-bundle",
       required=True,
       help="explicit caller-supplied JSON bundle path with 'line_refs'",
   )
   codebase_portfolio.add_argument(
       "--current-head-short",
       default=None,
       help="optional caller-supplied git HEAD short hash recorded verbatim",
   )
   ```

5. Add the dispatch branch in `main(...)` alongside `change-impact` / `architecture-candidates`:

   ```python
   if args.command == "codebase-evidence-portfolio":
       return _cmd_codebase_evidence_portfolio(
           instance_root=Path(args.instance),
           yyyymmdd=args.date,
           line_bundle_path=Path(args.line_bundle),
           current_head_short=args.current_head_short,
       )
   ```

**Verify GREEN:**

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py::test_codebase_evidence_portfolio_cli_writes_report -q
```

**Expected GREEN:** the CLI test passes.

---

## Task 3: Supplemental regression — bundle rejection, label/ref safety, bad-date propagation

**Objective:** Pin CLI-level safety invariants: malformed bundle, malformed line label, unsafe ref, bad date, and missing `line_refs` key must all propagate `ValueError` (or argparse-level errors when appropriate) rather than producing a partially written artifact.

**Files:**

- Modify: `tests/unit/test_domain_cli.py`

**Test sketch:**

```python
def test_codebase_evidence_portfolio_cli_rejects_missing_line_refs(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps({"not_line_refs": []}), encoding="utf-8")
    with pytest.raises(ValueError):
        main(
            [
                "codebase-evidence-portfolio",
                "--instance",
                str(instance_root),
                "--date",
                "20260521",
                "--line-bundle",
                str(bundle_path),
            ]
        )


def test_codebase_evidence_portfolio_cli_rejects_bad_date(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(
        json.dumps({"line_refs": [
            {
                "line_label": "M21",
                "artifact_refs": ["docs/plans/m21-1-traceability-coverage-report-implementation-tasks.md"],
            }
        ]}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        main(
            [
                "codebase-evidence-portfolio",
                "--instance",
                str(instance_root),
                "--date",
                "2026-05-21",
                "--line-bundle",
                str(bundle_path),
            ]
        )


def test_codebase_evidence_portfolio_cli_records_unsafe_inputs(tmp_path: Path, capsys) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(
        json.dumps({
            "line_refs": [
                {
                    "line_label": "M21",
                    "artifact_refs": [
                        "/etc/passwd",
                        "../escape.md",
                        "docs/plans/m21-1-traceability-coverage-report-implementation-tasks.md",
                    ],
                    "schema_ids": ["hisys.traceability.coverage.v1"],
                },
                {
                    "line_label": "lowercase-not-allowed",
                    "artifact_refs": ["docs/should-not-leak.md"],
                },
            ]
        }),
        encoding="utf-8",
    )
    result = main(
        [
            "codebase-evidence-portfolio",
            "--instance",
            str(instance_root),
            "--date",
            "20260521",
            "--line-bundle",
            str(bundle_path),
        ]
    )
    captured = capsys.readouterr()
    assert result == 0
    assert "unsafe_ref_count: 2" in captured.out
    assert "unsafe_line_label_count: 1" in captured.out
    json_path = (
        instance_root
        / "runtime-boundary"
        / "codebase-evidence-portfolio"
        / "20260521"
        / "portfolio-report.json"
    )
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert "/etc/passwd" in data["unsafe_refs"]
    assert "../escape.md" in data["unsafe_refs"]
    assert "lowercase-not-allowed" in data["unsafe_line_labels"]
    assert "docs/should-not-leak.md" not in data["artifact_refs"]
```

**Verify:**

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py -q -k codebase_evidence_portfolio
```

**Expected:** all M22 CLI tests pass; no other CLI test regressions.

---

## Task 4: Documentation, gate, and commit

**Files:**

- Modify: `docs/traceability/README.md` — prepend an `M22-CLI` row referencing the new subparser, dispatcher, tests, and the verified governance invariants.
- Modify: `ralph.md` — append a Reflection Log entry with Resume checkpoint, and rewrite Section 16 so the next safe Ralph row is `M22-PORTFOLIO-GOLDEN`.
- Modify: `docs/milestone-bootstrap/profile.yaml` — bump `version` to v0.0.18, `next_safe_task` to `M22-PORTFOLIO-GOLDEN`, refresh `planning_baseline_head` / `current_head_at_plan_creation` to the new HEAD label.
- Modify: `tests/unit/test_governance_docs_current_state.py` — assert `v0.0.18` and `M22-PORTFOLIO-GOLDEN`.

**Validation:**

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py tests/unit/test_codebase_evidence_portfolio.py tests/unit/test_change_impact.py tests/unit/test_architecture_candidates.py tests/unit/test_code_analysis_pass_contract.py tests/unit/test_subagent_evidence_collector_protocol.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_governance_docs_current_state.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit:**

```bash
git add src/hisys/cli/main.py tests/unit/test_domain_cli.py docs/plans/m22-cli-codebase-evidence-portfolio-implementation-tasks.md docs/traceability/README.md ralph.md docs/milestone-bootstrap/profile.yaml tests/unit/test_governance_docs_current_state.py
git commit -m "feat: add codebase-evidence-portfolio CLI wrapper"
```

---

## Stop conditions

Stop and ask for a new decision if any task would require:

- adding network/browser/connector/model/LSP/subprocess invocation in the CLI;
- credential lookup or persistence in the CLI;
- `runtime-boundary/` directory crawling, latest-artifact inference, or auto-discovery of bundle files;
- reading `.git/` directly or calling `date.today()` in the CLI;
- changing `EvidenceLineRef` / `CodebaseEvidencePortfolioRequest` / `CodebaseEvidencePortfolioReport` shapes in this increment (those changes require a separate RED on the pure module);
- expanding the report into approval/safe-to-deploy/readiness language;
- adding the golden-fixture work in this increment (deferred to `M22-PORTFOLIO-GOLDEN`).

## Out of scope for M22-PORTFOLIO-CLI (deferred)

- Golden-fixture round-trip test pinning a deterministic JSON/Markdown bundle (M22-PORTFOLIO-GOLDEN).
- Cross-line schema-id deep validation (the M21.3 consistency checker already covers that).
- Auto-discovery of M21/DARS artifacts from `runtime-boundary/`.
- Live-provider DARS panel execution (separately governed).
- Approved OSS comparison adapter / optional local LSP adapter (human-gated).
- Any change to existing M21/M22 schema shapes.

## Next executable action

After this Prepare plan is committed and pushed (normal push to existing `origin/dars`), run the RED command:

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py::test_codebase_evidence_portfolio_cli_writes_report -q
```

Expected failure: argparse rejects the unknown subcommand `codebase-evidence-portfolio` (`SystemExit: 2`).
