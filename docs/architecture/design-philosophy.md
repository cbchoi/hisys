# Hisys Design Philosophy

**Status:** adopted-architecture-baseline  
**Version:** 0.1.0  
**Traceability:** HISYS-FR-INV-001..006; HISYS-FR-MEM-001..005; HISYS-FR-AGT-001..005; HISYS-DARS-CONTRACT-001; HISYS-T-019; HISYS-T-020; HISYS-T-021; HISYS-T-024; HISYS-CON-010; HISYS-CON-011; HISYS-CON-012; HISYS-CON-022; HISYS-CON-023

## 1. Purpose

This document records the Hisys design philosophy that should guide future product decisions, implementation increments, and commercial architecture. It consolidates the current direction: Hisys is a governed, domain-general investigation and decision-support tool that Hermes can use across domains.

The philosophy is intentionally broader than any single use case. Codebase analysis, research support, investment assessment, ISO/process improvement, and business/product discovery should all reuse the same core pattern.

## 2. Core Thesis

```text
Hermes orchestrates conversation and tasks.
Hisys governs investigation, evidence, alternatives, and decisions.
DARS critiques alternatives as an advisory evaluator.
Humans or authorized governance select and approve consequential actions.
```

Hisys should not become a loose collection of agent prompts. It should become a controlled evidence and decision-support substrate that lets Hermes operate safely and repeatably in many domains.

## 3. First Principles

### 3.1 Domain-General, Adapter-Specific

Hisys should apply to any domain where evidence must be collected, interpreted, criticized, and converted into possible alternatives.

The core engine should be domain-general:

```text
request
  -> investigation plan
  -> evidence package
  -> candidate generation
  -> alternative decision set
  -> DARS critique
  -> synthesis
  -> recommendation memo
  -> runtime-boundary evidence
```

Domain details belong in adapters:

```text
codebase adapter
research adapter
business adapter
investment adapter
iso/process adapter
general adapter
```

Each adapter may define its own evidence schema, analyzer set, rubrics, prompt bundles, and recommendation template. The overall control boundary should stay consistent.

### 3.2 Evidence Before Interpretation

Investigator output should be evidence-first. Hisys should distinguish:

```text
raw source material
extracted observations
interpreted signals
design or decision candidates
DARS critique
synthesized recommendation
```

The system should preserve traceability from final recommendation back to concrete evidence refs. Interpretation without evidence should be flagged as uncertainty, not presented as fact.

### 3.3 Multi-Source Investigation

Investigator should not be limited to the current artifact. Depending on policy and approval, it may consider:

```text
current codebase or current domain artifact
approved open-source or public references
previous project results
controlled notes and memos
runtime-boundary reports
release/readiness evidence
experiment summaries
domain-specific external sources
```

All sources must carry source role, provenance, sensitivity, license/legal status where relevant, and access policy.

### 3.4 Alternatives, Not Single Answers

Hisys should not simply produce one recommendation. It should construct explicit alternatives, including baseline choices when useful:

```text
do nothing / continue current path
incremental hardening
redesign or refactor
reuse or adapt an external pattern
commercialize or package
request more evidence
stop / avoid due to risk
```

DARS then critiques the alternative set. The outcome should be a reasoned recommendation, not an opaque answer.

### 3.5 Progressive Adversarial Critique

DARS should operate like a progressive adversarial decision-improvement process, not a veto service.

Critics may include:

```text
logical conservative devil
domain expert devil
architecture/design devil
security/privacy/safety devil
business/value devil
source-governance devil
```

Their role is to expose unsupported claims, risks, missing evidence, weak assumptions, and better alternatives. Critique should improve decisions and candidate quality. It must not directly approve, block, execute, or mutate downstream artifacts.

### 3.6 Governance Separation

Hisys should keep governance responsibilities separated:

```text
ConfigRegistry
  -> operational/system configuration, policies, connector declarations, feature flags

PromptRegistry
  -> system prompts, role profiles, templates, rubrics, prompt bundles

SecretManager / Vault
  -> credentials only

Runtime evidence store
  -> evidence packages, memos, handoffs, alternatives, critiques, audit records
```

This separation is essential for commercialization because each class has different approval, audit, retention, rollback, and security needs.

### 3.7 File-First, Database-Ready

The early implementation should remain local, inspectable, and file-backed. However, every important artifact should be shaped so it can later migrate to a tenant-scoped database-backed registry or evidence store.

Near term:

```text
JSON files
Markdown reports
runtime-boundary artifacts
local validators
fixture harnesses
```

Commercial target:

```text
ConfigRegistry database
PromptRegistry database
SecretManager integration
append-only audit/event store
runtime evidence/object store
RBAC, tenant scope, approval, rollback
```

### 3.8 Ontology-Guided Configuration Suitability — Future Extension

As Hisys becomes domain-general, it should eventually include an ontology management tool that helps determine **which configuration is suitable for which domain, objective, evidence source, critic role, rubric, connector, tenant, and approval context**.

This should be treated as a future extension, not an immediate implementation dependency. The ontology layer should describe relationships such as:

```text
domain -> suitable evidence schemas
domain/objective -> suitable investigator adapter
evidence/source type -> required source-governance policy
objective/risk level -> suitable DARS critic panel
critic role -> suitable prompt bundle and rubric refs
tenant/site policy -> allowed connectors and backend classes
approval context -> allowed actions and runtime constraints
```

The ontology management tool should not replace `ConfigRegistry` or `PromptRegistry`. It should help select, explain, and validate suitable registry entries. Config and prompt registries remain the authoritative source of approved snapshots.

### 3.9 Harness Before Live Action

Hisys should prove behavior through fixtures, dry-runs, local loopback adapters, and runtime-boundary evidence before enabling live connectors, live browsing, external LLM calls, vault writes, deployments, or code mutation.

Default posture:

```text
read_only = true
external_calls_allowed = false
mutation_allowed = false
credential_use_allowed = false
action_taken = none
```

Live action requires explicit policy, approval, evidence, and validation.

### 3.10 Hermes Tool Boundary

Hisys should be exposed to Hermes as a governed tool boundary.

Hermes should send compact requests:

```text
domain
objective
allowed sources
constraints
output contract
```

Hisys should return compact structured results:

```text
status
summary
recommended alternative
human-review requirement
runtime-boundary refs
quality-gate status
```

Full evidence stays in Hisys runtime-boundary artifacts. This keeps Hermes useful and responsive while preserving Hisys as the auditable system of record.

### 3.11 Human/System-of-Record Authority

Hisys and DARS support decisions. They do not replace authority for consequential actions.

Human or approved governance must select or approve:

```text
live external data collection
credential use
code modification
pull requests
deployments
alerts or external messages
commercial release decisions
high-impact domain actions
```

## 4. Product Shape

Hisys should evolve as a reusable governed decision-support engine with these product-level capabilities:

| Capability | Purpose |
|---|---|
| Domain investigation request | Normalize Hermes/user goals into controlled work packages |
| Source governance gate | Decide what sources may be inspected and how |
| Investigator | Build evidence packages from approved sources |
| Candidate generator | Convert evidence into candidate options |
| Alternative decision set | Compare possible paths explicitly |
| DARS critic panel | Challenge alternatives with role/rubric-specific critique |
| Synthesizer | Convert evidence and critique into ranked recommendations |
| Runtime-boundary writer | Persist auditable artifacts and compact reports |
| Registry resolver | Resolve config/prompt/rubric snapshots |
| Approval gate | Prevent unapproved live or destructive actions |
| Ontology management tool | Future extension that maps domains, objectives, evidence types, policies, prompts, rubrics, connectors, and approvals to suitable configuration candidates |

## 5. Canonical Pattern

Every domain should try to fit this shape:

```text
HisysInvestigationRequest
  -> SourceGovernanceDecision
  -> InvestigationDataPackage
  -> DomainEvidencePackage[]
  -> CandidateRecord[]
  -> AlternativeDecisionSet
  -> DarsRequestEnvelope
  -> DarsResponseEnvelope
  -> RecommendationMemo
  -> HisysToolResult
```

Domain adapters may specialize the names, but the relationships should remain stable.

## 6. Design Implications for Current Use Cases

### 6.1 Codebase Analysis

Codebase analysis is the first concrete adapter, not the whole product.

It should analyze:

```text
current repository
approved open-source references
previous project results
```

It should produce design candidates and alternative decision sets before any code-modifying Ralph loop begins.

### 6.2 Research

Research use cases should treat papers, publisher pages, datasets, notes, and prior manuscripts as governed sources. Hisys should preserve source links, access/legal status, extracted claims, and uncertainty.

### 6.3 Investment and Business

Investment and business use cases should make uncertainty explicit and avoid unsupported advice. DARS should stress-test assumptions, market evidence, risk exposure, and alternative strategies. Where applicable, reports should include safety limitations such as not-financial-advice language.

### 6.4 ISO / Process Improvement

ISO/process use cases should connect findings to controlled documents, audit trails, NCR/CAPA evidence, and approval authority. DARS critique should improve process alternatives without bypassing formal approval.

## 7. Non-Goals

Hisys should not become:

- a direct autonomous mutation engine;
- a prompt-only wrapper around LLM calls;
- a source-ingestion system without provenance and approval;
- a configuration database that stores secrets;
- a DARS veto/approval service;
- a domain-specific one-off codebase analyzer only;
- an untraceable recommendation generator.

## 8. Acceptance Principles

Future increments should be accepted only when they preserve these principles:

1. Evidence and interpretation remain separable.
2. Source governance is explicit.
3. Recommendations cite evidence refs.
4. Alternatives are explicit before final recommendation.
5. DARS remains advisory and non-mutating.
6. Config, prompts, secrets, and runtime evidence stay separated.
7. Local fixture/dry-run behavior exists before live behavior.
8. Runtime-boundary records capture tool/user/agent/system crossings.
9. Configuration suitability is explainable; future ontology support may recommend suitable registry entries, but approved registries remain authoritative.
10. Commercial migration path remains file-first but database-ready.
11. Hermes receives compact results while Hisys preserves full audit evidence.
