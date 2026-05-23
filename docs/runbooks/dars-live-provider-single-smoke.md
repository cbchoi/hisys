# DARS single-critic live-provider smoke runbook (docs/control)

> **Status:** human-gated PREP. This runbook is the controlled PREP artifact
> for `DARS-LIVE-RELEASE-R3-SINGLE-SMOKE-PREP`. It records the conditions
> under which a single live-provider critic call **may** be attempted and
> the evidence the resulting run must produce. The runbook does not by itself authorize the live call. The actual single live call is a separately approved, **HUMAN-GATED** action governed by R3 ACTION and requires a fresh, human-approved decision packet.
>
> The R3 PREP work that produced this runbook performs no live provider
> call, no model call, no credential lookup, no network request, no
> mutation, no publication, no deployment, and no remote push beyond the
> normal `git push origin dars` checkpoint authorized by ralph.md §2.

This runbook supersedes nothing. It complements
`docs/runbooks/dars-codex-subscription-executor-runbook.md` (governed
Codex CLI subprocess prompt-mode transport) and
`docs/runbooks/dars-live-panel-localhost-smoke.md` (localhost rehearsal).
The R3 single live-provider smoke is the first time DARS panel
productization crosses one **external** provider boundary.

The DARS completion claim remains
`local_fixture_localhost_controlled_advisory_complete` until the R3
ACTION evidence is human-reviewed and accepted.

## 1. Controlled anchors

| Short name | Path |
|---|---|
| Release plan | `docs/plans/dars-panel-live-provider-unattended-release-final-plan.md` |
| Requirements | `docs/requirements/dars-critic-panel-runtime-requirements.md` |
| Design | `docs/design/dars-critic-panel-runtime-sdd.md` |
| Test description | `docs/test/dars-critic-panel-runtime-std.md` |
| Traceability | `docs/traceability/dars-critic-panel-runtime-traceability.md` |
| R1 policy validator | `src/hisys/agents/dars_live_provider_policy.py` |
| R1 transport contract | `src/hisys/agents/dars_live_provider_transport.py` |
| R2 fail-closed adapter | `src/hisys/agents/dars_live_provider_adapter.py` |
| Existing backend activation | `src/hisys/agents/dars_backend_activation.py` |
| Example policy packet | `docs/examples/dars/live-provider-single-smoke.policy.example.json` |
| Example activation packet | `docs/examples/dars/live-provider-single-smoke.activation.example.json` |
| Codex CLI subprocess runbook | `docs/runbooks/dars-codex-subscription-executor-runbook.md` |
| Active controller | `ralph.md` |

## 2. Preconditions

A single live-provider smoke **may** be attempted only after **all** of the
following are confirmed by the operator and recorded in the decision
packet:

1. A fresh, human-approved decision packet exists. The packet names the
   `approval_ref`, the request class (single advisory critic), the
   approved provider/model refs, the bounded prompt/output sizes, the
   redaction policy ref, the cost/rate budget refs, the post-run human
   review reviewer, and the rollback procedure.
2. A live-provider policy packet that validates under
   `validate_live_provider_policy_packet` with zero error issues and the
   deterministic warning
   `live_provider_dispatch_not_authorized_by_policy_alone`. The packet
   carries only a credential reference such as
   `env://HISYS_DARS_PROVIDER_TOKEN`,
   `secret-manager-ref://...`, `vault://...`,
   `subscription-account-ref://...`, or `keychain-ref://...`. It does
   **not** carry a raw token, API key, password, or Authorization header.
3. A backend activation packet that validates under
   `validate_dars_backend_activation_packet` with zero error issues, has
   `endpoint_scope=external_api`, `allowed_actions=advisory_only`,
   `human_approved=true`, and the `remote_policy_packet_ref` matches the
   policy packet path.
4. The activation `approval_ref`, the policy `approval_ref`, and the
   request `approval_ref` all match. The activation `backend_id` matches
   the request `backend_id`.
5. The credential reference resolves outside Hisys (operator-managed
   environment, secret manager, vault, or subscription account). Hisys
   does not read, log, or validate the credential value.
6. Bounded prompt/output sizes are confirmed:
   - `max_prompt_bytes` is positive and finite (example: 4096);
   - `max_output_bytes` is positive and finite (example: 4096);
   - `rate_limit_per_minute` is positive and finite (example: 6).
7. A `cost_budget_ref` is configured and finite. The operator confirms
   the bounded cost envelope outside Hisys.
8. The redaction policy ref
   (`policy://hisys/dars/live-provider-redaction-v1` or equivalent) is in
   force. The bounded prompt packet is constructed under that policy.
9. The R2 env gate is set in the operator shell only for the duration of
   the smoke:

   ```bash
   export HISYS_DARS_LIVE_PROVIDER_LIVE_TRANSPORT_ENABLED=true
   ```

   The env gate **must** be unset immediately after the single smoke
   completes or fails.
10. A controlled Hisys instance root is selected for evidence storage
    (the operator-supplied `$HISYS_INSTANCE`). The instance root is not
    a mutable production checkout unless the operator confirms read-only
    behavior outside this runbook.
11. Operator certainty: the operator is confident the procedure is
    correct and is willing to be the post-run reviewer.

## 3. Single-call procedure

A reviewed acceptable smoke runs exactly **one** advisory critic call
under exactly **one** approved decision packet and produces evidence in
a single boundary record. Multi-critic and unattended runs are explicitly
out of scope for R3 and require separately approved R4 / R5 decision
packets.

The reference command shape (R3 ACTION) is:

```text
# Construct request from approved decision packet
request_id=<DARS-LP-REQ-...>
source_execution_id=<src-exec-...>
backend_id=<dars-live-claude-single-smoke-001>
policy_packet_ref=docs/examples/dars/live-provider-single-smoke.policy.example.json
activation_packet_ref=docs/examples/dars/live-provider-single-smoke.activation.example.json
approval_ref=APPROVAL-DARS-LP-SINGLE-SMOKE-20260523-001
prompt_packet_ref=redacted://dars/live-provider/<request_id>
yyyymmdd=<YYYYMMDD>
mode=live

# R3 ACTION invokes run_dars_live_provider_adapter through a separately
# approved real-provider transport — NOT the fake/injected transport.
# The real-provider transport is OUT OF SCOPE for R3 PREP and requires a
# separately approved implementation row before any code can be merged.
```

Until a real-provider transport is implemented, the R2 adapter routes
both `dry_run` and `live` modes through `FakeLiveProviderTransport`.
PREP cannot promote that path into a real call.

## 4. Boundary record requirements

A successful R3 ACTION single smoke must persist a runtime-boundary JSON
+ Markdown pair under

```text
$HISYS_INSTANCE/runtime-boundary/dars-live-provider-adapter/<YYYYMMDD>/<request_id>/<backend_id>-<source_execution_id>.{json,md}
```

with at minimum:

```text
schema_id=hisys.dars.live_provider_adapter
mode=live
status=completed
provider_id=<approved provider>
model_id=<approved model>
transport_kind=<approved real-provider transport kind>
external_call_made=true
model_boundary_crossed=true
mutation_performed=false
publication_performed=false
allowed_actions=advisory_only
advisory_only=true
requires_human_review=true
approval_ref=<APPROVAL-...>
policy_ref=<path to approved policy packet>
activation_ref=<path to approved activation packet>
prompt_packet_ref=<redacted://...>
input_tokens=<recorded>
output_tokens=<recorded>
latency_ms=<recorded>
```

The record must not contain raw prompt text with sensitive evidence, raw
credentials, tokens, Authorization headers, provider account
identifiers, or unredacted secrets. The bounded critique preview field
is acceptable when it falls within the approved redaction policy.

## 5. Post-run review

A R3 ACTION smoke is only considered successful after a post-run human
review:

1. The reviewer reads the boundary record JSON and Markdown.
2. The reviewer confirms that the prompt and output redaction matches the
   approved policy.
3. The reviewer confirms that no mutation, publication, deployment,
   approval, or downstream action authority was claimed in the output.
4. The reviewer confirms the bounded cost/latency envelope was honored.
5. The reviewer confirms the env gate is now unset.
6. The reviewer creates a reviewed report under
   `docs/reports/dars-live-provider-single-smoke-<YYYYMMDD>.md` and
   updates traceability to record the human-accepted claim transition
   from `local_fixture_localhost_controlled_advisory_complete` to
   `live_provider_advisory_smoked`.

## 6. Stop conditions

Stop and ask before proceeding (or stop and revert during execution) if
any of the following is observed. Each is a hard stop; the operator
must record the stop condition in the decision packet and the smoke is
abandoned for that attempt.

- missing decision packet, missing approval ref, or any approval-ref
  mismatch across the request, policy, and activation packets;
- raw secret, token, password, API key, or Authorization header in the
  policy packet, activation packet, decision packet, prompt packet, or
  reviewed output (`scripts/scan_secrets.py` flags any of these);
- credential lookup by Hisys (Hisys must never read, log, validate, or
  serialize the credential value);
- credential reference scheme outside the controlled allowlist
  (`env://`, `secret-manager-ref://`, `vault://`,
  `subscription-account-ref://`, `keychain-ref://`);
- mutation request, publication request, deployment request, tool
  authority request, browser authority request, or search authority
  request from the model output;
- `mutation_performed=true`, `publication_performed=true`, or
  `requires_human_review=false` in the output or boundary record;
- budget violation (cost over `cost_budget_ref`) or rate-limit violation
  (exceeds `rate_limit_per_minute`);
- secret scan hit on any new file produced by the smoke;
- output redaction failure (raw secret-shaped values in the output,
  unauthorized authority claim, oversize output, empty output);
- working tree changes after a supposedly read-only smoke;
- runtime-boundary record cannot be written under `$HISYS_INSTANCE`;
- env gate `HISYS_DARS_LIVE_PROVIDER_LIVE_TRANSPORT_ENABLED` not set or
  set to anything other than `true` at the moment of the smoke;
- operator uncertainty about any precondition, command, or output;
- post-run human reviewer rejects the evidence.

If any of the above occurs, the smoke is **failed**, the env gate is
unset immediately, the decision packet is annotated with the stop
reason, and the claim ladder is **not** advanced.

## 7. Example packets

The R3 PREP example policy and activation packets at

- `docs/examples/dars/live-provider-single-smoke.policy.example.json`
- `docs/examples/dars/live-provider-single-smoke.activation.example.json`

pass the R1 validator (with the deterministic
`live_provider_dispatch_not_authorized_by_policy_alone` warning) and the
existing backend activation validator under
`tests/unit/test_dars_live_provider_single_smoke_runbook.py`. They are
intended as templates; the operator **must** substitute approved
`approval_ref`, `policy_id`, `activation_id`, `backend_id`,
`credential_ref`, `cost_budget_ref`, and `expires_at` values from a
fresh human-approved decision packet before any R3 ACTION attempt.

## 8. Traceability

This R3 PREP runbook satisfies:

- HISYS-FR-DARS-CP-011 (single-critic live provider smoke claim
  prerequisites);
- HISYS-T-DARS-CP-013 (single-critic live provider smoke gate
  documentation and validator coverage);
- the R3 milestone defined in
  `docs/plans/dars-panel-live-provider-unattended-release-final-plan.md`.

Prior controlled increments that this runbook composes:

- `DARS-LIVE-RELEASE-R1-POLICY` — credential-reference-only policy
  validator and fake transport contract (see `src/hisys/agents/dars_live_provider_policy.py`
  and `src/hisys/agents/dars_live_provider_transport.py`).
- `DARS-LIVE-RELEASE-R2-ADAPTER` — fail-closed adapter that requires the
  policy, the activation packet, approval/backend/policy-ref coherence,
  and the env gate before any transport entry point is reachable (see
  `src/hisys/agents/dars_live_provider_adapter.py`).

The runbook is anchored by `DARS-LIVE-RELEASE-R3-SINGLE-SMOKE-PREP` in
`ralph.md` and the matching reflection entry in
`docs/traceability/dars-critic-panel-runtime-traceability.md`.

## 9. Verification commands for this PREP revision

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_live_provider_policy.py tests/unit/test_dars_live_provider_transport.py tests/unit/test_dars_live_provider_adapter.py tests/unit/test_dars_live_provider_single_smoke_runbook.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
git status --short --branch
```

No live provider call, model call, credential lookup, network request,
mutation, publication, deployment, package upload, external
notification, or human-review removal is performed by this PREP
revision.
