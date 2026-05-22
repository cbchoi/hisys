# Real OSS comparison and license workflow planning validator (M24-RED-GREEN)

> **Status:** planning-only validator, builder, and writer. The contract
> defines the schema and fail-closed validator for a future real OSS
> comparison and license adjudication workflow. Hisys does **not** clone,
> fetch, search, inspect, archive, or adjudicate any real external
> repository or license at this milestone. Every valid packet emits a
> standing `live_workflow_not_implemented` warning so schema validity is
> never interpreted as authority to act.

## Scope

The planning packet covers only **placeholder declarations** for future
approved OSS comparison/license adjudication work. The following are
explicitly **out of scope** until separate human decisions land:

- real repository URLs of any scheme;
- real repository hosts (`github.com`, `gitlab.com`, `bitbucket.org`,
  `sourceforge.net`, `pypi.org`, `npmjs.com`, `crates.io`, `rubygems.org`,
  `repo1.maven.org`, `golang.org`, `go.dev`, `pkg.go.dev`,
  `huggingface.co`, `gitee.com`, `codeberg.org`, `launchpad.net`,
  `code.google.com`, `kernel.org`);
- network fetch, repository clone, package install, web/search/browser
  retrieval, or any equivalent live retrieval;
- LICENSE body capture or license-text retention;
- license compatibility or fitness-for-purpose adjudication claims;
- raw upstream source archival, diff-hunk archival, or raw
  diagnostic-message archival;
- automated cleanup of any cache directory;
- automated source ingestion of any kind;
- credential lookup, vault read/write, or secret capture;
- arbitrary CLI subprocess spawning;
- subagent execution or LSP subprocess spawning;
- publication, deployment, release, or remote configuration changes;
- non-fixture user/live data mutation;
- live-provider DARS execution.

## Validator surface

`validate_real_oss_license_workflow_packet(packet, *, config_ref)` returns
a deterministic `ConfigValidationReport` whose `schema_id` is
`hisys.oss_license_workflow.v1`. Even a fully valid packet emits a
deterministic `live_workflow_not_implemented` **warning** so callers
cannot interpret schema validity as live authority.

`build_real_oss_license_workflow_report(*, packet, date, current_head_short=None)`
returns a deterministic `OssLicenseWorkflowReport`. The builder reads no
file bodies, does not consult `.git/`, does not call `subprocess`, does
not contact the network, does not crawl `tests/fixtures/` or
`runtime-boundary/`, and does not read the system clock. The partition
`date` and `current_head_short` are caller-supplied.

`write_real_oss_license_workflow_report(*, instance_root, date, workflow_id, report)`
persists JSON and Markdown only under
`runtime-boundary/oss-license-workflow/<YYYYMMDD>/<WORKFLOW_ID>.{json,md}`
through the existing `resolve_instance_runtime_ref` chokepoint. The
writer never writes outside that partition. Bad-date and bad-`workflow_id`
shapes raise `ValueError`.

## Record types

- `ApprovedRepositoryDeclaration` — caller-supplied placeholder
  declaration. Required fields: `repository_id` (slug),
  `repository_url_placeholder` (must start with `placeholder://`),
  `commit_or_tag_placeholder` (must start with `placeholder-`),
  `operator_approval_ref` (docs/-relative path), `approval_timestamp_placeholder`
  (must start with `placeholder-`), `license_tag_placeholder` (SPDX
  allowlist). Optional fields: `repository_label`, `local_fixture_refs`,
  `notes` (max 1024 chars, printable ASCII only, no raw-secret tokens).
- `ProvenanceRecordSchema` — declares the field names that a future
  provenance record (not written by this milestone) must carry. No
  provenance record is produced by the validator.
- `RetentionPolicy` — declares the future cache directory under
  `placeholder-cache-dir/`, `max_age_days` in `[1, 365]`, cleanup
  command placeholder, and `cleanup_responsibility="operator_run_manually"`
  (the only allowed value at this milestone).
- `LicenseMetadataPolicy` — declares the SPDX-style license-tag
  allowlist used by declarations, plus three guard booleans that must
  all be `true`: `forbid_license_text_capture`,
  `forbid_license_adjudication_claim`, `human_review_required`.
- `SourceIngestionPolicy` — declares the allowed non-source identifier
  categories from the allowlist (`category_refs`, `license_tags`,
  `placeholder_commit`, `placeholder_timestamp`, `placeholder_url`,
  `repository_id`) plus the three guard booleans that must all be
  `true`: `forbid_raw_source_archival`, `forbid_diff_hunk_archival`,
  `forbid_raw_diagnostic_archival`. `ingestion_responsibility` must
  equal `operator_run_manually`.
- `HumanReviewHandoff` — declares a placeholder review owner slug, a
  docs-relative inbox ref, and a non-empty tuple of review tokens from
  the allowlist (`license_adjudication`, `license_text_capture`,
  `live_workflow_execution`, `network_fetch`, `raw_source_archival`,
  `repository_clone`).
- `OssLicenseWorkflowPacket` — composite intake surface holding
  `workflow_id`, `approval_ref`, `operator_id`, at least one
  declaration, the policies above, the handoff, and
  `live_workflow_authorized: bool` (must be `false`; the validator
  rejects `true`).
- `OssLicenseWorkflowReport` — bounded advisory report with
  `schema_id="hisys.oss_license_workflow.v1"`, `date`,
  `current_head_short`, `workflow_id`, sorted
  `declared_repository_ids`, sorted `declared_license_tags`, sorted
  `human_review_tokens`, sorted `unsafe_refs`, sorted
  `unsafe_repository_ids`, `declared_repository_count`, and the
  standing advisory/no-live flag set (`advisory_only=true`,
  `requires_human_review=true`, `external_call_made=false`,
  `mutation_performed=false`, `raw_source_content_persisted=false`,
  `live_external_action_authorized=false`,
  `live_workflow_executed=false`, `license_text_captured=false`,
  `license_adjudicated=false`, `allowed_actions="advisory_only"`).

## Deterministic issue codes

The validator emits the following deterministic codes:

| Code | Meaning |
|---|---|
| `missing_required_field` | At least one declaration is required |
| `invalid_workflow_id` | `workflow_id` does not match the slug pattern |
| `invalid_operator_id` | `operator_id` does not match the slug pattern |
| `unsafe_approval_ref` | `approval_ref` is absolute or contains `..` |
| `invalid_repository_id` | A declaration's `repository_id` does not match the slug pattern |
| `real_repository_url_not_allowed_in_planning` | `repository_url_placeholder` uses a real URL scheme or references a known forge/registry host |
| `invalid_commit_or_tag_placeholder` | A declaration's `commit_or_tag_placeholder` does not start with `placeholder-` |
| `invalid_approval_timestamp_placeholder` | A declaration's `approval_timestamp_placeholder` does not start with `placeholder-` |
| `license_tag_not_in_allowlist` | A `license_tag_placeholder` or `allowed_license_tags` entry is not in the SPDX-style allowlist |
| `unsafe_operator_approval_ref` | A declaration's `operator_approval_ref` is absolute or contains `..` |
| `notes_too_long` | A declaration's `notes` exceeds 1024 characters |
| `notes_contains_control_characters` | A declaration's `notes` contains control characters outside `\t\n` |
| `raw_secret_value_not_allowed` | A declaration's `notes` includes secret-like field names or secret-shaped values |
| `invalid_cache_directory_placeholder` | `cache_directory_placeholder` does not start with `placeholder-cache-dir/` |
| `invalid_retention_max_age` | `max_age_days` is not within `[1, 365]` |
| `automated_cleanup_not_allowed` | `cleanup_responsibility` is not `operator_run_manually` |
| `license_text_capture_not_allowed_in_planning` | `forbid_license_text_capture` is not `true` |
| `license_adjudication_claim_not_allowed_in_planning` | `forbid_license_adjudication_claim` is not `true` |
| `license_human_review_required_must_be_true` | `human_review_required` is not `true` |
| `automated_source_ingestion_not_allowed` | `ingestion_responsibility` is not `operator_run_manually` |
| `raw_source_archival_not_allowed_in_planning` | `forbid_raw_source_archival` is not `true` |
| `diff_hunk_archival_not_allowed_in_planning` | `forbid_diff_hunk_archival` is not `true` |
| `raw_diagnostic_archival_not_allowed_in_planning` | `forbid_raw_diagnostic_archival` is not `true` |
| `source_ingestion_category_not_in_allowlist` | An `allowed_in_product_artifacts` entry is not in the planning allowlist |
| `invalid_review_owner` | `review_owner` does not match the slug pattern |
| `unsafe_review_inbox_ref` | `review_inbox_ref` is absolute or contains `..` |
| `human_review_handoff_required` | `review_required_before` is empty |
| `human_review_token_not_in_allowlist` | A `review_required_before` entry is not in the token allowlist |
| `live_workflow_authority_not_allowed` | `live_workflow_authorized` is `true` |

And the deterministic warning:

| Code | Meaning |
|---|---|
| `live_workflow_not_implemented` | Emitted for every valid packet to declare that schema validity does not authorize any live workflow execution |

## Boundary invariants

- No `repository_url_placeholder` may carry a real URL scheme or a
  known forge/registry host token. The validator rejects all values
  outside the `placeholder://` scheme.
- No `commit_or_tag_placeholder` may match a real 40-char hex SHA shape
  paired with a real provider; the validator enforces the
  `placeholder-` prefix.
- No `approval_timestamp_placeholder` may be a wall-clock timestamp;
  the validator enforces the `placeholder-` prefix.
- No `notes` field may carry raw secret tokens or control characters.
- No flag granting clone, fetch, network, credential, publication,
  deployment, or live execution authority is allowed in the packet.
- No license text, diff hunk, raw diagnostic message, or raw upstream
  source may be archived under this milestone; the report carries
  `raw_source_content_persisted=false`, `license_text_captured=false`,
  `license_adjudicated=false`, and `live_workflow_executed=false`
  unconditionally.
- The writer partition is
  `runtime-boundary/oss-license-workflow/<YYYYMMDD>/<WORKFLOW_ID>.{json,md}`
  only.

## Relationship to other Hisys surfaces

- `src/hisys/operations/oss_comparison_adapter.py` (M23) is the
  fixture-local approved-OSS comparison adapter. M24 references the
  same caller-supplied descriptor pattern but does not import or
  modify the `hisys.oss_comparison_adapter.v1` report shape.
- `src/hisys/operations/codebase_evidence_portfolio.py` (M22) is the
  fixture-local codebase evidence portfolio. M24 does not import the
  portfolio's record types.
- `src/hisys/agents/dars_remote_subscription_policy.py` (M-DARS-BE-5)
  is the sibling fail-closed validator that informs the M24 contract
  shape: deterministic issue codes plus a standing not-implemented
  warning on valid packets.
- `roadmap.md` already declares the real OSS comparison/license
  adjudication line; M24 implements only the planning validator.

## Stop conditions

The validator and any future consumer must stop before any of:

- promoting `repository_url_placeholder` to a real URL or host;
- promoting `commit_or_tag_placeholder` to a real commit/tag value;
- promoting `approval_timestamp_placeholder` to a wall-clock
  timestamp;
- enabling automated cleanup of a cache directory;
- enabling automated source ingestion;
- capturing LICENSE body or making a license-compatibility claim;
- granting `live_workflow_authorized=true`;
- adding a CLI surface or any caller path that triggers network
  fetch/clone/search, credential resolution, package install, or
  subprocess execution;
- expanding the partition outside
  `runtime-boundary/oss-license-workflow/`;
- archiving raw upstream source, raw diagnostic messages, or diff
  hunks;
- publication, deployment, release, force push, destructive
  Git/history action, new or changed remote configuration, mutation
  of non-fixture/live user data, or live-provider DARS completion
  claim.
