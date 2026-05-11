# Hisys Public Browser Beta Quickstart

Hisys public browser beta is a governed, read-only public-web evidence workflow.
It produces local evidence and review artifacts for human-reviewed use; it does
not publish, post, contact third parties, buy, upload, log in, use credentials,
or perform consequential actions.

## 1. Install

From a clean checkout:

```bash
pip install -e ".[browser]"
python -m playwright install chromium
```

The public quickstart assumes the installed `hisys` console script. Developer
fixture mode remains available for CI and reproducibility, but it is not part of
normal public UX.

## 2. Validate the public beta profile

```bash
hisys validate-public-browser-profile \
  --profile examples/instance/config/profiles/public-browser.yaml
```

Expected shape:

```text
public browser profile: valid profile_id=public-browser-beta connector_id=playwright_read_only transport_kind=playwright_live
```

The profile requires:

```text
live_network_enabled=true
connector_id=playwright_read_only
mode=read_only
external_call_allowed=true
domain_decision_policy=orchestrator_decided
allow_credentials=false
allow_mutation=false
fixture_mode_publicly_exposed=false
transport_kind=playwright_live
```

## 3. Prepare a scoped live connector config

The checked-in baseline source connector registry is disabled by default. For a
real public beta run, use a scoped runtime copy that enables only
`playwright_read_only` and keeps the same forbidden actions.

Minimum public-browser connector posture:

```yaml
default_mode: read_only
policy:
  live_network_enabled: true
  require_human_approval_for_external_call: true
  allow_credentials: false
  allow_mutation: false
  require_allowlist: true
  require_provenance_record: true
connectors:
  playwright_read_only:
    connector_id: playwright_read_only
    connector_type: playwright_read_only
    enabled: true
    mode: read_only
    external_call_allowed: true
    domain_decision_policy: orchestrator_decided
    requires_human_approval: true
    approval_policy_ref: POLICY-LIVE-RESEARCH-001
    allowed_domains: []
    disallowed_domains: []
    forbidden_actions:
      - login
      - credential_use
      - form_submit
      - upload
      - purchase
      - post
      - mutation
      - access_control_bypass
    output_schema: EvidencePackage
    manual_smoke_only: true
    manual_smoke_env_var: HISYS_ALLOW_BROWSER_SMOKE
    smoke_test_in_ci: false
```

## 4. Run browser acquisition

Set the manual smoke gate only for the approved run window:

```bash
export HISYS_ALLOW_BROWSER_SMOKE=1
```

Run read-only browser acquisition:

```bash
hisys browser-investigate-topic \
  --instance <runtime-instance> \
  --config <scoped-source-connectors.yaml> \
  --date <YYYYMMDD> \
  --request-id <HISYS-REQ-PUBLIC-...> \
  --topic "<topic>" \
  --user-opinion "<operator context>" \
  --approval-ref <APPROVAL-REF> \
  --orchestrator-decide-domains \
  --follow-links \
  --max-follow-links-per-source 2 \
  --source-url https://example.com/page-a \
  --source-url https://example.org/page-b
```

Expected browser acquisition report:

```text
reports/run-summaries/<YYYYMMDD>/browser-investigation-report.json
```

The report should show:

```text
transport_kinds includes playwright_live
external_call_made=true
mutation_performed=false
orchestrator_domain_decision_ref is present when --orchestrator-decide-domains is used
```

## 5. Run the governed review chain

Use the artifact refs from the acquisition report:

```bash
hisys review-browser-investigation \
  --instance <runtime-instance> \
  --date <YYYYMMDD> \
  --browser-investigation-report-ref reports/run-summaries/<YYYYMMDD>/browser-investigation-report.json
```

Then run advisory DARS/Devil review:

```bash
hisys request-browser-dars-review \
  --instance <runtime-instance> \
  --date <YYYYMMDD> \
  --chief-editor-review-ref data/chief-editor-reviews/<YYYYMMDD>/CHIEF-REVIEW-<REQ>-BROWSER.json
```

Resolve required advisory revisions:

```bash
hisys resolve-browser-dars-revisions \
  --instance <runtime-instance> \
  --date <YYYYMMDD> \
  --dars-review-ref data/dars-reviews/<YYYYMMDD>/DARS-<REQ>-BROWSER.json
```

Finalize the local Chief Editor browser review package:

```bash
hisys final-review-browser-investigation \
  --instance <runtime-instance> \
  --date <YYYYMMDD> \
  --revision-resolution-ref data/browser-dars-revision-resolutions/<YYYYMMDD>/REVISION-<REQ>-BROWSER.json
```

## 6. Interpret final state

A successful final artifact is still bounded:

```text
decision=accept_for_human_reviewed_use
publication_or_live_action_approved=false
human_approval_required_for_consequential_use=true
action_taken=none
external_call_made=false for final review stage
mutation_performed=false
```

Hisys public beta produces governed evidence and review artifacts. Any public
publication, consequential use, outreach, vault persistence, or live mutation
requires a separate human approval workflow.

## 7. Known limits

- Public beta defaults to Playwright Chromium.
- Camoufox is not a public default; it remains an optional future experimental
  compatibility transport spike.
- Fixture mode is for tests/reproduction, not public UX.
- Expected operational failures should be treated as blocked runs and reviewed
  through the generated reports.
