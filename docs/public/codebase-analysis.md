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
gates.

## What is intentionally out of scope

Increments 1 and 2 do not implement and do not authorize:

- Scope-and-validation-plan synthesis (Increment 3 / M17).
- Risk-boundary scanning (Increment 4 / M18).
- Source-inspection decision packet (Increment 5 / M19).
- `investigate-domain --domain codebase` bridge (Increment 6 / M20).
- External repository clone, raw source content archiving, live network
  access, model calls, credential use, remote push, or publication.
