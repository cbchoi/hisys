# Readiness Decision Record v0.0.72 — DARS R3 critic live smoke review gate

## Decision

`r3_codex_subscription_single_critic_smoke_review_accepted`

## Request context

최창범 교수 instructed: `go for review gate`. The gate inspected the already captured R3 critic live-smoke report and runtime-boundary evidence without invoking Codex again and without any raw-provider API call.

## Evidence scope

Reviewed:

- `docs/reports/dars-r3-critic-live-smoke-2026-05-23.md`
- `docs/reports/dars-r3-critic-live-smoke-review-gate-2026-05-23.md`
- Runtime-boundary JSON under `/tmp/hisys-r3-critic-live-smoke-20260523/runtime-boundary/dars-remote-subscriptions/20260523/REQ-DARS-R3-CRITIC-LIVE-SMOKE-20260523-001/`
- Runtime-boundary Markdown at the same evidence path
- Decision-packet policy/activation refs under `/tmp/hisys-r3-critic-live-smoke-20260523/decision-packet/`
- `docs/milestone-bootstrap/profile.yaml`
- `ralph.md`
- `tests/unit/test_governance_docs_current_state.py`

## Validation status

This record is valid only after the commit containing it passes:

```bash
PYTHONPATH=src:. pytest tests/unit/test_governance_docs_current_state.py tests/unit/test_dars_codex_cli_subprocess.py tests/unit/test_dars_remote_subscription_dispatch.py tests/unit/test_dars_remote_subscription_policy.py tests/unit/test_dars_backend_activation.py -q
PYTHONPATH=src:. pytest tests/unit -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

## Claim boundary

The review accepts only one narrow R3 evidence claim:

```text
r3_codex_subscription_single_critic_smoke_review_accepted
```

The review does not upgrade the claim to `live_provider_advisory_smoked`, because the evidence records the `hisys.dars.remote_subscription_dispatch` schema with `adapter_class=codex_subscription`, not the R2 `hisys.dars.live_provider_adapter` raw-provider path.

No live model/provider call, Codex subprocess call, raw provider API call, credential lookup, standing unattended approval activation, R4 multi-critic action, R5 ACTION, release-candidate transition, deployment, publication, external notification, mutation outside repository docs/control files, destructive Git action, or human-review removal is authorized or performed by this review gate.

## Next action

Run `DARS-LIVE-RELEASE-R3-ACTION-TRANSPORT-PREP` as a preparation-only row. It should define how R3 evidence can satisfy the live-provider claim ladder without confusing the Codex subscription subprocess path with raw provider API transport.
