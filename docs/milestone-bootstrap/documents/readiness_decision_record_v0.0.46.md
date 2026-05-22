# Readiness Decision Record v0.0.46 — DARS remote subscription path authorization

Date: 2026-05-22

## Request context

User instruction after DARS local execution PREP stopped for operator prerequisites:

```text
local은 아직 준비가 덜 되어 있지 않나? 확인하고 준비가 되어 있으면 A 안되어 있면 C. subscription으로 진행
```

Hermes checked the local prerequisites and found the local path not ready: `HISYS_DARS_LOCAL_ENDPOINT` unset, `HISYS_INSTANCE` unset, no operator-provided live instance root, and no fresh activation packet path.

## Decision

Proceed with option C: open a governed DARS remote subscription path.

This decision authorizes a docs/control PREP row for remote subscription execution planning. It does not by itself authorize a real Codex or Claude subscription call. The PREP row must bind the existing M-DARS-BE-5/6 policy and injected-executor harness to a concrete operator packet before any provider boundary is crossed.

## Allowed first increment

- Record the local-not-ready evidence.
- Record this subscription-path decision.
- Update `ralph.md`, traceability, and bootstrap profile state.
- Seed `DARS-REMOTE-SUBSCRIPTION-AUTH-PREP` as the next Ralph row.

## Required follow-on decisions before any real subscription call

The PREP row must stop before live provider execution unless these are supplied explicitly:

- provider choice: `codex` or `claude`;
- operator identity and approval reference;
- subscription account reference, without raw credentials;
- redaction policy reference;
- egress scope;
- expiry/revocation references;
- executor boundary and audit record path;
- confirmation that output is advisory-only with no mutation, publication, browser, search, or tool authority.

## Non-claims

This decision is not evidence that remote subscription DARS has run. It does not authorize credential lookup, raw secret handling, arbitrary endpoint configuration, provider account configuration, publication/deployment, mutation, or expansion beyond the Codex/Claude subscription allowlist.

OSS comparison/license execution remains future-roadmap only.
