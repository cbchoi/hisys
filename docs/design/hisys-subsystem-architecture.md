---
doc_id: HISYS-SUBSYSTEM-ARCHITECTURE-001
title: Hisys Subsystem Architecture
version: v0.0.127
status: role-separation-recorded
created: 2026-05-28
---

# Hisys Subsystem Architecture

```text
Hisys = Altas + DARS + Judge
```

Hisys is a local evidence-grounded judgment-support system composed of three separable subsystems. The role split is recorded before package-level refactoring so later code movement can preserve authority boundaries and tests can detect accidental scope promotion.

## Subsystem roles

### Altas

```text
Altas = Agentic Layered Trace and Search
Altas finds and projects.
```

Altas is the knowledge acquisition, retrieval, trace, and curated projection subsystem. Altas may use MCP and web search connectors, local evidence-store indexes, me-vault or Obsidian read paths, source maps, and prior claim indexes to return grounded retrieval packets.

Altas responsibilities:

- find relevant stored knowledge, source handles, evidence handles, and prior claims;
- trace claim/source/note lineage across the evidence store and curated vault projections;
- capture MCP/web/search outputs only through governed connector boundaries;
- create curated note projections such as Stone, Claim Index, Gem-candidate, or source-handle notes when an explicit projection workflow authorizes the write;
- preserve the boundary that raw evidence belongs in the evidence store and vault writes are curated projections.

Altas boundaries:

- Altas does not accept or reject claims.
- Altas does not pass gates or authorize actions.
- Altas does not copy raw/heavy runtime evidence into a vault by default.
- Altas connector execution remains governed by existing disabled-by-default, fixture-first, and human-approval boundaries.

### DARS

```text
DARS challenges and improves.
```

DARS is the developmental opposition subsystem. DARS produces developmental opposition, counterarguments, risk analysis, missing-evidence pressure, failure-mode analysis, and improvement recommendations for claims, drafts, designs, and evidence packets.

DARS responsibilities:

- challenge claims, designs, and evidence packets constructively;
- expose weak evidence, overclaims, missing source support, and unsafe action assumptions;
- produce advisory review material for a human reviewer or for Judge;
- remain usable as an independent dars-only review tool.

DARS boundaries:

- DARS does not approve, mutate, or execute actions.
- DARS does not remove human review.
- The current DARS baseline is a bounded advisory productized subsystem, not raw provider API readiness, adapter-native provider readiness, bounded unattended readiness, or live external-action authority.

### Judge

```text
Judge decides and bounds.
```

Judge is the bounded advisory judgment subsystem. Judge issues bounded advisory judgments, gate outcomes, readiness reviews, and decision packets from prepared evidence, Altas retrieval packets, and DARS opposition packets.

Judge responsibilities:

- synthesize evidence and opposition into explicit advisory decisions;
- record pass/fail/block/needs-human-review outcomes under controlled gates;
- preserve decision packets and final-check records when work crosses durable mutation, release, publication, repository synchronization, or external-action boundaries;
- make human-approval requirements explicit.

Judge boundaries:

- Judge does not remove human review.
- Judge does not authorize live/external/destructive actions without explicit scoped approval.
- Judge does not mutate vaults, evidence stores, remotes, registries, deployments, or publications unless a separate approved execution workflow allows that specific action.

## Independent invocation modes

Hisys supports separable subsystem use:

```text
altas-only  = retrieval, tracing, capture planning, and curated projection preparation
dars-only   = developmental opposition and advisory critique
judge-only  = bounded advisory judgment over already prepared packets
full-loop   = Altas -> DARS -> Judge
```

The full-loop composition is:

```text
User question / claim / decision request
  -> Altas retrieval packet and source/evidence handles
  -> DARS developmental opposition packet
  -> Judge bounded advisory decision packet
  -> Human review / approved next action
```

## Storage and projection boundary

Hisys preserves the existing repository/evidence/vault separation:

```text
code repo != evidence repo != personal vault
```

Raw search results, retrieved page text, PDF extraction, MCP tool output, runtime-boundary JSON, and source metadata belong in the configured evidence store. Curated vault writes are projections that cite evidence-store handles and must be routed through the relevant vault workflow. This role-separation record does not grant live connector use, raw provider access, vault mutation, or external action authority.

## Current DARS baseline

The DARS subsystem is considered complete only for the bounded advisory productized baseline recorded by the existing DARS productization and Hermes smoke gates. The current accepted baseline does not claim autonomous completion or live authority:

```text
dars_bounded_advisory_productized_baseline=true
dars_completion_upgrade_claimed=false
bounded_unattended_advisory_operation_ready=false
raw_provider_api_readiness=false
adapter_native_readiness=false
live_external_action_authorized=false
requires_human_review=true
```
