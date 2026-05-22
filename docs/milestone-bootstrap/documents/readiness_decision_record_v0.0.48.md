# Readiness Decision Record v0.0.48 — Codex subscription prerequisite capture

Date: 2026-05-22
Request context: Discord operator message: `provider는 codex로 / 기존 auth정보 사용`
Baseline: `7a17ecf docs: prepare dars remote subscription auth packet`

## Decision

The operator selected the remote subscription provider as `codex` for the active
`DARS-REMOTE-SUBSCRIPTION-AUTH-EXECUTE-OPERATOR-PREREQUISITES` gate.

The operator also instructed Hisys/Ralph to use the existing authorization
information. This record captures that instruction only as an out-of-band
operator-account reference. Hisys does not inspect, resolve, copy, serialize, or
store any raw credential, API key, token, Authorization header, provider account
identifier, or vault secret.

## Captured prerequisite values

| Field | Captured value |
|---|---|
| `provider_id` | `codex` |
| `adapter_class` | `codex_subscription` |
| `approval_ref` | `APPROVAL-DARS-REMOTE-SUB-20260522-CODEX-EXISTING-AUTH` |
| `subscription_account_ref` | `vault://existing-auth/codex-subscription` |
| `operator_id` | `choi-cb` |
| `operator_auth_instruction` | `기존 auth정보 사용` |

## Still required before a provider boundary is crossed

The following remain required by
`docs/plans/dars-remote-subscription-auth-prep-tasks.md` §10 and are **not**
provided by this record:

- operator-controlled `redaction_policy_ref`;
- operator-controlled `egress_scope` label;
- current `expires_at` and `revocation_ref` for the policy packet;
- fresh policy packet JSON path matching §4.1;
- fresh activation packet JSON path matching §4.2 whose
  `remote_policy_packet_ref` points to the policy packet path;
- separately governed subscription executor function matching §4.3;
- explicit confirmation that the executor has no tool/search/browser/mutation
  authority;
- explicit confirmation that every §7 precondition is green;
- `HISYS_INSTANCE` for the runtime-boundary record partition.

## Boundary

This is a docs/control prerequisite-capture record. It performs no Codex call,
no Codex SDK invocation, no credential lookup, no vault resolution, no raw secret
handling, no provider account configuration, no browser/search/tool execution,
no mutation, no publication, and no runtime-boundary evidence write.

The DARS completion claim remains
`local_fixture_localhost_controlled_advisory_complete`.
