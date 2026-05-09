# Hisys Configuration Governance and Registry Strategy

**Status:** adopted-architecture-baseline  
**Version:** 0.1.0  
**Traceability:** HISYS-FR-AGT-001..005; HISYS-FR-ADM-001..004; HISYS-T-019; HISYS-T-020; HISYS-T-021; HISYS-T-024; HISYS-CON-010; HISYS-CON-011; HISYS-CON-012; HISYS-CON-022; HISYS-CON-023

## 1. Purpose

This document defines how Hisys should manage configurations beyond DARS prompts as the product moves toward commercialization. It supports the adopted design philosophy in `docs/architecture/design-philosophy.md`: separate **configuration governance** from **runtime evidence** and from **secret storage**, while preserving Hisys as a governed domain-general investigation and decision-support tool for Hermes.

Near-term implementation can continue to use versioned JSON/YAML files under an instance root. Future commercial deployment should use a database-backed `ConfigRegistry` for tenant-scoped, audited, approved configuration snapshots while preserving the existing common config envelope and validator behavior.

## 2. Configuration Classes

Not every configuration should be managed the same way.

| Class | Examples | Recommended source of truth | Runtime mutability |
|---|---|---|---|
| Product defaults | built-in schema defaults, disabled connector defaults | product repo / packaged defaults | immutable per release |
| Tenant/site policy | allowed connectors, backend availability, approval thresholds | DB-backed `ConfigRegistry` in commercial mode | controlled by admins |
| Runtime instance config | local fixture settings, source registry, DARS config | file-backed registry first; DB later | controlled, validated |
| Harness assets | prompts, rubrics, fixtures, scenarios, guidelines | file-backed artifacts; DB registry for commercial prompts/rubrics | versioned snapshots |
| User preferences | UI defaults, notification preferences | DB user/profile tables | mutable by user |
| Secrets | API keys, OAuth tokens, private credentials | secret manager only | never in config registry |
| Runtime evidence | handoffs, memos, decisions, audit records | runtime-boundary/data store | append-only or controlled mutation |

## 3. Design Position

Use two complementary registry abstractions:

```text
PromptRegistry
  owns system prompts, role profiles, prompt templates, rubric refs, prompt bundles

OntologyManager (future extension)
  recommends suitable ConfigRegistry/PromptRegistry entries by reasoning over domain, objective, evidence type, source policy, critic roles, rubrics, connector classes, tenant scope, and approval context

ConfigRegistry
  owns non-prompt operational configuration, policy, backend declarations, thresholds, and feature flags
```

Both registries should share the common Hisys configuration envelope and validation-report shape where practical:

```json
{
  "schema_id": "hisys.<domain>.config",
  "schema_version": "0.1.0",
  "config_id": "...",
  "config_version": "0.1.0",
  "owner": "tenant-or-site",
  "status": "draft|active|deprecated|disabled",
  "classification": "runtime_config|harness_config|test_config",
  "traceability": {
    "requirements": ["..."],
    "constraints": ["..."]
  },
  "metadata": {},
  "spec": {}
}
```

## 4. What Should Be Database-Managed Later

For commercialization, these should eventually move into a DB-backed `ConfigRegistry`:

| Domain | Examples | Why DB-backed later |
|---|---|---|
| Tenant/site configuration | tenant ID, enabled modules, deployment region | multi-tenant operations |
| Feature flags | enable DARS fixture adapter, enable read-only browser harness | controlled rollout |
| Connector registry | disabled/enabled connectors, allowed actions, allowed domains | safety and approval gates |
| Backend registry | LLM provider kind, model alias, endpoint class, timeout | backend switching without code deploy |
| Policy thresholds | alert severity thresholds, review requirements, max DARS rounds | admin-tunable governance |
| Approval policies | who can approve high-risk actions, approval expiry | audit and compliance |
| Data-retention policies | retention windows, export/redaction settings | customer contracts/compliance |
| Notification routing | Discord/email/webhook route configs | tenant operations |
| Evaluation configs | rubric refs, scoring aggregation policy | progressive decision quality |
| Ontology mappings | domain/objective/evidence-to-config suitability rules | explainable configuration selection |
| Release gates | required checks, traceability gates, scan policies | commercial quality control |

These should **not** be DB-managed as ordinary config:

| Data | Correct storage |
|---|---|
| API keys/tokens/private credentials | secret manager / vault |
| Raw runtime evidence | runtime data store / object store |
| Customer documents | governed document/evidence store |
| Prompt text requiring strict lifecycle | `PromptRegistry`, possibly backed by same DB but separate tables/policies |
| Generated audit reports | append-only audit/event store |

## 5. File-First, Registry-Compatible Path

Recommended migration path:

```text
Phase 1: Local files + common envelope + validators
Phase 2: File-backed ConfigRegistry abstraction
Phase 3: SQLite/Postgres-backed ConfigRegistry for deployments
Phase 4: Managed commercial config service with UI/RBAC/audit
```

The product code should call:

```text
ConfigRegistry.resolve(config_id, version_policy, tenant_scope)
```

instead of opening files directly. The returned snapshot should include:

```json
{
  "config_ref": "dars-default@0.1.0",
  "schema_id": "hisys.dars.config",
  "schema_version": "0.1.0",
  "tenant_scope": "sysailab-default",
  "status": "active",
  "source_backend": "file|database",
  "content_hash": "hex-string",
  "approval_ref": "APPROVAL-...",
  "resolved_at": "2026-05-09T00:00:00Z"
}
```

## 6. Database Model — Future Commercial Deployment

Recommended logical tables:

```text
config_documents
config_versions
config_tenant_bindings
config_approvals
config_audit_events
config_resolution_events
config_schema_registry
config_ontology_mappings
config_experiments
```

### 6.1 `config_documents`

| Column | Purpose |
|---|---|
| `config_id` | stable external ID |
| `domain` | dars, investigator, connector, alert_policy, notification, release_gate |
| `tenant_scope` | tenant/site/project scope |
| `current_version` | active version pointer |
| `status` | draft/review/active/deprecated/disabled |

### 6.2 `config_versions`

| Column | Purpose |
|---|---|
| `config_id` | stable config ID |
| `version` | immutable version |
| `schema_id` | expected schema |
| `schema_version` | expected schema version |
| `body_json` | validated config body |
| `content_hash` | deterministic hash of canonical JSON |
| `created_by`, `created_at` | audit fields |

### 6.4 `config_ontology_mappings` — future extension

A later ontology management tool may maintain suitability mappings that explain which configuration, prompt bundle, rubric, adapter, connector, or approval policy should be considered for a given domain context.

| Column | Purpose |
|---|---|
| `mapping_id` | stable ontology mapping ID |
| `domain` | codebase, research, business, investment, iso_process, general |
| `objective_tags` | normalized task/objective classes |
| `evidence_type` | source/evidence class the mapping applies to |
| `candidate_config_refs` | suitable ConfigRegistry entries |
| `candidate_prompt_refs` | suitable PromptRegistry entries |
| `suitability_rationale` | human-readable reason for recommendation |
| `constraints` | tenant, approval, source-governance, or connector constraints |
| `status` | draft/review/active/deprecated |

Ontology mappings should only recommend or explain suitability. They must not activate configs, bypass approval, store secrets, or override registry validation.

### 6.5 `config_audit_events`

Events should include:

```text
config_created
config_validated
config_submitted_for_review
config_approved
config_activated
config_deprecated
config_disabled
config_resolved_for_runtime
config_rejected_by_policy
```

## 7. Commercial Governance Rules

1. **Every runtime config has schema ID/version.** No ad-hoc JSON blobs.
2. **Every active config is validated before use.** Validation errors use `path`, `severity`, `code`, and `message`.
3. **Every commercial active config has approval metadata.** Draft configs cannot run production actions.
4. **Every resolved config records hash/version/source.** Runtime artifacts can reconstruct what policy was active.
5. **Secrets are references only.** Config may contain `credential_ref`, never raw secret values.
6. **Prompt governance remains separate.** Prompt lifecycle uses `PromptRegistry`; operational config uses `ConfigRegistry`.
7. **Runtime user input is not configuration.** User focus/request text may select approved configs but cannot create active config by itself.
8. **Safety defaults are disabled.** Live connectors and external LLM backends remain disabled until approved.
9. **Ontology advice is not approval.** Future ontology tooling may recommend suitable configs/prompts/rubrics, but active runtime use still requires registry validation, policy checks, and approval gates.

## 8. Runtime Boundary Requirement

Any workflow that depends on resolved configuration should persist a compact config snapshot reference in its runtime-boundary artifact:

```json
{
  "config_snapshot_refs": [
    {
      "config_id": "dars-default",
      "config_version": "0.1.0",
      "schema_id": "hisys.dars.config",
      "source_backend": "file",
      "content_hash": "hex-string",
      "approval_ref": null
    }
  ]
}
```

This gives commercial customers reproducibility without copying every config body into every report.

## 9. Suggested Domain Config IDs

| Config ID | Domain |
|---|---|
| `dars-default` | DARS backend/policy/role selection |
| `dars-progressive-decision-policy` | DARS rounds, synthesis, stop conditions |
| `investigator-agents` | Investigator connector/agent plan |
| `chief-editor-policy` | Alert severity and approval thresholds |
| `live-connector-registry` | Connector permissions and approval policy |
| `notification-routing` | Discord/email/webhook routing |
| `release-gates` | Required checks before release |
| `data-retention-policy` | retention/export/redaction policy |
| `configuration-suitability-ontology` | future ontology mappings for domain/objective/evidence-to-config suitability |

## 10. Acceptance Criteria for Future Implementation

A future implementation increment should verify:

1. File-backed `ConfigRegistry` resolves an approved JSON config snapshot.
2. Unsupported schema IDs/versions are rejected.
3. Draft/disabled production configs are rejected for production runtime use.
4. Raw secret-like fields are rejected; `credential_ref` is allowed.
5. Snapshot refs are persisted in runtime-boundary records.
6. DB-backed and file-backed registries return equivalent canonical snapshots.
7. Tenant mismatch is rejected.
8. Config resolution emits an audit event.
9. Future ontology mapping recommendations explain configuration suitability without bypassing registry validation or approvals.
