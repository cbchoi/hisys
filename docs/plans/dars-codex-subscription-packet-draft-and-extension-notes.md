# DARS Codex Subscription Packet Draft and Extension Notes

Date: 2026-05-22
Baseline: `3bc57c9 docs: capture codex subscription prerequisite`
Related authorization records:

- `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.46.md`
- `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.48.md`
- `docs/plans/dars-remote-subscription-auth-prep-tasks.md`

## Scope

This document records the recommended-default Codex subscription packet draft requested by the operator. It is a local docs/control artifact. It does not call Codex, invoke a Codex SDK, resolve the existing auth reference, unseal a vault entry, configure a provider account, write a runtime-boundary provider result, or upgrade the DARS completion claim.

## Draft packet paths

| Packet | Path | Role |
|---|---|---|
| Remote subscription policy packet | `docs/examples/dars/codex-subscription-policy.recommended.json` | Binds the operator-selected `codex` provider to a vault-style existing-auth account reference, redaction policy ref, egress scope, expiry, revocation ref, and audit requirement. |
| External-backend activation packet | `docs/examples/dars/codex-subscription-activation.recommended.json` | Binds the external-api activation to the policy packet through `remote_policy_packet_ref` and keeps `allowed_actions=advisory_only`. |

The packets are examples/drafts for validation and operator review. They are not runtime-boundary evidence.

## Recommended defaults used

| Field | Value |
|---|---|
| `provider_id` | `codex` |
| `adapter_class` | `codex_subscription` |
| `subscription_account_ref` | `vault://existing-auth/codex-subscription` |
| `redaction_policy_ref` | `policy://hisys/dars/codex-subscription-redaction-v1` |
| `egress_scope` | `advisory-dars-critic-prompt-and-bounded-evidence-summary-only` |
| `expires_at` | `2026-06-05T06:54:03Z` |
| `revocation_ref` | `revoke://hisys/dars/codex-subscription/20260522` |
| `HISYS_INSTANCE` recommendation | `/tmp/hisys-dars-codex-subscription` |
| `backend_id` | `codex_subscription_dars_critic` |
| `backend_kind` | `codex_subscription` |
| `approval_ref` | `APPROVAL-DARS-REMOTE-SUB-20260522-CODEX-EXISTING-AUTH` |

## Validation meaning

A valid policy packet means only that the M-DARS-BE-5 schema constraints pass. The validator intentionally emits the warning `remote_dispatch_not_implemented`; schema validity is not dispatch authority.

A valid activation packet means only that the M-DARS-BE-1 activation shape is internally consistent for `endpoint_scope=external_api` and references the policy packet. It is not provider execution authority.

The M-DARS-BE-6 dispatch harness still requires an explicit `executor=` argument. Without that separately governed executor, provider-boundary crossing remains blocked by `remote_subscription_executor_required`.

## Expansion points before live Codex smoke

1. **Concrete redaction policy implementation.** The current `redaction_policy_ref` is a reference token. A future row should define the exact pre-provider redaction transform, including which evidence fields are allowed, which fields are removed, and how the redacted prompt is audited without storing sensitive content.
2. **Egress audit binding.** The current `egress_scope` is a bounded label. A future row should bind it to an operator-owned network/audit policy that permits only advisory DARS critic prompts and bounded evidence summaries.
3. **External subscription executor.** A future row must provide an operator-owned `RemoteSubscriptionExecutor = Callable[[dict[str, Any]], str]` outside Hisys. It must resolve Codex credentials outside the repository, return only critique text, hold no tool/search/browser/mutation authority, and raise on provider errors.
4. **Instance-root selection.** The recommended `HISYS_INSTANCE=/tmp/hisys-dars-codex-subscription` is safe for local smoke rehearsal, but the operator may replace it with a governed instance root. The chosen root must own the runtime-boundary partition before smoke execution.
5. **Prompt/evidence packet.** The actual dispatch request still needs an operator-reviewed advisory prompt and a bounded evidence summary. Raw secrets, raw credentials, provider account identifiers, browser/search/tool instructions, mutation requests, and publication requests must be excluded.
6. **Single-critic smoke gate.** The first live row should run one Codex subscription critic through the injected executor, then inspect the JSON/Markdown boundary record under `runtime-boundary/dars-remote-subscriptions/<YYYYMMDD>/<REQUEST_ID>/`.
7. **Panel expansion gate.** Multi-critic panel execution should remain a later row after single-critic smoke. It should reuse the existing panel dispatch harness and write the aggregate panel record under `runtime-boundary/dars-remote-subscription-panels/<YYYYMMDD>/<REQUEST_ID>/<PANEL_ID>.json/.md`.
8. **Completion-claim review.** Even after a successful smoke, a separate GREEN/GATE row must review runtime-boundary evidence before changing the DARS completion claim beyond `local_fixture_localhost_controlled_advisory_complete`.

## Still not authorized by this draft

- real Codex subscription call;
- credential lookup or vault unseal by Hisys/Ralph;
- raw credential or Authorization header handling;
- provider account configuration;
- tool/search/browser authority;
- mutation, publication, deployment, release, or repo-changing provider output;
- arbitrary endpoint, raw API-key, custom HTTP, local proxy, Gemini, Grok, or pay-per-call integration;
- DARS completion-claim upgrade.

## Recommended next Ralph row

```text
DARS-CODEX-SUBSCRIPTION-PACKET-VALIDATE-AND-EXECUTOR-PREP
```

This row should validate the two draft packets, add or reference an operator-owned executor runbook/contract, and stop before the actual Codex call unless the operator supplies explicit live-smoke authorization plus executor evidence.
