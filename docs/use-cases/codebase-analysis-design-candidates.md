# Codebase Analysis and Design Candidate Discovery Use Case

**Status:** adopted-use-case-baseline  
**Version:** 0.1.0  
**Traceability:** HISYS-FR-INV-001..006; HISYS-FR-MEM-001..005; HISYS-FR-AGT-001..005; HISYS-DARS-CONTRACT-001; HISYS-T-019; HISYS-T-020; HISYS-T-024; HISYS-CON-010; HISYS-CON-011; HISYS-CON-012; HISYS-CON-022; HISYS-CON-023

## 1. Purpose

This use case applies Hisys to software repositories so it can analyze a codebase, extract evidence, identify design candidates, critique those candidates with DARS, and recommend better uses or better architecture paths.

The target output is not an automatic code change. The target output is a controlled advisory package:

```text
CodebaseEvidencePackage
  -> DesignCandidateRecord[]
  -> DarsRequestEnvelope
  -> DarsResponseEnvelope / rubric scores
  -> DesignRecommendationMemo
```

## 2. Business Motivation

Commercial customers often need to answer questions such as:

- What is this codebase good for?
- Which product/service use cases fit the existing architecture?
- Which modules are reusable as commercial assets?
- Where are design bottlenecks, hidden coupling, or missing abstractions?
- Which refactoring candidates produce the highest value with acceptable risk?
- Which agent/LLM workflows can safely assist this repository?
- Which productization paths are most feasible?

Hisys can become an advisory system that converts repository evidence into design candidates and progressive decision support.

## 3. Scope

Initial scope is **read-only codebase analysis**.

Allowed:

- read repository files;
- compute structure/LOC/language metrics;
- inspect dependency manifests;
- identify modules, packages, CLIs, tests, docs, and runtime boundaries;
- produce evidence packages and memos;
- request DARS critique of design candidates;
- produce advisory recommendations.

Not allowed by default:

- modifying code;
- opening PRs;
- running live deployments;
- sending data to external LLMs unless approved;
- exfiltrating proprietary code;
- storing secrets in config or prompts;
- executing untrusted project scripts without approval.

## 4. Actors

| Actor | Role |
|---|---|
| User / product owner | asks what the codebase can become or how it should improve |
| Investigator | reads repository evidence and builds `CodebaseEvidencePackage` |
| Candidate Generator | proposes possible design/use candidates |
| DARS critic panel | critiques candidates using logical, security, architecture, domain, and business rubrics |
| Synthesizer | merges evidence and critique into ranked recommendations |
| Human reviewer | approves any next implementation or external action |

## 5. Progressive Decision Flow

```text
1. Repository intake
   -> identify repo path, branch, scope, allowed analysis depth

2. Evidence extraction
   -> language/LOC metrics
   -> package/module graph
   -> dependency and CLI/API inventory
   -> test and quality-gate inventory
   -> README/docs intent signals
   -> runtime-boundary / integration signals

3. Candidate generation
   -> commercial use candidates
   -> architecture refactoring candidates
   -> automation/agent workflow candidates
   -> risk-reduction candidates

4. DARS progressive critique
   -> logical conservative devil checks reasoning and evidence
   -> architecture devil checks modularity/coupling/boundaries
   -> security/privacy devil checks data and secret risks
   -> product/business devil checks customer value and feasibility
   -> domain expert devil checks domain fit

5. Synthesis
   -> rank candidates by value, feasibility, risk, evidence support, and implementation cost
   -> produce better-use recommendations and next controlled increments

6. Human decision
   -> accept recommendation, request more evidence, or start a Ralph implementation loop
```

## 6. Evidence Model

A future `CodebaseEvidencePackage` should include:

```json
{
  "schema_id": "hisys.codebase.evidence",
  "schema_version": "0.1.0",
  "repo_ref": {
    "path": "...",
    "vcs": "git",
    "branch": "main",
    "commit": "hex"
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

## 7. Design Candidate Model

A future `DesignCandidateRecord` should include:

```json
{
  "candidate_id": "DESIGN-CAND-001",
  "candidate_type": "commercial_use|architecture_refactor|agent_workflow|risk_reduction|productization_path",
  "title": "Expose repository analysis as a governed advisory workflow",
  "claim": "The existing Investigator/DARS boundary can support read-only codebase assessment.",
  "supporting_evidence_refs": ["CODE-EVID-001", "CODE-EVID-002"],
  "expected_value": "high",
  "implementation_cost": "medium",
  "risk_level": "medium",
  "uncertainties": ["Needs stronger dependency graph extraction."],
  "next_increment": "Implement file-backed codebase evidence extractor."
}
```

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
| `codebase-analyzer-registry` | enabled analyzers such as metrics, dependency, test, architecture, docs |
| `codebase-rubric-binding` | selected rubric refs and aggregation policy |
| `codebase-output-policy` | memo format, redaction, retention, customer-visible fields |

Example future prompt bundles:

| Prompt bundle | Role |
|---|---|
| `pb-codebase-architecture-devil` | critiques architecture/coupling/boundaries |
| `pb-codebase-security-devil` | critiques secret/privacy/supply-chain risk |
| `pb-codebase-productization-devil` | critiques commercial fit and customer value |
| `pb-codebase-synthesizer` | synthesizes ranked better-use candidates |

## 10. Suggested MVP Increment

Start with a local read-only MVP:

1. Add a codebase-analysis fixture repository or analyze the Hisys repo itself.
2. Implement `CodebaseEvidencePackage` schema.
3. Implement read-only extractors for:
   - file inventory;
   - language/LOC summary;
   - dependency manifest summary;
   - test inventory;
   - docs/README intent signals.
4. Generate 3-5 `DesignCandidateRecord` entries.
5. Use loopback/fixture DARS critique only.
6. Persist runtime-boundary reports:

```text
runtime-boundary/codebase-analysis/<YYYYMMDD>/
  codebase-evidence-<analysis_id>.json
  design-candidates-<analysis_id>.json
  dars-request-<request_id>.json
  dars-response-<response_id>.json
  design-recommendation-memo-<analysis_id>.md
```

## 11. Acceptance Criteria

A future implementation should verify:

1. Codebase analysis is read-only by default.
2. Excluded directories such as `.git`, `node_modules`, `.venv`, caches, and build outputs are skipped.
3. The evidence package records repo path, branch, commit, and analysis scope.
4. Candidate recommendations cite concrete evidence refs.
5. DARS critique remains advisory and cannot modify code.
6. Config snapshot refs and prompt bundle refs are recorded.
7. Secret-like values are redacted from reports.
8. Human approval is required before any code-modifying Ralph loop starts.
