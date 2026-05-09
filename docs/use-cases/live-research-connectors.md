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

## Live-D open-access PDF collector boundary

Live-D introduces a legal open-access PDF collector boundary for the
`open_access_pdf_fetch` connector. It is **fixture-only first**: checked-in tests
must validate local PDF-like fixture bytes, license/open-access evidence,
provenance hashes, and extraction records before any live PDF URL is fetched.
The manual live smoke path is not part of CI.

PDF collection preconditions:

1. collect metadata or fixture evidence that records `license_signal=open_access`;
2. reject closed, unknown, or missing license signals before any PDF bytes are
   downloaded or persisted;
3. create a dry-run artifact first with `hisys smoke-source-connector --dry-run`;
4. provide an `approval_ref` recorded outside prompt text;
5. set `HISYS_ALLOW_LIVE_PDF_SMOKE=1` in the operator shell for a manual live
   smoke run;
6. request only read-only PDF retrieval from an allowlisted public OA URL;
7. preserve dispatch, source-access, source-evidence, content-hash, and report
   artifacts under `runtime-boundary/source-connectors/<YYYYMMDD>/`;
8. record `external_call_made` truthfully and keep `mutation_performed=false`.

CI, automated cron jobs, and default Ralph loops must not fetch live PDF bytes.
Without open-access license evidence, operator approval, and the environment
flag, the connector must write a blocked/dry-run artifact and perform no network
call.

## Live-E DOI metadata to OA PDF candidate planning boundary

Live-E connects DOI metadata OA hints to PDF candidate planning without fetching
PDF bytes. The output is a **candidate_plan_only** artifact: it may name a
`pdf_candidate` URL, DOI, source connector, and `license_signal`, but it must not
persist or download PDF content. DOI metadata OA hints are treated as planning
signals, not publication-ready source evidence.

Candidate planning preconditions:

1. input metadata must come from fixture/fake transport artifacts or an approved
   manual DOI metadata smoke artifact;
2. a candidate requires `license_signal=open_access` and a URL-like metadata
   location from an allowlisted public domain;
3. the planner must preserve DOI, metadata evidence refs, license/open-access
   signal, candidate URL, and reason codes;
4. the planner must write runtime-boundary candidate artifacts before any future
   PDF collector runs;
5. the planner must record `candidate_plan_only=true`, `pdf_downloaded=false`,
   `external_call_made=false`, and `mutation_performed=false`.

CI, automated cron jobs, and default Ralph loops must not fetch PDF bytes from
candidate URLs. Candidate artifacts can later feed the Live-D PDF gate only after
operator approval and open-access evidence are present.

## Live-F approved manual OA PDF fetch smoke boundary

Live-F permits a narrowly scoped **manual live smoke only** path for
`open_access_pdf_fetch` after the fixture connector and candidate planner have
passed. The production boundary must use an **injectable transport** so CI and
unit tests can prove behavior with fake PDF bytes and no network. A real network
transport may be used only by an operator-initiated manual smoke command after
all gates pass.

Manual OA PDF smoke preconditions:

1. candidate input or command arguments must carry `license_signal=open_access`;
2. the requested URL must be read-only and allowed by the source connector
   dispatch gate;
3. an `approval ref` must be supplied and recorded outside prompt text;
4. the operator shell must set `HISYS_ALLOW_LIVE_PDF_SMOKE=1`;
5. CI must still use fake transport only and never set the live smoke env flag;
6. the connector must record `pdf_downloaded=true`, `external_call_made=true`,
   `mutation_performed=false`, content hash, source access ref, and source
   evidence ref only after bytes are successfully retrieved;
7. a failed transport response must write a blocked/failed report and must not
   persist partial PDF bytes.

This is still not general web search, crawling, browser automation, credential
use, or publisher access bypass. Prompt text cannot grant approval or enable the
manual smoke path.

## Live-G evidence promotion boundary

Live-G promotes approved manual OA PDF smoke evidence into research investigation
packages only by **explicit source-access and source-evidence refs** supplied to
the investigation command. Hisys must perform **no implicit PDF discovery**, no
candidate URL fetching, and no automatic promotion from prompt text. The promoted
records are boundary evidence: source-access refs prove how PDF bytes crossed the
runtime boundary, and source-evidence refs identify the separated evidence item.

Promotion preconditions:

1. every promoted PDF source-access ref must point under
   `runtime-boundary/source-connectors/<YYYYMMDD>/`;
2. the source-access record must have `connector_id=open_access_pdf_fetch`,
   `pdf_downloaded=true`, `license_signal=open_access`,
   `mutation_performed=false`, and a content hash;
3. every promoted source-evidence ref must point to an evidence item with the
   same connector and a source URL already covered by a promoted access ref;
4. the investigation data package must record `promoted_pdf_evidence_refs` and
   keep them distinct from interpreted gap statements or recommendation text;
5. DARS trace records must preserve the promoted PDF evidence refs as advisory
   lineage only;
6. the Chief Editor review must surface the promoted PDF evidence refs and still
   recommend validation conditions for publication-level claims.

Live-G does not add live PDF fetching. It only allows previously approved,
recorded manual OA PDF smoke artifacts to become explicit inputs to a research
investigation package.

## Live-H PDF quote extraction boundary

Live-H extracts quote records from already promoted OA PDF evidence only when the
operator supplies **explicit promoted_pdf_evidence_refs** or the corresponding
validated source-access/source-evidence refs. The extractor is a fixture/manual-ref
boundary: CI may read only local fixture text embedded in governed evidence
artifacts, and there is **no OCR or PDF parsing in CI**, no browser automation,
no live PDF fetch, and no claim-strengthening based on extraction alone.

Boundary rules:

1. quote extraction must preserve quote-vs-interpretation separation: extracted
   quote text is source evidence, while gap statements, novelty claims, and
   recommendations remain interpreted products;
2. extraction artifacts must be persisted as governed `source_quote_refs` under
   `runtime-boundary/source-connectors/<YYYYMMDD>/` and linked back to the
   source-access and source-evidence refs that authorized promotion;
3. extracted quotes must record source URL, connector id, quote hash, byte/text
   provenance, and `external_call_made=false` for CI/manual-ref extraction;
4. `investigate-domain` may include `source_quote_refs` only when explicitly
   supplied or produced from explicit promoted refs; prompt text cannot trigger
   implicit PDF discovery, OCR, or fetching;
5. DARS trace may critique promoted source quotes as advisory lineage only;
6. Chief Editor novelty claims remain conditional even when quote refs are
   present, because quote extraction proves source linkage, not publication-level
   validation completeness.

## Live-I quote-to-claim evidence ledger boundary

Live-I maps extracted `source_quote_refs` to explicit claim-evidence ledger
entries. The ledger is an interpretation boundary, not a source mutation: **quote text remains source evidence** and the **claim mapping remains interpretation**.
It can classify a quote relationship to a proposed claim as
**support/contradict/needs_evidence**, but it must not rewrite quote artifacts,
upgrade recommendations automatically, or convert quote presence into validated
novelty.

Boundary rules:

1. ledger construction requires explicit `source_quote_refs`; prompts cannot
   discover quotes, fetch PDFs, or infer source refs implicitly;
2. ledger artifacts must be persisted as governed `claim_evidence_ledger_refs`
   under `runtime-boundary/source-connectors/<YYYYMMDD>/`;
3. each ledger entry must record the claim text, relation
   `support/contradict/needs_evidence`, rationale, quote ref, quote hash, and
   whether the mapping is advisory;
4. ledger construction performs no live calls, no PDF parsing/OCR, and no
   mutation of source-access/source-evidence/source-quote artifacts;
5. DARS may critique claim-evidence mappings as advisory lineage only;
6. Chief Editor claims remain conditional until source coverage and validation
   criteria are sufficient beyond the quote-to-claim ledger.
