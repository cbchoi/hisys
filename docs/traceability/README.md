# Hisys Traceability Summary

This summary links product-code modules and tests in this repository to the
controlled Hisys documentation at
`/home/cbchoi/workspaces/sysailab/pre-develop/Hisys/`.

The controlled docs (and especially `INDEX.md` there) are authoritative.
This file is a working pointer; if it drifts, fix it here, not in the docs.

## Implemented increments

| Increment | Source doc | Status here |
|---|---|---|
| I0 Repository skeleton | HISYS-IMP-001 (implementation-plan.md) Section 3 | Complete |
| I1 Schemas and IDs | HISYS-IMP-001 Section 3; HISYS-SCHEMA-001 (schema-definitions.md) | Initial Pydantic v2 models for all named records |
| I2 Source governance | HISYS-IMP-001 Section 3; HISYS-SRC-REG-INIT-001; HISYS-CHECK-WEB-001 | Initial in-memory registry, fixture registry, and web compliance gate |
| I3 Adapter framework | HISYS-IMP-001 Section 3; HISYS-IDD-001 HISYS-IF-003/HISYS-IF-015; HISYS-FIXTURE-001 | Common DataSource contract, fixture adapters, registry-gated runtime, health report, and failure isolation |
| I4 Investigator foundation | HISYS-INST-INV-001; HISYS-RUNTIME-DIR-001; HISYS-HARNESS-GUIDE-001; HISYS-D-015; HISYS-D-016 | Runtime instance paths, YAML config loader, audit/observation persistence, Hermes boundary writer, Investigator collection skeleton, example instance, and CI smoke gate |
| I4 CLI glue | HISYS-INST-INV-001; HISYS-RUNTIME-DIR-001; HISYS-D-015; HISYS-D-016 | `hisys validate-config`, fixture-backed `hisys collect`, Hermes Markdown boundary record persistence, and JSON/Markdown run summary persistence |
| I4 Investigator direct memo foundation | HISYS-INST-INV-001; HISYS-FR-INV-001..006; HISYS-FR-MEM-001..005; HISYS-TPL-RESEARCH-SEARCH-001; HISYS-DATA-002 | `hisys investigate-memo` collects from registry-gated fixture sources, applies the research topic search template, writes linked `ExtractedSignal` evidence-interpretation records, and persists runtime-local investigation `ZettelMemo` JSON/Markdown plus report artifacts without copying raw payload into the memo |
| I5 Extraction foundation | HISYS-IMP-001 Section 3; HISYS-SCHEMA-001 Section 5; HISYS-FR-EXT-001..005 | Fixture-backed `RawObservation` -> `ExtractedSignal` extractor, local signal JSON persistence, and `hisys extract` CLI report path |
| I6 Editorial foundation and vault-write dry-run boundary | HISYS-IMP-001 Section 3; HISYS-SCHEMA-001 Sections 6-7; HISYS-FR-PER-001..004; HISYS-FR-MEM-001..005; HISYS-IF-007; HISYS-DATA-002; HISYS-DATA-005; HISYS-CON-012 | Fixture-backed active perspective application, `ZettelMemo` draft JSON/Markdown persistence, `hisys draft-memo` CLI report path, `hisys review-memos` duplicate/conflict flagging report path, and `hisys.integrations.obsidian_vault` dry-run vault-write previews with sanitized target paths and runtime-boundary reports while live vault writes remain disabled |
| I7-A/B/C/D/E/F/G/H/I Chief Editor alert decision, suppression, approval-gate, dry-run action-plan, approval-transition, send-candidate, disabled-connector, product-factory, and live-connector-control foundation | HISYS-IMP-001 Section 3; HISYS-SCHEMA-001 Section 8; HISYS-FR-CE-001..006; HISYS-CE-POLICY-001; HISYS-FR-AGT-004; HISYS-T-020; HISYS-T-022; HISYS-CON-010; HISYS-CON-012; HISYS-CON-022..023 | Fixture-backed Chief Editor policy reads runtime-local memo review outputs, persists `AlertDecisionRecord` JSON/Markdown decisions, records duplicate non-escalation decisions, suppresses same-date repeated `suppression_key` alert candidates, requests approval for high/critical or non-local target candidates, selects `analysis_only` or `alert_delivery_dry_run` products from config/CLI, writes `alert-decision-report.{json,md}`, applies runtime-local approve/reject transitions with `alert-approval-transition-report.{json,md}`, writes dry-run `alert-action-plan-report.{json,md}` with approved pending decisions marked as `would_send=true` candidates while live delivery remains disabled, writes disabled connector execution records/reports with `execution_status=blocked`, exposes `hisys decide-alerts`/`hisys review-alert-approval`/`hisys plan-alert-actions`/`hisys execute-alert-actions` without live alert sending, and `hisys.integrations.live_connectors` records blocked runtime-boundary decisions for requested live connector actions unless connector/action/approval gates are satisfied |
| I8-A/B DARS advisory handoff loopback contract | HISYS-IMP-001 Section 3; HISYS-SCHEMA-001 Section 9; HISYS-FR-AGT-001..005; HISYS-DARS-CONTRACT-001 | Runtime-local `hisys request-dars-critique` creates advisory-only `AgentHandoffPackage` JSON/Markdown records linked to disabled connector executions and returns loopback placeholder critique records by default because DARS is not implemented yet; artifacts record `dars_backend=loopback_placeholder`, `external_call_made=false`, `allowed_actions=advisory_only`, `action_taken=none`, and no live DARS call or external action occurs |
| I9-A Secret/redaction scan baseline | HISYS-IMP-001 Section 3; HISYS-T-021; HISYS-NFR-SEC-001..002; HISYS-FR-ADM-001; HISYS-R-008 | `hisys.security.secret_scan` and `scripts/scan_secrets.py` scan repository/runtime text files for assignment-style secret-like values, skip runtime caches, and emit redacted reports only so quality-gate output does not leak matched values |
| I9-B Backup manifest and restore dry-run baseline | HISYS-IMP-001 Section 3; HISYS-T-023; HISYS-FR-ADM-003; HISYS-DATA-001..004 | `hisys.operations.backup` creates runtime-local zip backups plus SHA-256 manifests for controlled config/templates/harness/data/runtime-boundary/report files, excludes local-only secrets/tmp/cache/logs/backups, and verifies archive members through restore dry-run reports without writing restored files |
| I9-C Operator health status baseline | HISYS-IMP-001 Section 3; HISYS-FR-ADM-004; HISYS-T-006; HISYS-T-020; HISYS-T-023; HISYS-FR-AGT-004; HISYS-DARS-CONTRACT-001 | `hisys.operations.health` reports required runtime-directory readiness and disabled/loopback connector status without live external probes or side effects |
| I9-D Release-readiness evidence baseline | HISYS-IMP-001 Section 4; HISYS-T-024; HISYS-FR-ADM-001..004; HISYS-DATA-001..005; HISYS-CON-* | `hisys.operations.release_readiness` summarizes required quality gates, HISYS-T-024 trace-path evidence, known gaps, and the human-review/continue-hardening release decision without running live connectors |
| HISYS-T-027 Investigator multi-agent fixture research | docs/plans/investigator-multi-agent-research.md; HISYS-INST-INV-001; HISYS-FR-INV-001..006; HISYS-FR-MEM-001..005; HISYS-TPL-RESEARCH-SEARCH-001 | Implemented: `ResearchTask`, `EvidencePackage`, fixture research agents, evidence gate/merger, and `investigate-memo --agent ...` orchestration let multiple deterministic agents produce validated evidence packages before one template-based memo is built |
| HISYS-T-029 Formalism domain fixture research | HISYS-INST-INV-001; HISYS-FR-INV-001..006; HISYS-FR-MEM-001..005; HISYS-TPL-RESEARCH-SEARCH-001 | Implemented: `formalism_comparison` and `self_organization_mechanism` research agents produce domain-specific `EvidencePackage` claims about Dynamic Structure DEVS, graph rewriting, agent-based modeling, assessment criteria, selection heuristics, expressiveness/simulation/verification tradeoffs, self-organization mechanisms, and open questions for simulation semantics/proof/topology-change requirements |
| HISYS-T-030 Purpose-specific Investigator guidelines and evidence agents | HISYS-INST-INV-001; HISYS-FR-INV-001..006; HISYS-FR-MEM-001..005; HISYS-TPL-RESEARCH-SEARCH-001 | Implemented: `investigate-memo --purpose auto` selects `general_investigation`, `research_idea_discovery`, or `investment_decision_support` guideline profiles from topic/goal cues and records the selected `guideline_profile_id` in memo tags/body and the run report; `formalism_gap_analysis` produces explicit DSDEVS/graph-rewriting/ABM gap statements, hybrid novelty candidates, evaluation scenarios, and research questions; `investment_decision_support` produces bounded company fundamentals, market/competitor, valuation/risk, and needs-more-evidence decision-frame claims with a not-financial-advice safety limitation |
| HISYS-T-031 Purpose-aware automatic agent planning | HISYS-INST-INV-001; HISYS-FR-INV-001..006; HISYS-FR-MEM-001..005; HISYS-TPL-RESEARCH-SEARCH-001 | Implemented: if no explicit `--agent` is supplied, `investigate-memo` converts the selected guideline profile into a default evidence-agent plan: `research_idea_discovery` -> `formalism_gap_analysis`, `investment_decision_support` -> `investment_decision_support`, and `general_investigation` -> no extra agent; explicit `--agent` lists remain authoritative |
| HISYS-T-032 Configurable Investigator connector registry | HISYS-INST-INV-001; HISYS-FR-INV-001..006; HISYS-FR-MEM-001..005; HISYS-DATA-005; HISYS-TPL-RESEARCH-SEARCH-001 | Implemented: `investigator-agents.yaml` declares global connector safety policy, purpose default/optional agent plans, and disabled optional connector definitions for publisher web search, Claude/Codex read-only evidence extraction, local LLM offline mapping, market/news search, and company filing search; `investigate-memo` resolves the default plan from config and records `agent_plan_source`, `disabled_optional_agent_refs`, and `blocked_agent_refs` in the run report while preventing disabled explicit external connector execution |
| HISYS-T-028 Selenium read-only research harness | docs/plans/investigator-multi-agent-research.md; HISYS-CON-022..023; HISYS-D-015; HISYS-DATA-002 | Implemented: disabled-by-default `SeleniumReadOnlyAgent` enforces read-only and forbidden-action gates, rejects non-allowed live domains, extracts only local static HTML fixture content into an `EvidencePackage` with hash/path/title evidence, records `external_side_effects=false`, and performs no live browsing or network access |

I4 is present as a fixture-backed foundation/skeleton with CLI glue for local
runtime execution. I5 is present as a fixture-backed extraction foundation.
I6 is present as a fixture-backed editorial draft and duplicate/conflict review
foundation that writes only runtime-local memo draft/report artifacts and a
controlled Obsidian vault-write dry-run boundary that writes preview reports
under `runtime-boundary/obsidian/` without modifying the target vault. I7-A is
present as a fixture-backed Chief Editor alert decision foundation that writes
runtime-local alert decisions/reports, suppresses same-date repeated alert
candidates by `suppression_key`, requests approval for high/critical or non-local
target alert candidates, selects a Chief Editor product factory variant
(`analysis_only` or `alert_delivery_dry_run`) from `config/chief-editor.yaml` or
CLI override, writes dry-run alert action plans with blocked reasons
and approved pending send-candidate markers, applies runtime-local approve/reject
transitions while keeping `action_taken=none`, takes no live alert actions, and
records blocked live-connector decisions for explicit connector/action/approval
safety gates before any live adapter can be added. I8-A/B adds runtime-local advisory DARS handoff loopback artifacts without
implementing DARS or making live DARS calls. Investigator multi-agent fixture
research, the disabled Selenium read-only harness, purpose-specific evidence
agents, purpose-aware auto-planning, and the configurable connector registry are
implemented. I9-A adds a redacted secret-like value scanner for HISYS-T-021
quality gates, I9-B adds backup manifest plus restore dry-run verification for
HISYS-T-023, I9-C adds local operator health status for required runtime
directories and disabled/loopback connector posture, and I9-D adds
release-readiness evidence summaries for HISYS-T-024 trace path and gate status.
Full workflow coverage remains pending; later increments (real DARS adapter,
critique feedback, and any explicitly approved live connector adapter) are not
implemented yet.

## Module to controlled-doc map

| Module | Controlled doc / SRS area | Test |
|---|---|---|
| `hisys.core.ids` | HISYS-DATA-001 (stable IDs) | `tests/unit/test_core.py` |
| `hisys.core.time` | HISYS-IDD-001 Section 2 (ISO timestamps) | `tests/unit/test_core.py` |
| `hisys.core.errors` | HISYS-SDD-001 Section 8 (failure handling) | `tests/unit/test_core.py` |
| `hisys.core.result` | HISYS-IDD-001 Section 2 (error status) | `tests/unit/test_core.py` |
| `hisys.schemas.source` | HISYS-FR-SRC-001..005, HISYS-SCHEMA-001 Section 3 | `tests/unit/test_schemas.py` |
| `hisys.schemas.compliance` | HISYS-CHECK-WEB-001, HISYS-NFR-SEC-003, HISYS-NFR-SEC-005, HISYS-CON-022..023 | `tests/unit/test_registry.py` |
| `hisys.registry.source_registry` | HISYS-SRC-REG-INIT-001, HISYS-FR-SRC-001..005, HISYS-T-001..002 | `tests/unit/test_registry.py` |
| `hisys.adapters.base` | HISYS-IDD-001 Section 4, HISYS-FR-DS-001..006, normalize/provenance/error contract | `tests/unit/test_adapters.py` |
| `hisys.adapters.runtime` | HISYS-FR-DS-005, HISYS-NFR-REL-001, HISYS-CON-014, HISYS-T-006 | `tests/unit/test_adapters.py` |
| `hisys.schemas.observation` | HISYS-FR-INV-002..005, HISYS-DATA-002, HISYS-SCHEMA-001 Section 4 | `tests/unit/test_schemas.py` |
| `hisys.schemas.signal` | HISYS-FR-EXT-001..004, HISYS-SCHEMA-001 Section 5 | `tests/unit/test_schemas.py` |
| `hisys.schemas.perspective` | HISYS-FR-PER-001..004, HISYS-SCHEMA-001 Section 6 | `tests/unit/test_schemas.py` |
| `hisys.schemas.memo` | HISYS-FR-MEM-001..005, HISYS-SCHEMA-001 Section 7 | `tests/unit/test_schemas.py` |
| `hisys.schemas.alert` | HISYS-FR-CE-002..006, HISYS-SCHEMA-001 Section 8 | `tests/unit/test_schemas.py` |
| `hisys.schemas.handoff` | HISYS-FR-AGT-001..005, HISYS-SCHEMA-001 Section 9, HISYS-DARS-CONTRACT-001 | `tests/unit/test_schemas.py` |
| `hisys.schemas.hermes_trace` | HISYS-FR-DS-006, HISYS-FR-INV-006, HISYS-FR-AGT-005, HISYS-DATA-005, HISYS-SCHEMA-001 Section 10 | `tests/unit/test_schemas.py` |
| `hisys.schemas.audit` | HISYS-FR-ADM-002, HISYS-SCHEMA-001 Section 11 | `tests/unit/test_schemas.py` |
| `hisys.adapters.hardware_mock` | HISYS-FIXTURE-001 hardware-mock-temperature, HISYS-T-003 | `tests/unit/test_adapters.py` |
| `hisys.adapters.web_news_mock` | HISYS-FIXTURE-001 web-news-rss-permitted, HISYS-T-004 | `tests/unit/test_adapters.py` |
| `hisys.adapters.agent_system_mock` | HISYS-FIXTURE-001 agent-dars-critique, HISYS-T-005 | `tests/unit/test_adapters.py` |
| `hisys.adapters.hermes_tool_mock` | HISYS-FIXTURE-001 hermes-tool-hierarchy, HISYS-T-005A | `tests/unit/test_adapters.py`, `tests/integration/test_trace_path.py`, `tests/integration/test_cli_hermes_runtime.py` |
| `hisys.config.instance` | HISYS-RUNTIME-DIR-001, HISYS-D-015, HISYS-D-016 | `tests/unit/test_instance_config.py` |
| `hisys.config.loader` | HISYS-FR-SRC-001..005, HISYS-T-001..002 | `tests/unit/test_instance_config.py`, `tests/unit/test_example_instance.py` |
| `hisys.audit.writer` | HISYS-FR-ADM-002, HISYS-D-015, secret redaction guard | `tests/unit/test_runtime_writers.py` |
| `hisys.integrations.hermes_boundary` | HISYS-FR-DS-006, HISYS-FR-INV-006, HISYS-DATA-005 | `tests/unit/test_runtime_writers.py` |
| `hisys.integrations.obsidian_vault` | HISYS-FR-MEM-001..005, HISYS-IF-007, HISYS-DATA-002, HISYS-DATA-005, HISYS-CON-012 | `tests/unit/test_vault_writer.py` |
| `hisys.integrations.live_connectors` | HISYS-FR-AGT-004, HISYS-T-020, HISYS-T-022, HISYS-CON-010, HISYS-CON-012, HISYS-CON-022..023 | `tests/unit/test_live_connectors.py` |
| `hisys.investigator.runtime` | HISYS-INST-INV-001, HISYS-FR-INV-001..006, HISYS-T-007..008 | `tests/unit/test_investigator_runtime.py` |
| `hisys.extraction.extractor` | HISYS-FR-EXT-001..005, HISYS-DATA-002, HISYS-T-009..010 | `tests/unit/test_extraction_runtime.py` |
| `hisys.extraction.runtime` | HISYS-FR-EXT-001..005, HISYS-D-015, HISYS-T-009..010 | `tests/unit/test_extraction_runtime.py` |
| `hisys.editor.drafter` | HISYS-FR-PER-001..004, HISYS-FR-MEM-001..005, HISYS-DATA-002, HISYS-T-011..012 | `tests/unit/test_editor_runtime.py` |
| `hisys.editor.runtime` | HISYS-FR-PER-001..004, HISYS-FR-MEM-001..005, HISYS-D-015, HISYS-T-011..013 | `tests/unit/test_editor_runtime.py` |
| `hisys.chief_editor.policy` | HISYS-FR-CE-001..006, HISYS-CE-POLICY-001, HISYS-T-014..018 | `tests/unit/test_chief_editor_runtime.py` |
| `hisys.chief_editor.runtime` | HISYS-FR-CE-001..006, HISYS-D-015, HISYS-T-014..018 | `tests/unit/test_chief_editor_runtime.py` |
| `hisys.chief_editor.product` | HISYS-FR-CE-001..006, HISYS-CE-POLICY-001, HISYS-D-015, HISYS-T-025 | `tests/unit/test_chief_editor_runtime.py` |
| `hisys.chief_editor.action_plan` | HISYS-FR-CE-001..006, HISYS-D-015, HISYS-T-019, HISYS-T-021 | `tests/unit/test_chief_editor_runtime.py` |
| `hisys.chief_editor.approval` | HISYS-FR-CE-006, HISYS-D-015, HISYS-T-020 | `tests/unit/test_chief_editor_runtime.py` |
| `hisys.chief_editor.connector` | HISYS-FR-CE-006, HISYS-FR-AGT-004, HISYS-D-015, HISYS-T-022 | `tests/unit/test_alert_connector_runtime.py` |
| `hisys.agents.dars` | HISYS-FR-AGT-001..005, HISYS-DARS-CONTRACT-001, HISYS-D-015, HISYS-T-023..024 | `tests/unit/test_dars_runtime.py` |
| `hisys.operations.backup` | HISYS-T-023, HISYS-FR-ADM-003, HISYS-DATA-001..004 | `tests/unit/test_backup_restore.py` |
| `hisys.operations.health` | HISYS-FR-ADM-004, HISYS-T-006, HISYS-T-020, HISYS-T-023, HISYS-FR-AGT-004, HISYS-DARS-CONTRACT-001 | `tests/unit/test_health_status.py` |
| `hisys.operations.release_readiness` | HISYS-T-024, HISYS-FR-ADM-001..004, HISYS-DATA-001..005, HISYS-CON-* | `tests/unit/test_release_readiness.py` |
| `hisys.security.secret_scan` | HISYS-T-021, HISYS-NFR-SEC-001..002, HISYS-FR-ADM-001, HISYS-R-008 | `tests/unit/test_secret_scan.py` |
| `scripts/scan_secrets.py` | HISYS-T-021 quality-gate script | `tests/unit/test_secret_scan.py` |
| `hisys.cli.main` | HISYS-PKG-ARCH-001 Section 3, HISYS-RUNTIME-DIR-001, HISYS-INST-INV-001, HISYS-T-001, HISYS-T-005A, HISYS-T-007..026 | `tests/unit/test_cli_runtime.py`, `tests/integration/test_cli_hermes_runtime.py` |
| `examples/instance` | HISYS-RUNTIME-DIR-001, HISYS-HARNESS-GUIDE-001, HISYS-D-015, HISYS-D-016 | `tests/unit/test_example_instance.py` |

## End-to-end trace path tests

`tests/integration/test_trace_path.py` exercises the schema-level path required by
`HISYS-IMP-001` Section 4 and `HISYS-T-024`:

    SourceRegistryEntry
      -> HermesCollectionTrace + RawObservation
      -> ExtractedSignal
      -> ZettelMemo
      -> AlertDecisionRecord
      -> AuditEvent

`tests/integration/test_cli_hermes_runtime.py` exercises the runtime CLI path:

    validate-config
      -> collect SRC-HERMES-TOOL-001
      -> RawObservation JSON
      -> HermesCollectionTrace JSON
      -> Hermes Markdown boundary record
      -> Audit JSONL
      -> collection-report JSON/Markdown

For each path the tests assert:

- evidence and interpretation records are linked but distinct;
- Hermes hierarchical fields (campaign_id, hermes_parent_run_id, user_input_ref,
  delegated_task_id, tool_invocation_id, prompt_or_query_ref, tool_output_ref,
  boundary_record_ref, scope_policy_ref, approval_state) are populated;
- the boundary record path matches the controlled convention
  `hisys/runtime-boundary/hermes/<YYYYMMDD>/<campaign_id>/<record_kind>-<stable_id>.md`.

## Constraints honored here

- HISYS-CON-022..023: no live web/network calls in this code; only fixtures.
- HISYS-T-001..002: source registry entries require governance metadata;
  web/news collection is blocked without compliance checklist evidence.
- HISYS-T-003..006: adapter contract covers initialization, health,
  collection, normalization, provenance capture, bounded error records, and
  source failure isolation.
- HISYS-T-007..008: Investigator foundation and CLI glue collect from
  registered fixture sources, write RawObservation JSON records, skip
  unregistered sources, append audit JSONL records, persist Hermes Markdown
  boundary records for Hermes sources, and persist JSON/Markdown run summaries
  in the local runtime instance.
- HISYS-T-009..010: Extraction foundation and CLI glue create
  `ExtractedSignal` records from local `RawObservation` evidence references,
  preserve confidence/uncertainty/contradiction metadata, avoid raw payload
  copying, persist signal JSON under the runtime instance, and persist
  JSON/Markdown extraction reports.
- HISYS-T-011..012: Editorial foundation applies an active fixture
  `PerspectiveProfile`, rejects inactive perspectives, creates atomic
  `ZettelMemo` draft records with source/signal refs, confidence, tags,
  revision/review metadata, avoids raw payload copying, and persists runtime-
  local JSON/Markdown memo drafts plus memo draft reports.
- HISYS-T-013: Fixture duplicate/conflict review scans runtime-local memo
  drafts, flags duplicated summaries as `flagged_duplicate`, flags simple
  high-vs-normal source conflicts as `flagged_conflict`, rewrites reviewed memo
  JSON/Markdown records, and persists memo review JSON/Markdown reports.
- HISYS-T-026: Investigator direct memo foundation runs registry-gated fixture
  source investigation from a research topic/goal, applies
  `HISYS-TPL-RESEARCH-SEARCH-001`, persists linked `ExtractedSignal` records and
  `data/investigation-memos/<YYYYMMDD>/` `ZettelMemo` JSON/Markdown artifacts,
  writes `investigation-memo-report.{json,md}`, and keeps raw payload content out
  of the memo body by preserving only observation, signal, source, payload-ref,
  and payload-hash references.
- HISYS-T-027: Multi-agent Investigator research introduces explicit
  `ResearchTask` and `EvidencePackage` contracts, fixture research agents,
  evidence package validation/merging, and `investigate-memo --agent ...` so
  several subagents can research independently while the Investigator remains
  the only component that builds the final template memo.
- HISYS-T-028: Selenium/browser research remains disabled by default and
  is limited to a read-only harness using allowed domains/static local HTML,
  forbidden action gates, DOM/text/hash evidence capture, and
  `external_side_effects=false` package validation before any live browsing can
  be considered.
- HISYS-T-014..025: Chief Editor foundation reads runtime-local memo review
  reports and reviewed memo drafts, applies the fixture `HISYS-CE-POLICY-001`
  policy through a product factory selected by `config/chief-editor.yaml` or CLI,
  creates `AlertDecisionRecord` JSON/Markdown records for conflict
  escalation candidates, records duplicate memo non-escalations as suppressed
  decisions, suppresses repeated same-date alert candidates whose
  `suppression_key` already appears in prior non-suppressed alert decisions,
  requests human approval for high/critical or non-local target candidates while
  keeping `action_taken=none`, lets `analysis_only` close judgments with
  `target_channel=null` and no send candidate while `alert_delivery_dry_run`
  preserves the approval/action-plan path, persists alert decision JSON/Markdown reports,
  writes dry-run `AlertActionPlanRecord` JSON/Markdown records and action-plan
  reports with blocked reasons and approved pending `would_send=true` candidate
  markers while `live_delivery_permitted=false`, applies runtime-local
  approve/reject transitions to requested decisions while keeping
  `action_taken=none`, persists approval transition JSON/Markdown reports,
  writes disabled connector execution records/reports with
  `execution_status=blocked`, `live_delivery_permitted=false`, and
  `action_taken=none`, and performs no live alert sends or external connector
  actions.
- HISYS-T-023..024: I8-A/B DARS foundation creates runtime-local advisory
  `AgentHandoffPackage` JSON/Markdown artifacts from disabled connector
  execution evidence and returns loopback placeholder critique JSON/Markdown
  records because DARS is intentionally not implemented yet. The contract
  records `dars_backend=loopback_placeholder`, `external_call_made=false`,
  `allowed_actions=advisory_only`, and `action_taken=none`, persists
  `dars-critique-report.{json,md}`, and is shaped so a future DARS adapter can
  replace the loopback without changing downstream artifacts.
- HISYS-D-015: I4 persistence baseline is local JSON/JSONL, not a live database
  or external service.
- HISYS-D-016: Hermes foundation is collection-only and scoped to preapproved
  registered sources and Markdown boundary records.
- HISYS-CON-021: Python 3.11+ runtime baseline.
- HISYS-NFR-SEC-001..002: only fake non-secret tokens in fixtures.
- HISYS-DATA-005: Hermes provenance fields are non-optional in the trace
  record schema and validated at construction time.
