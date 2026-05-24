# DARS bounded unattended advisory operation runbook (docs/control)

> **Status:** R5 documentation PREP. This runbook defines the controlled documentation contract for `DARS-LIVE-RELEASE-R5-UNATTENDED-PREP`. It does not by itself authorize a standing unattended approval, live provider/model call, credential lookup, external notification, mutation, publication, deployment, release, or removal of human review. The bounded unattended live canary (R5 ACTION) remains a separately approved **HUMAN-GATED** action.
>
> This documentation checkpoint may be used to write RED tests for the standing approval policy validator and the unattended advisory runner. It performs no runtime dispatch.

R5 advances the claim ladder from multi-critic live-provider evidence toward `bounded_unattended_advisory_operation_ready`. That claim is not reached by this document alone. It requires implementation, dry-run fake/injected transport rehearsal, audit ledger evidence, circuit-breaker tests, and later human-reviewed canary evidence if an operator separately approves R5 ACTION.

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
| R3 single-smoke PREP runbook | `docs/runbooks/dars-live-provider-single-smoke.md` |
| R4 panel-smoke PREP runbook | `docs/runbooks/dars-live-provider-panel-smoke.md` |
| R5 standing approval example | `docs/examples/dars/unattended-standing-approval.example.json` |
| R5 canary standing approval example | `docs/examples/dars/unattended-standing-approval-canary.example.json` |
| R5 canary action decision packet | `docs/release/dars-r5-canary-action-decision-packet-v0.0.87.md` |
| R5 policy module | `src/hisys/agents/dars_unattended_policy.py` |
| R5 runner module | `src/hisys/operations/dars_unattended_runner.py` |
| Active controller | `ralph.md` |

## 2. R5 PREP scope

R5 PREP is local Python, tests, and documentation. It may create a `StandingApprovalPolicy` validator, a `DarsUnattendedAdvisoryRunner`, dry-run fake/injected transport rehearsal records, local audit ledger entries under a controlled Hisys instance root, tests, and controlled documents.

R5 PREP does **not** authorize:

- live provider/model calls;
- credential, token, keychain, or secret lookup;
- activation of a real standing unattended approval;
- mutation, publication, deployment, release, or external notification;
- browser/search/tool authority for any critic;
- autonomous approval or removal of `requires_human_review=true`;
- writes outside the selected controlled Hisys instance root except normal repository edits for implementation and docs.

## 3. Standing approval policy contract

A standing approval policy is finite, advisory-only, and revocable. The `validate_standing_approval_policy` validator rejects the policy unless all required fields are present and internally consistent.

Required policy fields:

- `policy_id` and `approval_ref`;
- `operator_id` and `post_run_reviewer_ref`;
- `valid_from` and `expires_at`, with the current time inside the finite window;
- `request_class_allowlist`, limited to explicitly named advisory classes such as `dars_live_provider_advisory_dry_run` and, for later HUMAN-GATED action only, `dars_live_provider_advisory_canary`;
- `provider_policy_refs` pointing to credential-reference-only R1 live-provider policies;
- `activation_packet_refs` pointing to approved activation packets when live action is separately authorized;
- `max_runs`, `max_runs_per_hour`, `max_prompt_bytes_per_run`, `max_output_bytes_per_run`, and `cost_budget_ref`;
- `rate_limit_per_minute` and `max_parallel_critics`;
- `kill_switch_ref` and `kill_switch_required=true`;
- `audit_ledger_ref` and `audit_retention_ref`;
- `redaction_policy_ref`;
- `circuit_breakers` for repeated failures, cost threshold, rate threshold, secret scan hit, policy mismatch, output redaction failure, stale approval, and kill-switch activation;
- `requires_post_run_human_review=true`;
- `mutation_allowed=false`;
- `publication_allowed=false`;
- `external_action_allowed=false`;
- `advisory_only=true`.

The policy stores references only. It must not contain raw credential values, provider tokens, Authorization headers, passwords, API keys, browser session material, or unrestricted raw prompt text.

## 4. Unattended runner contract

The `DarsUnattendedAdvisoryRunner` is a bounded advisory runner, not an autonomous decision system. Before each request it shall:

1. load and validate the `StandingApprovalPolicy`;
2. reject expired or not-yet-valid policies;
3. check the requested class against `request_class_allowlist`;
4. verify finite budget, rate, prompt, output, run-count, and critic-count caps;
5. verify `kill_switch_ref` exists and is in a non-triggered state for dry-run rehearsal;
6. reject mutation, publication, external action, browser, search, or tool authority;
7. verify that referenced R1 policy and activation packets match approval/request boundaries for the requested mode;
8. route dry-run rehearsal through fake/injected transports only;
9. write an audit ledger entry for completed, failed, blocked, or circuit-broken runs;
10. require post-run human review before any run can support a claim transition.

The runner must preserve these output flags in every ledger entry and boundary record:

```text
advisory_only=true
requires_human_review=true
requires_post_run_human_review=true
mutation_performed=false
publication_performed=false
external_action_performed=false
```

For R5 PREP dry-run rehearsal, the acceptable transport result remains:

```text
mode=dry_run
transport_kind=fake
external_call_made=false
model_boundary_crossed=false
```

## 5. Dry-run rehearsal procedure

The R5 PREP dry-run rehearsal should be deterministic and local-safe:

1. Select a temporary controlled Hisys instance root, for example `$HISYS_INSTANCE=$(mktemp -d)`.
2. Load `docs/examples/dars/unattended-standing-approval.example.json`.
3. Validate the standing approval policy against a fixed `now` inside its validity window.
4. Construct one or more advisory request envelopes whose `request_class` is allowlisted and whose provider policy references are R1-compatible.
5. Execute through injected fake transports only. Do not set `HISYS_DARS_LIVE_PROVIDER_LIVE_TRANSPORT_ENABLED=true` for PREP dry-run evidence.
6. Persist an audit ledger entry under:

   ```text
   $HISYS_INSTANCE/runtime-boundary/dars-unattended-advisory/<YYYYMMDD>/<policy_id>/<request_id>.{json,md}
   ```

7. Run `scripts/scan_secrets.py` over the repository and, when practical, over the generated runtime ledger.
8. Review the ledger and confirm no external call, credential lookup, mutation, publication, or external action occurred.

## 6. Audit ledger requirements

Each ledger entry shall contain:

- `schema_id=hisys.dars.unattended_advisory.ledger_entry`;
- `policy_id`, `approval_ref`, `operator_id`, and `post_run_reviewer_ref`;
- `request_id`, `request_class`, `source_execution_id`, and optional `panel_id`;
- referenced provider policy and activation packet refs;
- bounded prompt/output/rate/cost fields;
- kill-switch ref and observed kill-switch state;
- circuit-breaker state before and after the run;
- per-request boundary refs from the R2 adapter or fake transport;
- `external_call_made`, `model_boundary_crossed`, `mutation_performed`, `publication_performed`, `external_action_performed`, `advisory_only`, `requires_human_review`, and `requires_post_run_human_review` flags;
- outcome status: `completed`, `blocked`, `failed`, or `circuit_broken`;
- failure code when not completed;
- secret scan status and redaction status.

Ledger entries are evidence for post-run review. They are not approval decisions.

## 7. Circuit breaker matrix

| Trigger | Required runner behavior | Ledger code |
|---|---|---|
| Policy expired or not yet valid | Refuse before transport | `standing_approval_not_active` |
| Missing kill switch ref | Refuse before transport | `kill_switch_ref_missing` |
| Kill switch triggered | Refuse before transport | `kill_switch_triggered` |
| Missing budget or rate caps | Refuse before transport | `budget_or_rate_caps_missing` |
| Request class outside allowlist | Refuse before transport | `request_class_not_allowlisted` |
| Mutation/publication/action authority requested | Refuse before transport | `unattended_authority_rejected` |
| Provider policy mismatch | Refuse before transport | `provider_policy_mismatch` |
| Repeated failures threshold reached | Stop further runs | `repeated_failure_threshold_reached` |
| Cost threshold reached | Stop further runs | `cost_threshold_reached` |
| Secret scan hit | Stop and preserve blocked ledger | `secret_scan_hit` |
| Output redaction failure | Stop and preserve failed ledger | `output_redaction_failure` |
| Operator or reviewer uncertainty | Stop and request human decision | `operator_uncertainty` |

## 8. Post-run human review

Every R5 PREP dry-run and any later R5 ACTION canary requires post-run human review:

1. The reviewer reads the audit ledger entry and linked boundary records.
2. The reviewer confirms the request class, provider refs, budget/rate caps, and kill-switch state matched the standing approval policy.
3. The reviewer confirms no raw secret, unrestricted prompt, credential value, browser/search/tool authority, mutation, publication, external notification, deployment, release action, or autonomous approval was present.
4. The reviewer confirms `requires_post_run_human_review=true` was preserved.
5. The reviewer records whether the run remains dry-run evidence or supports a later human-approved `bounded_unattended_advisory_operation_ready` claim.

## 9. Stop conditions

Stop immediately and ask for a fresh human decision packet if any of the following is observed:

- missing standing approval policy;
- expired or future-dated policy;
- missing approval ref;
- missing kill switch;
- triggered kill switch;
- missing audit ledger ref;
- missing audit retention ref;
- missing budget caps;
- missing rate caps;
- request class outside allowlist;
- raw secret, token, password, API key, Authorization header, or credential value in policy, request, output, or ledger;
- credential lookup by Hisys;
- mutation authority;
- publication authority;
- external action authority;
- browser/search/tool authority;
- live provider/model call during PREP dry-run;
- `HISYS_DARS_LIVE_PROVIDER_LIVE_TRANSPORT_ENABLED=true` set during PREP dry-run;
- policy mismatch;
- approval-ref mismatch;
- secret scan hit;
- output redaction failure;
- repeated failures threshold reached;
- cost threshold reached;
- operator uncertainty.

## 9b. Canary mode contract (R5 canary-mode-prep)

`DARS-LIVE-RELEASE-R5-CANARY-MODE-PREP` adds a distinct canary-mode contract for the bounded unattended runner. The canary mode does not by itself authorize a live provider/model call. It is the local, fail-closed shape that a later HUMAN-GATED canary execution must satisfy before any live boundary may be crossed.

The runner exposes two modes:

```text
mode=dry_run   # default R5 PREP rehearsal class
mode=canary    # bounded canary path; still routes through the fake/injected adapter
```

For `mode=canary`:

- `request_class` must equal `dars_live_provider_advisory_canary`; the dry-run class is rejected by the runner.
- The standing approval policy is validated with `validate_standing_approval_policy(..., mode="canary")` and must declare all of:
  - `canary_action_decision_packet_ref` matching the request's `canary_action_decision_packet_ref`;
  - `canary_post_run_reviewer_ref`;
  - `canary_window_start` and `canary_window_end` (finite, current time within the window);
  - `canary_max_runs` (positive int, not exceeding `max_runs`);
  - `requires_post_canary_human_review=true`;
  - `request_class_allowlist` containing `dars_live_provider_advisory_canary`.
- All authority flags remain locked: `mutation_allowed=false`, `publication_allowed=false`, `external_action_allowed=false`, `advisory_only=true`, `requires_post_run_human_review=true`.
- The runner still calls the R2 fail-closed adapter with `mode=dry_run` because no approved real-provider transport exists yet. The ledger therefore records `adapter_mode=dry_run`, `transport_kind=fake_injected_provider_transport`, `external_call_made=false`, `model_boundary_crossed=false`, `live_provider_model_call_made=false`, `raw_provider_api_call_by_hisys=false`, and `credential_lookup_by_hisys=false`. No provider/model boundary is crossed.
- Deterministic failure codes for the canary path:
  - `canary_mode_policy_invalid` — standing approval policy fails canary-mode validation (e.g. missing canary fields, inactive canary window);
  - `canary_mode_requires_canary_request_class` — `mode=canary` was requested with a non-canary `request_class`;
  - `canary_action_decision_packet_ref_mismatch` — request `canary_action_decision_packet_ref` does not match the policy's.
- The dry-run path is preserved unchanged. `mode=dry_run` continues to accept only `dars_live_provider_advisory_dry_run` and continues to write the previously specified ledger envelope.

The canary-mode contract is local and read-only. It does not activate a standing unattended approval, does not authorize a live provider/model call, does not perform a credential lookup, does not request raw provider API readiness, and does not transition the claim ladder.

## 10. Validation commands

Documentation checkpoint validation:

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_unattended_docs.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

Full R5 PREP validation after implementation includes the policy and runner tests:

```bash
PYTHONPATH=src:. pytest tests/unit/test_dars_unattended_policy.py tests/unit/test_dars_unattended_runner.py tests/unit/test_dars_unattended_docs.py -q
PYTHONPATH=src:. pytest tests/unit -q -k dars
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```
