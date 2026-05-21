# Milestone M23 — LSP Adapter Golden Round-Trip Implementation Task Plan

> **Row:** This document is the artifact produced by Ralph row `M23-LSP-ADAPTER-GOLDEN`. The pure governed runner landed at `1874ad5 feat: add local lsp adapter`; the CLI wrapper landed at `e54bbf3 feat: add lsp adapter cli wrapper`. This row pins one canonical byte-equality round-trip so any future shape/serialization drift in `LspAdapterReport` or `render_lsp_adapter_markdown` fails one focused test.

> **For Hermes/Ralph:** Use `software-development:test-driven-development`. Mirror the M23-OSS-ADAPTER-GOLDEN deterministic byte-equality pattern (`tests/fixtures/oss-comparison/`). No new dependency, no network, no real `subprocess` invocation (the test monkey-patches `subprocess.run`), no `.git/`, no `date.today()`, no `runtime-boundary/` crawl, no auto-discovery.

**Goal:** Add `tests/fixtures/lsp-adapter/m23_lsp_bundle.json` (a canonical caller-authored input bundle) and `tests/fixtures/lsp-adapter/expected/lsp-report.{json,md}` (the deterministic writer output), plus one focused round-trip test `test_lsp_adapter_golden_round_trip` in `tests/unit/test_lsp_adapter.py` that loads the bundle, monkey-patches `subprocess.run` to return the existing canned ruff JSON, calls `run_lsp_adapter` + `write_lsp_adapter_report`, and asserts byte-equality against the checked-in expected files. The fixture must not embed raw upstream source bodies, raw diagnostic messages, license texts, or secrets.

**Architecture:** No new module. The test loads the JSON bundle through plain `json.loads`, constructs Pydantic records, sets up a workspace under `tmp_path` whose layout matches the canned ruff JSON file refs (`src/a.py`, `src/b.py`), monkey-patches `subprocess.run` to return `subprocess.CompletedProcess(stdout=canned, returncode=1)`, runs `run_lsp_adapter` and `write_lsp_adapter_report` against the `tmp_path` instance root, then byte-compares the resulting `runtime-boundary/lsp-adapter/<YYYYMMDD>/<command_id>/lsp-report.{json,md}` to the checked-in expected files.

**Tech Stack:** Python 3.11, json, pathlib, pytest, unittest.mock. No new dependency.

**Context Packet:**

- `tests/unit/test_oss_comparison_adapter.py` — `test_oss_comparison_adapter_golden_round_trip` is the sibling golden test pattern to mirror.
- `tests/fixtures/oss-comparison/m23_local_oss_bundle.json` + `tests/fixtures/oss-comparison/expected/comparison-report.{json,md}` — sibling fixture layout.
- `tests/fixtures/lsp-adapter/ruff/canned_ruff_output.json` — already checked-in canned ruff stdout from M23-LSP-ADAPTER-RED-GREEN.
- `src/hisys/operations/lsp_adapter.py` — builder/writer chokepoint.
- `docs/plans/m23-lsp-adapter-implementation-tasks.md` — parent M23 LSP adapter PREP.
- `docs/plans/m23-cli-lsp-adapter-implementation-tasks.md` — sibling CLI PREP.
- `docs/plans/m23-golden-oss-comparison-adapter-implementation-tasks.md` — sibling GOLDEN PREP shape.
- `docs/traceability/README.md`, `docs/milestone-bootstrap/profile.yaml`, `tests/unit/test_governance_docs_current_state.py`, `ralph.md`.

**Boundary Record:** Fixture-local pinning only. The bundle is plain JSON pinning the command id/argv/timeout/format, target refs, allowlist, approval ref, date, and current_head_short. No upstream source bodies, raw diagnostic messages, license texts, diff hunks, secrets, runtime artifact JSON contents, or binary content is embedded — only severity/code/file_ref/line/column/category_ref/message_digest fields (the digest is SHA-256 first-16-hex of the raw message and is itself non-reversible). No live network access, no real LSP server invocation, no model invocation, no real `subprocess` call, no system clock, and no `.git/` read happens at any time. The expected files are generated deterministically by the same builder/writer chokepoint the test exercises; they are never hand-edited.

---

## Accepted decisions

1. **Single canonical bundle.** The bundle pins `date="20260522"`, fixed `current_head_short="e54bbf3"`, one `command_id="ruff-check"`, fixed `argv=["ruff", "check", "--output-format=json", "src/"]`, `timeout_seconds=30`, `expected_exit_codes=[0, 1]`, `output_format="ruff_json"`, fixed `target_refs=["src/a.py", "src/b.py"]`, fixed `command_allowlist=["ruff"]`, fixed `human_approval_ref="docs/approvals/lsp-adapter-2026-05-22.md"`, and `canned_stdout_ref="tests/fixtures/lsp-adapter/ruff/canned_ruff_output.json"`. No fuzz, no randomness, no system-clock dependence.
2. **Reuse the existing canned ruff stdout.** The bundle references `tests/fixtures/lsp-adapter/ruff/canned_ruff_output.json` (committed at M23-LSP-ADAPTER-RED-GREEN at `1874ad5`); no new canned file is added.
3. **Bundle and expected files are byte-stable.** The expected JSON uses `json.dumps(..., indent=2, sort_keys=True) + "\n"` exactly as the writer emits; the expected Markdown is the writer output verbatim.
4. **No regeneration in the test.** The test loads the expected files and byte-compares; it never overwrites them. Regeneration happens only when a Ralph row deliberately updates the fixture, and the diff is committed alongside the schema/render change.
5. **Caller-authored bundle.** The bundle is committed as a JSON artifact under `tests/fixtures/lsp-adapter/`. The test does not crawl `runtime-boundary/`, does not list `docs/`, and does not auto-discover bundle files.
6. **No raw text leakage.** The fixture contains only severity/code/line/column/category/message_digest refs in the expected Markdown table; the raw diagnostic messages are never embedded in the expected files (they remain only in the canned ruff stdout fixture, which is itself a public test bundle pinning code prefixes — not secrets).
7. **`subprocess.run` is monkey-patched.** No real `ruff` binary is executed by the test suite. The test fakes the subprocess call with a `MagicMock` returning the canned stdout.

---

## Task 0: Reconstruct baseline before any edit

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_lsp_adapter.py tests/unit/test_oss_comparison_adapter.py tests/unit/test_codebase_evidence_portfolio.py tests/unit/test_domain_cli.py tests/unit/test_governance_docs_current_state.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

Expected: branch `dars`, HEAD at or after `e54bbf3 feat: add lsp adapter cli wrapper`; combined gate passes; traceability OK; secrets `hit_count=0`; diff-check clean.

---

## Task 1: Author canonical bundle JSON

**Files:**

- Create: `tests/fixtures/lsp-adapter/m23_lsp_bundle.json`

The bundle contains exactly:

```json
{
  "date": "20260522",
  "current_head_short": "e54bbf3",
  "command": {
    "command_id": "ruff-check",
    "argv": ["ruff", "check", "--output-format=json", "src/"],
    "timeout_seconds": 30,
    "expected_exit_codes": [0, 1],
    "output_format": "ruff_json"
  },
  "target_refs": ["src/a.py", "src/b.py"],
  "command_allowlist": ["ruff"],
  "human_approval_ref": "docs/approvals/lsp-adapter-2026-05-22.md",
  "canned_stdout_ref": "tests/fixtures/lsp-adapter/ruff/canned_ruff_output.json"
}
```

---

## Task 2: RED — add the golden round-trip test

Add `test_lsp_adapter_golden_round_trip(tmp_path, monkeypatch)` to `tests/unit/test_lsp_adapter.py` that:

1. Loads the bundle JSON.
2. Sets up `instance_root/workspace` plus `src/a.py`, `src/b.py` empty placeholder files (the ruff fixture references these refs).
3. Reads the canned ruff stdout from `bundle["canned_stdout_ref"]`.
4. Monkey-patches `subprocess.run` to return `subprocess.CompletedProcess(returncode=1, stdout=canned)`.
5. Constructs `LspAdapterCommand`, `LspAdapterRequest` from the bundle dicts.
6. Calls `run_lsp_adapter` and `write_lsp_adapter_report`.
7. Reads `tests/fixtures/lsp-adapter/expected/lsp-report.json` and `lsp-report.md` and asserts byte-equality with the persisted artifacts.

**Verify RED:**

```bash
PYTHONPATH=src pytest tests/unit/test_lsp_adapter.py::test_lsp_adapter_golden_round_trip -q
```

**Expected RED:** `FileNotFoundError` because the expected fixtures have not been created yet.

---

## Task 3: GREEN — generate the expected fixtures deterministically

Run the builder + writer against the bundle and a temporary instance root; copy the resulting `runtime-boundary/lsp-adapter/20260522/ruff-check/lsp-report.{json,md}` into `tests/fixtures/lsp-adapter/expected/`. The generation script must use the same chokepoint the test exercises — no hand-editing.

A one-liner generator (run from the repo root, captured by the Ralph row, not committed as a script):

```bash
PYTHONPATH=src python3 -c "
import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from hisys.operations.lsp_adapter import (
    LspAdapterCommand,
    LspAdapterRequest,
    run_lsp_adapter,
    write_lsp_adapter_report,
)

fixture_dir = Path('tests/fixtures/lsp-adapter')
bundle = json.loads((fixture_dir / 'm23_lsp_bundle.json').read_text('utf-8'))
canned = (Path('.') / bundle['canned_stdout_ref']).read_text('utf-8')
expected_dir = fixture_dir / 'expected'
expected_dir.mkdir(parents=True, exist_ok=True)

with tempfile.TemporaryDirectory() as td:
    instance_root = Path(td)
    workspace_root = instance_root / 'workspace'
    workspace_root.mkdir()
    (workspace_root / 'src').mkdir()
    (workspace_root / 'src' / 'a.py').write_text('', 'utf-8')
    (workspace_root / 'src' / 'b.py').write_text('', 'utf-8')
    command = LspAdapterCommand(**bundle['command'])
    request = LspAdapterRequest(
        instance_root=instance_root,
        date=bundle['date'],
        workspace_root=workspace_root,
        command=command,
        target_refs=tuple(bundle['target_refs']),
        command_allowlist=tuple(bundle['command_allowlist']),
        human_approval_ref=bundle['human_approval_ref'],
        current_head_short=bundle['current_head_short'],
    )
    original_run = subprocess.run
    fake_run = MagicMock()
    fake_run.return_value = subprocess.CompletedProcess(
        args=list(command.argv), returncode=1, stdout=canned, stderr=''
    )
    subprocess.run = fake_run
    try:
        report = run_lsp_adapter(request=request)
        write_lsp_adapter_report(
            instance_root=instance_root, date=bundle['date'], report=report
        )
    finally:
        subprocess.run = original_run
    base = (
        instance_root / 'runtime-boundary' / 'lsp-adapter'
        / bundle['date'] / command.command_id
    )
    (expected_dir / 'lsp-report.json').write_text(
        (base / 'lsp-report.json').read_text('utf-8'), 'utf-8'
    )
    (expected_dir / 'lsp-report.md').write_text(
        (base / 'lsp-report.md').read_text('utf-8'), 'utf-8'
    )
print('expected fixtures regenerated')
"
```

**Verify GREEN:**

```bash
PYTHONPATH=src pytest tests/unit/test_lsp_adapter.py::test_lsp_adapter_golden_round_trip -q
PYTHONPATH=src pytest tests/unit/test_lsp_adapter.py -q
```

Expected: golden test passes; all 14 LSP adapter tests pass.

---

## Task 4: Documentation, gate, and commit

- Modify: `docs/traceability/README.md` — prepend an `M23-LSP-ADAPTER-GOLDEN` row referencing the bundle, expected fixtures, and the byte-equality test.
- Modify: `docs/milestone-bootstrap/profile.yaml` — bump version to `v0.0.30`, set `next_safe_task: M23-LSP-ADAPTER-GATE`, refresh `planning_baseline_head` and `current_head_at_plan_creation` to the M23-LSP-ADAPTER-CLI commit `e54bbf3`.
- Modify: `tests/unit/test_governance_docs_current_state.py` — assert `v0.0.30` and `M23-LSP-ADAPTER-GATE`.
- Modify: `ralph.md` — append a Reflection Log entry with Resume checkpoint and rewrite Section 16 so the next safe Ralph row is `M23-LSP-ADAPTER-GATE`.

**Validation:**

```bash
PYTHONPATH=src pytest tests/unit/test_lsp_adapter.py tests/unit/test_oss_comparison_adapter.py tests/unit/test_codebase_evidence_portfolio.py tests/unit/test_domain_cli.py tests/unit/test_change_impact.py tests/unit/test_architecture_candidates.py tests/unit/test_code_analysis_pass_contract.py tests/unit/test_subagent_evidence_collector_protocol.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_governance_docs_current_state.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit:**

```bash
git add tests/fixtures/lsp-adapter/ tests/unit/test_lsp_adapter.py docs/traceability/README.md docs/milestone-bootstrap/profile.yaml tests/unit/test_governance_docs_current_state.py docs/plans/m23-golden-lsp-adapter-implementation-tasks.md ralph.md
git commit -m "test: pin lsp adapter golden fixture"
git push origin dars
```

---

## Stop conditions

Stop and ask if any task would require live network, LSP server installation (`pip` / `npm` / `apt-get`), live `ruff` / `pyright` / `mypy` / `flake8` / `eslint` execution, raw diagnostic message archival in the expected files, license-text capture, model invocation, real `subprocess` call from the test, `.git/` read from production code, `date.today()` from production code, or anything that mutates non-fixture data.

## Out of scope

- Multiple variant bundles (single canonical bundle in this row).
- CLI golden round-trip (the CLI is already tested at the value level; a CLI golden bytes round-trip would only duplicate coverage).
- Variant output formats (the canonical bundle covers `ruff_json`; other formats are covered by RED-GREEN focused tests via their own parsers).
- Live LSP server execution, real `ruff` binary invocation, package installation.
