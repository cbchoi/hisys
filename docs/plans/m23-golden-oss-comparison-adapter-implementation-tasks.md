# Milestone M23 — OSS Comparison Adapter Golden Round-Trip Implementation Task Plan

> **Row:** This document is the artifact produced by Ralph row `M23-OSS-ADAPTER-GOLDEN`. The pure adapter landed at `d610c53 feat: add oss comparison adapter`; the CLI wrapper landed at `d6023b4 feat: add oss comparison adapter cli wrapper`. This row pins one canonical byte-equality round-trip so any future shape/serialization drift fails one focused test.

> **For Hermes/Ralph:** Use `software-development:test-driven-development`. Mirror the M22-PORTFOLIO-GOLDEN deterministic byte-equality pattern (`tests/fixtures/codebase-evidence-portfolio/`). No new dependency, no network, no `subprocess`, no `.git/`, no `date.today()`, no `runtime-boundary/` crawl, no auto-discovery.

**Goal:** Add `tests/fixtures/oss-comparison/m23_local_oss_bundle.json` (a canonical caller-authored bundle) and `tests/fixtures/oss-comparison/expected/comparison-report.{json,md}` (the deterministic output), plus one focused round-trip test `test_oss_comparison_adapter_golden_round_trip` in `tests/unit/test_oss_comparison_adapter.py` that loads the bundle, calls the M23 builder + writer, and asserts byte-equality against the checked-in expected files. The fixture must not embed raw OSS source bodies, license texts beyond bounded `license_tag` strings, or secrets.

**Architecture:** No new module. The test loads the JSON bundle through plain `json.loads`, constructs Pydantic records, runs `build_oss_comparison_report` and `write_oss_comparison_report` against a `tmp_path` instance root, then byte-compares the resulting `runtime-boundary/oss-comparison/<YYYYMMDD>/comparison-report.{json,md}` to the checked-in expected files.

**Tech Stack:** Python 3.11, json, pathlib, pytest. No new dependency.

**Context Packet:**

- `tests/unit/test_codebase_evidence_portfolio.py` — `test_codebase_evidence_portfolio_golden_round_trip` is the sibling golden test pattern to mirror.
- `tests/fixtures/codebase-evidence-portfolio/m21_dars_bundle.json` + `tests/fixtures/codebase-evidence-portfolio/expected/portfolio-report.{json,md}` — sibling fixture layout.
- `src/hisys/operations/oss_comparison_adapter.py` — builder/writer chokepoint.
- `docs/plans/m23-oss-comparison-adapter-implementation-tasks.md` — parent M23 OSS adapter PREP.
- `docs/plans/m22-golden-codebase-evidence-portfolio-implementation-tasks.md` — sibling GOLDEN PREP shape.
- `docs/traceability/README.md`, `docs/milestone-bootstrap/profile.yaml`, `tests/unit/test_governance_docs_current_state.py`, `ralph.md`.

**Boundary Record:** Fixture-local pinning only. The fixture is plain JSON pinning labels, ids, license tags, category strings, refs, and counts. No upstream OSS source bodies, license texts, diff hunks, secrets, runtime artifact JSON contents, or binary content is embedded. No live network access, model invocation, subprocess, system clock, or `.git/` read happens at any time. The expected files are generated deterministically by the same builder/writer chokepoint the test exercises; they are never hand-edited.

---

## Accepted decisions

1. **Single canonical bundle.** The bundle pins `date="20260522"`, fixed `current_head_short="d6023b4"`, one `local_line` (`M21` evidence line), and two `approved_sources` (`understand-static-analysis` n/a, `pylint-style-rules` GPL-2.0-or-later). No fuzz, no randomness, no system-clock dependence.
2. **Bundle and expected files are byte-stable.** The expected JSON uses `json.dumps(..., indent=2, sort_keys=True) + "\n"` exactly as the writer emits; the expected Markdown is the writer output verbatim.
3. **No regeneration in the test.** The test loads the expected files and byte-compares; it never overwrites them. Regeneration happens only when a Ralph row deliberately updates the fixture, and the diff is committed alongside the schema/render change.
4. **Caller-authored bundle.** The bundle is committed as a JSON artifact under `tests/fixtures/oss-comparison/`. The test does not crawl `runtime-boundary/`, does not list `docs/`, and does not auto-discover bundle files.
5. **No upstream source bodies, license texts, or secrets.** The fixture contains only bounded label/version/scope/notes strings and refs that point to checked-in repository paths (not third-party URLs).

---

## Task 0: Reconstruct baseline before any edit

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_oss_comparison_adapter.py tests/unit/test_codebase_evidence_portfolio.py tests/unit/test_domain_cli.py tests/unit/test_governance_docs_current_state.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

Expected: branch `dars`, HEAD at or after `d6023b4 feat: add oss comparison adapter cli wrapper`; combined gate passes; traceability OK; secrets `hit_count=0`; diff-check clean.

---

## Task 1: Author canonical bundle JSON

**Files:**

- Create: `tests/fixtures/oss-comparison/m23_local_oss_bundle.json`

The bundle contains exactly:

```json
{
  "date": "20260522",
  "current_head_short": "d6023b4",
  "local_line": {
    "line_label": "M21",
    "category_refs": [
      "architecture_candidates",
      "change_impact",
      "code_analysis_pass_contract",
      "codebase_map_freshness",
      "runtime_boundary_consistency",
      "subagent_evidence_collector_protocol",
      "traceability_coverage"
    ],
    "portfolio_refs": [
      "docs/plans/m21-1-traceability-coverage-report-implementation-tasks.md",
      "docs/plans/m21-6-change-impact-analyzer-implementation-tasks.md",
      "docs/plans/m21-7-architecture-candidate-generator-implementation-tasks.md"
    ],
    "implemented_surface_count": 9,
    "human_gated_surface_count": 2
  },
  "approved_sources": [
    {
      "source_id": "understand-static-analysis",
      "source_name": "Approved static-analysis reference",
      "license_tag": "n/a",
      "category_refs": [
        "architecture_candidates",
        "change_impact",
        "traceability_coverage"
      ],
      "approved_refs": [
        "docs/plans/m23-advanced-codebase-adapter-integration-plan.md"
      ],
      "local_fixture_refs": [
        "tests/fixtures/oss/approved/understand-static-analysis.json"
      ],
      "notes": "Local fixture descriptor only; no upstream content fetched."
    },
    {
      "source_id": "pylint-style-rules",
      "source_name": "Approved style/lint reference",
      "license_tag": "GPL-2.0-or-later",
      "category_refs": [
        "code_analysis_pass_contract",
        "runtime_boundary_consistency",
        "style_conventions"
      ],
      "approved_refs": [
        "docs/plans/m23-advanced-codebase-adapter-integration-plan.md"
      ],
      "local_fixture_refs": [
        "tests/fixtures/oss/approved/pylint-style-rules.json"
      ],
      "notes": "Local fixture descriptor only."
    }
  ]
}
```

---

## Task 2: RED — add the golden round-trip test

Add `test_oss_comparison_adapter_golden_round_trip(tmp_path)` to `tests/unit/test_oss_comparison_adapter.py` that loads the bundle, constructs the records, runs the builder + writer, then reads `tests/fixtures/oss-comparison/expected/comparison-report.{json,md}` and asserts byte-equality.

**Verify RED:**

```bash
PYTHONPATH=src pytest tests/unit/test_oss_comparison_adapter.py::test_oss_comparison_adapter_golden_round_trip -q
```

**Expected RED:** `FileNotFoundError` because the expected fixtures have not been created yet.

---

## Task 3: GREEN — generate the expected fixtures deterministically

Run the builder + writer against the bundle and a temporary instance root; copy the resulting `runtime-boundary/oss-comparison/20260522/comparison-report.{json,md}` into `tests/fixtures/oss-comparison/expected/`. The generation script must use the same chokepoint the test exercises — no hand-editing.

A one-liner generator (run from the repo root, captured by the Ralph row, not committed as a script):

```bash
PYTHONPATH=src python3 -c "
import json
from pathlib import Path
from hisys.operations.oss_comparison_adapter import (
    ApprovedOssSource,
    LocalCodebaseLine,
    OssComparisonRequest,
    build_oss_comparison_report,
    write_oss_comparison_report,
)

fixture_dir = Path('tests/fixtures/oss-comparison')
bundle = json.loads((fixture_dir / 'm23_local_oss_bundle.json').read_text('utf-8'))
expected_dir = fixture_dir / 'expected'
expected_dir.mkdir(parents=True, exist_ok=True)

local_line = LocalCodebaseLine(**bundle['local_line'])
approved_sources = tuple(ApprovedOssSource(**s) for s in bundle['approved_sources'])
import tempfile
with tempfile.TemporaryDirectory() as td:
    instance_root = Path(td)
    request = OssComparisonRequest(
        instance_root=instance_root,
        date=bundle['date'],
        local_line=local_line,
        approved_sources=approved_sources,
        current_head_short=bundle['current_head_short'],
    )
    report = build_oss_comparison_report(request=request)
    write_oss_comparison_report(instance_root=instance_root, date=bundle['date'], report=report)
    base = instance_root / 'runtime-boundary' / 'oss-comparison' / bundle['date']
    (expected_dir / 'comparison-report.json').write_text(
        (base / 'comparison-report.json').read_text('utf-8'), 'utf-8'
    )
    (expected_dir / 'comparison-report.md').write_text(
        (base / 'comparison-report.md').read_text('utf-8'), 'utf-8'
    )
print('expected fixtures regenerated')
"
```

**Verify GREEN:**

```bash
PYTHONPATH=src pytest tests/unit/test_oss_comparison_adapter.py::test_oss_comparison_adapter_golden_round_trip -q
PYTHONPATH=src pytest tests/unit/test_oss_comparison_adapter.py -q
```

Expected: golden test passes; all 7 OSS comparison adapter tests pass.

---

## Task 4: Documentation, gate, and commit

- Modify: `docs/traceability/README.md` — prepend an `M23-OSS-ADAPTER-GOLDEN` row referencing the bundle, expected fixtures, and the byte-equality test.
- Modify: `docs/milestone-bootstrap/profile.yaml` — bump version to `v0.0.25`, set `next_safe_task: M23-OSS-ADAPTER-GATE`, refresh `planning_baseline_head` and `current_head_at_plan_creation` to the M23-OSS-ADAPTER-CLI commit `d6023b4`.
- Modify: `tests/unit/test_governance_docs_current_state.py` — assert `v0.0.25` and `M23-OSS-ADAPTER-GATE`.
- Modify: `ralph.md` — append a Reflection Log entry with Resume checkpoint and rewrite Section 16 so the next safe Ralph row is `M23-OSS-ADAPTER-GATE`.

**Validation:**

```bash
PYTHONPATH=src pytest tests/unit/test_oss_comparison_adapter.py tests/unit/test_domain_cli.py tests/unit/test_codebase_evidence_portfolio.py tests/unit/test_change_impact.py tests/unit/test_architecture_candidates.py tests/unit/test_code_analysis_pass_contract.py tests/unit/test_subagent_evidence_collector_protocol.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_governance_docs_current_state.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit:**

```bash
git add tests/fixtures/oss-comparison/ tests/unit/test_oss_comparison_adapter.py docs/traceability/README.md docs/milestone-bootstrap/profile.yaml tests/unit/test_governance_docs_current_state.py docs/plans/m23-golden-oss-comparison-adapter-implementation-tasks.md ralph.md
git commit -m "test: pin oss comparison adapter golden fixture"
git push origin dars
```

---

## Stop conditions

Stop and ask if any task would require live network, OSS clone/install, license-text capture, model invocation, subprocess from the test, `.git/` read from production code, `date.today()` from production code, or anything that mutates non-fixture data.

## Out of scope

- Multiple variant bundles (single canonical bundle in this row).
- CLI golden round-trip (the CLI is already tested at the value level; a CLI golden bytes round-trip would only duplicate coverage).
- Variant license tags or license adjudication (license-tag remains an opaque caller-supplied label).
