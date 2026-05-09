# Live Research Connector Boundary

Status: controlled design boundary plus fixture-backed connector integration for
the next Hisys live-source search phase.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.

## Purpose

This document defines what live data-source search means for Hisys before any
adapter is allowed to call a network, browser, external API, or external LLM.
The governing rule remains: **no live external action until harness passes** and
until registry policy plus explicit approval allow the connector.

The current MVP is fixture-local. Live connectors introduced after this boundary
must remain disabled-by-default in checked-in configuration.

## Allowed read-only live-source activities

A connector may be considered for approval only when it is read-only and records
provenance:

- read public publisher or journal landing pages;
- read public DOI/arXiv/metadata pages;
- read legal open-access PDF URLs after license/open-access status is recorded;
- read explicitly allowlisted domains;
- preserve source URL, access time, title, content type, hash, license signal,
  and quoted text separately from interpretation.

## Prohibited activities

Every live-source connector must enforce a `forbidden_actions` set that includes:

```json
[
  "login",
  "credential_use",
  "form_submit",
  "upload",
  "purchase",
  "post",
  "comment",
  "mutation",
  "access_control_bypass"
]
```

Prompt text may narrow research focus, but it may not enable live connectors,
change source policy, grant credentials, bypass approvals, or request prohibited
actions.

## Approval and dispatch boundary

A live connector can run only after a runtime connector dispatch decision records:

```json
{
  "decision": "allowed",
  "connector_id": "publisher_web_search",
  "approval_ref": "APPROVAL-...",
  "external_call_requested": true,
  "external_call_permitted": true,
  "external_call_made": false,
  "mutation_performed": false
}
```

If the connector is disabled, lacks an `approval_ref`, violates allowlist policy,
or requests a prohibited action, the dispatch decision must be `blocked` before
any adapter code performs an external call.

## Runtime evidence

Dispatch decisions and source-access records belong under:

```text
runtime-boundary/source-connectors/<YYYYMMDD>/
  connector-dispatch-<decision_id>.json
  connector-dispatch-<decision_id>.md
  source-access-<access_id>.json
  source-evidence-<evidence_id>.json
  connector-plan-<request_id>.json
  connector-plan-<request_id>.md
reports/run-summaries/<YYYYMMDD>/
  source-connector-smoke-report.json
  source-connector-smoke-report.md
```

Evidence packages must distinguish:

1. source evidence;
2. quoted/extracted text;
3. interpretation;
4. license/open-access status;
5. uncertainty or missing evidence;
6. downstream recommendation conditions.

## Non-goals for this boundary

This boundary does not enable live web search, PDF download, external LLM calls,
credential use, or browser automation. It defines the policy and evidence shape
that later fixture and live connector increments must satisfy.

## Live-C manual metadata smoke boundary

Live-C introduces only a manually invoked, read-only public metadata smoke
boundary for the `doi_metadata_search` connector. It is **manual_smoke_only**,
disabled by default, and **not part of CI**. The purpose is to validate the
approval/dispatch/provenance path for one low-risk metadata endpoint after the
fixture harness passes; it is not general live search.

Manual smoke preconditions:

1. create a dry-run artifact first with `hisys smoke-source-connector --dry-run`;
2. provide an `approval_ref` recorded outside prompt text;
3. set `HISYS_ALLOW_LIVE_SMOKE=1` in the operator shell;
4. request only read-only DOI metadata retrieval from the allowlisted endpoint;
5. preserve dispatch, source-access, source-evidence, and report artifacts under
   `runtime-boundary/source-connectors/<YYYYMMDD>/`;
6. record `external_call_made` truthfully and keep `mutation_performed=false`.

CI, automated cron jobs, and default Ralph loops must not run the live smoke
path. Without the environment flag and approval reference, the connector must
write a blocked/dry-run artifact and perform no network call.
