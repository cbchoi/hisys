# Milestone M23 — OSS Comparison Adapter CLI Implementation Task Plan

> **Row:** This document is the artifact produced by Ralph row `M23-OSS-ADAPTER-CLI`. The pure adapter and writer landed in `M23-OSS-ADAPTER-RED-GREEN` at commit `d610c53 feat: add oss comparison adapter`; this row only adds a thin argparse pass-through.

> **For Hermes/Ralph:** Use `software-development:test-driven-development`. The CLI is bundled into one Ralph increment (PREP + RED + GREEN + regression) because it is a thin JSON-bundle pass-through over the already-tested pure module. The CLI must not weaken any M23 OSS adapter invariant.

**Goal:** Add a `hisys oss-comparison-adapter` argparse subcommand that loads one caller-supplied JSON bundle and dispatches to `build_oss_comparison_report` + `write_oss_comparison_report`, printing bounded summary lines. The CLI never crawls `tests/fixtures/`, never crawls `runtime-boundary/`, never reads `.git/`, never calls `subprocess`, never calls `date.today()`, never installs OSS packages, never opens upstream OSS source, never auto-discovers bundle files, never adjudicates licenses, and never expands the source-id / line-label / category vocabulary.

**Architecture:** Add to `src/hisys/cli/main.py`:

1. A new module-level import block for `ApprovedOssSource`, `LocalCodebaseLine`, `OssComparisonRequest`, `build_oss_comparison_report`, and `write_oss_comparison_report` from `hisys.operations.oss_comparison_adapter`.
2. A `_load_oss_comparison_bundle(path)` helper that reuses the existing `_load_json_report` reader and returns `(LocalCodebaseLine, tuple[ApprovedOssSource, ...])`. The helper requires the JSON payload to be a top-level object with `local_line: object` and `approved_sources: list[object]`; mismatches raise `ValueError` with a precise message.
3. A `_cmd_oss_comparison_adapter(*, instance_root, yyyymmdd, bundle_path, current_head_short)` dispatcher that constructs the request, calls the builder, calls the writer, and prints the bounded summary lines documented below. Returns exit code `0` on success and propagates `ValueError` non-zero (the existing CLI top-level error handling carries them up).
4. A new `sub.add_parser("oss-comparison-adapter", ...)` subparser with `--instance`, `--date`, `--bundle`, and `--current-head-short` arguments. Mirror the existing M22 `codebase-evidence-portfolio` subparser's help text style.
5. A dispatcher branch `if args.command == "oss-comparison-adapter": return _cmd_oss_comparison_adapter(...)`.

**Output lines (bounded; mirrors the M22 portfolio CLI shape):**

```text
oss-comparison-adapter report: json=<json_ref>
markdown: <markdown_ref>
compared_source_count: <int>
union_category_count: <int>
intersection_category_count: <int>
local_only_category_count: <int>
oss_only_category_count: <int>
unsafe_ref_count: <int>
unsafe_source_id_count: <int>
unsafe_line_label_count: <int>
advisory_only: true
requires_human_review: true
external_call_made: false
mutation_performed: false
raw_source_content_persisted: false
live_external_action_authorized: false
allowed_actions: advisory_only
```

**Bundle JSON shape (caller-authored):**

```json
{
  "local_line": {
    "line_label": "M21",
    "category_refs": ["traceability_coverage", "change_impact"],
    "portfolio_refs": ["docs/plans/m21-1-traceability-coverage-report-implementation-tasks.md"],
    "implemented_surface_count": 9,
    "human_gated_surface_count": 2
  },
  "approved_sources": [
    {
      "source_id": "understand-static-analysis",
      "source_name": "Approved static-analysis reference",
      "license_tag": "n/a",
      "category_refs": ["traceability_coverage"],
      "approved_refs": ["docs/plans/m23-advanced-codebase-adapter-integration-plan.md"],
      "local_fixture_refs": ["tests/fixtures/oss/approved/understand-static-analysis.json"],
      "notes": "Local fixture descriptor only."
    }
  ]
}
```

**Tech Stack:** Python 3.11 argparse, json, pathlib. No new dependency. The CLI re-imports the existing M23 Pydantic models from `hisys.operations.oss_comparison_adapter` so it does not duplicate shape definitions.

**Context Packet:**

- `src/hisys/cli/main.py` — current argparse subparser table and dispatcher branches (insert before `evaluate-code-analysis-contract`).
- `src/hisys/operations/oss_comparison_adapter.py` — M23 builder/writer and Pydantic models.
- `tests/unit/test_domain_cli.py` — mirror the M22 `test_codebase_evidence_portfolio_cli_*` test layout.
- `docs/plans/m22-cli-codebase-evidence-portfolio-implementation-tasks.md` — sibling CLI PREP/RED/GREEN format.
- `docs/traceability/README.md` — top-of-file row prepended in this row.
- `docs/milestone-bootstrap/profile.yaml` v0.0.23 — `next_safe_task: M23-OSS-ADAPTER-CLI` before this row; bump to v0.0.24 / `M23-OSS-ADAPTER-GOLDEN` after commit.
- `tests/unit/test_governance_docs_current_state.py` — bump assertions in lockstep.
- `ralph.md` Reflection Log + Section 16 — append checkpoint and rewrite next-row pointer.

**Boundary Record:** Fixture-local CLI plumbing only. The dispatcher delegates to the M23-OSS-ADAPTER-RED-GREEN pure module; it makes no live model call, no remote provider call, no network clone/fetch/search, no credential lookup, no `subprocess`, no `.git/` read, no `date.today()`, no `runtime-boundary/` crawl, no auto-discovery of bundle files, no opening of `local_fixture_refs` to verify existence, no LSP subprocess, no subagent execution, no publication/deployment, no schema/data migration, no force push, no new remote configuration, no destructive operation, no raw upstream source-content archival, no license adjudication.

---

## Accepted decisions

1. **JSON bundle pass-through.** A single `--bundle <path>` flag points at a JSON object containing `local_line` plus `approved_sources`. Bundle mismatches raise `ValueError`; the CLI does not synthesize defaults, infer from `runtime-boundary/`, or auto-pick fixture files.
2. **Reuse of existing JSON loader.** The bundle loader builds on `_load_json_report`; it does not introduce a parallel reader.
3. **Pydantic-constructed records.** `LocalCodebaseLine`, `ApprovedOssSource`, and `OssComparisonRequest` are constructed from the bundle dicts via Pydantic so the CLI cannot drift from the M23 shape.
4. **Bounded summary lines.** The CLI prints fixed-key summary lines mirroring M22; no human-readable narrative, no markdown injection, no path expansion, no listing of refs.
5. **No CLI-side date generation.** `--date` is required and passed verbatim. `--current-head-short` is optional and recorded verbatim. The CLI never reads the system clock or `.git/`.
6. **Existing top-level error propagation.** `ValueError` from the builder/writer propagates through argparse handling unchanged (the M22 portfolio CLI follows the same convention; tests assert this with `pytest.raises(ValueError)`).
7. **No vocabulary expansion.** The CLI accepts whatever bundle dicts the caller provides; pattern validation continues to live in the builder.

---

## Task 0: Reconstruct baseline before any edit

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_oss_comparison_adapter.py tests/unit/test_codebase_evidence_portfolio.py tests/unit/test_governance_docs_current_state.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

Expected: branch `dars`, HEAD at or after `d610c53 feat: add oss comparison adapter`; combined gate passes; traceability OK; secrets `hit_count=0`; diff-check clean.

---

## Task 1: RED — four CLI tests in `tests/unit/test_domain_cli.py`

Add four focused tests at the end of `tests/unit/test_domain_cli.py`:

1. `test_oss_comparison_adapter_cli_writes_report` — happy-path round-trip: write bundle JSON, invoke `main(["oss-comparison-adapter", ...])`, assert exit code 0, summary lines, JSON and Markdown artifacts exist under `runtime-boundary/oss-comparison/20260522/comparison-report.{json,md}`, JSON contains the M23 advisory flag set and expected counts.
2. `test_oss_comparison_adapter_cli_rejects_missing_local_line` — bundle without `local_line` raises `ValueError`.
3. `test_oss_comparison_adapter_cli_rejects_bad_date` — `--date 2026-05-22` raises `ValueError` from the builder.
4. `test_oss_comparison_adapter_cli_records_unsafe_inputs` — bundle with `/etc/passwd`, `../escape.md`, `UPPERCASE_SOURCE`, and a `\x00binary` notes value exits 0 but records the rejected refs and source ids in the persisted report; the unsafe artifacts do NOT appear in the safe sets.

**Verify RED before adding the production dispatcher:**

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py::test_oss_comparison_adapter_cli_writes_report -q
```

Expected RED: `SystemExit: 2` (argparse rejecting the unknown subcommand) or equivalent error before the subparser/dispatcher exists.

---

## Task 2: GREEN — implement bundle loader, dispatcher, subparser, and dispatcher branch

**Files:**

- Modify: `src/hisys/cli/main.py` — add imports, `_load_oss_comparison_bundle`, `_cmd_oss_comparison_adapter`, the `oss-comparison-adapter` subparser, and the dispatcher branch.

**Verify GREEN:**

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py -k oss_comparison_adapter -q
PYTHONPATH=src pytest tests/unit/test_domain_cli.py tests/unit/test_oss_comparison_adapter.py tests/unit/test_codebase_evidence_portfolio.py -q
```

Expected GREEN: four CLI tests pass; M22 portfolio + M23 builder tests still pass.

---

## Task 3: Documentation, gate, and commit

- Modify: `docs/traceability/README.md` — prepend an `M23-OSS-ADAPTER-CLI` row.
- Modify: `docs/milestone-bootstrap/profile.yaml` — bump version to `v0.0.24`, set `next_safe_task: M23-OSS-ADAPTER-GOLDEN`, refresh `planning_baseline_head` and `current_head_at_plan_creation` to the M23-OSS-ADAPTER-RED-GREEN commit `d610c53`.
- Modify: `tests/unit/test_governance_docs_current_state.py` — assert `v0.0.24` and `M23-OSS-ADAPTER-GOLDEN`.
- Modify: `ralph.md` — append a Reflection Log entry with Resume checkpoint and rewrite Section 16 so the next safe Ralph row is `M23-OSS-ADAPTER-GOLDEN`.

**Validation:**

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py tests/unit/test_oss_comparison_adapter.py tests/unit/test_codebase_evidence_portfolio.py tests/unit/test_change_impact.py tests/unit/test_architecture_candidates.py tests/unit/test_code_analysis_pass_contract.py tests/unit/test_subagent_evidence_collector_protocol.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_governance_docs_current_state.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit:**

```bash
git add tests/unit/test_domain_cli.py src/hisys/cli/main.py docs/traceability/README.md docs/milestone-bootstrap/profile.yaml tests/unit/test_governance_docs_current_state.py docs/plans/m23-cli-oss-comparison-adapter-implementation-tasks.md ralph.md
git commit -m "feat: add oss comparison adapter cli wrapper"
git push origin dars
```

---

## Stop conditions

Stop and ask if any task would require credential lookup, network fetch/clone/install, raw OSS source archival, license adjudication, subprocess from the CLI module, `.git/` read, `date.today()`, `runtime-boundary/` crawl, `tests/fixtures/` crawl, auto-discovery of bundle files, opening `local_fixture_refs` to verify existence, force push, new remote configuration, publication, deployment, or LSP subprocess spawning.

## Out of scope

- Golden round-trip fixture for the CLI (deferred to `M23-OSS-ADAPTER-GOLDEN`).
- CLI argument grouping (`--local-line-label`, `--source-id`, ...) instead of the JSON bundle. The JSON bundle is the chosen surface and mirrors M22.
- Live OSS provider invocation, LSP subprocess, license verification, repo cloning, package installation.
