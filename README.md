# Hisys (Hierarchical Investigation System) - Product Code

This repository hosts the product code for Hisys. Authoritative requirements,
design, interface, and test documentation live in the controlled pre-develop
package at:

    /home/cbchoi/workspaces/sysailab/pre-develop/Hisys/

This repo is a thin product-code mirror of that package; it does not redefine
requirements or design baselines. When this repo and the controlled docs
disagree, the controlled docs (and `INDEX.md` within them) govern.

## Status

- Increment **I0** (Repository skeleton) - in place.
- Increment **I1** (Schemas + IDs) - initial schema modules and tests in place.
- Increment **I2** (Source governance) - initial in-memory source registry,
  fixture registry, and web compliance gate in place.
- Increment **I3** (Adapter framework) - common DataSource contract,
  fixture-backed hardware/web/agent/Hermes adapters, registry-gated adapter
  runtime, health report, and failure isolation in place.
- Increment **I4 foundation** (Investigator runtime preconditions) - runtime
  instance path abstraction, YAML config/source-registry loader, JSON/JSONL
  audit/observation writers, Hermes Markdown boundary writer, Investigator
  collection skeleton, CI smoke gate, and example runtime instance in place.
- Increment **I4 CLI glue** - `hisys validate-config` validates an instance
  source registry and `hisys collect` runs fixture-backed Investigator
  collection into local runtime records, Hermes boundary records, and run
  summaries.
- Later increments (I5-I9) are not implemented; I4 still needs expansion from
  fixture-backed CLI/runtime skeleton to full Investigator workflows.

See `docs/traceability/README.md` for the document and SRS ID map.

## Layout

Mirrors `HISYS-REPO-001` (repository-structure baseline):

    src/hisys/
      core/        IDs, time, errors, result types
      schemas/     Pydantic v2 records (source, observation, signal,
                   compliance, perspective, memo, alert, handoff, audit,
                   hermes_trace)
      registry/    source registry and web compliance collection gate
      adapters/    base + hardware/web/agent/Hermes mocks and runtime manager
      config/      runtime instance root and YAML config/source-registry loader
      audit/       JSONL audit writer with minimal redaction
      integrations/ Hermes Markdown boundary writer
      investigator/ registry-gated collection skeleton
      extraction/, editor/, chief_editor/, health/, cli/   (placeholders)

    examples/instance/
      config/, templates/, harness/guidelines/, harness/scenarios/, data/

    tests/
      unit/        schema, registry, and adapter unit tests
      integration/ end-to-end trace path test
      fixtures/    declarative fixture data

    scripts/
      validate_traceability.py

## Quick start

The package is pure Python with Pydantic v2 and PyYAML runtime dependencies. Install
into a project-local virtualenv (do not install globally):

    python3 -m venv .venv
    . .venv/bin/activate
    pip install -e '.[dev]'
    pytest

`hisys --help` exposes the runtime CLI. Fixture-backed I4 commands are:

```bash
hisys validate-config --instance examples/instance
hisys collect --instance /tmp/hisys-run \
  --config-from examples/instance \
  --source SRC-HW-MOCK-001 \
  --date 20260508
```

The `collect` command writes local JSON/JSONL runtime records and, for Hermes
sources, Markdown boundary records under
`runtime-boundary/hermes/<YYYYMMDD>/<campaign_id>/`. It does not perform live
network calls or external side effects.

## Quality and security constraints

- Evidence and interpretation are kept on separate linked records
  (`RawObservation` vs `ExtractedSignal`/`ZettelMemo`).
- Hermes hierarchical collection captures user input ref, parent run ID,
  delegated task / tool invocation IDs, prompt/query and output references,
  Markdown boundary record path, preapproved scope, and approval state, as
  required by `HISYS-IDD-001` HISYS-IF-016 and `HISYS-SCHEMA-001` Section 10.
- Source collection is registry-gated. Web/news sources require controlled
  compliance review metadata before collection.
- Adapter collection is failure-isolated; one failed source records an
  AdapterErrorRecord without blocking unrelated collectable sources.
- No live network calls; adapters are mocks fed from local fixtures.
- No credentials or secrets are committed. Fixture tokens are explicitly fake.

## Traceability

Every schema module declares the requirement and document IDs it implements
in its module docstring. `scripts/validate_traceability.py` checks that every
schema module references at least one HISYS-* requirement ID and that the
end-to-end trace path is exercised by a test.
