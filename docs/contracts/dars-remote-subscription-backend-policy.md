# DARS remote subscription backend policy and dispatch harness (M-DARS-BE-5/6)

> **Status:** policy packet plus first injected-executor dispatch harness. This
> contract defines the schema and validator for Codex/Claude subscription-backed
> DARS providers. M-DARS-BE-6 adds a runtime harness that can call only an
> explicitly supplied subscription executor after activation/policy checks pass.
> Hisys still does not resolve credentials, store raw secrets, or call a real
> provider by default.

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
  are written through the M-DARS-BE-6 surface below.
- M-DARS-BE-6 `run_dars_remote_subscription_dispatch(...)` composes the
  backend activation packet and this policy packet, blocks mismatches before
  executor contact, calls only an explicitly injected subscription executor,
  and writes `runtime-boundary/dars-remote-subscriptions/<YYYYMMDD>/<REQUEST_ID>/<BACKEND_ID>.{json,md}`.

## Dispatch harness boundary (M-DARS-BE-6)

The dispatch harness requires:

- activation packet: `endpoint_scope=external_api`, `allowed_actions=advisory_only`,
  matching `approval_ref`, `backend_id`, `backend_kind`, and
  `remote_policy_packet_ref`;
- policy packet: valid Codex/Claude subscription policy with matching
  `approval_ref`, `access_mode=subscription`, and `audit_required=true`;
- executor: explicit caller-supplied subscription executor. If absent, the
  harness raises `remote_subscription_executor_required`.

Successful harness execution writes a boundary record with
`external_call_made=true`, `model_boundary_crossed=true`,
`local_model_call_made=false`, `mutation_performed=false`,
`publication_performed=false`, `allowed_actions=advisory_only`, and
`transport_kind=injected_subscription_executor`.

## Stop conditions

The validator and any future consumer must stop before any of:

- real remote API/subscription call without an explicit injected executor and
  separately approved operator run scope
- credential/vault resolution
- provider account configuration
- adapter execution against a real subscription
- deployment/publication/vault mutation
- expansion of the provider allowlist beyond Codex and Claude
- expansion of the adapter class allowlist beyond
  `codex_subscription` / `claude_subscription`
