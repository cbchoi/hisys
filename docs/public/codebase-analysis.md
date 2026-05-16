# Codebase analysis

Hisys ships a deterministic, fixture-local codebase-analysis surface so a
governed investigation or domain adapter can inspect a target repository
without enabling external repository clone, raw source archival, model
calls, or any other live action. The first increment is the inventory
foundation; later increments add a symbol index, a scope-and-validation
map, a risk-boundary scanner, a source-inspection decision packet, and an
investigate-domain bridge.

## Increment 1 — Inventory foundation

`hisys.operations.codebase_analysis.build_codebase_inventory` walks a
caller-supplied repository root in a name-sorted depth-first order and
returns a `CodebaseInventory` Pydantic model. The walk is deterministic:
the same repository state produces a byte-identical model and a
byte-identical JSON serialization across runs.

### Default excluded directories

The walker prunes any directory whose basename matches one of the
following transient or generated-state names:

```
.git  .hg  .svn  .venv  venv  env  __pycache__  .pytest_cache  .mypy_cache
.ruff_cache  .tox  .cache  .eggs  build  dist  htmlcov  node_modules
```

### Path policy

The inventory carries a `PathPolicy` record describing the boundary the
walk enforced:

- `follow_symlinks=false` — symlinks are never followed.
- `reject_outside_repo=true` — a symlink whose real target falls outside
  the realpath of the repository root is recorded as a
  `outside_repo_symlink` skip event and never read.
- `max_file_size_bytes=1_048_576` — files larger than 1 MiB are counted
  under `large_file_count` and remain part of the inventory listing but
  receive no content sniffing beyond the head probe.
- `binary_null_byte_probe_bytes=8192` — a null byte anywhere in the
  first 8 KiB of a file marks it as binary.
- Generated-file heuristics:
  - suffixes: `.min.js`, `.min.css`, `.lock`, `.lockb`;
  - text markers in the head probe: `@generated`, `DO NOT EDIT`,
    `Auto-generated`, `AUTO-GENERATED`.

### Safety invariants

- `raw_source_content_persisted=false` is asserted on every
  `CodebaseInventory` and surfaced on the writer return value.
- The writer emits artifacts only under the caller's instance root at
  `runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/inventory.json`
  and `inventory.md`. Both `date` and `request_id` are slug-validated
  (`\d{8}` and `[A-Za-z0-9._-]+`) and explicit `.` / `..` segments are
  rejected so the writer cannot escape the runtime-boundary subtree.
- The writer return value records
  `external_call_made=false`,
  `mutation_performed=false`,
  `publication_or_live_action_approved=false`.

### Command

```bash
PYTHONPATH=src python3 -m hisys.cli.main build-codebase-inventory \
  --repo /path/to/repo \
  --instance /tmp/hisys-codebase-analysis \
  --date 20260516 \
  --request-id REQ-CODEBASE-001 \
  --scope src \
  --format json
```

The optional `--scope` flag restricts the walk to a repository-relative
subdirectory. Files in the inventory are still keyed relative to the
repository root.

## Increment 2 — Python AST symbol index

`hisys.operations.codebase_analysis.build_python_symbol_index` extends the
inventory walk with a stdlib-only Python AST pass that records, per file,
the module qualname, top-level imports, classes (with nested classes and
methods), and free functions, along with line ranges. The output is a
deterministic `PythonSymbolIndex` Pydantic model with
`schema_id=hisys.codebase.symbol_index` and
`raw_source_content_persisted=false`.

### Captured fields

- `modules[].path`, `modules[].module_qualname`
- `modules[].imports[]` with `module`, `name`, `asname`, and `line`, sorted by `(module, name, asname)`
- `modules[].functions[]` with `name`, `line_start`, `line_end`, `is_async`, `parameters`, and `tags`, sorted by `name`
- `modules[].classes[]` (recursive `nested_classes`) with `methods` and `line_start`/`line_end`
- `parse_errors[]` with `path`, `line`, `column`, and `message` for files the AST rejects; the build continues past those files so a single broken module never halts the walk
- aggregate counters: `module_count`, `import_count`, `class_count`, `function_count`, `parse_error_count`

### Heuristic tags

`SymbolFunction.tags` is sorted and may include the following labels based
on AST-only signals (no execution, no model call):

- `cli_handler` — function name starts with `_cmd_` (Hisys CLI convention).
- `parser_builder` — function body builds an `argparse.ArgumentParser` (via attribute or imported name).
- `pytest_test` — function name starts with `test_`, including methods inside `TestXxx` classes.

### Safety invariants

- `raw_source_content_persisted=false` is asserted on every `PythonSymbolIndex` and surfaced on the writer return value.
- The writer emits artifacts only under the caller's instance root at
  `runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/symbol-index.json`
  and `symbol-index.md`. Both `date` and `request_id` reuse the inventory
  slug validation, rejecting traversal segments so the writer cannot
  escape the runtime-boundary subtree.
- The writer return value records `external_call_made=false`,
  `mutation_performed=false`, and
  `publication_or_live_action_approved=false`.

### Command

```bash
PYTHONPATH=src python3 -m hisys.cli.main build-code-symbol-index \
  --repo /path/to/repo \
  --instance /tmp/hisys-codebase-analysis \
  --date 20260516 \
  --request-id REQ-CODEBASE-001 \
  --scope src \
  --format json
```

The optional `--scope` flag restricts the walk to a repository-relative
subdirectory; entries in the index are still keyed relative to the
repository root.

## Increment 3 — Scope map and validation plan

`hisys.operations.codebase_analysis.list_codebase_scope_profiles` declares
a static registry of named scopes (`docs-traceability`, `domain-adapter`,
`runtime-boundary`) and the entry files, focused tests, and controlled
docs that govern each scope. `build_codebase_scope_map` consumes already-
loaded `CodebaseInventory` and `PythonSymbolIndex` records and partitions
each profile's declared refs into present-vs-missing lists, filters the
symbol-index modules and parse errors per scope, and isolates traceability
references under the `docs/traceability/` subtree.
`build_codebase_validation_plan` then derives a deterministic
`CodebaseValidationPlan` from the scope map. Each scope receives the
appropriate `git_diff_check`, `traceability`, `focused_tests`,
`secret_scan`, and `full_tests` commands, with `requires_full_suite=true`
escalation when missing entry files or expected tests indicate drift or
when the scope crosses subsystems (currently `runtime-boundary`).

### Captured fields

- `scope_map.scope_entries[].scope_id`, `description`
- `scope_map.scope_entries[].files_in_scope` / `missing_entry_files`
- `scope_map.scope_entries[].tests_in_scope` / `missing_expected_tests`
- `scope_map.scope_entries[].docs_in_scope` / `missing_docs_refs`
- `scope_map.scope_entries[].traceability_refs_in_scope`
- `scope_map.scope_entries[].modules` (subset of the symbol index) plus
  per-scope `module_count`, `function_count`, `class_count`,
  `import_count`, and `parse_errors_in_scope`
- `validation_plan.scope_plans[].requires_full_suite`
- `validation_plan.scope_plans[].commands[]` with `kind`, `argv`, and
  `purpose`

### Safety invariants

- `raw_source_content_persisted=false` is asserted on every
  `CodebaseScopeMap` and surfaced on the writer return value.
- The writer emits artifacts only under the caller's instance root at
  `runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/scope-map.json`
  and `scope-map.md`. `date` and `request_id` reuse the inventory slug
  validation, rejecting traversal segments so the writer cannot escape
  the runtime-boundary subtree.
- `resolve_instance_runtime_ref` rejects empty refs, absolute paths,
  `..` traversal segments, and symlinks whose real target escapes the
  instance root. The `build-codebase-map` CLI resolves the supplied
  `--inventory-ref` and `--symbol-index-ref` through this chokepoint
  before reading any artifact JSON.
- The scope-map and validation-plan synthesizers are pure data
  transforms over already-loaded `CodebaseInventory` and
  `PythonSymbolIndex` records — they make no source content read, no
  live action, and no mutation.
- The writer return value records `external_call_made=false`,
  `mutation_performed=false`, and `publication_or_live_action_approved=false`.

### Command

```bash
PYTHONPATH=src python3 -m hisys.cli.main build-codebase-map \
  --instance /tmp/hisys-codebase-analysis \
  --date 20260517 \
  --request-id REQ-CODEBASE-001 \
  --inventory-ref runtime-boundary/codebase-analysis/20260517/REQ-CODEBASE-001/inventory.json \
  --symbol-index-ref runtime-boundary/codebase-analysis/20260517/REQ-CODEBASE-001/symbol-index.json \
  --format json
```

The CLI expects the inventory and symbol-index artifacts to already exist
under the instance root (write them first via `build-codebase-inventory`
and `build-code-symbol-index`). All three artifacts coexist under the
same `runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/` bundle
and downstream M19/M20 consumers should treat them as a single review
bundle.

## Increment 4 — Risk-boundary scanner

`hisys.operations.codebase_analysis.scan_codebase_risk_boundaries`
conservatively flags AST call sites that look like they cross sensitive
boundaries — network calls, browser calls, filesystem mutation,
runtime-boundary artifact writes, subprocess execution, model/LLM
boundary crossings, and ByeSys generated-evidence markers — without
making any live call itself. Each finding is **review evidence, not a
vulnerability or action verdict**: `action_authorized=false` is asserted
at both the scan and finding level so a reviewer cannot infer authority
from absence.

### Detected categories

- `network_external_call` — `requests.<verb>`, `httpx.<verb>`,
  `urllib3.<verb>`
- `browser_external_call` — `webbrowser.{open,open_new,open_new_tab}`
- `filesystem_mutation` — `<receiver>.write_text` / `.write_bytes` in a
  module that does **not** contain a `runtime-boundary` string literal
- `runtime_boundary_artifact_write` — `<receiver>.write_text` /
  `.write_bytes` in a module that contains a `runtime-boundary` string
  literal (the controlled Hisys writers)
- `subprocess_execution` — `subprocess.{run,Popen,call,check_call,check_output,getoutput}`
  and `os.{system,spawnX}`
- `model_llm_boundary` — `openai.*`, `anthropic.*` (attribute-chain
  rooted), and `requests.<verb>` / `httpx.<verb>` calls in a module
  whose string literals contain a model endpoint token
  (`/v1/chat/completions`, `/v1/completions`, `/v1/messages`,
  `/v1/embeddings`)
- `byesys_generated_evidence` — one finding per string literal that
  contains the controlled markers `ByeSys` or `byesys_generated`

### Captured fields

- `scan.findings[].category`, `path`, `line`, `signal`,
  `action_authorized=false`
- `scan.category_counts` — deterministic dict keyed by category
- `scan.parse_errors[]` — `SymbolParseError` records so a single broken
  module never halts the scan
- `scan.action_authorized=false` and `scan.raw_source_content_persisted=false`
  at the top level

### Safety invariants

- The scanner is AST-only. It makes no live call, no network access,
  no subprocess execution, and no source content persistence.
- `action_authorized=false` is asserted at both the scan and the
  finding level. Findings are review evidence, not vulnerability
  verdicts; a reviewer must perform separate analysis before acting.
- The writer emits artifacts only under the caller's instance root at
  `runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/risk-scan.json`
  and `risk-scan.md`. `date` and `request_id` reuse the inventory slug
  validation, rejecting traversal segments so the writer cannot escape
  the runtime-boundary subtree.
- The writer return value records `external_call_made=false`,
  `mutation_performed=false`, and `publication_or_live_action_approved=false`.

### Command

```bash
PYTHONPATH=src python3 -m hisys.cli.main scan-codebase-boundaries \
  --repo /path/to/repo \
  --instance /tmp/hisys-codebase-analysis \
  --date 20260517 \
  --request-id REQ-CODEBASE-RISK-001 \
  --scope src \
  --format json
```

The optional `--scope` flag restricts the scanner walk to a repo-relative
subdirectory; findings are still keyed relative to the repository root.
The risk-scan artifact joins the same `runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/`
bundle as the inventory, symbol-index, and scope-map artifacts.

## Increment 5 — Source-inspection decision packet

`hisys.operations.codebase_analysis.review_codebase_source_inspection` is
a pure reviewer that consumes the four-file bundle (inventory, Python
symbol index, scope map + validation plan, risk-boundary scan) and
returns a `CodebaseSourceInspectionDecision`. The allowed decision values
are exactly `complete_for_human_review` and `blocked_needs_more_evidence`;
the record's Pydantic `Literal` structurally rejects `approved`,
`safe_to_deploy`, and `ready_for_live_action`, so the reviewer cannot
cross the no-live-action boundary even if a caller asks it to.

### Inputs

- `inventory: CodebaseInventory | None`
- `symbol_index: PythonSymbolIndex | None`
- `scope_map: CodebaseScopeMap | None`
- `validation_plan: CodebaseValidationPlan | None`
- `risk_scan: CodebaseRiskScan | None`
- `unresolved_blockers: Iterable[str] | None` — optional caller-supplied
  blockers (e.g., "secret-scan: hit_count>0 in fixture run") that gate
  the decision

### Decision rules

- Any required artifact missing -> `missing_evidence` records the canonical
  name; the decision downgrades to `blocked_needs_more_evidence`.
- Any per-record safety invariant violation populates
  `validation_findings` and downgrades the decision:
  - `<artifact>.raw_source_content_persisted=true` on any of the five records
  - `risk_scan.action_authorized=true`
  - any `RiskBoundaryFinding.action_authorized=true`
  - `scope_map.inventory_schema_id != inventory.schema_id`
  - `scope_map.symbol_index_schema_id != symbol_index.schema_id`
- Any non-empty `unresolved_blockers` downgrades the decision.
- Only when all three lists (`missing_evidence`, `validation_findings`,
  `unresolved_blockers`) are empty does the decision become
  `complete_for_human_review`.

### Safe artifact loading

`load_codebase_review_bundle` is the single chokepoint that resolves the
four caller-supplied refs through `resolve_instance_runtime_ref` (which
rejects empty refs, absolute paths, `..` traversal segments, and
symlinks whose real target escapes the instance root) before any file
read. It returns a `CodebaseReviewBundle` Pydantic record with the five
typed artifact fields plus `raw_source_content_persisted=False` and
`action_authorized=False`.

### Captured fields

- `decision.schema_id = "hisys.codebase.source_inspection_decision"`
- `decision.decision` — one of the two allowed Literal values
- `decision.missing_evidence` — sorted canonical artifact names
- `decision.validation_findings` — sorted grep-friendly finding strings
- `decision.unresolved_blockers` — caller-supplied blockers as-is
- `decision.raw_source_content_persisted=false`,
  `decision.action_authorized=false`,
  `decision.external_call_made=false`,
  `decision.mutation_performed=false`,
  `decision.publication_or_live_action_approved=false`

### Safety invariants

- The reviewer makes no live call, no filesystem read, no source content
  read, and no mutation. It inspects already-loaded Pydantic records.
- Allowed decision values are exactly `complete_for_human_review` and
  `blocked_needs_more_evidence`. The Pydantic `Literal` rejects
  `approved`, `safe_to_deploy`, and `ready_for_live_action`.
- The writer emits artifacts only under the caller's instance root at
  `runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/source-inspection-decision.{json,md}`.
- The Markdown rendering explicitly states "review evidence, not an
  authorization" and lists the two allowed decision values alongside the
  three forbidden ones so a reviewer reading the artifact in isolation
  cannot misread it as an authorization signal.

### Command

```bash
PYTHONPATH=src python3 -m hisys.cli.main review-codebase-analysis \
  --instance /tmp/hisys-codebase-analysis \
  --date 20260517 \
  --request-id REQ-CODEBASE-DECISION-001 \
  --inventory-ref runtime-boundary/codebase-analysis/20260517/REQ-CODEBASE-001/inventory.json \
  --symbol-index-ref runtime-boundary/codebase-analysis/20260517/REQ-CODEBASE-001/symbol-index.json \
  --scope-map-ref runtime-boundary/codebase-analysis/20260517/REQ-CODEBASE-001/scope-map.json \
  --risk-scan-ref runtime-boundary/codebase-analysis/20260517/REQ-CODEBASE-001/risk-scan.json \
  --unresolved-blocker "secret-scan: hit_count>0 in fixture run" \
  --format json
```

The CLI exits 0 for `complete_for_human_review` and 2 for
`blocked_needs_more_evidence`, so automation can branch on the decision
without re-parsing the JSON. The decision artifact joins the same
`runtime-boundary/codebase-analysis/<YYYYMMDD>/<REQUEST_ID>/` bundle as
the four input artifacts, separated only by filename.

## Spec packet

The codebase-analysis surface is governed by a Hisys spec-first packet:

```
SPEC-HISYS-CODEBASE-ANALYSIS-001
```

The packet is built through `hisys build-spec-first-packet` and persisted
under `runtime-boundary/agent-workflows/<YYYYMMDD>/SPEC-HISYS-CODEBASE-ANALYSIS-001.{json,md}`.
It pins the bounded objective, scope, non-goals, allowed actions,
evidence contract, expected artifacts, gate criteria, and human-approval
boundary. The matching `FINISH-HISYS-CODEBASE-ANALYSIS-001` finish
packet is produced after the M15 inventory milestone passes its local
gates; the symbol-index increment is recorded as
`FINISH-HISYS-CODEBASE-ANALYSIS-002` after M16 completes its local
gates; the scope-map-and-validation-plan increment is recorded as
`FINISH-HISYS-CODEBASE-ANALYSIS-003` after M17 completes its local
gates; the risk-boundary scanner is recorded as
`FINISH-HISYS-CODEBASE-ANALYSIS-004` after M18 completes its local
gates; the source-inspection decision packet is recorded as
`FINISH-HISYS-CODEBASE-ANALYSIS-005` after M19 completes its local
gates.

## What is intentionally out of scope

Increments 1 through 5 do not implement and do not authorize:

- `investigate-domain --domain codebase` bridge (Increment 6 / M20).
- External repository clone, raw source content archiving, live network
  access, model calls, credential use, remote push, or publication.
