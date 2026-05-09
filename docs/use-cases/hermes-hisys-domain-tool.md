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
    "include_evidence_package": true,
    "include_alternative_set": true,
    "include_dars_critique": true,
    "include_recommendation_memo": true
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

## 5. Domain Adapter Model

Hisys should not hardcode every domain into one workflow. Instead use domain adapters selected by configuration:

```text
DomainAdapter
  -> source policy
  -> evidence schema
  -> extraction/analyzer set
  -> candidate generator
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
runtime-boundary/domain-investigation/<YYYYMMDD>/
  hisys-tool-request-<request_id>.json
  investigation-data-<investigation_id>.json
  evidence-package-<investigation_id>.json
  design-or-decision-candidates-<investigation_id>.json
  alternative-decision-set-<investigation_id>.json
  dars-request-<dars_request_id>.json
  dars-response-<dars_response_id>.json
  recommendation-memo-<investigation_id>.md
  hisys-tool-result-<request_id>.json
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

## 10. Suggested MVP Increment

The first implementation should remain local and file-backed:

1. Add `DomainInvestigationRequest` and `DomainInvestigationResult` schemas.
2. Add a local `hisys investigate-domain` CLI command that reads a JSON request.
3. Implement only `domain="codebase"` first, backed by existing codebase-analysis design.
4. Persist generic runtime-boundary artifacts.
5. Return a compact JSON result suitable for Hermes tool wrapping.
6. Keep external calls and mutations disabled.
7. Add tests for blocked external calls, blocked mutation requests, domain validation, artifact refs, and advisory-only DARS behavior.
