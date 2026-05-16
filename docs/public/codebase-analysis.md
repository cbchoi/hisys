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
gates.

## What is intentionally out of scope

Increment 1 does not implement and does not authorize:

- Python AST symbol indexing (Increment 2 / Milestone M16).
- Scope-and-validation-plan synthesis (Increment 3 / M17).
- Risk-boundary scanning (Increment 4 / M18).
- Source-inspection decision packet (Increment 5 / M19).
- `investigate-domain --domain codebase` bridge (Increment 6 / M20).
- External repository clone, raw source content archiving, live network
  access, model calls, credential use, remote push, or publication.
