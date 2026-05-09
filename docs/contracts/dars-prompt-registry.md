# DARS Prompt Registry and Commercial Prompt Governance

**Status:** future-design-baseline  
**Version:** 0.1.0  
**Traceability:** HISYS-DARS-CONTRACT-001; HISYS-FR-AGT-001..005; HISYS-T-019; HISYS-T-020; HISYS-T-024; HISYS-CON-010; HISYS-CON-011; HISYS-CON-012

## 1. Purpose

This document defines a future commercial design for managing DARS system prompts, role profiles, rubric references, and prompt assembly rules through a controlled prompt registry. The near-term implementation can continue with JSON files, but the product should be able to migrate to a database-backed registry without changing the Hisys↔DARS protocol contract.

Commercial motivation:

- multiple tenants/sites need different approved prompt sets;
- system prompts and rubrics become product assets that require versioning, approval, rollback, and audit;
- customers need reproducible evidence showing which prompt version produced which critique;
- prompt changes must not silently alter regulated or safety-relevant decisions;
- administrators need controlled prompt lifecycle management separate from runtime user messages.

## 2. Design Position

Use a **prompt registry abstraction** now, even if storage starts as files.

```text
Hisys DARS runtime
  -> PromptRegistry interface
      -> file-backed registry for fixture/local development
      -> database-backed registry for commercial deployment
  -> PromptBundle snapshot
  -> DarsRequestEnvelope.prompt_bundle_ref
```

The DARS request should reference a resolved prompt bundle by ID, version, content hash, and approval status. The backend adapter may receive the fully assembled prompt text, but Hisys must preserve the registry reference and deterministic assembly metadata.

## 3. What the Registry Owns

The registry owns controlled prompt-related artifacts:

| Artifact | Purpose |
|---|---|
| `system_contract` | Non-overridable product/safety/output-schema instructions |
| `role_profile` | Profession/persona/knowledge/sampling defaults for a critic role |
| `rubric_ref` | Approved evaluation matrix references and hashes |
| `prompt_template` | Deterministic assembly template with allowed variables |
| `output_schema_ref` | Expected structured response schema/version |
| `policy_binding` | Allowed actions, side-effect policy, approval requirements |
| `tenant_binding` | Which tenant/site/project can use the bundle |
| `lifecycle_state` | draft/review/approved/deprecated/retired |

The registry does **not** own live user focus text, raw evidence payloads, credentials, or backend-specific secrets.

## 4. Prompt Bundle Shape

Recommended canonical JSON shape:

```json
{
  "schema_id": "hisys.dars.prompt_bundle",
  "schema_version": "0.1.0",
  "prompt_bundle_id": "pb-dars-logical-conservative-devil",
  "prompt_bundle_version": "0.1.0",
  "tenant_scope": "sysailab-default",
  "status": "approved",
  "approval": {
    "approved_by": "human-reviewer-id",
    "approved_at": "2026-05-09T00:00:00Z",
    "approval_ref": "APPROVAL-..."
  },
  "system_contract_ref": {
    "artifact_id": "system-contract-dars-advisory-only",
    "version": "0.1.0",
    "sha256": "hex-string"
  },
  "role_profile_ref": {
    "role_id": "logical_conservative_devil",
    "version": "0.1.0",
    "sha256": "hex-string"
  },
  "rubric_refs": [
    {
      "rubric_id": "dars-progressive-decision",
      "rubric_version": "0.1.0",
      "sha256": "hex-string"
    }
  ],
  "prompt_template_ref": {
    "template_id": "dars-critique-json-envelope-template",
    "version": "0.1.0",
    "sha256": "hex-string"
  },
  "output_schema_ref": {
    "schema_id": "hisys.dars.response",
    "schema_version": "0.1.0"
  },
  "policy": {
    "allowed_actions": "advisory_only",
    "allow_external_side_effects": false,
    "allow_mutation": false,
    "require_structured_output": true
  }
}
```

## 5. Database Model — Future Commercial Deployment

Recommended logical tables:

```text
prompt_bundles
prompt_artifacts
prompt_bundle_artifacts
prompt_versions
prompt_approvals
prompt_tenant_bindings
prompt_audit_events
prompt_evaluation_results
```

### 5.1 `prompt_bundles`

| Column | Purpose |
|---|---|
| `id` | internal DB ID |
| `prompt_bundle_id` | stable external ID |
| `version` | semver or monotonic version |
| `tenant_scope` | tenant/site/project scope |
| `status` | draft/review/approved/deprecated/retired |
| `content_hash` | hash of resolved bundle contents |
| `created_at`, `updated_at` | audit timestamps |

### 5.2 `prompt_artifacts`

Stores immutable artifact versions:

| Column | Purpose |
|---|---|
| `artifact_id` | stable artifact ID |
| `artifact_type` | system_contract, role_profile, rubric, template, schema_ref, policy_binding |
| `version` | artifact version |
| `body_json` | JSON artifact body |
| `body_text` | optional prompt/template text |
| `sha256` | content hash |
| `status` | draft/review/approved/deprecated/retired |

### 5.3 `prompt_audit_events`

Every prompt lifecycle and runtime resolution event should be auditable:

| Event | Meaning |
|---|---|
| `artifact_created` | prompt/rubric/template version created |
| `artifact_approved` | human or controlled policy approved version |
| `bundle_resolved` | runtime selected and snapshotted bundle for request |
| `bundle_deprecated` | bundle no longer recommended |
| `bundle_retired` | bundle blocked from new use |
| `runtime_used_bundle` | DARS request used bundle hash/version |

## 6. Runtime Resolution Flow

```text
DARS config selects prompt_bundle_id + allowed version policy
        ↓
PromptRegistry validates tenant/status/policy/output schema
        ↓
PromptRegistry resolves immutable PromptBundle snapshot
        ↓
Hisys records prompt_bundle_ref and artifact hashes in DarsRequestEnvelope
        ↓
Adapter assembles backend prompt from bundle + handoff context + evidence refs + user_focus
        ↓
DARS response echoes prompt_bundle_ref and rubric refs
        ↓
Hisys persists runtime-boundary evidence for reproducibility
```

The prompt registry may store text in a database, but the runtime boundary must store enough references and hashes to reconstruct exactly what was used.

## 7. Prompt Assembly Boundary

Prompt assembly order remains deterministic:

```text
system_contract
+ role_profile
+ rubric_snapshot
+ handoff_context
+ evidence_refs
+ output_schema_instruction
+ user_focus
```

Rules:

1. `system_contract` is non-overridable.
2. `role_profile` and `rubric_snapshot` come from approved registry artifacts.
3. `handoff_context` and `evidence_refs` come from Hisys runtime records.
4. `output_schema_instruction` comes from the protocol/schema version.
5. `user_focus` is optional last-mile guidance only.
6. User focus cannot change bundle ID, policy, schema, tools, allowed actions, rubric, approval, or backend.

## 8. Security and Commercial Governance

Commercial deployment should include:

- tenant isolation for prompt bundles;
- RBAC for prompt author/reviewer/admin roles;
- immutable approved prompt versions;
- rollback to earlier approved versions;
- audit events for every create/update/approve/deprecate/use action;
- content hashing for prompt artifacts and bundles;
- optional A/B experiment records, but only behind approved experiment policy;
- migration path from file-backed registry to database-backed registry;
- no credentials or API keys in prompt registry artifacts;
- redaction of prompt text in customer-facing logs when needed while retaining hashes and approval refs.

## 9. Near-Term File-Backed Compatibility

Before adding a database, implement the same abstraction with files:

```text
<instance-root>/harness/prompts/dars/
  bundles/pb-dars-logical-conservative-devil-v0.1.0.json
  artifacts/system-contract-dars-advisory-only-v0.1.0.json
  artifacts/role-logical-conservative-devil-v0.1.0.json
  artifacts/template-dars-critique-json-envelope-v0.1.0.json
```

This makes the migration straightforward:

```text
file-backed JSON registry -> SQLite/Postgres registry -> managed commercial registry service
```

The Hisys product code should depend on `PromptRegistry` behavior, not on whether storage is local files or database.

## 10. Acceptance Criteria for Future Implementation

A future implementation increment should verify:

1. Approved prompt bundle resolves by ID/version.
2. Draft or retired bundle is rejected for runtime use.
3. Tenant mismatch is rejected.
4. Bundle hash is recorded in `DarsRequestEnvelope`.
5. Response echoes prompt bundle reference.
6. User focus cannot override bundle policy or rubric.
7. File-backed registry and database-backed registry produce equivalent resolved snapshots for the same artifacts.
8. Runtime-boundary report records prompt bundle ID/version/hash without leaking restricted prompt text unless configured.
