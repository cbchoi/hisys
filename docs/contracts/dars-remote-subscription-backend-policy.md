# DARS remote subscription backend policy (M-DARS-BE-5)

> **Status:** fail-closed preparation only. This contract defines the schema
> and default-blocking validator for future Codex/Claude subscription-backed
> DARS providers. It does **not** authorize remote dispatch. Remote dispatch
> remains blocked until a later separately approved implementation lands.

## Scope

The policy packet covers only subscription-style access to Codex and
Claude. The following are explicitly **out of scope** until a separate
human decision changes the allowlist:

- raw API-key / provider-token integration
- arbitrary OpenAI-compatible endpoints
- arbitrary Anthropic-compatible endpoints
- Gemini, Grok, and any other vendor
- generic HTTP / custom URL providers
- local proxy providers
- pay-per-call provider APIs

## Validator surface

`validate_dars_remote_subscription_policy_packet(data, *, config_ref, now=None)`
returns a deterministic `ConfigValidationReport` whose `schema_id` is
`hisys.dars.remote_subscription_policy`. Even a fully valid packet emits a
deterministic `remote_dispatch_not_implemented` **warning** so callers
cannot interpret schema validity as live authority.

## Required fields

The policy packet must include the following non-empty string fields:

- `policy_id`
- `approval_ref`
- `operator_id`
- `provider_id` (allowlist: `codex` | `claude`)
- `access_mode` (must equal `subscription`)
- `subscription_account_ref` (e.g. `vault://...`)
- `adapter_class` (must equal `codex_subscription` for codex,
  `claude_subscription` for claude)
- `redaction_policy_ref`
- `egress_scope`
- `expires_at` (ISO-8601)
- `revocation_ref`

And the boolean field:

- `audit_required=true`

## Deterministic issue codes

The validator emits the following deterministic codes:

| Code | Meaning |
|---|---|
| `missing_required_field` | Any required string field missing or empty |
| `missing_subscription_account_ref` | `subscription_account_ref` missing or empty |
| `provider_not_allowlisted` | `provider_id` outside `codex` / `claude` |
| `invalid_access_mode` | `access_mode` not equal to `subscription` |
| `adapter_class_mismatch` | `adapter_class` does not match provider's allowed adapter |
| `audit_required_must_be_true` | `audit_required` not equal to `true` |
| `endpoint_url_not_allowed_for_subscription` | Any forbidden endpoint URL field present |
| `raw_secret_value_not_allowed` | Raw secret-like field or raw secret-looking value detected |
| `mutation_authority_not_allowed` | Any mutation/publication/tool/browser/search authority flag set |
| `policy_expired` | `expires_at` <= injected `now` |
| `invalid_expires_at` | `expires_at` not ISO-8601 |

And the deterministic warning:

| Code | Meaning |
|---|---|
| `remote_dispatch_not_implemented` | Emitted for every valid packet to declare that schema validity does not authorize remote dispatch |

## Boundary invariants

- No raw token, API key, password, secret, or credential field is allowed
  in the packet. Subscription access is mediated through
  `subscription_account_ref` only.
- No `endpoint`, `endpoint_url`, `base_url`, `api_url`, or `api_base`
  field is allowed. Subscription access must not be reshaped into an
  arbitrary API path.
- No `mutation_authorized=true`, `publication_authorized=true`,
  `tool_authority_granted=true`, `browser_authority_granted=true`, or
  `search_authority_granted=true` flag is allowed. The policy carries
  advisory-only authority only.
- `expires_at` is checked against an injected `now` so tests and runtime
  callers do not depend on wall-clock time.

## Relationship to other DARS surfaces

- M-DARS-BE-1 `validate_dars_backend_activation_packet(...)` validates
  per-call backend activation. Its `external_api` endpoint scope reserves
  a slot for remote dispatch but does not authorize it; the remote
  subscription policy packet defined here is the second precondition.
- M-DARS-BE-2 `DarsRuntime.run_configured_critique(...)` is the enforcement
  chokepoint for the backend activation packet. Remote dispatch wiring
  through this runtime is deferred until a separate implementation
  approval consumes the M-DARS-BE-5 policy.
- M-DARS-BE-3 `write_dars_backend_boundary_record(...)` rejects any
  `endpoint_scope` other than `localhost_only`. Remote dispatch records
  will require a different writer surface in a later increment.

## Stop conditions

The validator and any future consumer must stop before any of:

- real remote API/subscription call
- credential/vault resolution
- provider account configuration
- adapter execution against a real subscription
- deployment/publication/vault mutation
- expansion of the provider allowlist beyond Codex and Claude
- expansion of the adapter class allowlist beyond
  `codex_subscription` / `claude_subscription`
