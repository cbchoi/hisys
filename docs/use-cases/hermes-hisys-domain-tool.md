# Hisys as a Hermes-Callable Domain Investigation Tool

**Status:** adopted-use-case-baseline  
**Version:** 0.1.0  
**Traceability:** HISYS-FR-INV-001..006; HISYS-FR-MEM-001..005; HISYS-FR-AGT-001..005; HISYS-DARS-CONTRACT-001; HISYS-T-019; HISYS-T-020; HISYS-T-024; HISYS-CON-010; HISYS-CON-011; HISYS-CON-012; HISYS-CON-022; HISYS-CON-023

## 1. Purpose

Hisys should be designed as a **domain-general investigation and decision-support tool** that Hermes can call. Codebase analysis is one important specialization, but the core product should apply to any domain where Hermes needs controlled investigation, evidence packaging, progressive DARS critique, and advisory alternatives. This use case follows the adopted design philosophy in `docs/architecture/design-philosophy.md`.

Conceptually:

```text
Hermes conversation/task
  -> Hisys tool request
  -> Investigator builds domain evidence package
  -> Candidate/alternative generation
  -> DARS progressive critique using domain rubrics
  -> Recommendation memo and runtime-boundary records
  -> Hermes returns advisory result to user or starts a human-approved next loop
```

Hisys is not just a background service. It is a governed tool boundary that helps Hermes transform informal user goals into auditable investigation data, alternatives, critique, and recommendations.

## 2. Design Position

Hisys should expose a tool-like interface that Hermes can use from CLI, Discord, scheduled jobs, or future MCP/native tool integration.

Recommended product boundary:

```text
Hermes = conversational/task orchestrator
Hisys = controlled investigation + evidence + DARS decision-support engine
DARS = advisory critic/evaluator role inside Hisys
```

Hermes may decide when to call Hisys, but Hisys remains the system of record for:

- source scope and source-governance decisions;
- investigation evidence packages;
- candidate and alternative records;
- DARS request/response artifacts;
- rubric scores and critique traces;
- recommendation memos;
- runtime-boundary reports.

## 3. Domain-General Flow

```text
1. Hermes receives a user/domain question
   -> "Analyze this codebase"
   -> "Compare possible research topics"
   -> "Evaluate investment alternatives"
   -> "Assess an ISO/process improvement option"
   -> "Find better productization paths"

2. Hermes calls Hisys with a controlled request
   -> domain
   -> objective
   -> allowed sources
   -> output expectations
   -> safety/external-call constraints

3. Hisys Investigator builds evidence
   -> current artifacts
   -> external/open references when approved
   -> previous project results
   -> domain-specific metrics/signals

4. Hisys generates candidates and alternatives
   -> explicit baseline/do-nothing option when useful
   -> incremental options
   -> redesign/reuse/productization options
   -> uncertainty and evidence gaps

5. DARS critiques alternatives progressively
   -> logical conservative devil
   -> domain expert devil
   -> safety/security/privacy devil
   -> business/value devil
   -> source-governance devil when external sources are involved

6. Hisys synthesizes advisory recommendation
   -> ranked alternatives
   -> evidence refs
   -> rubric scores
   -> unresolved risks
   -> next safe Ralph-loop increment if implementation is desired

7. Hermes reports result
   -> returns summary to user
   -> asks for human approval before live/external/destructive actions
   -> may start implementation loop only after approval
```

## 4. Hermes Tool Contract

A future Hermes-facing Hisys tool should accept a compact request such as:

```json
{
  "tool": "hisys_investigate",
  "request_id": "HERMES-HISYS-REQ-...",
  "domain": "codebase|research|business|investment|iso_process|general",
  "objective": "Find possible alternatives and recommend the best next path.",
  "sources": [
    {
      "source_type": "current_artifact",
      "ref": "/path/or/url/or/id",
      "access_mode": "read_only"
    },
    {
      "source_type": "previous_project_result",
      "ref": "runtime-boundary/...",
      "access_mode": "read_only"
    }
  ],
  "constraints": {
    "external_calls_allowed": false,
    "mutation_allowed": false,
    "credential_use_allowed": false,
    "max_rounds": 3
  },
  "output_contract": {
    "include_summary": true,
    "include_recommended_alternative": true,
    "include_runtime_boundary_refs": true,
    "include_quality_gate": true
  }
}
```

Hisys should return a structured tool result:

```json
{
  "request_id": "HERMES-HISYS-REQ-...",
  "status": "completed|blocked|needs_approval|failed",
  "domain": "codebase",
  "summary": "...",
  "recommended_alternative_id": "ALT-002",
  "requires_human_review": true,
  "external_call_made": false,
  "mutation_performed": false,
  "runtime_boundary_refs": [
    "runtime-boundary/domain-investigation/20260509/investigation-data-INV-....json",
    "runtime-boundary/domain-investigation/20260509/recommendation-memo-INV-....md"
  ],
  "quality_gate": {
    "traceability_recorded": true,
    "secret_scan_passed": true,
    "rubric_scores_recorded": true
  }
}
```

## 5. Three-Layer Domain Use-Case Model

Hisys should not hardcode every domain into one workflow. Each domain should be
implemented as an object-oriented use case composed of three layers:

```text
DomainUseCase
  -> InvestigationLayer
  -> AggregationLayer
  -> DecisionLayer
```

Layer responsibilities are separated:

| Layer | Responsibility | Boundary |
|---|---|---|
| Investigation | Select/search local and approved source evidence | read-only evidence and memo refs |
| Aggregation | Aggregate memos/evidence into a report | no decision authority |
| Decision | Run DARS or another approved review over the report | advisory/human-review boundary |

Base interfaces live under `hisys.domain.layers`:

```text
InvestigationLayer.investigate(request, context) -> InvestigationWorkProduct
AggregationLayer.aggregate(request, context, investigation) -> AggregationWorkProduct
DecisionLayer.decide(request, context, aggregation) -> DecisionWorkProduct
DomainUseCase.run(request, context) -> DomainUseCaseResult
```

Concrete classes do the domain work. The current concrete use-case classes are:

| Use case | Investigation | Aggregation | Decision |
|---|---|---|---|
| `ResearchAnalysisUseCase` | `ResearchInvestigationLayer`: search local `/home/cbchoi/me` memos and planned publisher-source evidence | `MemoReportAggregationLayer`: aggregate memos and evidence into a report | `DarsDecisionLayer(decision_type="research_review")` |
| `CodeAnalysisUseCase` | `CodeInvestigationLayer`: search local `/home/cbchoi/me` plus a local requirements folder | `MemoReportAggregationLayer`: aggregate memos and evidence into a report | `DarsDecisionLayer(decision_type="code_evaluation_review")` |

The existing `DomainAdapter` remains the CLI dispatch seam. A domain adapter may
own one concrete `DomainUseCase`, call its three layers, then translate the
`DomainUseCaseResult` into Hisys investigation artifacts and tool results.

```text
DomainAdapter
  -> source policy
  -> DomainUseCase(investigation, aggregation, decision)
  -> evidence schema
  -> rubric binding
  -> DARS critic panel
  -> recommendation memo template
```

Example domain adapters:

| Domain | Evidence examples | Candidate examples |
|---|---|---|
| `codebase` | repo metrics, modules, tests, docs, previous release reports, OSS refs | refactor, productize, reuse, agent workflow |
| `research` | papers, publisher pages, datasets, notes, previous manuscripts | topic, gap, method, journal strategy |
| `business` | market notes, customer interviews, competitor refs, prior experiments | product direction, pricing, go-to-market |
| `investment` | company/project data, risk factors, market indicators, previous theses | invest, hold, avoid, request diligence |
| `iso_process` | process docs, audit records, NCR/CAPA records, previous decisions | improve process, add control, revise SOP |
| `general` | user-provided evidence and controlled references | alternatives chosen by objective |

## 6. Registry Implications

This use case extends the adopted registry strategy:

```text
ConfigRegistry
  -> domain adapter registry
  -> source policies
  -> allowed analyzers/connectors
  -> DARS round/threshold policies
  -> output/retention/redaction policies

OntologyManager (future extension)
  -> configuration suitability mappings across domains, objectives, evidence types, rubrics, prompts, connectors, tenant policy, and approval context

PromptRegistry
  -> domain investigator prompts
  -> DARS critic role bundles
  -> domain rubrics
  -> synthesis templates

SecretManager
  -> credentials for approved private sources only

Runtime evidence store
  -> investigation packages, alternatives, DARS critiques, recommendation memos
```

Suggested config IDs:

| Config ID | Purpose |
|---|---|
| `hisys-domain-adapter-registry` | Available domain adapters and enabled status |
| `hisys-tool-policy` | Hermes-facing Hisys tool permissions and external-call/mutation defaults |
| `configuration-suitability-ontology` | future ontology mapping that recommends suitable domain adapters, configs, prompt bundles, rubrics, and connector policies for a request context |
| `domain-source-policy-<domain>` | Allowed source types and governance rules by domain |
| `domain-rubric-binding-<domain>` | Rubrics and DARS critic panel by domain |
| `domain-output-policy-<domain>` | Report/memo format, redaction, and retention |

Suggested prompt bundles:

| Prompt bundle | Role |
|---|---|
| `pb-domain-investigator-<domain>` | Domain-specific evidence planning and extraction guidance |
| `pb-domain-logical-devil` | Cross-domain conservative logical critic |
| `pb-domain-source-governance-devil` | Source, license, and provenance critic |
| `pb-domain-synthesizer-<domain>` | Domain-specific alternative synthesis |

Research-gap request framing should use constrained fields before free prose. A
recommended frame is:

```json
{
  "intent": ["find", "compare", "analyze", "assess", "synthesize"],
  "object": ["research_gap", "formalism_alternatives", "evidence_tension"],
  "domain": "self_organizing_structure_formalism",
  "target_topic": "find research gap among formalisms for self-organizing structure",
  "criteria": [
    "local_interaction_rules",
    "feedback_representation",
    "emergent_global_structure",
    "adaptation_over_time",
    "topology_behavior_coevolution",
    "executable_simulation_semantics",
    "verification_readability_tradeoff"
  ],
  "outputs": [
    "gap_matrix",
    "formalism_comparison",
    "synthesis_opportunity",
    "evaluation_scenario",
    "recommended_research_direction"
  ],
  "constraints": {
    "separate_evidence_from_interpretation": true,
    "cite_source_or_evidence_ref_per_gap": true,
    "external_calls_allowed": false,
    "mutation_allowed": false,
    "chief_editor_final_action": "recommend_or_request_more_evidence_only"
  }
}
```

This mirrors investment/business prompts such as `intent=[find, analyze, assess]`
plus `object=[valuable company in IT sector, valuation gap, risk factor]`, while
keeping the domain-specific object and rubric controlled by Hisys configuration.
Prompt text can narrow the topic but cannot override source policy, connector
policy, output schema, or approval gates.

## 7. Runtime Boundary Layout

For domain-general use, persist artifacts under:

```text
runtime-boundary/domain-investigation/<domain>/<YYYYMMDD>/
  hisys-tool-request-<request_id>.json
  hisys-tool-request-<request_id>.md
  investigation-data-<investigation_id>.json
  alternative-decision-set-<alternative_set_id>.json
  domain-investigation-result-<result_id>.json
  hisys-tool-result-<request_id>.json
  hisys-tool-result-<request_id>.md
runtime-boundary/dars/<YYYYMMDD>/
  dars-request-<dars_request_id>.json
  dars-response-<dars_response_id>.json
  dars-trace-<trace_id>.json
runtime-boundary/chief-editor/research/<YYYYMMDD>/
  research-recommendation-review-<decision_id>.json
  research-recommendation-review-<decision_id>.md
reports/run-summaries/<YYYYMMDD>/
  domain-investigation-report.json
  domain-investigation-report.md
```

Domain-specific subdirectories may be used for clarity:

```text
runtime-boundary/domain-investigation/codebase/<YYYYMMDD>/...
runtime-boundary/domain-investigation/research/<YYYYMMDD>/...
runtime-boundary/domain-investigation/business/<YYYYMMDD>/...
```

## 8. Safety and Commercialization Rules

1. Hisys tool calls are read-only by default.
2. Hermes cannot grant itself live external access through prompt text.
3. External collection requires source policy, connector policy, and approval.
4. Mutation/code changes/deployment require separate human approval and a Ralph loop.
5. DARS critique is advisory only and cannot select final decisions by itself.
6. Runtime artifacts must record config snapshot refs and prompt bundle refs.
7. Secrets are never included in Hisys tool requests, prompt bundles, or config bodies.
8. Domain adapters must declare what evidence they inspect and what they refuse to inspect.
9. Commercial deployments should enforce tenant scope, RBAC, approval, audit, retention, and rollback through `ConfigRegistry`/`PromptRegistry`.
10. Future ontology management may recommend which approved configuration is suitable for a Hermes request, but it cannot activate configurations, bypass validation, or override approval gates.

## 9. Relationship to Codebase Analysis

The codebase-analysis use case is now a specialization of this domain-general tool model:

```text
hisys_investigate(domain="codebase")
  -> current codebase evidence
  -> open-source reference evidence
  -> previous project result evidence
  -> design candidates
  -> alternative decision set
  -> DARS critique
  -> recommendation memo
```

Other domains should reuse the same shape with domain-specific evidence and rubrics.

## 10. Implemented Local MVP Increment

The local MVP boundary now exists for the research-gap/formalism path and remains
fixture-backed/read-only:

1. `DomainInvestigationRequest`, `InvestigationDataPackage`,
   `AlternativeDecisionSet`, `DomainInvestigationResult`, and compact
   `HisysToolResult` schemas exist.
2. `hisys investigate-domain --request <json>` validates the request and writes
   runtime-boundary artifacts.
3. `hisys.domain.adapters.DomainAdapterRegistry` and
   `DomainInvestigationContext` now provide the dispatch seam for domain-specific
   adapters. The CLI no longer needs to call one hardcoded domain builder
   directly; it builds a context and resolves the ordered adapter registry.
4. `hisys.domain.layers` defines base interfaces for the three-layer object
   model: `InvestigationLayer`, `AggregationLayer`, `DecisionLayer`, and
   `DomainUseCase`.
5. `hisys.domain.use_cases` provides concrete research and code use-case classes
   with the requested layer split: investigation searches local me-vault plus
   publisher or requirements sources, aggregation builds memo reports, and
   decision runs the DARS boundary.
6. `domain="research"` with an objective containing research gap/formalism
   language generates a deterministic fixture recommendation for
   Self-organizing Dynamic Structure DEVS with graph-rewrite structural
   transitions through the research-gap adapter.
7. DARS local loopback fixture critique writes advisory-only request, response,
   and trace artifacts; it may recommend more evidence but cannot execute,
   mutate, block, or approve.
8. Chief Editor writes a `research_recommendation_review` product with
   `recommend_with_conditions`, human-review-required, and no external action.
9. Tests cover adapter dispatch, three-layer use cases, artifact refs, safety
   flags, advisory-only DARS behavior, and the Chief Editor research decision
   product.
10. External calls and mutations remain disabled by default.

Next post-MVP increments should add file-backed ConfigRegistry/PromptRegistry
snapshots, a requirements-analysis adapter for stakeholder-intent and
requirement-candidate packets, and the codebase domain adapter.

## 11. Pass-Contract Self-Improvement

Hisys now has a governed proposal path for broadening pass-contract coverage
without weakening evidence standards. Repeated `needs_more_evidence` outcomes
should first be classified by dominant reason, for example `adapter_missing`,
`domain_contract_missing`, `independent_corroboration_missing`,
`contradiction_unchecked`, or `claim_coverage_incomplete`. The
`propose-pass-contract` CLI writes proposal artifacts that describe a candidate
contract, expected fixture/test artifacts, validation gates, and the strict
boundary that Hisys must not self-authorize lower standards.

```bash
hisys propose-pass-contract \
  --instance "$HISYS_INSTANCE" \
  --date <YYYYMMDD> \
  --domain product_architecture \
  --question-type architecture_choice \
  --failure-mode adapter_missing \
  --example-request-id REQ-ARCH-001 \
  --format json
```

The command writes only local proposal artifacts and a run-summary report. It
sets `automatic_promotion_allowed=false`, `external_call_made=false`,
`mutation_performed=false`, and `publication_or_live_action_approved=false`.
Promotion from proposal to active contract remains a later human-reviewed,
traceable change with focused tests, traceability validation, secret scan, and
DARS/Chief Editor review where relevant.

The full staged workflow is now CLI-backed: convert the proposal to an inactive
candidate, evaluate it against a local evidence summary, request an advisory
Chief Editor/DARS review package, promote only with a human approval ref plus
local review/validation refs, and optionally let `investigate-domain` consume an
explicit active registry for the scoped domain/question type. Routine proposal,
evaluation, review, audit, and domain-evaluation paths remain local-only and do
not perform external calls, mutations, publication, or live actions.

## Domain Naming Strategy for Example Specs

Traceability: HISYS-DOM-005, HISYS-DOM-006, HISYS-DOM-012.

For the first structured-domain Ralph loop, the canonical domain is `codebase` for development/codebase evaluation. `development` is not accepted as a direct `DomainName` unless a future pre-validation alias-normalization seam is explicitly added.

Requirements-analysis uses `domain="codebase"` with an explicit objective convention such as `requirements-analysis: ...` until a later governed schema increment decides whether `requirements_analysis` should become a first-class `DomainName`.

Compatibility sentence: requirements-analysis uses `domain="codebase"` for the first structured-domain loop.

## Adding a New Structured-Domain Spec

Traceability: HISYS-FR-DOM-001..005, HISYS-NFR-MNT-001, HISYS-T-025..027.

Follow these steps to register a new example domain spec without adding ad-hoc `if domain == ...` CLI branches.

### Step 1 — Cite controlled-document anchors

Before writing code or tests, record the relevant anchors for the new spec in the Ralph task header:

- SRS requirements that justify the spec (`HISYS-FR-DOM-001..005` for example domains; `HISYS-FR-DOM-006` for investment).
- SDD design entry under `Domain Investigation Adapter Design`.
- IDD interface `HISYS-IF-017` and section `5.7 DomainInvestigationAdapter / DomainAdapterSpec`.
- STD tests `HISYS-T-025..028` covering registration, bridge, and runtime-artifact governance.

### Step 2 — Define the spec fields

A new spec is a `DomainAdapterSpec` (`src/hisys/domain/domain_adapters.py`) declaring:

- `domain_id`: canonical domain string from `DomainName` (`codebase`, `research`, `investment`, ...). Do not add new `DomainName` entries without a controlled schema increment.
- `aliases`: extra accepted `request.domain` strings. Must not collide with any other spec's canonical domain or alias.
- `use_case_factory`: zero-argument callable returning a `DomainUseCase` (`investigation_layer`, `aggregation_layer`, `decision_layer`).
- `translator`: `DomainUseCaseArtifactTranslator()`.
- `artifact_writer`: `DomainRuntimeArtifactWriter()`.
- `traceability_ids`: tuple of `HISYS-*` IDs the spec must trace to.
- `safety_policy`: keep `read_only_advisory` unless a controlled task lifts the boundary.

### Step 3 — Implement the three-layer use case

Add the new use case in `src/hisys/domain/use_cases.py` as three classes (investigation, aggregation, decision) plus a `DomainUseCase` subclass that wires them together. Keep all evidence references as governed memo/ref strings; do not perform filesystem, network, or credential access.

### Step 4 — Write RED tests before code

Create `tests/unit/test_<domain>_structured_domain_spec.py` and write failing tests for:

- `<domain>_spec()` exists and returns `DomainAdapterSpec(domain_id="<domain>", ...)`.
- The structured adapter accepts `DomainInvestigationRequest(domain="<domain>")` and returns a bridgeable `DomainInvestigationResult` with `requires_human_review=true`, `external_call_made=false`, `mutation_performed=false`.
- The registry resolves the request to `StructuredDomainAdapter(<domain>_spec())` (and not to the legacy research-gap adapter for non-formalism objectives).

Confirm RED by running the focused command:

```bash
python3 -m pytest tests/unit/test_<domain>_structured_domain_spec.py -q
```

### Step 5 — Check alias collisions

After adding the spec to `_default_domain_adapter_registry` in `src/hisys/cli/main.py`, `validate_spec_collisions()` (`src/hisys/domain/specs.py`) rejects:

- Duplicate canonical domains.
- An alias that equals another spec's canonical domain.
- An alias duplicated across specs.

Aliases identical to the spec's own `domain_id` are allowed redundancy. Cover the rejection cases with at least one focused test in `tests/unit/test_domain_spec_collisions.py`.

### Step 6 — Run quality gates

Run focused, milestone, and global gates from `ralph.md` Section 10 before reporting the new spec ready:

```bash
python3 -m pytest \
  tests/unit/test_<domain>_structured_domain_spec.py \
  tests/unit/test_domain_example_specs.py \
  tests/unit/test_domain_spec_collisions.py \
  tests/unit/test_domain_cli.py \
  tests/unit/test_structured_domain_adapter.py \
  -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
python3 -m pytest -q
```

Stop the Ralph loop if any gate fails; do not paper over a failure with broader try/except or fallbacks.

## Investment Structured-Domain Adapter

Traceability: HISYS-FR-DOM-006, HISYS-FR-DOM-003..004, HISYS-FR-AGT-003..004, HISYS-NFR-SEC-001..004, HISYS-T-028.

The investment domain is migrated to the structured-domain substrate via `investment_spec()` (`src/hisys/domain/specs.py`) and `InvestmentAnalysisUseCase` (`src/hisys/domain/use_cases.py`). The adapter is advisory-only by construction:

- The decision layer recommendation embeds the safety phrases `not financial advice` and `no autonomous execution` plus the governance flags `execution_authorized=false` and `publication_or_live_action_approved=false`, so the persisted runtime artifact surfaces the boundary without re-resolving the underlying investment packet.
- `requires_human_review=true`, `external_call_made=false`, and `mutation_performed=false` are preserved.
- The investigation layer is read-only over local me-vault and `runtime-boundary/investment-decisions` artifacts and performs no network, credential, or filesystem mutation.
- The structured-domain adapter does not duplicate `InvestmentDecisionPacket` or `InvestmentWeightPolicy` schemas: it references existing packet/dry-run/weight-policy artifacts via `request.sources` and `request.config_snapshot_refs` so the existing `build-investment-decision-packet`, `run-investment-decision-dry-run`, and `review-investment-decision-packet` CLI workflows remain the system of record.
- Registry order is `_ResearchGapDomainAdapter → StructuredDomainAdapter(research_spec()) → StructuredDomainAdapter(codebase_spec()) → StructuredDomainAdapter(investment_spec())`.

Any future change that would set `execution_authorized=true`, `publication_or_live_action_approved=true`, allow live broker connectors, or perform autonomous order placement must come through a new controlled SRS/SDD/IDD/STD increment with explicit human-approved scopes and fixture-first tests. Hisys/Ralph must never enable these in code.
