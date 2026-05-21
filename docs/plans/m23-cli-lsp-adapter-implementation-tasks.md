# Milestone M23 — LSP Adapter CLI Implementation Task Plan

> **Row:** This document is the artifact produced by Ralph row `M23-LSP-ADAPTER-CLI`. The pure governed runner, parsers, and writer landed in `M23-LSP-ADAPTER-RED-GREEN` at commit `1874ad5 feat: add local lsp adapter`; this row only adds a thin argparse pass-through that loads a caller-supplied JSON bundle and dispatches to `run_lsp_adapter` + `write_lsp_adapter_report`.

> **For Hermes/Ralph:** Use `software-development:test-driven-development`. The CLI is bundled into one Ralph increment (PREP + RED + GREEN + regression) because it is a thin JSON-bundle pass-through over the already-tested pure module. The CLI must not weaken any M23 LSP adapter safety invariant — the caller-supplied `command_allowlist`, `human_approval_ref`, `workspace_root` containment, 120-second timeout cap, 4 MiB output truncation, `output_format` allowlist, shell-metacharacter rejection, no-shell invocation, and `env={"PATH": PATH}` rule all continue to live in the pure runner. The CLI is a transport layer only.

**Goal:** Add a `hisys lsp-adapter` argparse subcommand that loads one caller-supplied JSON bundle and dispatches to `run_lsp_adapter` + `write_lsp_adapter_report`, printing bounded summary lines. The CLI never crawls `tests/fixtures/`, never crawls `runtime-boundary/`, never reads `.git/`, never calls `date.today()`, never installs LSP servers, never invokes `pip` / `npm` / `apt-get`, never auto-discovers bundle files, never opens the workspace files itself, never expands the command-id or output-format vocabulary, and never invokes `subprocess` directly — the only `subprocess` call goes through the M23-RED-GREEN runner which already enforces the safety contract.

**Architecture:** Add to `src/hisys/cli/main.py`:

1. A new module-level import block for `LspAdapterCommand`, `LspAdapterRequest`, `run_lsp_adapter`, and `write_lsp_adapter_report` from `hisys.operations.lsp_adapter`.
2. A `_load_lsp_adapter_bundle(path)` helper that reuses the existing `_load_json_report` reader and returns `(LspAdapterCommand, Path, tuple[str, ...], tuple[str, ...], str)`. The helper requires the JSON payload to be a top-level object with `command: object`, `workspace_root: str`, optional `target_refs: list[str]`, `command_allowlist: list[str]`, and `human_approval_ref: str`; mismatches raise `ValueError` with a precise message.
3. A `_cmd_lsp_adapter(*, instance_root, yyyymmdd, bundle_path, current_head_short)` dispatcher that constructs the request, calls the runner, calls the writer, and prints the bounded summary lines documented below. Returns exit code `0` on success and propagates `ValueError` non-zero (the existing CLI top-level error handling carries them up).
4. A new `sub.add_parser("lsp-adapter", ...)` subparser with `--instance`, `--date`, `--bundle`, and `--current-head-short` arguments. Mirror the existing M23 `oss-comparison-adapter` subparser's help text style.
5. A dispatcher branch `if args.command == "lsp-adapter": return _cmd_lsp_adapter(...)`.

**Output lines (bounded; mirrors the M23 OSS adapter CLI shape):**

```text
lsp-adapter report: json=<json_ref>
markdown: <markdown_ref>
command_id: <id>
output_format: <format>
diagnostic_count: <int>
error_count: <int>
warning_count: <int>
info_count: <int>
subprocess_exit_code: <int>
subprocess_timed_out: <bool>
subprocess_killed: <bool>
output_truncated: <bool>
output_bytes: <int>
unsafe_ref_count: <int>
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
  "workspace_root": "/abs/path/to/instance/workspace",
  "command": {
    "command_id": "ruff-check",
    "argv": ["ruff", "check", "--output-format=json", "src/"],
    "timeout_seconds": 30,
    "expected_exit_codes": [0, 1],
    "output_format": "ruff_json"
  },
  "target_refs": ["src/a.py", "src/b.py"],
  "command_allowlist": ["ruff"],
  "human_approval_ref": "docs/approvals/lsp-adapter-2026-05-22.md"
}
```

`workspace_root` is a caller-supplied string path; the CLI converts it to a `Path` without resolution and hands it to `LspAdapterRequest`. The pure runner enforces containment under `instance_root` after `Path.resolve()` so a bundle that names a path outside the instance root still fails closed with `ValueError("lsp_workspace_root_outside_instance")`.

**Tech Stack:** Python 3.11 argparse, json, pathlib. No new dependency. The CLI re-imports the existing Pydantic models from `hisys.operations.lsp_adapter` so it does not duplicate shape definitions. The CLI tests monkey-patch `subprocess.run` to avoid any real LSP server invocation.

**Context Packet:**

- `src/hisys/cli/main.py` — current argparse subparser table and dispatcher branches (insert after `oss-comparison-adapter`).
- `src/hisys/operations/lsp_adapter.py` — M23 runner/writer and Pydantic models (committed at `1874ad5 feat: add local lsp adapter`).
- `tests/unit/test_domain_cli.py` — mirror the M23 `test_oss_comparison_adapter_cli_*` test layout.
- `docs/plans/m23-cli-oss-comparison-adapter-implementation-tasks.md` — sibling CLI PREP/RED/GREEN format.
- `docs/plans/m23-lsp-adapter-implementation-tasks.md` — parent LSP plan (M23-LSP-ADAPTER-RED-GREEN).
- `docs/traceability/README.md` — top-of-file row prepended in this row.
- `docs/milestone-bootstrap/profile.yaml` v0.0.28 — `next_safe_task: M23-LSP-ADAPTER-CLI` before this row; bump to v0.0.29 / `M23-LSP-ADAPTER-GOLDEN` after commit.
- `tests/unit/test_governance_docs_current_state.py` — bump assertions in lockstep.
- `ralph.md` Reflection Log + Section 16 — append checkpoint and rewrite next-row pointer.

**Boundary Record:** Fixture-local CLI plumbing only. The dispatcher delegates to the M23-LSP-ADAPTER-RED-GREEN pure module; it makes no live model call, no remote provider call, no network clone/fetch/search, no credential lookup, no direct `subprocess` (only through the pure runner under monkey-patched `subprocess.run` in tests), no `.git/` read, no `date.today()`, no `runtime-boundary/` crawl, no auto-discovery of bundle files, no opening of workspace source files, no LSP server installation, no subagent execution, no publication/deployment, no schema/data migration, no force push, no new remote configuration, no destructive operation, no raw upstream source-content archival, no license adjudication, no real LSP wire-protocol speech.

---

## Accepted decisions

1. **JSON bundle pass-through.** A single `--bundle <path>` flag points at a JSON object containing `workspace_root`, `command`, `target_refs`, `command_allowlist`, and `human_approval_ref`. Bundle mismatches raise `ValueError`; the CLI does not synthesize defaults, infer from `runtime-boundary/`, or auto-pick fixture files.
2. **Reuse of existing JSON loader.** The bundle loader builds on `_load_json_report`; it does not introduce a parallel reader.
3. **Pydantic-constructed records.** `LspAdapterCommand` and `LspAdapterRequest` are constructed from the bundle dicts via Pydantic so the CLI cannot drift from the M23 shape. The pure runner re-validates every safety invariant.
4. **Bounded summary lines.** The CLI prints fixed-key summary lines mirroring M23 OSS adapter; no human-readable narrative, no markdown injection, no path expansion, no listing of diagnostic messages, no raw text leak.
5. **No CLI-side date generation.** `--date` is required and passed verbatim. `--current-head-short` is optional and recorded verbatim. The CLI never reads the system clock or `.git/`.
6. **Existing top-level error propagation.** `ValueError` from the runner/writer propagates through argparse handling unchanged (the M23 OSS comparison CLI follows the same convention; tests assert this with `pytest.raises(ValueError)`).
7. **No vocabulary expansion.** The CLI accepts whatever bundle dicts the caller provides; pattern validation (command_id, output_format, timeout range, shell-metacharacter, allowlist) continues to live in the pure runner.
8. **`subprocess.run` is monkey-patched in tests.** No real `ruff` / `pyright` / `mypy` / `flake8` / `eslint` binary is executed by the CLI test suite. Production-mode invocation against a real LSP-aware tool is human-gated to the operator running the CLI.

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

Expected: branch `dars`, HEAD at or after `1874ad5 feat: add local lsp adapter`; combined gate passes; traceability OK; secrets `hit_count=0`; diff-check clean.

---

## Task 1: RED — four CLI tests in `tests/unit/test_domain_cli.py`

Add four focused tests at the end of `tests/unit/test_domain_cli.py`:

1. `test_lsp_adapter_cli_writes_report` — happy-path round-trip: write bundle JSON, monkey-patch `subprocess.run` to return canned ruff JSON, invoke `main(["lsp-adapter", ...])`, assert exit code 0, summary lines, JSON and Markdown artifacts exist under `runtime-boundary/lsp-adapter/20260522/ruff-check/lsp-report.{json,md}`, JSON contains the M23 advisory flag set, deterministic counts, and no raw message text in the Markdown body.
2. `test_lsp_adapter_cli_rejects_missing_command` — bundle without `command` raises `ValueError`.
3. `test_lsp_adapter_cli_rejects_bad_date` — `--date 2026-05-22` raises `ValueError` from the runner.
4. `test_lsp_adapter_cli_rejects_command_not_in_allowlist` — bundle with `argv=["rm","-rf","/"]` and `command_allowlist=["ruff"]` raises `ValueError("lsp_command_not_in_allowlist")` before any `subprocess.run` call.

**Verify RED before adding the production dispatcher:**

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py::test_lsp_adapter_cli_writes_report -q
```

Expected RED: `SystemExit: 2` (argparse rejecting the unknown subcommand) or equivalent error before the subparser/dispatcher exists.

---

## Task 2: GREEN — implement bundle loader, dispatcher, subparser, and dispatcher branch

**Files:**

- Modify: `src/hisys/cli/main.py` — add imports, `_load_lsp_adapter_bundle`, `_cmd_lsp_adapter`, the `lsp-adapter` subparser (inserted after `oss-comparison-adapter`), and the dispatcher branch.

**Verify GREEN:**

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py -k lsp_adapter -q
PYTHONPATH=src pytest tests/unit/test_domain_cli.py tests/unit/test_lsp_adapter.py tests/unit/test_oss_comparison_adapter.py tests/unit/test_codebase_evidence_portfolio.py -q
```

Expected GREEN: four CLI tests pass; M22 portfolio + M23 OSS adapter + M23 LSP runner tests still pass.

---

## Task 3: Documentation, gate, and commit

- Modify: `docs/traceability/README.md` — prepend an `M23-LSP-ADAPTER-CLI` row.
- Modify: `docs/milestone-bootstrap/profile.yaml` — bump version to `v0.0.29`, set `next_safe_task: M23-LSP-ADAPTER-GOLDEN`, refresh `planning_baseline_head` and `current_head_at_plan_creation` to the M23-LSP-ADAPTER-RED-GREEN commit `1874ad5`.
- Modify: `tests/unit/test_governance_docs_current_state.py` — assert `v0.0.29` and `M23-LSP-ADAPTER-GOLDEN`.
- Modify: `ralph.md` — append a Reflection Log entry with Resume checkpoint and rewrite Section 16 so the next safe Ralph row is `M23-LSP-ADAPTER-GOLDEN`.

**Validation:**

```bash
PYTHONPATH=src pytest tests/unit/test_domain_cli.py tests/unit/test_lsp_adapter.py tests/unit/test_oss_comparison_adapter.py tests/unit/test_codebase_evidence_portfolio.py tests/unit/test_change_impact.py tests/unit/test_architecture_candidates.py tests/unit/test_code_analysis_pass_contract.py tests/unit/test_subagent_evidence_collector_protocol.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py tests/unit/test_governance_docs_current_state.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Commit:**

```bash
git add tests/unit/test_domain_cli.py src/hisys/cli/main.py docs/traceability/README.md docs/milestone-bootstrap/profile.yaml tests/unit/test_governance_docs_current_state.py docs/plans/m23-cli-lsp-adapter-implementation-tasks.md ralph.md
git commit -m "feat: add lsp adapter cli wrapper"
git push origin dars
```

---

## Stop conditions

Stop and ask if any task would require credential lookup, network fetch/clone/install, real LSP server installation (`pip` / `npm` / `apt-get`), live LSP-protocol wire speech, raw source archival, license adjudication, direct `subprocess` from the CLI module (other than through the pure runner), `.git/` read, `date.today()`, `runtime-boundary/` crawl, `tests/fixtures/` crawl, auto-discovery of bundle files, opening workspace source files, force push, new remote configuration, publication, deployment, or `output_format` / `command_allowlist` expansion beyond caller-supplied values.

## Out of scope

- Golden round-trip fixture for the CLI (deferred to `M23-LSP-ADAPTER-GOLDEN`).
- CLI argument grouping (`--command-id`, `--argv`, ...) instead of the JSON bundle. The JSON bundle is the chosen surface and mirrors M23 OSS adapter.
- Live LSP provider invocation, real `ruff` / `pyright` / `mypy` / `flake8` / `eslint` execution, LSP server installation, repo cloning, package installation.
- Persistent daemon mode or watch mode; each `hisys lsp-adapter` call is independent.
