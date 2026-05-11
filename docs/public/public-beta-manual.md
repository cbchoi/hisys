# Hisys Controlled Public Beta Manual

This manual explains how to run Hisys as a controlled public beta for governed,
read-only public-web evidence investigation. If you are integrating Hisys as a
tool for Hermes or another agentic AI system, also see
`docs/public/agent-tool-manual.md`.

Hisys does **not** publish, post, log in, use credentials, submit forms, upload,
purchase, bypass access controls, solve CAPTCHAs, rotate proxies, or approve
consequential action. It creates local evidence and review artifacts for human
review.

## Audience

Use this manual if you are an operator or reviewer who wants to run a public beta
investigation with the public browser workflow.

Use the developer docs and tests instead if you are changing Hisys internals.

## Public beta flow

```text
install/setup
  -> validate-public-browser-profile
  -> prepare scoped source connector config
  -> public-browser-readiness
  -> public-browser-run
  -> read public browser summary and final Chief Editor artifact
  -> human review / separate approval for any consequential use
```

## 1. Install Hisys with browser support

From the repository root:

```bash
pip install -e ".[browser]"
python -m playwright install chromium
```

Confirm the CLI is available:

```bash
hisys --help
```

## 2. Choose a runtime instance directory

Use a dedicated runtime directory for beta artifacts. Example:

```bash
export HISYS_INSTANCE="$PWD/.runtime/public-beta-demo"
mkdir -p "$HISYS_INSTANCE"
```

Hisys writes local run artifacts under this directory, including:

```text
reports/run-summaries/<YYYYMMDD>/
data/source-access/<YYYYMMDD>/
data/evidence-packages/<YYYYMMDD>/
data/chief-editor-reviews/<YYYYMMDD>/
data/dars-browser-reviews/<YYYYMMDD>/
data/browser-dars-revision-resolutions/<YYYYMMDD>/
data/chief-editor-final-browser-reviews/<YYYYMMDD>/
```

## 3. Validate the public browser profile

The checked-in public profile is:

```text
examples/instance/config/profiles/public-browser.yaml
```

Run:

```bash
hisys validate-public-browser-profile \
  --profile examples/instance/config/profiles/public-browser.yaml
```

Expected shape:

```text
public browser profile: valid profile_id=public-browser-beta connector_id=playwright_read_only transport_kind=playwright_live
```

The profile intentionally allows only the public beta browser posture:

```text
connector_id=playwright_read_only
transport_kind=playwright_live
mode=read_only
external_call_allowed=true
allow_credentials=false
allow_mutation=false
fixture_mode_publicly_exposed=false
experimental_transports_enabled=false
```

## 4. Prepare a scoped source connector config

The repository baseline config is conservative and disabled by default. For a
real public beta run, create a scoped runtime config that enables only
`playwright_read_only`.

Create a file such as:

```text
$HISYS_INSTANCE/config/public-source-connectors.yaml
```

Minimal content:

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

Set a shell variable for convenience:

```bash
export HISYS_SOURCE_CONFIG="$HISYS_INSTANCE/config/public-source-connectors.yaml"
```

## 5. Run readiness check, no live network call

Before a live run, verify the profile/config/import posture:

```bash
hisys public-browser-readiness \
  --instance "$HISYS_INSTANCE" \
  --config "$HISYS_SOURCE_CONFIG" \
  --profile examples/instance/config/profiles/public-browser.yaml \
  --date 20260511
```

Readiness writes:

```text
reports/run-summaries/20260511/public-browser-readiness-report.json
reports/run-summaries/20260511/public-browser-readiness-report.md
```

A ready report should have:

```text
status=ready
profile_valid=true
connector_ready=true
external_call_made=false
mutation_performed=false
publication_or_live_action_approved=false
```

If `status=blocked`, inspect `blockers` in the JSON/Markdown report. Common
blockers are missing Playwright installation, an invalid config, or a disabled
connector.

## 6. Approve the run window and enable the manual smoke gate

Only set this environment variable for the approved run window:

```bash
export HISYS_ALLOW_BROWSER_SMOKE=1
```

This is not a general production enablement flag. It is a bounded operator gate
for read-only browser collection.

## 7. Run the public browser workflow

Use `public-browser-run` for the public beta operator UX.

Example:

```bash
hisys public-browser-run \
  --instance "$HISYS_INSTANCE" \
  --config "$HISYS_SOURCE_CONFIG" \
  --profile examples/instance/config/profiles/public-browser.yaml \
  --date 20260511 \
  --request-id HISYS-REQ-PUBLIC-DEMO-001 \
  --topic "industrial x-ray tube competitive evidence" \
  --user-opinion "Operator requests governed read-only public beta evidence collection." \
  --approval-ref APPROVAL-PUBLIC-BETA-DEMO-001 \
  --follow-links \
  --max-follow-links-per-source 2 \
  --source-url https://example.com/page-a \
  --source-url https://example.org/page-b
```

Use real public URLs only when the run is explicitly approved and scoped. Do not
use login-required, paywalled, credentialed, private, or access-controlled URLs.

## 8. Read the generated outputs

The most useful operator outputs are:

```text
$HISYS_INSTANCE/reports/run-summaries/20260511/public-browser-run-summary.md
$HISYS_INSTANCE/reports/run-summaries/20260511/public-browser-run-summary.json
```

For CLI-first agents such as Hermes, use the artifact helper commands instead
of guessing paths:

```bash
hisys get-run-summary \
  --instance "$HISYS_INSTANCE" \
  --date 20260511

hisys list-run-artifacts \
  --instance "$HISYS_INSTANCE" \
  --date 20260511 \
  --request-id HISYS-REQ-PUBLIC-DEMO-001

hisys show-artifact \
  --instance "$HISYS_INSTANCE" \
  --ref data/chief-editor-final-browser-reviews/20260511/FINAL-CHIEF-REVIEW-HISYS-REQ-PUBLIC-DEMO-001-BROWSER.json
```

`show-artifact` accepts only safe relative JSON/Markdown refs under the runtime
instance.

The run also produces intermediate and review artifacts, including:

```text
reports/run-summaries/20260511/browser-investigation-report.json
data/evidence-packages/20260511/<REQUEST-ID>-BROWSER.json
data/investigation-memos/20260511/<REQUEST-ID>-BROWSER.md
data/chief-editor-reviews/20260511/CHIEF-REVIEW-<REQUEST-ID>-BROWSER.json
data/dars-browser-reviews/20260511/DARS-REVIEW-<REQUEST-ID>-BROWSER.json
data/browser-dars-revision-resolutions/20260511/REVISION-<REQUEST-ID>-BROWSER.json
data/chief-editor-final-browser-reviews/20260511/FINAL-CHIEF-REVIEW-<REQUEST-ID>-BROWSER.json
```

## 9. Interpret the final decision

The expected successful final review decision is bounded:

```text
decision=accept_for_human_reviewed_use
publication_or_live_action_approved=false
human_approval_required_for_consequential_use=true
action_taken=none
mutation_performed=false
```

This means Hisys judged the local evidence/review package acceptable for human
review. It does **not** mean Hisys approved publication, customer outreach,
trading, purchasing, uploading, posting, vault writing, or any other live
consequential action.

## 10. Manual gate-by-gate debugging

If the wrapper fails, run the gates manually in order:

```text
browser-investigate-topic
  -> review-browser-investigation
  -> request-browser-dars-review
  -> resolve-browser-dars-revisions
  -> final-review-browser-investigation
```

The shorter quickstart contains the manual commands:

```text
docs/public/browser-quickstart.md
```

## Troubleshooting

### `public-browser-readiness` says Playwright is unavailable

Run:

```bash
pip install -e ".[browser]"
python -m playwright install chromium
```

Then run readiness again.

### Readiness says connector is not ready

Check the config passed to `--config`. For public beta, `playwright_read_only`
must be enabled and read-only, with `external_call_allowed: true`, no credentials,
and no mutations.

### Run blocks before accessing a URL

Expected. Hisys blocks if the approval/env/config/domain gates are not satisfied.
Check the generated run summary and source-connector decision artifacts.

### Final review does not accept

Read the DARS review and revision-resolution artifact. The usual cause is
insufficient evidence breadth or missing independent corroboration. Add approved,
read-only source URLs and rerun within a governed scope.

## Hard public beta limits

Do not use this workflow for:

```text
login automation
credentialed browsing
form submission
posting/uploading/purchasing
CAPTCHA or access-control bypass
proxy rotation or stealth scraping
unrestricted autonomous web automation
automatic publication or consequential action
```

Camoufox/Camoufox-like transport is not the public beta default. The public beta
default is Playwright Chromium through `playwright_read_only`.
