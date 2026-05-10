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
- Increment **HISYS-T-033 Orchestrator-to-Investigator harness source plan** -
  `hisys investigate-memo --orchestrator-harness <json>` lets the orchestrator
  pass a governed harness containing planned `source_ids`, optional `agent_types`,
  `user_opinion`, and rationale. The Investigator accepts harness-selected
  registry sources without requiring duplicate CLI `--source` flags, records
  `agent_plan_source=orchestrator_harness`, `harness_source_refs`,
  `orchestrator_harness_ref`, and `user_opinion` in the run report, and writes
  Orchestrator Harness/User Opinion sections in the memo. This loosens restricted
  autonomy by moving source selection to the orchestrator harness while preserving
  registry validation and disabled-connector blocking before execution.
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
- Increment **Hisys MVP A6 Chief Editor DARS acceptance** -
  The Chief Editor research review now explicitly decides whether to accept DARS
  advice. Safe DARS responses (`blocks_decision=false`, no mutation, no external
  side effects, and non-executable recommended actions) are accepted as review
  conditions via `dars_acceptance_decision=accepted_as_conditions`; DARS still
  cannot approve, block, execute, or mutate.
- Increment **Live-A2 Source connector registry schemas** -
  `hisys.connectors.live_source_config` defines disabled-by-default live source
  connector registry models and loader behavior for future publisher/search/PDF,
  metadata, local-file, Selenium read-only, fixture, and read-only LLM evidence
  connectors. The registry rejects mutating modes, credential refs, enabled
  external connectors when live-network policy is disabled, and external
  connectors without approval policy or allowlisted domains.
- Increment **Live-A3 disabled source connector examples** -
  `examples/instance/config/source-connectors.yaml` declares disabled examples
  for a disabled-by-default general web search connector, publisher web search,
  DOI metadata search, open-access PDF fetch, arXiv metadata search, local PDF
  reading, and Selenium read-only browsing.
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
- Increment **Live-B1 source connector dry-run planning** -
  `hisys plan-source-connectors` reads a `DomainInvestigationRequest` and the
  governed source connector registry, writes `connector-plan-*.json|md` under
  `runtime-boundary/source-connectors/<YYYYMMDD>/`, and writes
  `source-connector-plan-report.{json,md}` without executing adapters, making
  external calls, or performing mutations. Research-domain plans now include the
  disabled-by-default `general_web_search` connector so Live-Z can plan broad
  topic search while keeping routine execution blocked until approved.
- Increment **Search-A fixture-backed general web search evidence connector** -
  `hisys.connectors.general_web_search.GeneralWebSearchConnector` collects
  injected JSON search-result fixtures into `SourceAccessRecord` and
  `SourceEvidenceItem` artifacts. `hisys smoke-source-connector --connector-id
  general_web_search --transport-fixture-search <json>` validates the approved
  manual path with fixture transport only; without fixture transport it blocks
  with `search_fixture_transport_required`, so CI performs no live provider
  search.
- Increment **Live-B2 fixture publisher evidence connector** -
  `hisys.connectors.fixture_publisher` reads local static publisher-shaped HTML
  fixtures only, extracts title/quoted evidence, writes `SourceAccessRecord` and
  `SourceEvidenceItem` artifacts with SHA-256 provenance under
  `runtime-boundary/source-connectors/<YYYYMMDD>/`, and records
  `external_call_made=false` and `mutation_performed=false`.
- Increment **Live-B3 fixture connector evidence in domain investigation** -
  The research-gap `investigate-domain` fixture path invokes the local fixture
  publisher connector, writes source-access/source-evidence records, and links
  those refs into `DomainEvidencePackage.evidence_refs` and
  `InvestigationDataPackage.source_governance_refs` while preserving
  `external_call_made=false` and `mutation_performed=false`.
- Increment **Live-B4 connector evidence in DARS trace** -
  The DARS advisory fixture handoff now includes fixture source-access and
  source-evidence refs in DARS request `record_refs.runtime_boundary`, critique
  evidence refs, rubric evidence refs, and trace evidence/runtime-boundary refs
  so DARS critique lineage covers source connector evidence as well as the
  domain result.
- Increment **Live-B5 source-aware Chief Editor research review** -
  The Chief Editor `research_recommendation_review` records
  `source_validation_status`, `source_evidence_refs`, and an explicit condition
  requiring fixture evidence to be validated against live publisher pages before
  publication-level novelty claims.
- Increment **Live-C manual DOI metadata smoke boundary** -
  `source-connectors.yaml` marks `doi_metadata_search` as
  `manual_smoke_only`, guarded by `HISYS_ALLOW_LIVE_SMOKE`, and excluded from
  CI. `hisys.connectors.doi_metadata` provides a read-only Crossref DOI metadata
  connector with injectable transport so tests use fake responses only.
  `hisys smoke-source-connector --dry-run` writes blocked dispatch/report
  artifacts without a network call; a manual live run additionally requires an
  approval ref plus the operator environment flag before any external metadata
  call is made.
- Increment **Live-D legal open-access PDF collector boundary** -
  `source-connectors.yaml` marks `open_access_pdf_fetch` as
  `manual_smoke_only`, guarded by `HISYS_ALLOW_LIVE_PDF_SMOKE`, and excluded
  from CI. `hisys.connectors.open_access_pdf` provides a fixture-only OA PDF
  collector that rejects non-`open_access` license signals before persisting PDF
  bytes and records source-access/source-evidence provenance with
  `pdf_downloaded=true`, `external_call_made=false`, and `mutation_performed=false`.
  `hisys smoke-source-connector` now dry-runs/blocks PDF smoke attempts unless
  open-access license evidence, approval, allowlist, and the operator env flag
  are present; manual live PDF fetching remains blocked/not implemented.
- Increment **Live-E DOI metadata to OA PDF candidate planning** -
  `hisys.connectors.pdf_candidate_planner` derives `pdf_candidate` plan
  artifacts from DOI metadata OA hints without fetching PDF bytes. `hisys plan-pdf-candidates` writes `pdf-candidate-plan-<request_id>.json` and a run
  report with `candidate_plan_only=true`, `pdf_downloaded=false`,
  `external_call_made=false`, and `mutation_performed=false`. Source connector
  planning now records a `doi_metadata_search -> open_access_pdf_fetch` planned
  handoff of type `pdf_candidate_plan_only`, so DOI metadata and OA PDF gates are
  linked without making live PDF calls.
- Increment **Live-F approved manual OA PDF fetch smoke** -
  `hisys.connectors.open_access_pdf.collect_manual_smoke` uses an injectable
  transport so tests and CI use `--transport-fixture-pdf` fake PDF bytes while an
  operator-only live path remains behind `HISYS_ALLOW_LIVE_PDF_SMOKE`, approval,
  allowlist, and dispatch gates. On success, `hisys smoke-source-connector`
  writes `manual_pdf_smoke_completed` with `pdf_downloaded=true`,
  `external_call_made=true`, `mutation_performed=false`, source-access refs, and
  source-evidence refs. Checked-in config remains disabled and CI still performs
  no live PDF fetch.
- Increment **Live-G manual OA PDF evidence promotion** -
  `PdfEvidencePromotionLoader` validates explicit `open_access_pdf_fetch`
  source-access/source-evidence refs before promotion. `hisys investigate-domain`
  accepts `--promote-pdf-source-access-ref` and
  `--promote-pdf-source-evidence-ref`, records `promoted_pdf_evidence_refs` in
  `InvestigationDataPackage`, keeps source-access/source-evidence refs in source
  governance, and preserves promoted PDF refs in DARS trace and Chief Editor
  `research_recommendation_review` with `manual_pdf_evidence_promoted` status.
  This adds no implicit PDF discovery or live fetch.
- Increment **Live-H PDF quote extraction from promoted OA evidence** -
  `PdfQuoteExtractor` derives quote-only `source_quote_refs` from explicit
  promoted OA PDF evidence refs. `hisys extract-pdf-quotes` writes
  `source-quote-<quote_id>.json` artifacts and a
  `pdf-quote-extraction-report.json` without OCR, PDF parsing, or network calls
  in CI. `hisys investigate-domain --source-quote-ref` preserves quote refs in
  `InvestigationDataPackage`, DARS trace, and Chief Editor review while keeping
  novelty/publication claims conditional.
- Increment **Live-I quote-to-claim evidence ledger** -
  `ClaimEvidenceLedgerBuilder` maps explicit `source_quote_refs` to
  support/contradict/needs-evidence claim ledger records while preserving that
  quote text remains source evidence and claim mapping remains interpretation.
  `hisys build-claim-evidence-ledger` writes `claim-evidence-ledger-*.json`
  artifacts without network calls or source mutation. `hisys investigate-domain
  --claim-evidence-ledger-ref` preserves `claim_evidence_ledger_refs` in
  `InvestigationDataPackage`, DARS trace, and Chief Editor review with
  `claim_evidence_ledger_present` status while keeping novelty claims
  conditional.
- Increment **Live-J claim evidence summary** -
  `ClaimEvidenceSummaryBuilder` aggregates explicit `claim_evidence_ledger_refs`
  into support/contradict/needs-evidence balance summaries while keeping
  confidence advisory confidence only. `hisys build-claim-evidence-summary`
  writes `claim-evidence-summary-*.json` artifacts without network calls or
  ledger/source mutation. `hisys investigate-domain --claim-evidence-summary-ref`
  preserves `claim_evidence_summary_refs` in `InvestigationDataPackage`, DARS
  trace, and Chief Editor review with `claim_evidence_summary_present` status.
  The summary does not prove novelty or publication readiness.
- Increment **Live-K claim coverage gate** -
  `ClaimCoverageGateBuilder` checks required recommendation claims against
  explicit `claim_evidence_summary_refs` and writes `claim-coverage-gate-*.json`
  artifacts without network calls, source mutation, or claim strengthening.
  `hisys build-claim-coverage-gate` writes gate reports and `hisys
  investigate-domain --claim-coverage-gate-ref` preserves
  `claim_coverage_gate_refs` in `InvestigationDataPackage`, DARS trace, and
  Chief Editor review with `claim_coverage_gate_present` status,
  `conditional_manuscript_language_only=true`, and a conditional manuscript
  language gate.
- Increment **Live-L recommendation claim registry** -
  `RecommendationClaimRegistryBuilder` records controlled required recommendation
  claims from explicit recommendation text and writes
  `recommendation-claim-registry-*.json` artifacts without network calls, source
  mutation, novelty proof, or publication-readiness approval. `hisys
  build-recommendation-claim-registry` writes registry reports with
  `feeds_live_k_coverage_gates=true`, and `hisys investigate-domain
  --recommendation-claim-registry-ref` preserves
  `recommendation_claim_registry_refs` in `InvestigationDataPackage`, DARS trace,
  and Chief Editor review with `recommendation_claim_registry_present` status and
  condition `Run Live-K claim coverage gates before stronger manuscript-facing claims`.
- Increment **Live-M approved live ideation run** -
  `hisys live-ideation-run` is the first one-command live-source ideation loop:
  it requires `--explicit-live-source-enable`, `HISYS_ALLOW_LIVE_IDEATION=1`, an
  approval ref, enabled/read-only `doi_metadata_search`, and dispatch allowlist
  approval before a DOI metadata source access. It writes source-access/evidence
  provenance, feeds those refs into `investigate-domain`, then invokes the
  existing DARS and Chief Editor research-review pipeline. Tests use
  `--metadata-fixture`; real DOI metadata access remains approval-gated and
  read-only, with `mutation_performed=false`.
- Increment **Live-N approved live ideation persistence pipeline** -
  `hisys live-ideation-persist` fills the remaining live-autonomy gap by chaining
  approved live ideation, approval-gated Obsidian vault transaction apply, and
  approval-gated Obsidian Git sync into one command. It requires explicit source,
  write, and Git enable flags, a single approval ref, a credential reference, and
  clean/scoped vault Git status confirmation. Tests use injected DOI metadata and
  a local fixture Git remote; real `/home/cbchoi/obsidian` use remains behind
  `--allow-real-obsidian-vault` and records `real_obsidian_vault_write_performed`
  plus `network_push_performed` in `live-ideation-persist-report.json`.
- Increment **Live-O standing autonomous approval envelope** -
  `hisys live-ideation-persist --standing-approval-policy` lets a prior approved
  policy substitute for repeated per-run CLI approval flags inside a scoped
  operating envelope. The policy must be `status=approved`, contain an
  `approval_ref`, include the `live_source_access`, `live_vault_write`, and
  `obsidian_git_push` capabilities, and match allowed domain, vault root, remote,
  branch, credential-ref, and expiry controls. Reports record
  `standing_approval_applied`; out-of-scope requests block before source access,
  vault mutation, or Git push.
- Increment **Live-P autonomous queue runner** -
  `hisys live-autonomy-run` executes a JSON queue of live ideation persistence
  entries under one standing approval policy. Each queue item runs in an isolated
  runtime sub-instance, invokes the full `live-ideation-persist` path, and writes
  a batch `live-autonomy-run-report.json` with completed/blocked counts, per-entry
  report refs, vault refs, mutation state, and network-push state. Missing DOI or
  request refs block at the queue-entry layer; out-of-policy items still block in
  the standing-approval gate before live source access or mutation.
- Increment **Live-Q queue idempotency and retry ledger** -
  `hisys live-autonomy-run` now maintains a JSON ledger, defaulting to
  `data/live-autonomy-ledgers/<YYYYMMDD>/<queue_id>.json`, or an explicit
  `--ledger` path. Completed entries are skipped on rerun instead of re-mutating
  the vault or re-pushing Git. Blocked entries record `attempt_count`,
  `retry_eligible`, and the last reason/report refs; `--max-retries` prevents
  exhausted retry entries from running again. Batch reports include the ledger ref,
  skipped-completed count, retry-exhausted count, and retry-eligible count.
- Increment **Live-R queue state transitions and watchdog reports** -
  The live autonomy ledger now records scheduler-readable `current_state` and
  `state_history` transitions such as `queued`, `running`, `completed`, `blocked`,
  `skipped_completed`, and `skipped_retry_exhausted`. Every queue run also writes
  `live-autonomy-watchdog-report.json|md` with `scheduler_ready`, `health_status`,
  retry counts, ledger ref, and `next_scheduler_action`, so cron/watchdog wrappers
  can decide whether to sleep, retry, or request operator review without parsing
  every per-entry pipeline report.
- Increment **Live-S scheduler tick wrapper** -
  `hisys live-autonomy-tick` is a cron-ready wrapper that discovers queue JSON
  files from `--queue-dir`, processes up to `--max-queues` through the governed
  `live-autonomy-run` path, and writes
  `live-autonomy-scheduler-tick-report.json|md`. An empty queue directory is an
  explicit idle success with `next_scheduler_action=sleep`; queue runs that need
  operator attention are summarized with queue report/watchdog refs and exit code
  `2` for external schedulers. The hardened scheduler keeps overhead deterministic:
  per-queue reports are namespaced under `run-summaries/<YYYYMMDD>/<queue_id>/`,
  malformed non-retryable queue entries become terminal `skipped_non_retryable`
  on later ticks instead of re-blocking forever, and standing approval expiry
  dates are validated as `YYYYMMDD` before any live action.
- Increment **Live-T queue lifecycle handoff** -
  `hisys live-autonomy-tick --queue-lifecycle` treats `--queue-dir` as an
  incoming handoff directory and deterministically moves queue files through
  sibling `active/`, `done/`, `attention/`, and `rejected/` directories. The
  scheduler copies a queue into `active/` before processing, removes the active
  copy at finalization, moves successful queue files to `done/`, attention-needed
  queue files to `attention/`, and invalid JSON queue files to `rejected/`. Tick
  reports include lifecycle enablement, lifecycle dirs, per-queue active/final
  refs, and final lifecycle state without adding prompt-based checks.
- Increment **Live-U queue admission validator** -
  `hisys live-autonomy-admit` validates candidate queue JSON files before they
  reach the scheduler incoming directory. The admission step performs only cheap
  deterministic checks: valid JSON object, safe optional `queue_id`, non-empty
  `entries`, unique entry IDs, required `doi`, and required safe relative
  `request_path` fields. It moves accepted candidate files to `--incoming-dir`,
  rejected files to `--rejected-dir`, writes
  `live-autonomy-admission-report.json|md`, and records
  `external_call_made=false`, `mutation_performed=false`, and
  `network_push_performed=false`. Candidate rejection remains a normal admission
  outcome: the report status records `attention_required`, but the command exits
  `0` unless an unexpected process error occurs, avoiding scheduler paging for
  routine malformed candidates.
- Increment **Live-V compact operator status dashboard** -
  `hisys live-autonomy-status` writes `live-autonomy-status-report.json|md` by
  aggregating only existing admission reports, scheduler tick reports, watchdog
  reports, and queue ledgers. It records compact counts for admitted/rejected
  candidates, processed queues, watchdog attention, retry-eligible entries,
  completed ledger entries, and ledger attention entries. It is read-only with
  respect to live systems: `external_call_made=false`, `mutation_performed=false`,
  and `network_push_performed=false`; no prompt/LLM review is part of routine
  dashboard generation.
- Increment **Live-W queue artifact hashing** -
  Live autonomy admission, scheduler tick, queue-run, watchdog, ledger, and
  status reports now include deterministic SHA-256 content identity for queue
  JSON and per-entry JSON. Hashes are computed from canonical JSON with sorted
  keys for valid queues, and from raw file bytes for malformed JSON, so operators
  can identify unchanged/replayed queue work cheaply without source calls, vault
  mutation, Git/network pushes, or prompt-based checks.
- Increment **Live-X duplicate/replay classification** -
  `hisys live-autonomy-admit` now compares candidate queue and entry hashes with
  existing incoming/rejected handoff artifacts and records deterministic replay
  classifications: `new`, `same_hash_replay`, `changed_same_entry_id`, or
  `duplicate_queue_content`. The classification is report-only and intentionally
  scoped to local admission handoff artifacts (`incoming` and `rejected`); already
  processed queues remain governed by the scheduler/ledger/status path. Malformed
  JSON queues use raw-file hashes, so they match only byte-identical malformed
  artifacts. It does not add prompt checks, source calls, vault mutation, or
  Git/network pushes.
- Increment **Live-Obsidian-Config-A scaffold** -
  `docs/use-cases/obsidian-live-research-layout.md` captures the Claude-reviewed
  Obsidian live-research structure before implementation. It defines
  `registry.json` as the global entry point, canonical topics under `topics/`,
  `topics/INDEX.json`, group overlays, `topic-manifest.json`,
  `investigation-manifest.json`, `runtime-index.json`, `attachment-index.json`,
  content-addressed attachment blobs, structured `type`/`phase` metadata, and
  evidence-citing Topic Gatekeeper decisions. The scaffold examples under
  `examples/obsidian-live/` define registry, topic, investigation, gatekeeper,
  and missing-task artifacts for future `vault-plan --dry-run` and
  `vault-validate` work. The scaffold is a planner-only dry-run boundary with no
  real vault writes.
- Increment **Live-Obsidian-Config-B vault planner** -
  `hisys.config.obsidian_live.build_vault_plan` and `hisys vault-plan --dry-run`
  compute registry-first, topic/investigation vault-relative paths from fixture
  registry input, write planner artifacts only under `runtime-boundary/obsidian-live/`
  and `reports/run-summaries/`, preserve evidence-citing gatekeeper scores, and
  record `vault_write_attempted=false`, `external_call_made=false`, and
  `mutation_performed=false`. The CLI does not create `/home/cbchoi/obsidian` or
  any `91 Hisys/` vault content.
- Increment **Live-Obsidian-Config-C vault validator** -
  `hisys.config.obsidian_live.validate_vault_manifests` and `hisys vault-validate`
  validate fixture registry/topic/investigation/gatekeeper manifests without
  vault writes. The validator rejects missing gatekeeper score evidence refs,
  unsafe vault-relative refs, invalid topic IDs/slugs, and merge/split decisions
  missing required human approval refs, then writes validation reports with
  `vault_write_attempted=false`, `external_call_made=false`, and
  `mutation_performed=false`.
- Increment **Live-Obsidian-Config-D memo ontology template planner** -
  `hisys.config.obsidian_live.build_vault_template_plan` and `hisys
  vault-template-plan` produce fixture-only memo ontology/template/index planning
  artifacts. The plan enumerates controlled `type` values, requires `phase` as
  structured metadata rather than a tag, uses structured links as the governance
  record, treats Obsidian wikilinks as projections, lists allowed relation
  vocabulary and required index files, and writes only runtime-boundary/report
  artifacts with no vault mutation.
- Increment **Live-Obsidian-Config-E validator hardening** -
  `hisys.config.obsidian_live.validate_vault_manifests` now shares the memo
  ontology relation vocabulary with the template planner and rejects unknown
  structured link relations, invalid `GROUP-YYYYMMDD-XXXXXX` group IDs, invalid
  `INV-YYYYMMDD-HHMM-XXXX` investigation/run IDs, and overlong vault-relative
  refs. These checks keep registry/topic/investigation/gatekeeper manifests
  bounded, relation-controlled, and safe for future vault-write planning while
  preserving `vault_write_attempted=false`, `external_call_made=false`, and
  `mutation_performed=false`.
- Increment **Live-Obsidian-Config-F fixture vault apply** -
  `hisys.config.obsidian_live.apply_vault_plan_to_fixture` and `hisys
  vault-apply` add the first controlled local vault writer for fixture targets
  only. The command requires an explicit `--approval-ref`, requires
  `--fixture-vault-only`, blocks `/home/cbchoi/obsidian`, writes only the
  provided target fixture vault root, and records runtime-boundary apply reports
  with `real_obsidian_vault_write_performed=false` and `external_call_made=false`.
- Increment **Live-Obsidian-Config-G topic transition plan** -
  `hisys.config.obsidian_live.build_topic_identity_transition_plan` and `hisys
  vault-topic-transition-plan` plan non-destructive canonical topic merge/split
  transitions. Merge and split actions require approval refs, never delete old
  topic folders, produce tombstone refs such as `MERGED_INTO.md` or
  `SPLIT_INTO.md`, plan manifest updates, and write only runtime-boundary plan
  artifacts with `real_obsidian_vault_write_performed=false`.
- Increment **Live-Obsidian-Config-H fixture vault roundtrip validation** -
  `hisys.config.obsidian_live.validate_fixture_vault_roundtrip` and `hisys
  vault-roundtrip-validate` prove planned fixture vault files match the applied
  fixture vault projection. The report detects missing or unexpected fixture
  files, validates projection metadata, compares the apply report with actual
  fixture files, and records no real Obsidian vault writes.
- Increment **Live-Obsidian-Config-I live vault preflight** -
  `hisys.config.obsidian_live.build_live_vault_preflight_report` and `hisys
  vault-live-preflight` inspect a candidate Obsidian vault without writing to it.
  The preflight checks for the vault root, `.obsidian`, a Git repository marker,
  and an attachment ignore policy, records `write_probe_performed=false` and
  `live_write_enabled=false`, and only prepares the next approval-package gate.
- Increment **Live-Obsidian-Config-J live vault approval package** -
  `hisys.config.obsidian_live.build_live_vault_approval_package` and `hisys
  vault-live-approval-package` generate a human approval package for a future
  live vault write without enabling one. The package lists planned vault-relative
  writes, required approvals, rollback strategy, and final gates while recording
  `live_write_enabled=false` and `real_obsidian_vault_write_performed=false`.
- Increment **Live-Obsidian-Config-K live vault write gate** -
  `hisys.config.obsidian_live.build_live_vault_write_gate_report` and `hisys
  vault-live-write-gate` evaluate final live-write preconditions but intentionally
  remain a gate-only boundary. They require approval package evidence, an
  approval ref, clean-git status, and explicit live-write enablement, but still
  return blocked with `implementation_boundary=gate_only_no_writer` and
  `real_obsidian_vault_write_performed=false`.
- Increment **Live-Obsidian-Config-L live vault transaction plan** -
  `hisys.config.obsidian_live.build_live_vault_transaction_plan` and `hisys
  vault-live-transaction-plan` convert the approval package plus write-gate
  report into a non-executable transaction manifest. It enumerates planned
  operations, rollback hints, and placeholder pre/post hashes without reading or
  writing the live vault, and records `transaction_manifest_only_no_writer` plus
  `real_obsidian_vault_write_performed=false`.
- Increment **Live-Obsidian-Config-M fixture transaction rehearsal** -
  `hisys.config.obsidian_live.rehearse_live_vault_transaction_in_fixture` and
  `hisys vault-live-transaction-rehearse` exercise the transaction manifest
  against an explicit fixture vault only. The command requires `--approval-ref`
  and `--fixture-vault-only`, refuses `/home/cbchoi/obsidian`, writes fixture
  projection payloads only, and records `real_obsidian_vault_write_performed=false`.
- Increment **Live-Obsidian-Config-N approved transaction apply** -
  `hisys.config.obsidian_live.apply_live_vault_transaction` and `hisys
  vault-live-transaction-apply` provide the final approval-gated writer boundary.
  The command requires approval, an explicit write-enable switch, and clean-git
  confirmation; it refuses `/home/cbchoi/obsidian` unless the separate
  `--allow-real-obsidian-vault` flag is present. Tests exercise only temporary
  candidate vault roots, not the real vault.
- Increment **Live-Obsidian-Config-O completion status** -
  `hisys.config.obsidian_live.build_live_obsidian_config_status_report` and
  `hisys vault-live-config-status` record that Live-Obsidian-Config A through O
  are complete, with zero open stages and no real Obsidian vault write performed.
- Increment **Topic-Gatekeeper complete** -
  `hisys.config.obsidian_live.build_topic_gatekeeper_decision` and `hisys
  vault-topic-gatekeeper` provide read-only, evidence-citing topic routing over a
  registry. The completion sequence also covers approval package, transaction
  plan, fixture rehearsal, and status reporting helpers; all default artifacts
  record no external calls and no real Obsidian vault writes.
- Increment **Obsidian Evidence Promotion-A** -
  `hisys.config.obsidian_live.build_obsidian_evidence_promotion_plan` and `hisys
  vault-evidence-promotion-plan` plan promotion of explicit source, evidence,
  claim, and decision refs into topic-level canonical indexes. Fixture rehearsal
  writes only projection payloads to explicit fixture roots and records no real
  Obsidian vault writes.
- Increment **Obsidian Milestone Status** -
  `hisys.config.obsidian_live.build_obsidian_milestone_status_report` and `hisys
  vault-obsidian-milestone-status` record the Obsidian milestone complete across
  Live-Obsidian-Config, Topic-Gatekeeper, Obsidian Evidence Promotion, and
  Obsidian Git Management with zero open milestones and no real Obsidian vault
  write.
- Increment **Obsidian Git Management-A** -
  `hisys.config.obsidian_live.build_obsidian_git_initialization_plan` and
  `build_obsidian_git_sync_plan` capture the corrected lifecycle: Hisys should
  initialize the Obsidian vault as a Git-managed repository using only
  operator-provided credential refs and explicit approval refs, then after
  approved memo or runtime-boundary vault writes stage at least one approved
  memo/runtime-boundary ref, commit it, push to the configured remote, and record
  Git status/push evidence. This increment is still plan-only: it rejects raw
  credential values and records no mutation or external calls.
- Increment **Obsidian Git Management-B fixture executor** -
  `execute_obsidian_git_initialization_in_fixture` and
  `execute_obsidian_git_sync_in_fixture` turn the Git plans into a gated local
  fixture executor: it requires `fixture_git_only`, refuses the real Obsidian
  vault, uses only local fixture Git remotes, never resolves credential refs, and
  records initialization/sync push evidence with `external_call_made=false`.
- Increment **Obsidian Git Management-C finalization** -
  `vault-git-fixture-init`, `vault-git-fixture-sync`, and
  `vault-obsidian-milestone-status` expose the fixture Git executor through the
  CLI and mark Obsidian Git Management complete in the overall Obsidian milestone
  report while preserving `real_obsidian_vault_write_performed=false` and
  `external_call_made=false` for finalization evidence.
- Increment **Obsidian Git Management-D live sync** -
  `execute_obsidian_git_sync_live` and `vault-git-live-sync` execute an approved
  sync plan against a Git-managed vault only after explicit `approval_ref`,
  `--explicit-live-git-enable`, clean/scoped Git status confirmation, and the
  real-vault opt-in flag when the target is `/home/cbchoi/obsidian`. The executor
  stages only approved memo/runtime-boundary refs, commits, pushes to the
  configured remote, and writes runtime-boundary evidence with network push state.
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
