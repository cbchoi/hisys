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
- Increment **I5 foundation** (Extraction pipeline) - fixture-backed extractor
  converts `RawObservation` evidence into `ExtractedSignal` interpretation
  records and persists signal JSON under the local runtime instance; `hisys
  extract` connects collected runtime observations to persisted signal records
  and extraction reports.
- Increment **I6 foundation** (Editorial pipeline) - fixture-backed Associate
  Editor applies an active `PerspectiveProfile` to extracted signals and writes
  runtime-local `ZettelMemo` draft JSON/Markdown plus memo draft reports via
  `hisys draft-memo`; `hisys review-memos` performs fixture duplicate/conflict
  review over runtime-local memo drafts and flags draft status without writing to
  a live Obsidian vault.
- Increment **I7-A foundation** (Chief Editor alert decisions) - fixture-backed
  Chief Editor policy reads runtime-local memo review outputs, creates
  `AlertDecisionRecord` JSON/Markdown records, records duplicate non-escalation
  decisions, and writes alert decision reports via `hisys decide-alerts` without
  sending live alerts.
- Later increments (I7 suppression windows/approval workflow/connectors, I8-I9)
  are not implemented; controlled vault writer workflows remain pending.

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
      extraction/  fixture-backed signal extractor and persistence runtime
      editor/      fixture-backed memo drafter, local draft persistence, and
                   duplicate/conflict review runtime
      chief_editor/ fixture-backed alert decision policy/runtime
      health/, cli/ runtime entry points / placeholders

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

`hisys --help` exposes the runtime CLI. Fixture-backed I4-I7-A commands are:

```bash
hisys validate-config --instance examples/instance
hisys collect --instance /tmp/hisys-run \
  --config-from examples/instance \
  --source SRC-HW-MOCK-001 \
  --date 20260508
hisys extract --instance /tmp/hisys-run --date 20260508
hisys draft-memo --instance /tmp/hisys-run \
  --date 20260508 \
  --perspective PERSP-OPS-001
hisys review-memos --instance /tmp/hisys-run --date 20260508
hisys decide-alerts --instance /tmp/hisys-run --date 20260508
```

The `collect` command writes local JSON/JSONL runtime records and, for Hermes
sources, Markdown boundary records under
`runtime-boundary/hermes/<YYYYMMDD>/<campaign_id>/`. It does not perform live
network calls or external side effects. The `extract` command reads only local
`data/raw-observations/<YYYYMMDD>/` JSON records, writes
`data/extracted-signals/<YYYYMMDD>/` JSON records, and stores
`reports/run-summaries/<YYYYMMDD>/extraction-report.{json,md}`. The
`draft-memo` command reads local signal and observation records, applies the
fixture active perspective `PERSP-OPS-001`, and writes runtime-local draft
memos under `data/memo-drafts/<YYYYMMDD>/` plus
`reports/run-summaries/<YYYYMMDD>/memo-draft-report.{json,md}`. The
`review-memos` command reads only runtime-local memo draft JSON, flags fixture
duplicates/conflicts by updating draft status, and writes
`reports/run-summaries/<YYYYMMDD>/memo-review-report.{json,md}`. The
`decide-alerts` command reads runtime-local memo drafts plus the memo review
report, applies the fixture Chief Editor policy, writes
`data/alert-decisions/<YYYYMMDD>/` JSON/Markdown decisions and
`reports/run-summaries/<YYYYMMDD>/alert-decision-report.{json,md}`, and does not
send live alerts. These commands do not write to a live Obsidian vault or call
external alert connectors.

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
