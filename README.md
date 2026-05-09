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
- Increment **I4 Investigator direct memo foundation** - `hisys investigate-memo`
  runs registered fixture-source investigation from a research topic/goal,
  applies `HISYS-TPL-RESEARCH-SEARCH-001`, and writes a runtime-local
  template-based investigation `ZettelMemo` JSON/Markdown artifact before Chief
  Editor orchestration.
- Increment **HISYS-T-027 Investigator multi-agent fixture research** -
  `hisys investigate-memo --agent fixture --agent fixture_contradiction`
  creates governed `ResearchTask` records, dispatches deterministic fixture
  research agents, validates/merges `EvidencePackage` outputs, persists
  `data/research-tasks/<YYYYMMDD>/` and `data/evidence-packages/<YYYYMMDD>/`
  artifacts, and builds one template memo from validated evidence while
  Selenium/browser and delegated LLM agents remain disabled until harnesses pass.
- Increment **HISYS-T-028 Selenium read-only research harness** - the
  `SeleniumReadOnlyAgent` remains disabled-by-default, enforces read-only and
  forbidden-action gates, rejects non-allowed live domains, validates local static
  HTML fixture extraction into an `EvidencePackage`, records
  `external_side_effects=false`, and does not start a browser or access the
  network in this harness stage.
- Increment **HISYS-T-029 Formalism domain fixture research** -
  `hisys investigate-memo --agent formalism_comparison --agent
  self_organization_mechanism` adds controlled domain fixtures for
  self-organizing-system formalism topics. The agents return `EvidencePackage`
  claims for Dynamic Structure DEVS, graph rewriting, agent-based modeling,
  assessment criteria, selection heuristics, expressiveness/simulation/verification
  tradeoffs, local interaction rules, emergent global structure, and structural change as
  first-class state, plus domain-specific open questions about simulation
  semantics, proof/verification, and topology change representation.
- Increment **HISYS-T-030 Purpose-specific Investigator guidelines and evidence agents** -
  `hisys investigate-memo --purpose auto` selects a memo guideline profile from
  the requested topic/goal. `research_idea_discovery` requires gap statements,
  novelty/synthesis opportunities, and evaluation scenarios and can dispatch the
  `formalism_gap_analysis` agent to produce explicit DSDEVS/graph-rewriting/ABM
  gap statements, hybrid novelty candidates, and evaluation scenarios. `investment_decision_support`
  requires company fundamentals, market/competitor/valuation/risk evidence, and a
  buy/hold/avoid/needs-more-evidence decision frame; the
  `investment_decision_support` agent returns bounded fixture evidence and records
  that outputs are not financial advice.
- Increment **HISYS-T-031 Purpose-aware automatic agent planning** -
  when no `--agent` is supplied, `hisys investigate-memo --purpose auto` now
  converts the selected guideline into a default agent plan: `research_idea_discovery`
  dispatches `formalism_gap_analysis`, `investment_decision_support` dispatches
  `investment_decision_support`, and `general_investigation` dispatches no extra
  agent. Explicit `--agent` values remain authoritative overrides/additions for
  controlled manual plans.
- Increment **HISYS-T-032 Configurable Investigator connector registry** -
  `examples/instance/config/investigator-agents.yaml` now declares the purpose
  agent plans and disabled optional connectors for publisher web search,
  Claude/Codex read-only evidence extraction, local LLM offline mapping,
  market/news search, and company filing search. `investigate-memo` resolves
  default agents from this config, records `agent_plan_source`,
  `disabled_optional_agent_refs`, and `blocked_agent_refs` in the run report,
  and still rejects disabled explicit external connectors before execution.
- Increment **Hisys MVP A1 domain-general schema boundary** -
  `hisys.schemas.domain_investigation` defines the local/Hermes-facing
  `DomainInvestigationRequest`, read-only source refs, safety constraints,
  `InvestigationDataPackage`, `DomainEvidencePackage`, `CandidateRecord`,
  `AlternativeDecisionSet`, full `DomainInvestigationResult`, and compact
  `HisysToolResult` projection. These schemas keep the MVP read-only by default
  and provide the contract for the future `investigate-domain` CLI/runtime flow.
- Increment **Hisys MVP A2 domain investigation CLI boundary** -
  `hisys investigate-domain --request <json>` validates a
  `DomainInvestigationRequest`, writes request/result JSON and Markdown under
  `runtime-boundary/domain-investigation/<domain>/<YYYYMMDD>/`, and writes a
  `domain-investigation-report` while returning `needs_more_evidence` until a
  concrete domain adapter executes in the next increment.
- Increment **Hisys MVP A3 research domain adapter fixture** -
  `hisys investigate-domain` now recognizes research-gap/formalism requests and
  writes deterministic local `InvestigationDataPackage`, `AlternativeDecisionSet`,
  `DomainInvestigationResult`, and compact `HisysToolResult` artifacts. The
  fixture recommendation is Self-organizing Dynamic Structure DEVS with
  graph-rewrite structural transitions, marked human-review-required and
  publisher-source-validation-needed, with `external_call_made=false` and
  `mutation_performed=false`.
- Increment **Hisys MVP A4 DARS fixture critique trace** -
  The research domain fixture writes advisory-only DARS request, response, and
  trace-link artifacts under `runtime-boundary/dars/<YYYYMMDD>/`. The local
  loopback critique flags novelty/proof-obligation risks, recommends publisher
  source validation, never blocks the decision, and records `action_taken=none`,
  `external_call_made=false`, and `mutation_performed=false`.
- Increment **Hisys MVP A5 Chief Editor research review** -
  The domain investigation flow writes a Chief Editor
  `research_recommendation_review` product under
  `runtime-boundary/chief-editor/research/<YYYYMMDD>/`. For the research-gap
  fixture, the decision is `recommend_with_conditions`, requires human review,
  requests publisher-source/evaluation-scenario evidence, and takes no external
  action or mutation.
- Increment **Live-A2 Source connector registry schemas** -
  `hisys.connectors.live_source_config` defines disabled-by-default live source
  connector registry models and loader behavior for future publisher/search/PDF,
  metadata, local-file, Selenium read-only, fixture, and read-only LLM evidence
  connectors. The registry rejects mutating modes, credential refs, enabled
  external connectors when live-network policy is disabled, and external
  connectors without approval policy or allowlisted domains.
- Increment **Live-A3 disabled source connector examples** -
  `examples/instance/config/source-connectors.yaml` declares disabled examples
  for publisher web search, DOI metadata search, open-access PDF fetch,
  arXiv metadata search, local PDF reading, and Selenium read-only browsing.
  All checked-in examples keep `enabled=false`, `external_call_allowed=false`,
  `requires_human_approval=true`, no credentials, and forbidden live actions.
- Increment **Live-A4 source connector dispatch gate** -
  `hisys.connectors.live_source_dispatch` records allow/block decisions under
  `runtime-boundary/source-connectors/<YYYYMMDD>/` before any future source
  connector adapter can run. The gate blocks disabled connectors, forbidden
  prompt/request actions, missing approval references, and non-allowlisted
  domains while always recording `external_call_made=false` and
  `mutation_performed=false` at decision time.
- Increment **Live-A5 live source evidence provenance records** -
  `hisys.connectors.live_source_evidence` defines `SourceAccessRecord` and
  `SourceEvidenceItem` for future live-source evidence. Records require URL,
  access time, connector ID, SHA-256 hash, license/open-access signal, and
  separation between quoted source text and interpretation; PDF downloads require
  `license_signal=open_access`.
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
  a live Obsidian vault. The controlled vault-writer dry-run helper
  `hisys.integrations.obsidian_vault` now builds sanitized target paths,
  frontmatter/body previews, and runtime-boundary preview reports without
  creating or modifying the target vault path.
- Increment **I7-A/B/C/D/E/F/G/H foundation** (Chief Editor alert decisions,
  suppression, approval gate, dry-run action planning, approval transition stub,
  approved-decision send-candidate classification, disabled connector harness,
  and product factory selection) - fixture-backed Chief
  Editor policy reads runtime-local memo review outputs, creates
  `AlertDecisionRecord` JSON/Markdown records, records duplicate non-escalation
  decisions, suppresses repeated alert candidates with the same `suppression_key`
  in the same run/date, requests human approval for high/critical or non-local
  target alert candidates, selects either `analysis_only` or
  `alert_delivery_dry_run` Chief Editor products from
  `config/chief-editor.yaml`/CLI, writes alert decision reports via `hisys
  decide-alerts`, applies runtime-local approve/reject transitions via `hisys
  review-alert-approval`, and writes dry-run `AlertActionPlanRecord`
  JSON/Markdown plus run reports via `hisys plan-alert-actions`, including
  approved pending decisions as `would_send=true` candidates while live delivery
  remains disabled; `hisys execute-alert-actions` writes disabled connector
  execution records/reports and still sends nothing. The live connector control
  helper `hisys.integrations.live_connectors` evaluates requested live Discord or
  software-trigger actions as blocked runtime-boundary decisions until a connector
  is explicitly enabled, the requested action is allow-listed, and approval is
  present; this baseline still records `external_call_made=false` and
  `action_taken=none`.
- Increment **I8-A/B/C foundation** (DARS advisory handoff loopback contract and
  config-validation gate) -
  DARS itself is intentionally not implemented. The adopted Hisys design
  philosophy is documented in `docs/architecture/design-philosophy.md`: Hermes
  orchestrates conversation and tasks; Hisys governs investigation, evidence,
  alternatives, and runtime-boundary records; DARS critiques alternatives as an
  advisory evaluator; and humans or approved governance select consequential
  actions. `hisys request-dars-critique`
  creates runtime-local `AgentHandoffPackage` JSON/Markdown records linked to
  disabled connector executions and returns a loopback placeholder critique when
  no critique text is supplied. The artifact shape records
  `dars_backend=loopback_placeholder`, `external_call_made=false`,
  `allowed_actions=advisory_only`, and `action_taken=none`, so a future DARS
  adapter can replace the loopback without changing downstream records. The
  DARS protocol contract is now represented by `hisys.agents.dars_protocol`,
  which validates canonical `DarsRequestEnvelope` and `DarsResponseEnvelope`
  JSON objects and rejects mutation, execution, external side effects, and
  blocking behavior at the envelope boundary. `hisys.agents.dars_dispatch`
  adds a runtime-boundary dispatch gate that records allow/block decisions for
  loopback, local fixture, disabled, unknown, and unapproved external-call
  backends before any adapter is invoked. `hisys.agents.dars_backend` adds the
  first deterministic local fixture-file backend: it requires an allowed
  dispatch decision, validates fixture JSON as `DarsResponseEnvelope`, checks
  request alignment, writes validation reports for accepted/rejected outputs,
  and persists accepted response artifacts under `runtime-boundary/dars/`.
  `hisys.agents.dars_trace` records end-to-end DARS lineage from source/memo/alert
  and evidence refs through request, dispatch, validation, response, critique,
  and recommended-action refs. A `mock_endpoint`/`DarsMockEndpointAdapter`
  boundary is present but disabled by default and performs no HTTP/network call.
  The
  DARS configuration contract uses a common Hisys JSON config envelope and validates
  concise role/backend settings before any DARS adapter is selected. The target
  DARS design is progressive and GAN-like: generator candidates are challenged
  by conservative logical and domain-specific critics, then converted into
  evidence-linked improvement proposals rather than automatic blocks. Future
  commercialization should manage operational settings through a `ConfigRegistry`
  and manage DARS system prompts, role profiles, templates, policy bindings, and
  rubric refs through a specialized `PromptRegistry`; both can start file-backed
  and later move to tenant-scoped databases with immutable versions, approvals,
  hashes, audit events, and rollback. A future ontology management tool should
  help decide which domain adapter, configuration, prompt bundle, rubric, and
  connector policy are suitable for a given domain/objective/evidence context,
  while remaining advisory to the approved registries and approval gates. `docs/use-cases/hermes-hisys-domain-tool.md`
  defines Hisys as a Hermes-callable, domain-general investigation and
  decision-support tool: Hermes passes a controlled request, Hisys builds
  evidence and alternatives, DARS critiques them, and Hisys returns compact
  advisory results while preserving runtime-boundary records. `docs/use-cases/codebase-analysis-design-candidates.md`
  specializes that model for `domain="codebase"`, where Hisys analyzes repositories,
  approved open-source references, and previous project results read-only, produces
  `InvestigationDataPackage`, `CodebaseEvidencePackage`, `DesignCandidateRecord`,
  and `AlternativeDecisionSet` artifacts, then uses DARS progressive critique to
  recommend better product, architecture, and automation uses without modifying
  code by default.
- Increment **I9-A/B/C/D product hardening** - `hisys.security.secret_scan` and
  `scripts/scan_secrets.py` scan repository/runtime files for assignment-style
  secret-like values, skip runtime caches such as `.git`/`.pytest_cache`/
  `__pycache__`, and report only redacted excerpts so validation output can be
  shared safely. `hisys.operations.backup` creates runtime-local zip backups for
  controlled `config`/`templates`/`harness`/`data`/`runtime-boundary`/`reports`
  files, writes a SHA-256 manifest, excludes local-only `secrets`/`tmp`/`cache`/
  `logs`/`backups`, and verifies archives through restore dry-run reports.
  `hisys.operations.health` reports required runtime-directory readiness plus
  disabled/loopback connector status without live external probes.
  `hisys.operations.release_readiness` summarizes quality-gate evidence,
  HISYS-T-024 trace-path completeness, and known release gaps for human review.
- Later increments (real DARS adapter and expanded critique feedback)
  are not implemented; live Obsidian vault writes remain pending behind the
  dry-run vault-writer boundary.

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
      config/      runtime instance root, YAML source-registry loader,
                   common config validation, and JSON DARS role/backend config
      audit/       JSONL audit writer with minimal redaction
      integrations/ Hermes Markdown boundary writer
      investigator/ registry-gated collection skeleton
      extraction/  fixture-backed signal extractor and persistence runtime
      editor/      fixture-backed memo drafter, local draft persistence, and
                   duplicate/conflict review runtime
      chief_editor/ fixture-backed alert decision policy/runtime, approval
                    transition stub, and dry-run alert action planning
      agents/     runtime-local DARS advisory handoff/critique harness
      operations/ runtime-local backup, restore dry-run, health status, and
                   release-readiness evidence helpers
      security/    secret-like value scanner and redacted scan reports

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

`hisys --help` exposes the runtime CLI. Fixture-backed I4-I8-B commands are:

```bash
hisys validate-config --instance examples/instance
hisys collect --instance /tmp/hisys-run \
  --config-from examples/instance \
  --source SRC-HW-MOCK-001 \
  --date 20260508
hisys investigate-memo --instance /tmp/hisys-investigation \
  --config-from examples/instance \
  --source SRC-HW-MOCK-001 \
  --date 20260508 \
  --topic "hardware overheating risk" \
  --goal "Assess whether fixture sensor evidence requires operations attention." \
  --perspective PERSP-OPS-001 \
  --agent fixture \
  --agent fixture_contradiction
hisys extract --instance /tmp/hisys-run --date 20260508
hisys draft-memo --instance /tmp/hisys-run \
  --date 20260508 \
  --perspective PERSP-OPS-001
hisys review-memos --instance /tmp/hisys-run --date 20260508
hisys decide-alerts --instance /tmp/hisys-run --date 20260508
# Product can also be selected per run:
#   --product-type analysis_only
#   --product-type alert_delivery_dry_run
hisys plan-alert-actions --instance /tmp/hisys-run --date 20260508
hisys review-alert-approval --instance /tmp/hisys-run \
  --date 20260508 \
  --alert-id ALERT-... \
  --outcome approved \
  --rationale 'fixture approval'
hisys execute-alert-actions --instance /tmp/hisys-run --date 20260508
hisys request-dars-critique --instance /tmp/hisys-run \
  --date 20260508 \
  --source-execution-id EXEC-...
# Optional fixture override while DARS is not implemented:
#   --critique-text 'Fixture advisory critique.'
```

The `collect` command writes local JSON/JSONL runtime records and, for Hermes
sources, Markdown boundary records under
`runtime-boundary/hermes/<YYYYMMDD>/<campaign_id>/`. It does not perform live
collection beyond configured fixture adapters. The `investigate-memo` command
runs a registry-gated fixture investigation from a `--topic` and `--goal`,
applies `HISYS-TPL-RESEARCH-SEARCH-001`, writes linked `ExtractedSignal`
records, and persists a template-based Investigator memo under
`data/investigation-memos/<YYYYMMDD>/` plus
`reports/run-summaries/<YYYYMMDD>/investigation-memo-report.{json,md}`. When
`--agent` is supplied, `investigate-memo` additionally writes governed
`ResearchTask` artifacts under `data/research-tasks/<YYYYMMDD>/`, validates and
persists each agent `EvidencePackage` under `data/evidence-packages/<YYYYMMDD>/`,
and merges agent claims, limitations, and open questions into the final template
memo. It keeps
raw payload content in RawObservation records and copies only source,
observation, signal, payload-ref, and hash references into the memo. The
`extract` command
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
report, applies the fixture Chief Editor policy through a configuration-selected
product factory, suppresses repeated alert
candidates whose `suppression_key` already exists in same-date alert decisions,
requests approval for high/critical or non-local target alert candidates while
keeping `action_taken=none`, writes `data/alert-decisions/<YYYYMMDD>/`
JSON/Markdown decisions and
`reports/run-summaries/<YYYYMMDD>/alert-decision-report.{json,md}`, and does not
send live alerts. `product_type=analysis_only` records the Chief Editor judgment
but forces `target_channel=null`, `approval_status=not_required`, `status=closed`,
and `action_taken=none`; `product_type=alert_delivery_dry_run` preserves the
existing approval/action-plan path while still prohibiting live delivery. The
`plan-alert-actions` command reads local alert decisions,
writes dry-run action plans under `data/alert-action-plans/<YYYYMMDD>/`, records
why live delivery is blocked (`approval_required`, `suppressed`,
`no_target_channel`, or `live_delivery_disabled`), marks approved pending
candidate decisions with a target channel as `would_send=true` while keeping
`live_delivery_permitted=false`, persists
`reports/run-summaries/<YYYYMMDD>/alert-action-plan-report.{json,md}`, and never
sends or triggers external connectors. The `review-alert-approval` command
applies a runtime-local approve/reject transition to `needs_approval` decisions,
updates the decision JSON/Markdown, writes
`reports/run-summaries/<YYYYMMDD>/alert-approval-transition-report.{json,md}`,
keeps `action_taken=none`, and never sends or triggers external connectors. The
`execute-alert-actions` command reads dry-run action plans, writes disabled
connector execution records under
`data/alert-connector-executions/<YYYYMMDD>/`, persists
`reports/run-summaries/<YYYYMMDD>/alert-connector-execution-report.{json,md}`,
records `execution_status=blocked`, `live_delivery_permitted=false`, and
`action_taken=none`, and never sends live alerts. The `request-dars-critique`
command does **not** implement DARS. It creates a runtime-local advisory
`AgentHandoffPackage` under `data/agent-handoffs/<YYYYMMDD>/` and, by default,
returns a loopback placeholder critique under `data/agent-critiques/<YYYYMMDD>/`
with `dars_backend=loopback_placeholder`, `external_call_made=false`,
`allowed_actions=advisory_only`, and `action_taken=none`. Optional
`--critique-text` only supplies fixture text into the same artifact shape; it is
not a DARS call. The contract is intended to let a future DARS adapter replace
the loopback without changing downstream files. The command persists
`reports/run-summaries/<YYYYMMDD>/dars-critique-report.{json,md}` and never calls
a live DARS service. These commands do not write to a live Obsidian vault or call
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
