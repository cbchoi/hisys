# DARS Codex subscription executor runbook (operator-owned, docs/control)

> **Status:** human-gated. This runbook defines the contract for the
> operator-supplied `RemoteSubscriptionExecutor` that must run outside
> Hisys before any Codex subscription DARS critic call can cross the
> provider boundary. Hisys/Ralph **does not** implement, install, or
> invoke this executor. Hisys/Ralph **does not** resolve credentials,
> read API keys, send `Authorization` headers, or call the Codex SDK.

This runbook is the docs/control artifact authored by Ralph row
`DARS-CODEX-SUBSCRIPTION-PACKET-VALIDATE-AND-EXECUTOR-PREP`. It binds the
recommended-default Codex packet drafts at
`docs/examples/dars/codex-subscription-policy.recommended.json` and
`docs/examples/dars/codex-subscription-activation.recommended.json` to a
named, operator-controlled executor surface so that the
`run_dars_remote_subscription_dispatch(..., executor=...)` and
`run_dars_remote_subscription_panel_dispatch(..., executor=...)`
chokepoints in
`src/hisys/agents/dars_remote_subscription_dispatch.py` have a precise
operator-side counterpart documented before any live smoke row is
opened.

This runbook does not authorize a live Codex call. The DARS completion
claim remains `local_fixture_localhost_controlled_advisory_complete`
until a later, separately approved GREEN/GATE row inspects a real
runtime-boundary record written under the M-DARS-BE-6 partition.

## Controlled anchors

| Short name | Path |
|---|---|
| Remote subscription PREP | `docs/plans/dars-remote-subscription-auth-prep-tasks.md` |
| Recommended-default packet draft notes | `docs/plans/dars-codex-subscription-packet-draft-and-extension-notes.md` |
| Codex policy packet draft | `docs/examples/dars/codex-subscription-policy.recommended.json` |
| Codex activation packet draft | `docs/examples/dars/codex-subscription-activation.recommended.json` |
| Remote subscription policy validator (M-DARS-BE-5) | `src/hisys/agents/dars_remote_subscription_policy.py` |
| Remote subscription dispatch harness (M-DARS-BE-6) | `src/hisys/agents/dars_remote_subscription_dispatch.py` |
| Activation packet validator (M-DARS-BE-1) | `src/hisys/agents/dars_backend_activation.py` |
| Remote subscription contract | `docs/contracts/dars-remote-subscription-backend-policy.md` |
| Localhost smoke runbook (sibling, local path) | `docs/runbooks/dars-live-backend-localhost-smoke.md` |

## 1. Scope and non-scope

In scope (this runbook):

- the operator-side signature, payload contract, output contract, and
  invariants of `RemoteSubscriptionExecutor`;
- the rehearsal commands the operator runs **before** any live Codex
  call to confirm the executor surface exists and behaves correctly
  against fixture-only payloads;
- the dispatch shape Ralph/Hermes will call once an operator delivers a
  governed executor and the live-smoke gate is opened.

Out of scope (this runbook):

- any real Codex subscription call;
- any Codex SDK import inside Hisys;
- any credential resolution, vault unseal, API key, or
  `Authorization` header by Hisys;
- any provider account configuration, account onboarding, or
  subscription-account linking;
- any DARS completion-claim upgrade beyond
  `local_fixture_localhost_controlled_advisory_complete`;
- any allowlist expansion beyond `codex` / `claude` providers and
  `codex_subscription` / `claude_subscription` adapter classes.

## 2. Validation evidence for the draft packets

The recommended-default draft packets at
`docs/examples/dars/codex-subscription-policy.recommended.json` and
`docs/examples/dars/codex-subscription-activation.recommended.json`
have been rehearsed against the M-DARS-BE-5 and M-DARS-BE-1 validators
with an injected `now=2026-05-22T00:00:00Z`. The validators are pure
and do not call any provider.

Reproducible rehearsal command (no provider call, no credential
lookup):

```bash
PYTHONPATH=src:. python3 - <<'PY'
import json
from pathlib import Path
from hisys.agents.dars_remote_subscription_policy import (
    validate_dars_remote_subscription_policy_packet,
)
from hisys.agents.dars_backend_activation import (
    validate_dars_backend_activation_packet,
)

policy_path = Path("docs/examples/dars/codex-subscription-policy.recommended.json")
activation_path = Path("docs/examples/dars/codex-subscription-activation.recommended.json")

policy = json.loads(policy_path.read_text())
activation = json.loads(activation_path.read_text())

NOW = "2026-05-22T00:00:00Z"

pol = validate_dars_remote_subscription_policy_packet(
    policy, config_ref=str(policy_path), now=NOW,
)
act = validate_dars_backend_activation_packet(
    activation, config_ref=str(activation_path), now=NOW,
)

print(f"policy valid={pol.valid}")
for issue in pol.issues:
    print(f"  policy {issue.severity}: {issue.code} @ {issue.path}")
print(f"activation valid={act.valid}")
for issue in act.issues:
    print(f"  activation {issue.severity}: {issue.code} @ {issue.path}")
PY
```

Recorded result with the committed draft packets and the injected
`now` above:

```text
policy valid=True
  policy warning: remote_dispatch_not_implemented @ *
activation valid=True
```

Interpretation:

- The policy packet matches the `hisys.dars.remote_subscription_policy`
  schema (id `hisys.dars.remote_subscription_policy`, version `0.1.0`)
  with no errors. The standing `remote_dispatch_not_implemented`
  warning is **expected** and indicates that schema validity is not
  authority to dispatch.
- The activation packet matches the `hisys.dars.backend.activation`
  schema (id `hisys.dars.backend.activation`, version `0.1.0`) with no
  errors and aligns with the policy packet through
  `remote_policy_packet_ref`, `approval_ref`, and `expires_at`.

A passing rehearsal is **not** authorization to call Codex. It only
confirms that the operator-supplied packet drafts can be consumed by
the dispatch harness without an early fail-closed signal.

## 3. Executor signature and payload contract

The executor is declared in
`src/hisys/agents/dars_remote_subscription_dispatch.py` as:

```python
RemoteSubscriptionExecutor = Callable[[dict[str, Any]], str]
```

When `run_dars_remote_subscription_dispatch(...)` reaches the executor
call site (after every fail-closed packet check passes), it passes the
executor exactly the following payload, freshly built per call from
the request and the policy packet:

```python
executor_payload = {
    "request_id":            request.request_id,
    "source_execution_id":   request.source_execution_id,
    "backend_id":            request.backend_id,
    "backend_kind":          request.backend_kind,
    "provider_id":           policy_data["provider_id"],      # "codex"
    "adapter_class":         policy_data["adapter_class"],    # "codex_subscription"
    "approval_ref":          request.approval_ref,
    "policy_ref":            request.policy_packet_ref,
    "activation_ref":        request.activation_packet_ref,
    "allowed_actions":       "advisory_only",
    "prompt":                request.prompt,
    "external_call_made":    True,
    "mutation_performed":    False,
    "publication_performed": False,
}
```

This payload is the **entire** information surface that Hisys hands to
the executor. There is no credential, no API key, no `Authorization`
header, no provider account identifier, no live network handle, no
file descriptor, no subprocess, and no browser/search/tool object.

The executor returns a non-empty `str` critique. The dispatch harness:

- raises `ValueError("remote_subscription_executor_required")` if
  `executor` is `None` (so merely importing or wiring the module
  cannot perform a live provider call);
- raises `ValueError("remote_subscription_executor_empty_output")` if
  the return is not a string or is empty/whitespace after `.strip()`;
- writes the runtime-boundary record only after a non-empty critique
  is returned;
- never retries on provider error; the executor must raise and the
  caller must surface the error to the operator.

## 4. Operator-owned executor invariants

The executor function lives **outside** Hisys (e.g. in
`operator_local.dars_subscription` or another operator-controlled
package). It must satisfy every invariant below before it is supplied
to a Ralph live-smoke row.

1. **No tool / search / browser / mutation authority.** The executor
   may not spawn subprocesses, open browsers, run web search, mutate
   the filesystem outside the operator's external audit area, perform
   git operations, change CI/CD configuration, post to Slack/email,
   create pull requests, or upload artifacts.
2. **No credential surface inside Hisys.** Hisys passes no
   credentials; the executor resolves Codex authentication entirely
   outside Hisys (vault, OS keychain, OS-level session, etc.) using
   the operator's existing auth path bound by
   `subscription_account_ref=vault://existing-auth/codex-subscription`.
   The executor must not return raw tokens, API keys, refresh
   tokens, or `Authorization` headers to Hisys.
3. **No raw secret in the return value.** The returned critique
   string must not include API keys, tokens, refresh tokens,
   `Authorization` header values, provider account identifiers,
   operator PII, operator IP/MAC/host metadata, or any value matching
   the M-DARS-BE-5 raw-secret prefixes (`sk-`, `sk_`, `ghp_`,
   `xoxb-`, `xoxp-`, `hf_`). The operator owns this contract; Hisys
   only enforces the M-DARS-BE-5 / M-DARS-BE-1 packet checks, not the
   return-content scan.
4. **No arbitrary endpoint.** The executor must not be reshaped into
   an OpenAI-compatible / Anthropic-compatible / Gemini / Grok /
   pay-per-call / raw-HTTP / local-proxy adapter. The recommended
   Codex subscription path is the only allowed surface for
   `adapter_class="codex_subscription"` under the current policy
   allowlist.
5. **Bounded prompt + evidence.** The executor must accept the
   `executor_payload["prompt"]` value as-is and must not introduce
   additional model-tunable parameters that change scope (system
   prompts that grant tools/mutation authority, function-calling
   schemas that grant filesystem/network/mutation authority, etc.).
6. **Apply the operator redaction policy before the provider call.**
   The executor must apply the redaction policy referenced by
   `policy://hisys/dars/codex-subscription-redaction-v1`
   (operator-controlled implementation) to the payload before any
   provider boundary crossing. The redaction policy implementation is
   an operator deliverable; this runbook does not author it.
7. **Match the operator egress audit policy.** The executor must
   operate inside the operator-controlled audit/network scope labeled
   `advisory-dars-critic-prompt-and-bounded-evidence-summary-only`.
   If the operator's audit/network policy does not permit Codex
   subscription egress for that label, the executor must raise and
   stop.
8. **Raise on provider error.** The executor must raise on any
   provider error (HTTP 4xx/5xx, SDK exception, timeout, refusal).
   The dispatch harness does not retry; the operator must inspect
   the failure and supply a fresh packet if needed.
9. **Return non-empty critique.** The executor must return a
   non-empty critique string. The harness rejects empty/whitespace
   output with `remote_subscription_executor_empty_output`.
10. **No external state mutation.** The executor must not write to
    operator-owned mutable systems (issue trackers, repositories,
    runbooks, dashboards, monitoring alerts, etc.) as part of its
    contract. Its only output is the returned critique string.

## 5. Executor stub for operator reference (no Codex SDK import)

The stub below is provided **only as an interface shape reference**.
It does not import a Codex SDK, does not call a provider, and does not
resolve any credential. The operator is responsible for adding the
real provider integration outside Hisys before any live smoke row.

```python
# operator_local/dars_subscription.py  (operator-owned, outside Hisys)
#
# Reference shape only. This stub raises; replace the body with the
# operator's external Codex subscription call. The operator is
# responsible for credential resolution, redaction enforcement, egress
# audit, error handling, and tool/search/browser/mutation isolation.

from typing import Any


def subscription_executor(payload: dict[str, Any]) -> str:
    """Operator-owned Codex subscription executor.

    Hisys passes only the payload fields documented in
    docs/runbooks/dars-codex-subscription-executor-runbook.md §3.
    """

    if payload.get("allowed_actions") != "advisory_only":
        raise RuntimeError("dars_codex_subscription_executor_blocked: not advisory-only")
    if payload.get("mutation_performed", False):
        raise RuntimeError("dars_codex_subscription_executor_blocked: mutation flag set")
    if payload.get("publication_performed", False):
        raise RuntimeError("dars_codex_subscription_executor_blocked: publication flag set")
    if payload.get("provider_id") != "codex":
        raise RuntimeError("dars_codex_subscription_executor_blocked: provider_id mismatch")
    if payload.get("adapter_class") != "codex_subscription":
        raise RuntimeError("dars_codex_subscription_executor_blocked: adapter_class mismatch")
    prompt = payload.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise RuntimeError("dars_codex_subscription_executor_blocked: empty prompt")

    # ---- operator-owned redaction and audit step (this runbook §4.6/§4.7) ----
    # apply policy://hisys/dars/codex-subscription-redaction-v1
    # confirm egress scope advisory-dars-critic-prompt-and-bounded-evidence-summary-only
    # ---- end operator-owned redaction and audit step --------------------------

    # ---- operator-owned Codex subscription call goes here ---------------------
    # Hisys does not import or invoke a Codex SDK. The operator's external
    # subscription call must:
    #   - resolve credentials outside Hisys via the existing-auth path
    #     bound by subscription_account_ref=vault://existing-auth/codex-subscription
    #   - send only the redacted prompt
    #   - return only the critique text
    #   - hold no tool/search/browser/mutation authority
    #   - raise on any provider error
    raise NotImplementedError(
        "operator-owned Codex subscription executor not yet wired; "
        "see docs/runbooks/dars-codex-subscription-executor-runbook.md §4-§5"
    )
```

The operator may replace the body with their actual Codex
subscription call. The reference contract Hisys enforces remains the
M-DARS-BE-5 / M-DARS-BE-1 packet checks plus the M-DARS-BE-6
`remote_subscription_executor_required` /
`remote_subscription_executor_empty_output` chokepoints.

## 6. Fixture-only rehearsal commands (no provider call)

The rehearsal commands below confirm that the dispatch chokepoint
behaves correctly against an **injected fake executor** — they do not
talk to Codex.

1. Confirm the harness module imports and the symbols exist:

   ```bash
   PYTHONPATH=src:. python3 -c "from hisys.agents.dars_remote_subscription_dispatch import \
       RemoteSubscriptionDispatchRequest, run_dars_remote_subscription_dispatch, \
       run_dars_remote_subscription_panel_dispatch; print('ok')"
   ```

2. Run the existing focused subscription cohort (fixture-only, no
   provider call):

   ```bash
   PYTHONPATH=src:. pytest \
     tests/unit/test_dars_remote_subscription_policy.py \
     tests/unit/test_dars_remote_subscription_dispatch.py \
     tests/unit/test_dars_backend_activation.py -q
   ```

   This cohort already pins the fail-closed signals
   (`remote_subscription_executor_required`,
   `remote_subscription_executor_empty_output`,
   `activation_*_mismatch`, `remote_policy_*`, `provider_not_allowlisted`,
   `adapter_class_mismatch`, `audit_required_must_be_true`,
   `raw_secret_value_not_allowed`, `endpoint_url_not_allowed_for_subscription`,
   `mutation_authority_not_allowed`, `policy_expired`, `activation_expired`,
   `external_backend_requires_remote_policy_packet`,
   `multi_critic_panel_requires_at_least_two_requests`,
   `panel_date_partition_mismatch`, `panel_request_id_mismatch`,
   `duplicate_panel_source_execution_id`).

3. (Operator-only) Rehearse the executor stub in §5 against a fake
   payload outside Hisys:

   ```bash
   # Operator runs this against the operator-owned package, not Hisys.
   python3 -c "from operator_local.dars_subscription import subscription_executor; \
       subscription_executor({'allowed_actions': 'advisory_only', \
                              'mutation_performed': False, \
                              'publication_performed': False, \
                              'provider_id': 'codex', \
                              'adapter_class': 'codex_subscription', \
                              'prompt': 'fixture rehearsal'})"
   ```

   The stub in §5 raises `NotImplementedError` until the operator
   wires the real Codex subscription call. A real run is **not**
   authorized by this runbook.

## 7. Stop-condition matrix (applies to the executor side)

The operator stops, notifies Ralph/Hermes, and runs no further command
on any of these signals. Each signal maps to the M-DARS-BE-5 contract
and the M-DARS-BE-6 dispatch chokepoint.

| Signal | Effect | Existing surface |
|---|---|---|
| `RemoteSubscriptionExecutor` not yet supplied | Stop before any executor call | dispatch raises `remote_subscription_executor_required` |
| Operator vault not configured for `vault://existing-auth/codex-subscription` | Stop before any executor call | operator runbook §4.2 |
| Redaction policy `policy://hisys/dars/codex-subscription-redaction-v1` not yet implemented | Stop before any executor call | operator runbook §4.6 |
| Egress scope `advisory-dars-critic-prompt-and-bounded-evidence-summary-only` not bound to operator audit policy | Stop before any executor call | operator runbook §4.7 |
| Executor demands raw credentials / API key / Authorization header from Hisys | Stop and ask | contract §boundary invariants |
| Executor demands tool / search / browser permission | Stop and ask | contract §boundary invariants |
| Executor demands mutation / publication / deployment authority | Stop and ask | contract §boundary invariants |
| Executor returns empty/whitespace critique | Stop before boundary record write | dispatch raises `remote_subscription_executor_empty_output` |
| Executor returns a value containing raw secret prefixes (`sk-`, `sk_`, `ghp_`, `xoxb-`, `xoxp-`, `hf_`) | Stop and ask | operator runbook §4.3 |
| Provider error (HTTP 4xx/5xx, SDK exception, timeout, refusal) | Stop and ask | operator runbook §4.8 |
| Operator request to add raw-API-key / arbitrary-endpoint / Gemini / Grok / local-proxy / pay-per-call surface | Stop and ask | PREP §2 out-of-scope list |
| Operator request to upgrade DARS completion claim before a GREEN/GATE row | Stop and ask | Ralph §16 |
| Secret scan failure (`python3 scripts/scan_secrets.py` → `hit_count > 0`) | Stop before any further critique | Ralph §2.2 |
| Working tree dirty in a non-execution surface | Stop before commit/push | Ralph §10.3 |
| Branch / upstream is not `dars` / `origin/dars` | Stop before push | Ralph §10.3 |

## 8. Files this runbook touches

This runbook is docs/control only and touches only documentation,
governance, and traceability surfaces:

- `docs/runbooks/dars-codex-subscription-executor-runbook.md` (this
  file; new).
- `docs/milestone-bootstrap/profile.yaml` — version bump and
  `next_artifact_ref` advance.
- `tests/unit/test_governance_docs_current_state.py` — assertion
  update to match the new profile state.
- `docs/traceability/README.md` — prepend a
  `DARS-CODEX-SUBSCRIPTION-PACKET-VALIDATE-AND-EXECUTOR-PREP` row.
- `ralph.md` — Section 16 queue status update and Reflection Log
  entry.

No file under `src/`, `tests/unit/test_dars_*.py`, fixture trees,
`docs/contracts/`, `docs/examples/dars/`, or runtime-boundary
partitions is modified by this runbook.

## 9. Next safe Ralph row after this PREP commits

```text
DARS-REMOTE-SUBSCRIPTION-AUTH-EXECUTE-OPERATOR-PREREQUISITES
```

This row remains the non-delegable stop-and-ask gate already declared
by `docs/plans/dars-remote-subscription-auth-prep-tasks.md` §10. It
can advance only after the operator supplies, out of band:

- a wired `RemoteSubscriptionExecutor` matching §3 and §4 of this
  runbook;
- a concrete redaction policy implementation matching
  `policy://hisys/dars/codex-subscription-redaction-v1`;
- an audit/network binding for
  `advisory-dars-critic-prompt-and-bounded-evidence-summary-only`;
- a current `expires_at` window and the revocation reference;
- a fresh policy packet JSON path (matching §4.1 of the PREP);
- a fresh activation packet JSON path (matching §4.2 of the PREP)
  whose `remote_policy_packet_ref` points to the policy packet path;
- a governed `HISYS_INSTANCE` for the runtime-boundary partition;
- explicit confirmation of every §7 stop condition above.

Until those land, the Ralph loop must remain at this gate and ask.
