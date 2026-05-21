# M24 — Real OSS Comparison and License Workflow PREP Task Plan

> **Row:** This document is the artifact produced by Ralph row
> `M24-REAL-OSS-LICENSE-WORKFLOW-PREP`. Subsequent rows
> `M24-REAL-OSS-LICENSE-WORKFLOW-RED-GREEN` and
> `M24-REAL-OSS-LICENSE-WORKFLOW-GATE` follow under this same M24 plan and
> the same docs/control-only opening boundary.

> **For Hermes/Ralph:** Use `software-development:test-driven-development` for
> every code-bearing task. This file is the document-RED/Prepare artifact for
> the M24 real OSS comparison and license workflow line, authored after the
> M24 authorization checkpoint at `27e45c0 docs: open m24 oss license workflow
> prep` and the parent plan `docs/plans/m24-real-oss-comparison-license-
> workflow-plan.md`. The M24 workflow line is **planning/validator-only**: it
> does **not** authorize network fetch, real OSS clone, credential lookup,
> live OSS API access, license-text capture, license adjudication,
> subagent execution, LSP subprocess spawning, package install, publication,
> deployment, or raw upstream source archival.

**Goal:** Add a pure, local-only, advisory **planning validator** that pins
the shape of a future "real OSS comparison and license adjudication" workflow
without executing any step of it. The validator accepts an `OssLicenseWorkflowPacket`
describing approved-repository **declarations** (placeholder identifiers
only), a provenance record schema, retention/cleanup policy, license
metadata policy, source-ingestion policy, and a human-review handoff. It
returns a deterministic `ConfigValidationReport` plus an
`OssLicenseWorkflowReport` and **always emits a standing warning**
(`live_workflow_not_implemented`) so callers cannot misinterpret schema
validity as authority to clone, fetch, capture license text, or adjudicate.

**Architecture:** Add a new pure-Python module
`src/hisys/operations/real_oss_license_workflow.py` exposing:

1. A Pydantic `ApprovedRepositoryDeclaration` record describing one caller-
   supplied **placeholder** approval entry:
   - `repository_id` matching `^[a-z][a-z0-9_\-]{1,63}$`
   - `repository_label` (human-readable bounded ASCII)
   - `repository_url_placeholder` — must start with `placeholder://`. The
     validator rejects any value matching real URL schemes including
     `http://`, `https://`, `git://`, `git@`, `git+ssh://`, `git+https://`,
     `ssh://`, `ftp://`, `gopher://`, `file://`, `pkg:`, `oci://`, or any
     URL-like form containing a real hostname/domain such as `github.com`,
     `gitlab.com`, `bitbucket.org`, `sourceforge.net`, `pypi.org`,
     `npmjs.com`, `crates.io`, `rubygems.org`, `repo1.maven.org`,
     `golang.org`, `go.dev`, `pkg.go.dev`, `huggingface.co`, `gitee.com`,
     `codeberg.org`, `launchpad.net`, `code.google.com`, `kernel.org`. The
     placeholder is **not** a fetchable URL.
   - `commit_or_tag_placeholder` — opaque caller string (e.g.,
     `placeholder-commit-aaaaaaa` or `placeholder-tag-v0.0.0`). Must not
     match a real 40-character hex SHA pattern with any real provider in
     the same packet.
   - `operator_approval_ref` — path ref under `docs/` only, sanitized
     against the existing unsafe-ref rule (`..`, absolute path, empty).
   - `approval_timestamp_placeholder` — ISO-8601-shaped placeholder or
     `placeholder-YYYYMMDD` literal.
   - `license_tag_placeholder` — one of an allowlisted set of metadata
     tags (`MIT`, `Apache-2.0`, `BSD-2-Clause`, `BSD-3-Clause`,
     `ISC`, `MPL-2.0`, `GPL-2.0-or-later`, `GPL-3.0-or-later`,
     `LGPL-2.1-or-later`, `LGPL-3.0-or-later`, `AGPL-3.0-or-later`,
     `Unlicense`, `CC0-1.0`, `n/a`). A `license_text_placeholder` field is
     **forbidden** so this declaration cannot carry a license body.
   - Sorted `local_fixture_refs: tuple[str, ...]` — paths under
     `tests/fixtures/` describing the in-test approval surface only.
   - Optional `notes` — bounded ASCII, max 1024 characters.

2. A Pydantic `ProvenanceRecordSchema` record declaring the fields that
   **a future provenance record** (not written by this validator) must
   carry: `repository_url_placeholder_field`, `commit_or_tag_field`,
   `retrieval_command_placeholder_field`, `operator_approval_ref_field`,
   `retrieval_timestamp_placeholder_field`. No provenance record is
   produced by this milestone. The schema is metadata only.

3. A Pydantic `RetentionPolicy` record:
   - `cache_directory_placeholder` — must start with
     `placeholder-cache-dir/`.
   - `max_age_days` integer in `[1, 365]`.
   - `cleanup_command_placeholder` — opaque caller string; no shell tokens
     beyond `placeholder-` prefix vocabulary.
   - `cleanup_responsibility` enum: `operator_run_manually` (the only
     allowed value in this opening checkpoint). The validator rejects any
     `automated_cleanup` value.

4. A Pydantic `LicenseMetadataPolicy` record:
   - `allowed_license_tags` — sorted tuple of allowlisted tags from the
     `license_tag_placeholder` allowlist above.
   - `forbid_license_text_capture: bool = True` — must be `True`; the
     validator rejects `False`.
   - `forbid_license_adjudication_claim: bool = True` — must be `True`;
     the validator rejects `False`.
   - `human_review_required: bool = True` — must be `True`.

5. A Pydantic `SourceIngestionPolicy` record:
   - `forbid_raw_source_archival: bool = True` — must be `True`.
   - `forbid_diff_hunk_archival: bool = True` — must be `True`.
   - `forbid_raw_diagnostic_archival: bool = True` — must be `True`.
   - `ingestion_responsibility` enum: `operator_run_manually` (the only
     allowed value in this opening checkpoint).
   - `allowed_in_product_artifacts` — sorted tuple of declared
     non-source identifier categories (e.g., `category_refs`,
     `license_tags`, `repository_id`, `placeholder_url`, `placeholder_commit`,
     `placeholder_timestamp`). The validator rejects entries outside this
     allowlist.

6. A Pydantic `HumanReviewHandoff` record:
   - `review_owner` string matching `^[a-z][a-z0-9_\-]{1,63}$`.
   - `review_inbox_ref` — `docs/`-relative path ref only.
   - `review_required_before` — sorted tuple of operation tokens from the
     allowlist `network_fetch`, `repository_clone`, `license_text_capture`,
     `license_adjudication`, `raw_source_archival`,
     `live_workflow_execution`. Empty tuple is rejected
     (`human_review_handoff_required`).

7. A Pydantic `OssLicenseWorkflowPacket` record carrying:
   - `workflow_id` matching `^[a-z][a-z0-9_\-]{1,63}$`
   - `approval_ref` (path ref under `docs/` only, sanitized)
   - `operator_id` matching the same slug pattern as `workflow_id`
   - sorted `approved_repository_declarations: tuple[ApprovedRepositoryDeclaration, ...]`
   - `provenance_record_schema: ProvenanceRecordSchema`
   - `retention_policy: RetentionPolicy`
   - `license_metadata_policy: LicenseMetadataPolicy`
   - `source_ingestion_policy: SourceIngestionPolicy`
   - `human_review_handoff: HumanReviewHandoff`
   - `live_workflow_authorized: bool` — must be `False`. The validator
     **rejects** `True` with `live_workflow_authority_not_allowed`.

8. A Pydantic `OssLicenseWorkflowReport` record holding:
   - `schema_id = "hisys.oss_license_workflow.v1"`
   - `date` (`YYYYMMDD`, caller-supplied)
   - `current_head_short: str | None` (caller-supplied; never read from
     `.git/`)
   - `workflow_id`
   - sorted `declared_repository_ids: tuple[str, ...]`
   - sorted `declared_license_tags: tuple[str, ...]`
   - sorted `human_review_tokens: tuple[str, ...]`
   - sorted `unsafe_refs: tuple[str, ...]`
   - sorted `unsafe_repository_ids: tuple[str, ...]`
   - `declared_repository_count: int`
   - the existing advisory flag set: `advisory_only=True`,
     `requires_human_review=True`, `external_call_made=False`,
     `mutation_performed=False`, `raw_source_content_persisted=False`,
     `live_external_action_authorized=False`,
     `allowed_actions="advisory_only"`,
     `live_workflow_executed=False`,
     `license_text_captured=False`,
     `license_adjudicated=False`.

9. A pure validator
   `validate_real_oss_license_workflow_packet(packet, *, config_ref, now=None)`
   returning a deterministic `ConfigValidationReport` whose `schema_id`
   matches the report. The validator runs only the rules listed below and
   **always** appends the deterministic warning
   `live_workflow_not_implemented` to every valid packet.

10. A pure builder
    `build_real_oss_license_workflow_report(*, packet, date, current_head_short=None)`
    that returns an `OssLicenseWorkflowReport`, classifies refs through the
    same unsafe-ref rule as M21.6/M22/M23 (`..`, absolute path, empty ->
    unsafe), and computes counts. The builder reads no file bodies,
    performs no globbing of `runtime-boundary/`, does not consult `.git/`,
    and does not contact the network.

11. A writer
    `write_real_oss_license_workflow_report(*, instance_root, date, workflow_id, report)`
    that persists JSON + Markdown **only** under
    `runtime-boundary/oss-license-workflow/<YYYYMMDD>/<WORKFLOW_ID>.{json,md}`
    through the existing `resolve_instance_runtime_ref` chokepoint. The
    writer never writes outside that partition.

Reuse the `_DATE_PATTERN`, `resolve_instance_runtime_ref`, and unsafe-ref
rule from `src/hisys/operations/codebase_analysis.py` and
`src/hisys/operations/oss_comparison_adapter.py`. Reuse the
`ConfigValidationIssue` / `ConfigValidationReport` shape from
`src/hisys/config/validation.py` (the same shape used by M-DARS-BE-1 and
M-DARS-BE-5). Mirror the writer convention shared by
`change_impact.py`, `architecture_candidates.py`,
`codebase_map_freshness.py`, `codebase_evidence_portfolio.py`, and
`oss_comparison_adapter.py`. No new dependency, no network call, no model
invocation, no credential resolution, no destructive Git, no remote push,
no `git log` execution, no CLI argument expansion in this RED-GREEN
increment (a thin CLI wrapper is deferred), no raw source archival, no
package installation, and no `subprocess` call.

**Tech Stack:** Python 3.11, regex, pathlib, Pydantic v2 for the
record/report shapes, pytest. No new dependency.

**Context Packet:** Required source handles:

- `docs/plans/m24-real-oss-comparison-license-workflow-plan.md` (parent
  M24 plan; pins the M24 authorization boundary and the initial M24 task
  queue).
- `docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.39.md`
  (user authorization record `go for m24`; non-claims list; allowed scope
  list).
- `roadmap.md` real OSS comparison and license adjudication section
  (scope to define before implementation; safety boundary; related
  current surfaces).
- `docs/plans/m23-oss-comparison-adapter-implementation-tasks.md` (sister
  fixture-local OSS adapter PREP/RED/GREEN shape; mirror caller-supplied
  inputs, no crawling, advisory-only output, set-based comparison; M24
  does **not** import or change M23 record shapes).
- `docs/plans/m23-advanced-codebase-adapter-integration-plan.md`
  (recorded M23 authorization boundary; pinned the OSS adapter as
  fixture-local only).
- `src/hisys/operations/oss_comparison_adapter.py` (analogous Pydantic
  shape, `_LINE_LABEL_PATTERN`, `_DATE_PATTERN`, `_is_unsafe_ref`,
  `_normalize`, writer chokepoint).
- `src/hisys/operations/codebase_analysis.py`
  (`resolve_instance_runtime_ref` chokepoint).
- `src/hisys/operations/codebase_evidence_portfolio.py`
  (`EvidenceLineRef`, `_LINE_LABEL_PATTERN`, `_DATE_PATTERN`,
  `_is_unsafe_ref`, writer chokepoint).
- `src/hisys/config/validation.py` (`ConfigValidationIssue`,
  `ConfigValidationReport` deterministic shape).
- `src/hisys/agents/dars_remote_subscription_policy.py` (sibling
  fail-closed validator pattern with a standing `not_implemented`
  warning; M-DARS-BE-5).
- `docs/contracts/dars-remote-subscription-backend-policy.md` (sibling
  contract that pins deterministic issue/warning codes; M24 mirrors the
  same fail-closed contract shape without reusing the schema id).
- `docs/traceability/README.md` (controlled traceability anchor; an
  `M24-REAL-OSS-LICENSE-WORKFLOW-RED-GREEN` row is appended only in the
  implementation increment).
- `docs/milestone-bootstrap/profile.yaml` (`next_safe_task` advances to
  `M24-REAL-OSS-LICENSE-WORKFLOW-RED-GREEN` after this PREP increment
  commits).
- `tests/unit/test_governance_docs_current_state.py` (governance current
  state pins the new `profile_version` and `next_safe_task` strings).
- `ralph.md` Section 16 + Reflection Log (PREP/RED/GREEN/GATE
  checkpoints).

**Boundary Record:** This Prepare packet performs only docs/control
writes. Subsequent rows perform fixture-local test/code edits inside the
M24 authorization boundary recorded in `ralph.md` Section 16 and
`docs/plans/m24-real-oss-comparison-license-workflow-plan.md`. **Not
authorized** in any M24 increment without a separate human gate:
network fetch, real OSS repository clone, package installation,
license-text capture, raw OSS source archival, credential lookup, live
OSS API access, secret capture, subagent execution, LSP subprocess
spawning, publication / deployment / release, remote configuration
change, force push, destructive Git/history actions, mutation of
non-fixture user/live data, raw source bodies inside fixture
descriptors, real-URL placeholders, real-host placeholders, repair /
deletion / quarantine of artifacts under inspection, or live-provider
DARS completion claim. The validator and report are advisory only and
never claim license compliance, fitness, deployment readiness, or
authorization for live action.

---

## Accepted decisions

1. **Caller-supplied placeholders only.** All repository identifiers,
   URLs, commits, tags, timestamps, retention paths, and license tags
   are caller-supplied placeholder strings. The validator does not crawl
   `tests/fixtures/`, does not glob `docs/`, does not call `subprocess`,
   does not run `git`, does not contact the network, does not import
   or install any OSS package, and does not consult `.git/`.
2. **No `date.today()` use.** The partition `date` and
   `current_head_short` are supplied by the caller. The builder never
   reads the system clock or `.git/`. `expires_at`-style fields are
   absent from this opening packet because no clone/fetch lifetime
   exists yet.
3. **Placeholder URLs only.** `repository_url_placeholder` must start
   with `placeholder://`. The validator rejects any real-URL scheme
   (`http://`, `https://`, `git://`, `git@`, `git+ssh://`,
   `git+https://`, `ssh://`, `ftp://`, `gopher://`, `file://`, `pkg:`,
   `oci://`) and any real-host token (`github.com`, `gitlab.com`,
   `bitbucket.org`, `sourceforge.net`, `pypi.org`, `npmjs.com`,
   `crates.io`, `rubygems.org`, `repo1.maven.org`, `golang.org`,
   `go.dev`, `pkg.go.dev`, `huggingface.co`, `gitee.com`,
   `codeberg.org`, `launchpad.net`, `code.google.com`, `kernel.org`).
4. **No license text.** `license_tag_placeholder` is metadata only.
   `LicenseMetadataPolicy.forbid_license_text_capture` and
   `LicenseMetadataPolicy.forbid_license_adjudication_claim` must both
   be `True`. The validator rejects any deviation.
5. **Operator-run cleanup only.** `RetentionPolicy.cleanup_responsibility`
   must equal `operator_run_manually`. Automated cleanup is forbidden in
   this opening checkpoint.
6. **Operator-run ingestion only.**
   `SourceIngestionPolicy.ingestion_responsibility` must equal
   `operator_run_manually`. The policy declares only allowlisted
   non-source identifier categories.
7. **Standing not-implemented warning.** Every valid packet emits the
   deterministic warning `live_workflow_not_implemented` so a green
   validator result cannot be misread as authority to clone, fetch,
   capture, adjudicate, or claim license compliance.
8. **No deletion/repair authority.** The builder and writer never
   rewrite, delete, regenerate, or quarantine code, tests, docs,
   runtime-boundary artifacts, or fixture sources; the writer only
   writes its own runtime-boundary partition.
9. **Advisory only.** The report carries `advisory_only=True`,
   `requires_human_review=True`, `external_call_made=False`,
   `mutation_performed=False`, `raw_source_content_persisted=False`,
   `live_external_action_authorized=False`,
   `allowed_actions="advisory_only"`, `live_workflow_executed=False`,
   `license_text_captured=False`, `license_adjudicated=False`.
10. **No CLI in this increment.** A `hisys real-oss-license-workflow`
    subcommand is `M24-REAL-OSS-LICENSE-WORKFLOW-CLI` work (deferred
    after the pure builder is stable). `M24-REAL-OSS-LICENSE-WORKFLOW-
    RED-GREEN` ships only the pure module, validator, builder, and
    writer.
11. **Anchor reuse, not anchor mutation.** M24 references the M23 OSS
    adapter and the M22 codebase evidence portfolio by path/refs only.
    It does not import M22/M23 record types and does not change the
    `hisys.oss_comparison_adapter.v1` report shape.
12. **Bounded reads.** The builder reads no file bodies. Ref strings
    are sanitized against the same unsafe-ref rule used in M21.6/M22/M23
    (`_is_unsafe_ref`-style: absolute paths, `..` traversal, or empty
    strings are rejected as unsafe). Notes are clamped to max 1024
    characters and printable ASCII so a malformed fixture cannot smuggle
    binary content through `notes`.
13. **Traceability required.** An
    `M24-REAL-OSS-LICENSE-WORKFLOW-RED-GREEN` traceability row is
    appended only in the implementation increment. Append a Reflection
    Log entry plus Resume checkpoint to `ralph.md` for every M24
    checkpoint.

---

## Task 0: Reconstruct baseline before any edit

**Objective:** Confirm the M24 authorization commit and PREP packet are
current, the working tree is clean, and the M22/M23/DARS/governance
focused gates remain green.

**Commands:**

```bash
git status --short --branch
git log --oneline -5
PYTHONPATH=src pytest tests/unit/test_codebase_evidence_portfolio.py tests/unit/test_oss_comparison_adapter.py tests/unit/test_lsp_adapter.py tests/unit/test_change_impact.py tests/unit/test_architecture_candidates.py tests/unit/test_code_analysis_pass_contract.py tests/unit/test_subagent_evidence_collector_protocol.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py tests/unit/test_dars_remote_subscription_dispatch.py -q
PYTHONPATH=src pytest tests/unit/test_governance_docs_current_state.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:** branch `dars`, HEAD at or after the M24-PREP commit; focused
M22/M21/M23 gate passes; DARS critic-panel + remote subscription dispatch
focused regression passes; governance current-state passes with
`profile_version == "v0.0.40"` and
`next_safe_task == "M24-REAL-OSS-LICENSE-WORKFLOW-RED-GREEN"`;
traceability validator OK; secret scan `hit_count=0`; `git diff --check`
clean.

If any expected outcome diverges, stop and re-run QUEUE-REFILL-PREP
before continuing.

---

## Task 1: RED — pure planning validator and builder reject a live-authority packet and accept a fully placeholder packet with a standing warning

**Objective:** Add a failing pytest that constructs in-memory
`OssLicenseWorkflowPacket` instances (one fully valid placeholder packet
and a battery of negative packets) plus an `OssLicenseWorkflowReport`,
calls `validate_real_oss_license_workflow_packet` and
`build_real_oss_license_workflow_report`, and asserts the deterministic
issue codes, the standing `live_workflow_not_implemented` warning, the
advisory boundary flags, and the writer round-trip. The test must fail
before the production module exists.

**Files:**

- Create: `tests/unit/test_real_oss_license_workflow.py`
- (No fixtures required; descriptors are inline placeholder strings.)

**Test sketch (illustrative; minor naming may evolve during RED):**

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.operations.real_oss_license_workflow import (
    ApprovedRepositoryDeclaration,
    HumanReviewHandoff,
    LicenseMetadataPolicy,
    OssLicenseWorkflowPacket,
    OssLicenseWorkflowReport,
    ProvenanceRecordSchema,
    RetentionPolicy,
    SourceIngestionPolicy,
    build_real_oss_license_workflow_report,
    validate_real_oss_license_workflow_packet,
    write_real_oss_license_workflow_report,
)


def _placeholder_declaration() -> ApprovedRepositoryDeclaration:
    return ApprovedRepositoryDeclaration(
        repository_id="placeholder-ref-impl",
        repository_label="Placeholder reference implementation",
        repository_url_placeholder="placeholder://approved-ref-impl",
        commit_or_tag_placeholder="placeholder-commit-0000000",
        operator_approval_ref="docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.39.md",
        approval_timestamp_placeholder="placeholder-20260522",
        license_tag_placeholder="MIT",
        local_fixture_refs=("tests/fixtures/oss/approved/placeholder-ref-impl.json",),
        notes="Placeholder only; no real upstream repository is referenced.",
    )


def _valid_packet() -> OssLicenseWorkflowPacket:
    return OssLicenseWorkflowPacket(
        workflow_id="placeholder-m24-planning",
        approval_ref="docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.39.md",
        operator_id="placeholder-operator",
        approved_repository_declarations=(_placeholder_declaration(),),
        provenance_record_schema=ProvenanceRecordSchema(),
        retention_policy=RetentionPolicy(
            cache_directory_placeholder="placeholder-cache-dir/m24",
            max_age_days=30,
            cleanup_command_placeholder="placeholder-cleanup-script",
            cleanup_responsibility="operator_run_manually",
        ),
        license_metadata_policy=LicenseMetadataPolicy(
            allowed_license_tags=("Apache-2.0", "BSD-3-Clause", "MIT", "n/a"),
        ),
        source_ingestion_policy=SourceIngestionPolicy(
            allowed_in_product_artifacts=(
                "category_refs",
                "license_tags",
                "placeholder_commit",
                "placeholder_timestamp",
                "placeholder_url",
                "repository_id",
            ),
            ingestion_responsibility="operator_run_manually",
        ),
        human_review_handoff=HumanReviewHandoff(
            review_owner="placeholder-reviewer",
            review_inbox_ref="docs/runbooks/m24-real-oss-license-workflow-review.md",
            review_required_before=(
                "license_adjudication",
                "license_text_capture",
                "live_workflow_execution",
                "network_fetch",
                "raw_source_archival",
                "repository_clone",
            ),
        ),
        live_workflow_authorized=False,
    )


def test_valid_packet_emits_standing_not_implemented_warning() -> None:
    packet = _valid_packet()
    report = validate_real_oss_license_workflow_packet(
        packet,
        config_ref="docs/plans/m24-real-oss-comparison-license-workflow-prep-tasks.md",
    )
    assert report.schema_id == "hisys.oss_license_workflow.v1"
    assert report.issues == ()
    assert any(
        warning.code == "live_workflow_not_implemented"
        for warning in report.warnings
    )


@pytest.mark.parametrize(
    "url_override,expected_code",
    [
        ("https://github.com/example/repo", "real_repository_url_not_allowed_in_planning"),
        ("git@github.com:example/repo.git", "real_repository_url_not_allowed_in_planning"),
        ("ssh://git@gitlab.com/example/repo", "real_repository_url_not_allowed_in_planning"),
        ("ftp://example.com/repo", "real_repository_url_not_allowed_in_planning"),
        ("file:///tmp/repo", "real_repository_url_not_allowed_in_planning"),
        ("pkg:pypi/example@1.0.0", "real_repository_url_not_allowed_in_planning"),
        ("oci://registry.example.com/repo", "real_repository_url_not_allowed_in_planning"),
    ],
)
def test_real_url_schemes_rejected(url_override: str, expected_code: str) -> None:
    packet = _valid_packet()
    bad_declaration = _placeholder_declaration().model_copy(
        update={"repository_url_placeholder": url_override}
    )
    packet = packet.model_copy(
        update={"approved_repository_declarations": (bad_declaration,)}
    )
    report = validate_real_oss_license_workflow_packet(
        packet,
        config_ref="docs/plans/m24-real-oss-comparison-license-workflow-prep-tasks.md",
    )
    assert any(issue.code == expected_code for issue in report.issues)


def test_live_workflow_authority_rejected() -> None:
    packet = _valid_packet().model_copy(update={"live_workflow_authorized": True})
    report = validate_real_oss_license_workflow_packet(
        packet,
        config_ref="docs/plans/m24-real-oss-comparison-license-workflow-prep-tasks.md",
    )
    assert any(
        issue.code == "live_workflow_authority_not_allowed"
        for issue in report.issues
    )


def test_license_text_capture_rejected() -> None:
    packet = _valid_packet()
    packet = packet.model_copy(
        update={
            "license_metadata_policy": LicenseMetadataPolicy(
                allowed_license_tags=("MIT",),
                forbid_license_text_capture=False,
                forbid_license_adjudication_claim=True,
                human_review_required=True,
            ),
        }
    )
    report = validate_real_oss_license_workflow_packet(
        packet,
        config_ref="docs/plans/m24-real-oss-comparison-license-workflow-prep-tasks.md",
    )
    assert any(
        issue.code == "license_text_capture_not_allowed_in_planning"
        for issue in report.issues
    )


def test_license_adjudication_claim_rejected() -> None:
    packet = _valid_packet()
    packet = packet.model_copy(
        update={
            "license_metadata_policy": LicenseMetadataPolicy(
                allowed_license_tags=("MIT",),
                forbid_license_text_capture=True,
                forbid_license_adjudication_claim=False,
                human_review_required=True,
            ),
        }
    )
    report = validate_real_oss_license_workflow_packet(
        packet,
        config_ref="docs/plans/m24-real-oss-comparison-license-workflow-prep-tasks.md",
    )
    assert any(
        issue.code == "license_adjudication_claim_not_allowed_in_planning"
        for issue in report.issues
    )


def test_automated_cleanup_rejected() -> None:
    packet = _valid_packet()
    packet = packet.model_copy(
        update={
            "retention_policy": RetentionPolicy(
                cache_directory_placeholder="placeholder-cache-dir/m24",
                max_age_days=30,
                cleanup_command_placeholder="placeholder-cleanup-script",
                cleanup_responsibility="automated_cleanup",
            ),
        }
    )
    report = validate_real_oss_license_workflow_packet(
        packet,
        config_ref="docs/plans/m24-real-oss-comparison-license-workflow-prep-tasks.md",
    )
    assert any(
        issue.code == "automated_cleanup_not_allowed"
        for issue in report.issues
    )


def test_human_review_handoff_required() -> None:
    packet = _valid_packet()
    packet = packet.model_copy(
        update={
            "human_review_handoff": HumanReviewHandoff(
                review_owner="placeholder-reviewer",
                review_inbox_ref="docs/runbooks/m24-real-oss-license-workflow-review.md",
                review_required_before=(),
            ),
        }
    )
    report = validate_real_oss_license_workflow_packet(
        packet,
        config_ref="docs/plans/m24-real-oss-comparison-license-workflow-prep-tasks.md",
    )
    assert any(
        issue.code == "human_review_handoff_required"
        for issue in report.issues
    )


def test_build_and_write_workflow_report(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    packet = _valid_packet()
    report = build_real_oss_license_workflow_report(
        packet=packet,
        date="20260522",
        current_head_short="27e45c0",
    )
    assert report.schema_id == "hisys.oss_license_workflow.v1"
    assert report.workflow_id == "placeholder-m24-planning"
    assert report.declared_repository_ids == ("placeholder-ref-impl",)
    assert report.declared_license_tags == ("MIT",)
    assert report.declared_repository_count == 1
    assert report.live_workflow_executed is False
    assert report.license_text_captured is False
    assert report.license_adjudicated is False
    assert report.advisory_only is True
    assert report.requires_human_review is True
    assert report.external_call_made is False
    assert report.allowed_actions == "advisory_only"

    json_ref, md_ref = write_real_oss_license_workflow_report(
        instance_root=instance_root,
        date="20260522",
        workflow_id=packet.workflow_id,
        report=report,
    )
    assert (
        json_ref
        == "runtime-boundary/oss-license-workflow/20260522/placeholder-m24-planning.json"
    )
    assert (
        md_ref
        == "runtime-boundary/oss-license-workflow/20260522/placeholder-m24-planning.md"
    )
    payload = json.loads((instance_root / json_ref).read_text(encoding="utf-8"))
    assert payload["schema_id"] == "hisys.oss_license_workflow.v1"
    assert payload["live_workflow_executed"] is False
```

**Verify RED:**

```bash
PYTHONPATH=src pytest tests/unit/test_real_oss_license_workflow.py -q
```

**Expected RED:**
`ModuleNotFoundError: No module named 'hisys.operations.real_oss_license_workflow'`
because the module has not been created yet.

---

## Task 2: GREEN — implement minimal planning validator, builder, and writer

**Objective:** Add the smallest production logic that satisfies the RED
tests, the writer invariant, and the standing
`live_workflow_not_implemented` warning.

**Files:**

- Create: `src/hisys/operations/real_oss_license_workflow.py`

**Module shape (illustrative; minor naming may evolve during GREEN):**

```python
"""Advisory real-OSS comparison/license workflow planning validator (M24).

Planning-only. The validator and builder do not clone, fetch, search,
inspect, archive, or adjudicate any real external repository or license.
They accept caller-supplied placeholder descriptors only and always emit
a standing `live_workflow_not_implemented` warning so callers cannot
misread schema validity as authority to act.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import BaseModel

from hisys.config.validation import ConfigValidationIssue, ConfigValidationReport
from hisys.operations.codebase_analysis import resolve_instance_runtime_ref

_DATE_PATTERN = re.compile(r"^\d{8}$")
_SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9_\-]{1,63}$")
_NOTES_MAX_LENGTH = 1024
_PARTITION_PREFIX = "runtime-boundary/oss-license-workflow"

_FORBIDDEN_URL_SCHEMES = (
    "http://",
    "https://",
    "git://",
    "git@",
    "git+ssh://",
    "git+https://",
    "ssh://",
    "ftp://",
    "gopher://",
    "file://",
    "pkg:",
    "oci://",
)

_FORBIDDEN_URL_HOSTS = (
    "github.com",
    "gitlab.com",
    "bitbucket.org",
    "sourceforge.net",
    "pypi.org",
    "npmjs.com",
    "crates.io",
    "rubygems.org",
    "repo1.maven.org",
    "golang.org",
    "go.dev",
    "pkg.go.dev",
    "huggingface.co",
    "gitee.com",
    "codeberg.org",
    "launchpad.net",
    "code.google.com",
    "kernel.org",
)

_LICENSE_TAG_ALLOWLIST = (
    "AGPL-3.0-or-later",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "CC0-1.0",
    "GPL-2.0-or-later",
    "GPL-3.0-or-later",
    "ISC",
    "LGPL-2.1-or-later",
    "LGPL-3.0-or-later",
    "MIT",
    "MPL-2.0",
    "Unlicense",
    "n/a",
)

_HUMAN_REVIEW_TOKEN_ALLOWLIST = (
    "license_adjudication",
    "license_text_capture",
    "live_workflow_execution",
    "network_fetch",
    "raw_source_archival",
    "repository_clone",
)

_SOURCE_INGESTION_ALLOWLIST = (
    "category_refs",
    "license_tags",
    "placeholder_commit",
    "placeholder_timestamp",
    "placeholder_url",
    "repository_id",
)

# Record types omitted here for brevity; mirror the test sketch in Task 1.
```

**Verify GREEN:**

```bash
PYTHONPATH=src pytest tests/unit/test_real_oss_license_workflow.py -q
```

**Expected GREEN:** all RED test cases now pass.

---

## Task 3: focused regression and documentation

**Objective:** Confirm the new module does not affect existing M22/M23/
DARS/governance surfaces, and pin the contract in a sibling docs entry.

**Files:**

- Create: `docs/contracts/real-oss-license-workflow.md` — concise
  contract document modeled after
  `docs/contracts/dars-remote-subscription-backend-policy.md`. It must
  state: schema id, validator surface, required record types, allowed
  license-tag allowlist, allowed human-review-token allowlist, forbidden
  URL schemes/hosts, deterministic issue codes, the standing
  `live_workflow_not_implemented` warning, advisory-only boundary, and
  explicit stop conditions for any later clone/fetch/license-text/
  adjudication/raw-source row.
- Update (RED-GREEN row only): prepend an
  `M24-REAL-OSS-LICENSE-WORKFLOW-RED-GREEN` row to
  `docs/traceability/README.md` linking the validator module, the test
  file, the new contract doc, and the no-network / no-credential /
  no-license-text / no-adjudication invariants.

**Validation commands:**

```bash
PYTHONPATH=src pytest tests/unit/test_real_oss_license_workflow.py tests/unit/test_codebase_evidence_portfolio.py tests/unit/test_oss_comparison_adapter.py tests/unit/test_lsp_adapter.py tests/unit/test_change_impact.py tests/unit/test_architecture_candidates.py tests/unit/test_code_analysis_pass_contract.py tests/unit/test_subagent_evidence_collector_protocol.py tests/unit/test_codebase_map_freshness.py tests/unit/test_runtime_boundary_consistency.py tests/unit/test_traceability_coverage.py -q
PYTHONPATH=src pytest tests/unit/test_dars_critic_panel_cli.py tests/unit/test_dars_critic_panel_adapters.py tests/unit/test_dars_critic_panel_runtime.py tests/unit/test_dars_critic_panel_tool_execution_runtime.py tests/unit/test_dars_critic_panel_execution_graph_plan.py tests/unit/test_dars_remote_subscription_dispatch.py -q
PYTHONPATH=src pytest tests/unit/test_governance_docs_current_state.py -q
PYTHONPATH=src pytest -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
```

**Expected:** all focused gates pass; project-wide pytest passes; the
governance current-state remains green after `profile_version` advances
to `v0.0.41` and `next_safe_task` advances to
`M24-REAL-OSS-LICENSE-WORKFLOW-GATE`; traceability validator OK; secret
scan `hit_count=0`; `git diff --check` clean.

---

## Task 4: Ralph reflection and resume checkpoint

**Objective:** Record the M24-REAL-OSS-LICENSE-WORKFLOW-RED-GREEN
checkpoint in `ralph.md` and advance Section 16 to
`M24-REAL-OSS-LICENSE-WORKFLOW-GATE`.

**Files:**

- Update: `ralph.md` — prepend a Reflection Log entry covering phase,
  controlled anchors, baseline, RED, GREEN, focused regression,
  documentation/traceability, quality gate result, potential issues,
  continue decision, stop condition, commit pending. Append a Resume
  checkpoint block with `- Current HEAD:` matching the HEAD prior to the
  RED-GREEN commit. Rewrite Section 16 to mark
  `M24-REAL-OSS-LICENSE-WORKFLOW-RED-GREEN` as done and the next safe
  Ralph queue target as `M24-REAL-OSS-LICENSE-WORKFLOW-GATE`.
- Update: `docs/milestone-bootstrap/profile.yaml` to `v0.0.41` with
  `next_safe_task=M24-REAL-OSS-LICENSE-WORKFLOW-GATE`,
  `next_artifact_ref` pointing at a future GATE document if planned, and
  `current_head_at_plan_creation` matching the new last
  `- Current HEAD:` line in `ralph.md`.
- Update: `tests/unit/test_governance_docs_current_state.py` to assert
  `v0.0.41` and the M24 GATE row.

---

## Out of scope for the M24-REAL-OSS-LICENSE-WORKFLOW-RED-GREEN row

- Naming or approving real repository URLs.
- Running web search, package-manager search, `git clone`, `git fetch`,
  `gh repo clone`, `curl`, `wget`, `pip install`, `npm install`, or any
  equivalent network retrieval.
- Capturing LICENSE file bodies or adjudicating license compatibility.
- Persisting raw external source, diff hunks, or third-party code
  snapshots.
- Changing the existing M23 `hisys.oss_comparison_adapter.v1` report
  contract.
- Adding a thin `hisys real-oss-license-workflow` CLI (deferred to a
  later row).
- Expanding DARS live-provider authority.
- Touching `docs/milestone-bootstrap/profile.yaml` beyond the v0.0.41
  bump and the `next_safe_task` advance.
- Promoting any placeholder URL or commit-or-tag value to a real value.
- Adding any field that grants live execution, credential resolution, or
  subagent/LSP/network access.

---

## Gate commands for this PREP row only

```bash
PYTHONPATH=src pytest tests/unit/test_governance_docs_current_state.py -q
python3 scripts/validate_traceability.py
python3 scripts/scan_secrets.py
git diff --check
git status --short --branch
```

**Expected for the PREP commit:** governance current-state passes with
`profile_version == "v0.0.40"` and
`next_safe_task == "M24-REAL-OSS-LICENSE-WORKFLOW-RED-GREEN"`;
traceability validates; secret scan reports `hit_count=0`; diff check is
clean; branch is `dars` with upstream `origin/dars`.

---

## Stop conditions for this M24 planning row

This PREP row stops and asks the user before any of:

- promoting `repository_url_placeholder` to a real URL;
- promoting `commit_or_tag_placeholder` to a real commit/tag;
- promoting `approval_timestamp_placeholder` to a wall-clock timestamp;
- writing any provenance record that records a real retrieval;
- capturing any LICENSE body or license-compatibility claim;
- enabling any automated cleanup of a cache directory;
- enabling any automated ingestion of upstream source;
- expanding the M24 line into a CLI surface or a runtime-boundary
  writer that touches paths outside
  `runtime-boundary/oss-license-workflow/`;
- crossing into credentials, vault, secrets, package install, network
  fetch/clone/search, browser/search/tool execution, subagent
  execution, LSP subprocess spawning, publication/deployment/release,
  destructive Git/history action, force push, new or changed remote
  configuration, mutation of non-fixture/live user data, raw upstream
  source archival, raw diagnostic-message archival, or live-provider
  DARS completion claim.
