---
doc_id: HISYS-DARS-R7-RC-CHECKLIST-001
title: DARS Panel Release Candidate Checklist
version: v0.0.94
status: r7-residual-risk-human-gate-entered
created: 2026-05-24
---

# DARS Panel Release Candidate Checklist

This checklist defines what must be present before Hisys can report `release_candidate_ready`. The current R7 residual-risk human gate is entered for human review; `release_candidate_ready` remains false because residual risk acceptance is still not recorded and live-provider/model canary evidence remains absent.

release_candidate_ready remains false until every required evidence row is accepted.

## Required evidence rows

- [ ] R3 reviewed single-smoke evidence is linked and scoped to the accepted transport claim.
- [ ] R4 reviewed multi-critic evidence or accepted scoped substitute is linked.
- [x] R5 bounded unattended canary packet prep has advanced to a prepared packet for human review.
- [x] R5 bounded unattended canary packet prep document is present at `docs/release/dars-r5-canary-packet-prep-v0.0.86.md`.
- [x] R5 bounded unattended canary action decision packet document is present at `docs/release/dars-r5-canary-action-decision-packet-v0.0.87.md`.
- [x] R5 bounded unattended canary action decision packet is reviewed before the scoped fake-transport canary execution.
- [x] R5 fake/injected-transport canary post-run review is accepted at `docs/reports/dars-r5-canary-post-run-review-gate-2026-05-24.md`.
- [ ] R5 bounded unattended live canary evidence is reviewed and accepted before any `bounded_unattended_advisory_operation_ready` claim.
- [ ] R6 live operations status report is current and references latest boundary records without copying raw payloads.
- [ ] rollback runbook is present and its disable/recovery sequence is reviewable.
- [ ] full unit gate passes: `PYTHONPATH=src:. pytest tests/unit -q`.
- [ ] traceability validator passes: `python3 scripts/validate_traceability.py`.
- [ ] secret scan passes: `python3 scripts/scan_secrets.py`.
- [x] R7 RC readiness decision packet is present at `docs/release/dars-r7-rc-readiness-decision-packet-v0.0.93.md` and accepts only `r7_rc_readiness_decision_packet_recorded_for_human_review`.
- [x] R7 residual-risk human gate is entered at `docs/release/dars-r7-rc-residual-risk-human-gate-v0.0.94.md` and accepts only `r7_rc_residual_risk_human_gate_entered`; residual risk acceptance is still not recorded.
- [ ] residual risk acceptance is recorded in the RC decision packet.
- [ ] human release approval state is explicit and separate from release execution approval.

## Scoped substitute rule

R4H is a scoped human-review advisory substitute, not R4C Codex subprocess completion. R4C is excluded from this release scope. If the RC packet uses R4H evidence while R4C remains deferred, the packet must say so and must keep raw provider API readiness, adapter-native readiness, and R4C subprocess completion false.

## Non-goals

The RC gate does not authorize release execution, tag creation, package upload, deployment, publication, external notification, provider credential lookup, standing unattended approval activation, or removal of `requires_human_review=true`.
