# DARS multi-critic live-provider panel smoke runbook (docs/control)

> **Status:** human-gated PREP. This runbook is the controlled PREP artifact for `DARS-LIVE-RELEASE-R4-PANEL-SMOKE-PREP`. It records the conditions under which a multi-critic live-provider panel smoke **may** be attempted and the evidence the resulting run must produce. The runbook does not by itself authorize the live call. The actual multi-critic panel live call is a separately approved, **HUMAN-GATED** action governed by R4 ACTION and requires a fresh, human-approved decision packet.
>
> The R4 PREP work that produced this runbook performs no live provider call, no model call, no credential lookup, no network request, no mutation, no publication, no deployment, and no remote push beyond the normal `git push origin dars` checkpoint authorized by ralph.md §2.

This runbook supersedes nothing. It complements
`docs/runbooks/dars-live-provider-single-smoke.md` (R3 single-critic smoke
PREP) and the existing remote subscription panel dispatch surface at
`src/hisys/agents/dars_remote_subscription_dispatch.py`.

R4 requires a **reviewed R3 single-critic smoke** (`live_provider_advisory_smoked`)
as a precondition before any multi-critic call is attempted. The DARS
completion claim remains `live_provider_advisory_smoked` until R4 ACTION
evidence is human-reviewed and accepted as
`multi_critic_live_provider_advisory_complete`.

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
| Remote subscription dispatch + panel | `src/hisys/agents/dars_remote_subscription_dispatch.py` |
| Named panel config | `examples/instance/config/dars.json` (`spec.panels.r4_mapped_subscription_panel`) |
| Single-smoke PREP runbook | `docs/runbooks/dars-live-provider-single-smoke.md` |
| Panel example policy | `docs/examples/dars/live-provider-panel-smoke.policy.example.json` |
| Panel example activation | `docs/examples/dars/live-provider-panel-smoke.activation.example.json` |
| Single-smoke example policy | `docs/examples/dars/live-provider-single-smoke.policy.example.json` |
| Single-smoke example activation | `docs/examples/dars/live-provider-single-smoke.activation.example.json` |
| Active controller | `ralph.md` |

## 2. Preconditions

A multi-critic live-provider panel smoke **may** be attempted only after
**all** of the following are confirmed by the operator and recorded in the
decision packet:

1. A reviewed R3 single-critic smoke has already produced an accepted
   `live_provider_advisory_smoked` claim. R4 cannot precede R3.
2. A fresh, human-approved decision packet exists. The packet names the
   `approval_ref`, the request class (multi-critic advisory panel), the
   `panel_id`, the list of approved critic roles, the approved
   provider/model refs for each critic, the bounded prompt/output sizes,
   the redaction policy ref, the cost/rate budget refs, the post-run
   human reviewer, and the rollback procedure.
3. A live-provider policy packet that validates under
   `validate_live_provider_policy_packet` with zero error issues and the
   deterministic warning
   `live_provider_dispatch_not_authorized_by_policy_alone`. The packet
   carries only a credential reference (`env://`, `secret-manager-ref://`,
   `vault://`, `subscription-account-ref://`, or `keychain-ref://`); it
   does **not** carry a raw token, API key, password, or Authorization
   header. The same packet may be reused across critics or each critic
   may have its own packet; if multiple packets are used, each must
   declare a matching `approval_ref` and `cost_budget_ref` envelope.
4. A backend activation packet that validates under
   `validate_dars_backend_activation_packet` with zero error issues, has
   `endpoint_scope=external_api`, `allowed_actions=advisory_only`,
   `human_approved=true`, and `remote_policy_packet_ref` matching the
   policy packet path.
5. The activation `approval_ref`, the policy `approval_ref`, and every
   per-critic request `approval_ref` all match.
6. The approved panel composition is recorded in Hisys DARS config, not
   assembled from an ad-hoc sidecar JSON. The checked-in PREP example is
   `spec.panels.r4_mapped_subscription_panel` in
   `examples/instance/config/dars.json`; an operator instance must carry
   the same schema shape under `$HISYS_INSTANCE/config/dars.json` before
   R4 ACTION. The configured panel remains advisory-only and references
   disabled backends by id; the config alone does not authorize dispatch.
7. Every per-critic dispatch request shares the same `request_id` and
   `panel_id`, and each critic has a unique `source_execution_id`. The
   panel runbook explicitly rejects duplicate `source_execution_id`
   values across critics and rejects mismatched `request_id` across
   critics (see `_validate_panel_shape` in
   `src/hisys/agents/dars_remote_subscription_dispatch.py`).
8. The credential reference resolves outside Hisys
   (operator-managed environment, secret manager, vault, or subscription
   account). Hisys does not read, log, or validate the credential value.
9. Bounded prompt/output sizes are confirmed across **all** critics:
   - `max_prompt_bytes` is positive and finite for every critic;
   - `max_output_bytes` is positive and finite for every critic;
   - `rate_limit_per_minute` is positive and finite for every critic.
   The panel-level cost envelope `cost_budget_ref` is set to a finite
   limit that covers every critic and any retry quota.
10. The redaction policy ref
   (`policy://hisys/dars/live-provider-redaction-v1` or equivalent) is in
   force. Every per-critic bounded prompt packet is constructed under
   that policy.
11. The R2 env gate is set in the operator shell only for the duration of
    the panel smoke:

    ```bash
    export HISYS_DARS_LIVE_PROVIDER_LIVE_TRANSPORT_ENABLED=true
    ```

    The env gate **must** be unset immediately after the panel smoke
    completes or fails.
12. A controlled Hisys instance root is selected for evidence storage
    (`$HISYS_INSTANCE`). Per-critic and panel-level boundary records
    will be written under this root.
13. Operator certainty: the operator is confident the procedure is
    correct, the rollback is verified, and is willing to be the post-run
    reviewer.

## 3. Multi-critic procedure

A reviewed acceptable panel smoke runs two or more critics (each
producing one advisory critic call) under exactly **one** approved
decision packet and produces both per-critic and panel-level boundary
records. Unattended runs and
release-related artifacts are explicitly out of scope for R4 and require
separately approved R5 / R7 / R8 decision packets.

The reference command shape (R4 ACTION) is:

```text
# Construct request set from approved decision packet
request_id=<DARS-LP-PANEL-REQ-...>
panel_id=<DARS-LP-PANEL-...>
panel_key=r4_mapped_subscription_panel
backend_id=<dars-live-claude-panel-smoke-001>
policy_packet_ref=docs/examples/dars/live-provider-panel-smoke.policy.example.json
activation_packet_ref=docs/examples/dars/live-provider-panel-smoke.activation.example.json
approval_ref=APPROVAL-DARS-LP-PANEL-SMOKE-20260523-001
yyyymmdd=<YYYYMMDD>
mode=live

# Two or more critics, each with a unique source_execution_id and a
# redacted bounded prompt_packet_ref. Every request shares request_id
# and panel_id; source_execution_id values are unique across the panel.
# R4 ACTION invokes either:
#   - run_dars_remote_subscription_panel_dispatch (existing seam) with a
#     governed real-provider executor wired through the R2 adapter
#     stack, OR
#   - a multi-critic loop that calls run_dars_live_provider_adapter for
#     each critic and writes a panel-level summary boundary record.
# Both paths require a separately approved real-provider transport that
# is OUT OF SCOPE for R4 PREP.

# Fixture/local CLI rehearsals for the same configured panel use:
hisys run-dars-panel \
  --instance "$HISYS_INSTANCE" \
  --date "$yyyymmdd" \
  --request-id "$request_id" \
  --panel-key "$panel_key" \
  --candidate-ref <instance-relative-candidate-ref> \
  --evidence-ref <instance-relative-evidence-ref> \
  --format json
```

Until a real-provider transport is approved and merged, the R2 adapter
routes both `dry_run` and `live` modes through
`FakeLiveProviderTransport`. PREP cannot promote that path into a real
multi-critic call.

## 4. Boundary record requirements

A successful R4 ACTION multi-critic panel smoke must persist:

1. A **per-critic boundary record** for each critic under the existing
   R2 adapter path:

   ```text
   $HISYS_INSTANCE/runtime-boundary/dars-live-provider-adapter/<YYYYMMDD>/<request_id>/<backend_id>-<source_execution_id>.{json,md}
   ```

   carrying `schema_id=hisys.dars.live_provider_adapter`, `mode=live`,
   `external_call_made=true`, `model_boundary_crossed=true`,
   `mutation_performed=false`, `publication_performed=false`,
   `advisory_only=true`, `requires_human_review=true`, and per-critic
   cost/latency metadata.

2. A **panel-level boundary record** that summarizes the panel run.
   When the existing remote-subscription panel dispatch seam is reused,
   the record path is:

   ```text
   $HISYS_INSTANCE/runtime-boundary/dars-remote-subscription-panels/<YYYYMMDD>/<request_id>/<panel_id>.{json,md}
   ```

   The panel record carries the panel id, request id, critic count,
   completed critic count, provider ids, adapter classes, per-critic
   boundary refs, `external_call_made=true`, `model_boundary_crossed=true`,
   `mutation_performed=false`, `publication_performed=false`,
   `allowed_actions=advisory_only`, `requires_human_review=true`, and
   `transport_kind` reflecting the approved real-provider transport.

Per-critic and panel records together must support **failure isolation**:
one critic failing does not erase completed critic evidence, and the
panel record must distinguish completed critics from failed critics so a
post-run reviewer can decide whether the partial evidence is acceptable.
The synthesis remains advisory and may report `needs_more_evidence` if
fewer critics complete than the decision packet requires.

## 5. Post-run review

A R4 ACTION panel smoke is only considered successful after a post-run
human review:

1. The reviewer reads every per-critic boundary record and the panel
   boundary record.
2. The reviewer confirms that prompt and output redaction matches the
   approved policy across all critics.
3. The reviewer confirms that no critic claimed mutation, publication,
   deployment, approval, or downstream action authority in its output.
4. The reviewer confirms the bounded cost/latency envelope was honored
   at both the per-critic level and the panel-aggregate level.
5. The reviewer confirms the env gate is now unset.
6. The reviewer creates a reviewed report under
   `docs/reports/dars-live-provider-panel-smoke-<YYYYMMDD>.md` and
   updates traceability to record the human-accepted claim transition
   from `live_provider_advisory_smoked` to
   `multi_critic_live_provider_advisory_complete`.

## 6. Stop conditions

Stop and ask before proceeding (or stop and revert during execution) if
any of the following is observed. Each is a hard stop; the operator
must record the stop condition in the decision packet and the panel
smoke is abandoned for that attempt.

- missing decision packet, missing approval ref, or any approval-ref
  mismatch across the request set, policy, and activation packets;
- raw secret, token, password, API key, or Authorization header in any
  policy/activation/decision/prompt packet or reviewed output
  (`scripts/scan_secrets.py` flags any of these);
- credential lookup by Hisys (Hisys must never read, log, validate, or
  serialize the credential value);
- credential reference scheme outside the controlled allowlist
  (`env://`, `secret-manager-ref://`, `vault://`,
  `subscription-account-ref://`, `keychain-ref://`);
- mutation request, publication request, deployment request, tool
  authority request, browser authority request, or search authority
  request from any critic output;
- `mutation_performed=true`, `publication_performed=true`, or
  `requires_human_review=false` in any per-critic output, per-critic
  boundary record, or the panel boundary record;
- budget violation (cost over `cost_budget_ref`) or rate-limit violation (exceeds `rate_limit_per_minute`) at any critic;
- secret scan hit on any new file produced by the panel smoke;
- output redaction failure (raw secret-shaped values, unauthorized
  authority claim, oversize output, empty output) at any critic;
- duplicate source execution id across critics;
- mismatched request_id across critics in the same panel;
- policy mismatch across critics unless explicitly allowed in the
  decision packet;
- working tree changes after a supposedly read-only panel smoke;
- runtime-boundary record cannot be written under `$HISYS_INSTANCE`;
- env gate `HISYS_DARS_LIVE_PROVIDER_LIVE_TRANSPORT_ENABLED` not set or
  set to anything other than `true` at the moment of the smoke;
- operator uncertainty about any precondition, command, or output;
- post-run human reviewer rejects the evidence.

If any of the above occurs, the smoke is **failed**, the env gate is
unset immediately, the decision packet is annotated with the stop
reason, and the claim ladder is **not** advanced. Partial completed
critic evidence may be retained for audit but does not by itself
authorize the `multi_critic_live_provider_advisory_complete` claim.

## 7. Example packets

The R4 PREP example policy and activation packets at

- `examples/instance/config/dars.json` (`spec.panels.r4_mapped_subscription_panel`)
- `docs/examples/dars/live-provider-panel-smoke.policy.example.json`
- `docs/examples/dars/live-provider-panel-smoke.activation.example.json`

pass the R1 validator (with the deterministic
`live_provider_dispatch_not_authorized_by_policy_alone` warning) and the
existing backend activation validator under
`tests/unit/test_dars_live_provider_panel_smoke_runbook.py`. They are
intended as templates; the operator **must** substitute approved
`approval_ref`, `policy_id`, `activation_id`, `backend_id`, `panel_id`, `panel_key`,
`credential_ref`, `cost_budget_ref`, and `expires_at` values from a
fresh human-approved decision packet before any R4 ACTION attempt.

## 8. Traceability

This R4 PREP runbook satisfies:

- HISYS-FR-DARS-CP-012 (multi-critic live-provider panel smoke claim
  prerequisites and failure-isolation requirements);
- HISYS-T-DARS-CP-014 (multi-critic live provider panel smoke gate
  documentation and validator coverage at PREP scope);
- HISYS-T-DARS-CP-014 (named Hisys config panel path for R4 mapped
  subscription panel prep without ad-hoc sidecar panel config);
- the R4 milestone defined in
  `docs/plans/dars-panel-live-provider-unattended-release-final-plan.md`.

Prior controlled increments that this runbook composes:

- `DARS-LIVE-RELEASE-R1-POLICY` — credential-reference-only policy
  validator and fake transport contract.
- `DARS-LIVE-RELEASE-R2-ADAPTER` — fail-closed per-critic adapter that
  enforces policy + activation + approval/backend/policy-ref coherence
  and the env gate before any transport entry point is reachable.
- `DARS-LIVE-RELEASE-R3-SINGLE-SMOKE-PREP` — single-critic live-provider
  smoke PREP runbook and example packets; reviewed R3 ACTION is a
  precondition for R4 ACTION.

The runbook is anchored by `DARS-LIVE-RELEASE-R4-PANEL-SMOKE-PREP` in
`ralph.md` and the matching reflection entry in
`docs/traceability/dars-critic-panel-runtime-traceability.md`.

## 9. Verification commands for this PREP revision

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_config.py tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_live_provider_policy.py tests/unit/test_dars_live_provider_transport.py tests/unit/test_dars_live_provider_adapter.py tests/unit/test_dars_live_provider_single_smoke_runbook.py tests/unit/test_dars_live_provider_panel_smoke_runbook.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
git status --short --branch
```

No live provider call, model call, credential lookup, network request,
mutation, publication, deployment, package upload, external
notification, or human-review removal is performed by this PREP
revision.
