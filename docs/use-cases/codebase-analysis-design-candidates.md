# Codebase Analysis and Design Candidate Discovery Use Case

**Status:** adopted-use-case-baseline  
**Version:** 0.1.0  
**Traceability:** HISYS-FR-INV-001..006; HISYS-FR-MEM-001..005; HISYS-FR-AGT-001..005; HISYS-DARS-CONTRACT-001; HISYS-T-019; HISYS-T-020; HISYS-T-024; HISYS-CON-010; HISYS-CON-011; HISYS-CON-012; HISYS-CON-022; HISYS-CON-023

## 1. Purpose

This use case specializes the domain-general Hermes-facing Hisys tool model in `docs/use-cases/hermes-hisys-domain-tool.md` for software repositories and follows the adopted Hisys design philosophy in `docs/architecture/design-philosophy.md`. It applies Hisys to software repositories and related project evidence so it can analyze the **current codebase**, relevant **open-source references**, and **previous project results**, then identify design candidates, critique alternatives with DARS, and recommend better uses or better architecture paths.

The target output is not an automatic code change. The target output is a controlled advisory package:

```text
InvestigationDataPackage
  -> CodebaseEvidencePackage[]
  -> ComparativeReferencePackage[]
  -> PreviousResultPackage[]
  -> DesignCandidateRecord[]
  -> AlternativeDecisionSet
  -> DarsRequestEnvelope
  -> DarsResponseEnvelope / rubric scores
  -> DesignRecommendationMemo
```

The Investigator owns evidence collection and normalization. DARS receives only the curated investigation package and evaluates alternatives; it does not independently mutate repositories, fetch unapproved sources, or decide final implementation.

## 2. Business Motivation

Commercial customers often need to answer questions such as:

- What is this codebase good for?
- Which product/service use cases fit the existing architecture?
- Which open-source projects solve similar problems, and what design patterns can be borrowed legally and safely?
- Which previous internal project results, memos, experiments, or release reports should inform the new decision?
- Which modules are reusable as commercial assets?
- Where are design bottlenecks, hidden coupling, or missing abstractions?
- Which refactoring candidates produce the highest value with acceptable risk?
- Which agent/LLM workflows can safely assist this repository?
- Which productization paths are most feasible?

Hisys can become an advisory tool that Hermes calls to convert multi-source investigation evidence into design candidates, DARS critique, possible alternatives, and progressive decision support. The same pattern should apply beyond codebases; this document defines the `domain="codebase"` adapter specialization.

## 3. Scope

Initial scope is **read-only multi-source software investigation**.

Allowed:

- read the current repository files;
- read approved local previous project results such as controlled docs, memos, runtime-boundary reports, release-readiness evidence, and experiment summaries;
- inspect approved open-source repositories or downloaded snapshots when licensing/source policy allows it;
- compute structure/LOC/language metrics;
- inspect dependency manifests;
- identify modules, packages, CLIs, tests, docs, and runtime boundaries;
- produce evidence packages and memos;
- generate possible alternatives from current-codebase evidence, open-source comparison, and previous-result lessons;
- request DARS critique of design candidates and alternative sets;
- produce advisory recommendations.

Not allowed by default:

- modifying code;
- opening PRs;
- running live deployments;
- cloning/fetching external repositories unless the connector/source policy allows it;
- sending proprietary or third-party code to external LLMs unless approved;
- exfiltrating proprietary code;
- copying third-party code into the product without license review;
- storing secrets in config or prompts;
- executing untrusted project scripts without approval.

## 4. Actors

| Actor | Role |
|---|---|
| User / product owner | asks what the codebase can become or how it should improve |
| Hermes | conversational/task orchestrator that may call Hisys with `domain="codebase"` and return the advisory result to the user |
| Hisys domain tool boundary | validates the request, applies config/prompt registry snapshots, persists runtime-boundary records, and prevents unapproved external calls or mutation |
| Investigator | plans source scope, gathers current-codebase/open-source/previous-result evidence, and builds `InvestigationDataPackage` |
| Source Governance Gate | validates source type, license/sensitivity, connector permissions, and external-call policy before evidence collection |
| Candidate Generator | proposes possible design/use candidates and alternative decision paths |
| DARS critic panel | critiques candidates and alternatives using logical, security, architecture, domain, business, and legal/source-governance rubrics |
| Synthesizer | merges investigation evidence and critique into ranked alternatives and recommendations |
| Human reviewer | selects an alternative, requests more evidence, or approves the next implementation action |

## 5. Progressive Decision Flow

```text
1. Hermes/Hisys investigation planning
   -> Hermes passes a controlled `hisys_investigate(domain="codebase")` request
   -> Hisys identifies current repo path/branch, approved open-source references, previous project-result sources, source-governance limits, and allowed analysis depth

2. Evidence extraction
   -> current-codebase language/LOC metrics
   -> current package/module graph
   -> dependency and CLI/API inventory
   -> test and quality-gate inventory
   -> README/docs intent signals
   -> runtime-boundary / integration signals
   -> previous project lessons, release reports, failed attempts, accepted decisions
   -> open-source architecture/design comparisons with license/source-governance notes

3. Candidate and alternative generation
   -> commercial use candidates
   -> architecture refactoring candidates
   -> automation/agent workflow candidates
   -> risk-reduction candidates
   -> reuse/adaptation candidates based on open-source references
   -> continuation/revival candidates based on previous project results
   -> explicit alternative set, including do-nothing / incremental / redesign / reuse / commercialize options

4. DARS progressive critique
   -> logical conservative devil checks reasoning and evidence
   -> architecture devil checks modularity/coupling/boundaries
   -> security/privacy devil checks data and secret risks
   -> product/business devil checks customer value and feasibility
   -> domain expert devil checks domain fit
   -> source-governance devil checks open-source licensing, provenance, and previous-result applicability

5. Synthesis
   -> compare alternatives by value, feasibility, risk, evidence support, implementation cost, and legal/source constraints
   -> produce better-use recommendations and next controlled increments

6. Human decision boundary
   -> user/Hermes may choose an alternative, request more evidence, or approve a Ralph implementation loop

7. Hisys tool result
   -> persist runtime-boundary artifacts and return compact structured result to Hermes
   -> Hermes reports the advisory recommendation and asks for approval before any implementation or live action
```

## 6. Investigation Data Model

A future `InvestigationDataPackage` should normalize multiple evidence sources before DARS evaluation:

```json
{
  "schema_id": "hisys.investigation.data",
  "schema_version": "0.1.0",
  "investigation_id": "INV-...",
  "objective": "Find better design/use alternatives for the target codebase.",
  "sources": [
    {
      "source_id": "SRC-CURRENT-001",
      "source_type": "current_codebase",
      "governance_status": "approved_local_read_only"
    },
    {
      "source_id": "SRC-OSS-001",
      "source_type": "open_source_reference",
      "license_status": "review_required|compatible|incompatible|unknown"
    },
    {
      "source_id": "SRC-PREV-001",
      "source_type": "previous_project_result",
      "result_type": "memo|release_report|experiment|decision_log|runtime_boundary"
    }
  ],
  "evidence_packages": [],
  "design_candidates": [],
  "alternative_decision_set": {}
}
```

### 6.1 Codebase Evidence Model

A future `CodebaseEvidencePackage` should include:

```json
{
  "schema_id": "hisys.codebase.evidence",
  "schema_version": "0.1.0",
  "repo_ref": {
    "source_id": "SRC-CURRENT-001",
    "source_role": "current_codebase|open_source_reference",
    "path": "...",
    "vcs": "git",
    "branch": "main",
    "commit": "hex",
    "license_ref": "MIT|Apache-2.0|proprietary|unknown"
  },
  "analysis_scope": {
    "mode": "read_only",
    "include_tests": true,
    "include_docs": true,
    "include_dependency_manifests": true,
    "execute_project_code": false
  },
  "metrics": {
    "languages": [],
    "file_counts": {},
    "loc_summary": {}
  },
  "architecture_signals": [],
  "dependency_signals": [],
  "test_signals": [],
  "documentation_signals": [],
  "risk_signals": [],
  "evidence_refs": []
}
```

Evidence references should include file path, line range when applicable, hash, and interpretation boundary:

```json
{
  "evidence_id": "CODE-EVID-001",
  "artifact_type": "source_file|manifest|test|doc|metric_report",
  "path": "src/example/module.py",
  "line_range": [10, 45],
  "sha256": "hex-string",
  "claim_supported": "Module exposes reusable ingestion boundary."
}
```

## 7. Design Candidate and Alternative Decision Model

A future `DesignCandidateRecord` should include:

```json
{
  "candidate_id": "DESIGN-CAND-001",
  "candidate_type": "commercial_use|architecture_refactor|agent_workflow|risk_reduction|productization_path",
  "title": "Expose repository analysis as a governed advisory workflow",
  "claim": "The existing Investigator/DARS boundary can support read-only codebase assessment.",
  "supporting_evidence_refs": ["CODE-EVID-001", "OSS-EVID-001", "PREV-EVID-001"],
  "source_basis": ["current_codebase", "open_source_reference", "previous_project_result"],
  "expected_value": "high",
  "implementation_cost": "medium",
  "risk_level": "medium",
  "uncertainties": ["Needs stronger dependency graph extraction."],
  "next_increment": "Implement file-backed codebase evidence extractor."
}
```

A future `AlternativeDecisionSet` should group candidates into explicit decision alternatives before DARS critique:

```json
{
  "schema_id": "hisys.design.alternatives",
  "schema_version": "0.1.0",
  "decision_id": "ALTDEC-...",
  "objective": "Select the best next design/use path for the analyzed system.",
  "alternatives": [
    {
      "alternative_id": "ALT-001",
      "title": "Continue current architecture with incremental hardening",
      "candidate_refs": ["DESIGN-CAND-001"],
      "evidence_refs": ["CODE-EVID-001", "PREV-EVID-001"],
      "expected_benefit": "medium",
      "implementation_cost": "low",
      "risk_level": "low",
      "source_constraints": []
    },
    {
      "alternative_id": "ALT-002",
      "title": "Adopt open-source-inspired plugin architecture",
      "candidate_refs": ["DESIGN-CAND-002"],
      "evidence_refs": ["CODE-EVID-002", "OSS-EVID-001"],
      "expected_benefit": "high",
      "implementation_cost": "medium",
      "risk_level": "medium",
      "source_constraints": ["license_review_required"]
    }
  ],
  "decision_policy": {
    "selection_mode": "human_review_after_dars",
    "dars_role": "advisory_only",
    "include_do_nothing_baseline": true
  }
}
```

DARS should evaluate the alternative set and return critique/rubric scores. Hisys then records the recommended alternative, unresolved risks, and next Ralph-loop increment, but the final selection remains a human/system-of-record decision.

## 8. Codebase Rubric Axes

The codebase-analysis DARS rubric should extend the progressive decision matrix with software-specific axes:

| Axis | Question |
|---|---|
| `architectural_cohesion` | Are modules organized around clear responsibilities? |
| `boundary_clarity` | Are runtime, user, tool, data, and external boundaries explicit? |
| `testability` | Can candidate changes be tested safely and locally? |
| `reuse_potential` | Which components can become reusable products/services? |
| `commercial_fit` | Does a candidate solve a recognizable customer problem? |
| `integration_risk` | What external systems or permissions are required? |
| `security_privacy_risk` | Could code/data/secrets be exposed? |
| `implementation_incrementality` | Can it be delivered through Ralph/TDD increments? |
| `evidence_support` | Is the recommendation supported by concrete repository evidence? |
| `cross_source_consistency` | Do current codebase, open-source references, and previous results support or contradict one another? |
| `source_governance_fit` | Are open-source license/provenance and previous-result reuse constraints acceptable? |
| `alternative_quality` | Are alternatives explicit, comparable, and not prematurely narrowed to one path? |

## 9. Registry and Configuration Implications

This use case adopts the final registry recommendation:

```text
ConfigRegistry
  manages codebase-analysis configs, allowed analyzers, execution policy, repository-scope rules, connector gates, and retention policy.

PromptRegistry
  manages codebase-analysis prompts, critic roles, rubrics, and synthesis templates.

SecretManager
  manages credentials only, if private repository access is needed.

Runtime evidence store
  stores extracted evidence, candidate records, DARS critiques, and recommendation memos.
```

Example future configs:

| Config ID | Purpose |
|---|---|
| `codebase-analysis-policy` | read-only vs execution permissions, excluded directories, file-size caps |
| `investigation-source-policy` | allowed current-codebase, open-source, and previous-result sources plus connector/source-governance requirements |
| `codebase-analyzer-registry` | enabled analyzers such as metrics, dependency, test, architecture, docs, open-source comparison, and previous-result mining |
| `codebase-rubric-binding` | selected rubric refs and aggregation policy |
| `alternative-decision-policy` | alternative-set construction, do-nothing baseline, ranking dimensions, DARS rounds, and human-review requirements |
| `codebase-output-policy` | memo format, redaction, retention, customer-visible fields |

Example future prompt bundles:

| Prompt bundle | Role |
|---|---|
| `pb-codebase-architecture-devil` | critiques architecture/coupling/boundaries |
| `pb-codebase-security-devil` | critiques secret/privacy/supply-chain risk |
| `pb-codebase-productization-devil` | critiques commercial fit and customer value |
| `pb-codebase-source-governance-devil` | critiques open-source provenance, license constraints, and previous-result applicability |
| `pb-codebase-alternative-synthesizer` | synthesizes possible alternatives and ranked decision recommendations |
| `pb-codebase-synthesizer` | synthesizes ranked better-use candidates |

## 10. Suggested MVP Increment

Start with a local read-only MVP:

1. Analyze Hisys repo itself plus one local previous-result package.
2. Add approved open-source reference support only through a local fixture/snapshot first; no live cloning by default.
3. Implement `InvestigationDataPackage`, `CodebaseEvidencePackage`, and `AlternativeDecisionSet` schemas.
4. Implement read-only extractors for:
   - file inventory;
   - language/LOC summary;
   - dependency manifest summary;
   - test inventory;
   - docs/README intent signals;
   - previous-result memo/report summaries;
   - open-source reference comparison from fixture snapshots.
5. Generate 3-5 `DesignCandidateRecord` entries and 2-4 explicit alternatives.
6. Use loopback/fixture DARS only.
7. Persist runtime-boundary reports:

```text
runtime-boundary/codebase-analysis/<YYYYMMDD>/
  investigation-data-<analysis_id>.json
  codebase-evidence-<analysis_id>.json
  comparative-references-<analysis_id>.json
  previous-results-<analysis_id>.json
  design-candidates-<analysis_id>.json
  alternative-decision-set-<analysis_id>.json
  dars-request-<request_id>.json
  dars-response-<response_id>.json
  design-recommendation-memo-<analysis_id>.md
```

## 11. Acceptance Criteria

A future implementation should verify:

1. Codebase analysis is read-only by default.
2. Excluded directories such as `.git`, `node_modules`, `.venv`, caches, and build outputs are skipped.
3. Investigation data records source roles for current codebase, open-source references, and previous project results.
4. The evidence package records repo path, branch, commit, license/provenance status where applicable, and analysis scope.
5. Candidate recommendations cite concrete evidence refs across all used source types.
6. Alternative decision sets include at least one baseline/do-nothing or incremental option when applicable.
7. DARS critique remains advisory and cannot modify code or select the final alternative by itself.
8. Config snapshot refs and prompt bundle refs are recorded.
9. Secret-like values are redacted from reports.
10. Human approval is required before live external collection, code modification, or a code-modifying Ralph loop starts.

## 12. Relationship to Domain-General Hisys Tool

This codebase use case must remain compatible with `docs/use-cases/hermes-hisys-domain-tool.md`:

- `domain="codebase"` selects the codebase adapter.
- Hermes receives compact tool results; full evidence stays in Hisys runtime-boundary artifacts.
- Domain-specific schemas may refine generic `InvestigationDataPackage`, `AlternativeDecisionSet`, and recommendation memo shapes.
- The same Hermes-facing tool can later support research, business, investment, ISO/process, and other domains by changing domain adapter, rubric binding, and prompt bundle.
- Any domain adapter remains read-only by default and advisory unless a later human-approved workflow explicitly enables mutation.
