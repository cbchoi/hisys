"""Advisory real-OSS comparison/license workflow planning validator (M24).

Planning-only. The validator, builder, and writer do not clone, fetch,
search, inspect, archive, or adjudicate any real external repository or
license. They accept caller-supplied placeholder descriptors only and
always emit a standing ``live_workflow_not_implemented`` warning so
callers cannot misread schema validity as authority to act.

Traceability: docs/plans/m24-real-oss-comparison-license-workflow-plan.md
and docs/plans/m24-real-oss-comparison-license-workflow-prep-tasks.md.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import BaseModel

from hisys.config.validation import (
    ConfigValidationIssue,
    ConfigValidationReport,
)
from hisys.operations.codebase_analysis import resolve_instance_runtime_ref


REAL_OSS_LICENSE_WORKFLOW_SCHEMA_ID = "hisys.oss_license_workflow.v1"

_DATE_PATTERN = re.compile(r"^\d{8}$")
_SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9_\-]{1,63}$")
_PLACEHOLDER_URL_PREFIX = "placeholder://"
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
    "bitbucket.org",
    "code.google.com",
    "codeberg.org",
    "crates.io",
    "gitee.com",
    "github.com",
    "gitlab.com",
    "go.dev",
    "golang.org",
    "huggingface.co",
    "kernel.org",
    "launchpad.net",
    "npmjs.com",
    "pkg.go.dev",
    "pypi.org",
    "repo1.maven.org",
    "rubygems.org",
    "sourceforge.net",
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

_CACHE_DIR_PREFIX = "placeholder-cache-dir/"

_RETENTION_MIN_DAYS = 1
_RETENTION_MAX_DAYS = 365

_CLEANUP_RESPONSIBILITY_ALLOWED = "operator_run_manually"
_INGESTION_RESPONSIBILITY_ALLOWED = "operator_run_manually"

# Secret detection (same shape as M-DARS-BE-5 / config/validation primitives).
_SECRET_FIELD_MARKERS = (
    "api_key",
    "apikey",
    "auth_token",
    "access_token",
    "credential",
    "password",
    "secret",
    "token",
)
_SECRET_VALUE_PATTERNS = (
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"\bsk_[A-Za-z0-9_\-]{16,}"),
    re.compile(r"\bghp_[A-Za-z0-9_\-]{16,}"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"\bhf_[A-Za-z0-9_\-]{8,}"),
)


class ApprovedRepositoryDeclaration(BaseModel):
    repository_id: str
    repository_label: str = ""
    repository_url_placeholder: str = ""
    commit_or_tag_placeholder: str = ""
    operator_approval_ref: str = ""
    approval_timestamp_placeholder: str = ""
    license_tag_placeholder: str = "n/a"
    local_fixture_refs: tuple[str, ...] = ()
    notes: str = ""


class ProvenanceRecordSchema(BaseModel):
    repository_url_placeholder_field: str = "repository_url_placeholder"
    commit_or_tag_field: str = "commit_or_tag_placeholder"
    retrieval_command_placeholder_field: str = "retrieval_command_placeholder"
    operator_approval_ref_field: str = "operator_approval_ref"
    retrieval_timestamp_placeholder_field: str = (
        "retrieval_timestamp_placeholder"
    )


class RetentionPolicy(BaseModel):
    cache_directory_placeholder: str
    max_age_days: int
    cleanup_command_placeholder: str = ""
    cleanup_responsibility: str = "operator_run_manually"


class LicenseMetadataPolicy(BaseModel):
    allowed_license_tags: tuple[str, ...] = ()
    forbid_license_text_capture: bool = True
    forbid_license_adjudication_claim: bool = True
    human_review_required: bool = True


class SourceIngestionPolicy(BaseModel):
    forbid_raw_source_archival: bool = True
    forbid_diff_hunk_archival: bool = True
    forbid_raw_diagnostic_archival: bool = True
    ingestion_responsibility: str = "operator_run_manually"
    allowed_in_product_artifacts: tuple[str, ...] = ()


class HumanReviewHandoff(BaseModel):
    review_owner: str
    review_inbox_ref: str
    review_required_before: tuple[str, ...] = ()


class OssLicenseWorkflowPacket(BaseModel):
    workflow_id: str
    approval_ref: str
    operator_id: str
    approved_repository_declarations: tuple[
        ApprovedRepositoryDeclaration, ...
    ] = ()
    provenance_record_schema: ProvenanceRecordSchema = ProvenanceRecordSchema()
    retention_policy: RetentionPolicy
    license_metadata_policy: LicenseMetadataPolicy
    source_ingestion_policy: SourceIngestionPolicy
    human_review_handoff: HumanReviewHandoff
    live_workflow_authorized: bool = False


class OssLicenseWorkflowReport(BaseModel):
    schema_id: str = REAL_OSS_LICENSE_WORKFLOW_SCHEMA_ID
    date: str
    current_head_short: str | None = None
    workflow_id: str
    declared_repository_ids: tuple[str, ...] = ()
    declared_license_tags: tuple[str, ...] = ()
    human_review_tokens: tuple[str, ...] = ()
    unsafe_refs: tuple[str, ...] = ()
    unsafe_repository_ids: tuple[str, ...] = ()
    declared_repository_count: int = 0
    advisory_only: bool = True
    requires_human_review: bool = True
    external_call_made: bool = False
    mutation_performed: bool = False
    raw_source_content_persisted: bool = False
    live_external_action_authorized: bool = False
    live_workflow_executed: bool = False
    license_text_captured: bool = False
    license_adjudicated: bool = False
    allowed_actions: str = "advisory_only"


def _is_unsafe_ref(ref: str) -> bool:
    if not ref:
        return True
    if ref.startswith("/"):
        return True
    parts = ref.replace("\\", "/").split("/")
    return any(part == ".." for part in parts)


def _has_control_characters(text: str) -> bool:
    return any((ch < " " and ch not in "\t\n") for ch in text)


def _looks_like_real_url(value: str) -> bool:
    if not value:
        return False
    lowered = value.lower()
    if not lowered.startswith(_PLACEHOLDER_URL_PREFIX):
        for scheme in _FORBIDDEN_URL_SCHEMES:
            if lowered.startswith(scheme):
                return True
        return True
    remainder = lowered[len(_PLACEHOLDER_URL_PREFIX):]
    for host in _FORBIDDEN_URL_HOSTS:
        if host in remainder:
            return True
    return False


def _has_raw_secret(text: str) -> bool:
    if not text:
        return False
    lowered = text.lower()
    for marker in _SECRET_FIELD_MARKERS:
        if marker in lowered:
            return True
    for pattern in _SECRET_VALUE_PATTERNS:
        if pattern.search(text):
            return True
    return False


def _issue(
    *, path: str, code: str, message: str, severity: str = "error"
) -> ConfigValidationIssue:
    return ConfigValidationIssue(
        path=path, severity=severity, code=code, message=message
    )


def _validate_declaration(
    decl: ApprovedRepositoryDeclaration, index: int
) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    base_path = f"approved_repository_declarations[{index}]"

    if not _SLUG_PATTERN.fullmatch(decl.repository_id):
        issues.append(
            _issue(
                path=f"{base_path}.repository_id",
                code="invalid_repository_id",
                message=(
                    "repository_id must match ^[a-z][a-z0-9_-]{1,63}$"
                ),
            )
        )

    if _looks_like_real_url(decl.repository_url_placeholder):
        issues.append(
            _issue(
                path=f"{base_path}.repository_url_placeholder",
                code="real_repository_url_not_allowed_in_planning",
                message=(
                    "repository_url_placeholder must start with "
                    "placeholder:// and must not reference any real URL "
                    "scheme or known forge/registry host"
                ),
            )
        )

    if not decl.commit_or_tag_placeholder.startswith("placeholder-"):
        issues.append(
            _issue(
                path=f"{base_path}.commit_or_tag_placeholder",
                code="invalid_commit_or_tag_placeholder",
                message=(
                    "commit_or_tag_placeholder must start with 'placeholder-'"
                ),
            )
        )

    if not decl.approval_timestamp_placeholder.startswith("placeholder-"):
        issues.append(
            _issue(
                path=f"{base_path}.approval_timestamp_placeholder",
                code="invalid_approval_timestamp_placeholder",
                message=(
                    "approval_timestamp_placeholder must start with "
                    "'placeholder-'"
                ),
            )
        )

    if decl.license_tag_placeholder not in _LICENSE_TAG_ALLOWLIST:
        issues.append(
            _issue(
                path=f"{base_path}.license_tag_placeholder",
                code="license_tag_not_in_allowlist",
                message=(
                    "license_tag_placeholder must be one of the SPDX-style "
                    "allowlisted tags"
                ),
            )
        )

    if _is_unsafe_ref(decl.operator_approval_ref):
        issues.append(
            _issue(
                path=f"{base_path}.operator_approval_ref",
                code="unsafe_operator_approval_ref",
                message=(
                    "operator_approval_ref must be a docs/-relative path "
                    "without '..' traversal or absolute paths"
                ),
            )
        )

    if len(decl.notes) > _NOTES_MAX_LENGTH:
        issues.append(
            _issue(
                path=f"{base_path}.notes",
                code="notes_too_long",
                message=(
                    f"notes must be at most {_NOTES_MAX_LENGTH} characters"
                ),
            )
        )
    if _has_control_characters(decl.notes):
        issues.append(
            _issue(
                path=f"{base_path}.notes",
                code="notes_contains_control_characters",
                message=(
                    "notes must contain only printable ASCII; "
                    "control characters are not allowed"
                ),
            )
        )
    if _has_raw_secret(decl.notes):
        issues.append(
            _issue(
                path=f"{base_path}.notes",
                code="raw_secret_value_not_allowed",
                message=(
                    "notes may not contain secret-like field names or "
                    "secret-shaped values"
                ),
            )
        )

    return issues


def _validate_retention(policy: RetentionPolicy) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    if not policy.cache_directory_placeholder.startswith(_CACHE_DIR_PREFIX):
        issues.append(
            _issue(
                path="retention_policy.cache_directory_placeholder",
                code="invalid_cache_directory_placeholder",
                message=(
                    "cache_directory_placeholder must start with "
                    f"'{_CACHE_DIR_PREFIX}'"
                ),
            )
        )
    if not (
        _RETENTION_MIN_DAYS <= policy.max_age_days <= _RETENTION_MAX_DAYS
    ):
        issues.append(
            _issue(
                path="retention_policy.max_age_days",
                code="invalid_retention_max_age",
                message=(
                    "max_age_days must be in "
                    f"[{_RETENTION_MIN_DAYS}, {_RETENTION_MAX_DAYS}]"
                ),
            )
        )
    if policy.cleanup_responsibility != _CLEANUP_RESPONSIBILITY_ALLOWED:
        issues.append(
            _issue(
                path="retention_policy.cleanup_responsibility",
                code="automated_cleanup_not_allowed",
                message=(
                    "cleanup_responsibility must equal "
                    f"'{_CLEANUP_RESPONSIBILITY_ALLOWED}'"
                ),
            )
        )
    return issues


def _validate_license_policy(
    policy: LicenseMetadataPolicy,
) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    if not policy.forbid_license_text_capture:
        issues.append(
            _issue(
                path="license_metadata_policy.forbid_license_text_capture",
                code="license_text_capture_not_allowed_in_planning",
                message=(
                    "forbid_license_text_capture must be true in the planning "
                    "row; license text capture is not authorized"
                ),
            )
        )
    if not policy.forbid_license_adjudication_claim:
        issues.append(
            _issue(
                path=(
                    "license_metadata_policy."
                    "forbid_license_adjudication_claim"
                ),
                code="license_adjudication_claim_not_allowed_in_planning",
                message=(
                    "forbid_license_adjudication_claim must be true in the "
                    "planning row; license adjudication is not authorized"
                ),
            )
        )
    if not policy.human_review_required:
        issues.append(
            _issue(
                path="license_metadata_policy.human_review_required",
                code="license_human_review_required_must_be_true",
                message="human_review_required must be true",
            )
        )
    for tag in policy.allowed_license_tags:
        if tag not in _LICENSE_TAG_ALLOWLIST:
            issues.append(
                _issue(
                    path="license_metadata_policy.allowed_license_tags",
                    code="license_tag_not_in_allowlist",
                    message=(
                        f"allowed_license_tags entry '{tag}' is not in the "
                        "SPDX-style allowlist"
                    ),
                )
            )
    return issues


def _validate_source_ingestion(
    policy: SourceIngestionPolicy,
) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    if policy.ingestion_responsibility != _INGESTION_RESPONSIBILITY_ALLOWED:
        issues.append(
            _issue(
                path="source_ingestion_policy.ingestion_responsibility",
                code="automated_source_ingestion_not_allowed",
                message=(
                    "ingestion_responsibility must equal "
                    f"'{_INGESTION_RESPONSIBILITY_ALLOWED}'"
                ),
            )
        )
    if not policy.forbid_raw_source_archival:
        issues.append(
            _issue(
                path="source_ingestion_policy.forbid_raw_source_archival",
                code="raw_source_archival_not_allowed_in_planning",
                message="forbid_raw_source_archival must be true",
            )
        )
    if not policy.forbid_diff_hunk_archival:
        issues.append(
            _issue(
                path="source_ingestion_policy.forbid_diff_hunk_archival",
                code="diff_hunk_archival_not_allowed_in_planning",
                message="forbid_diff_hunk_archival must be true",
            )
        )
    if not policy.forbid_raw_diagnostic_archival:
        issues.append(
            _issue(
                path="source_ingestion_policy.forbid_raw_diagnostic_archival",
                code="raw_diagnostic_archival_not_allowed_in_planning",
                message="forbid_raw_diagnostic_archival must be true",
            )
        )
    for entry in policy.allowed_in_product_artifacts:
        if entry not in _SOURCE_INGESTION_ALLOWLIST:
            issues.append(
                _issue(
                    path=(
                        "source_ingestion_policy.allowed_in_product_artifacts"
                    ),
                    code="source_ingestion_category_not_in_allowlist",
                    message=(
                        f"allowed_in_product_artifacts entry '{entry}' is "
                        "not in the planning allowlist"
                    ),
                )
            )
    return issues


def _validate_human_review(
    handoff: HumanReviewHandoff,
) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    if not _SLUG_PATTERN.fullmatch(handoff.review_owner):
        issues.append(
            _issue(
                path="human_review_handoff.review_owner",
                code="invalid_review_owner",
                message=(
                    "review_owner must match ^[a-z][a-z0-9_-]{1,63}$"
                ),
            )
        )
    if _is_unsafe_ref(handoff.review_inbox_ref):
        issues.append(
            _issue(
                path="human_review_handoff.review_inbox_ref",
                code="unsafe_review_inbox_ref",
                message=(
                    "review_inbox_ref must be a docs/-relative path "
                    "without '..' traversal or absolute paths"
                ),
            )
        )
    if not handoff.review_required_before:
        issues.append(
            _issue(
                path="human_review_handoff.review_required_before",
                code="human_review_handoff_required",
                message=(
                    "review_required_before must list at least one human "
                    "review token before any later live action"
                ),
            )
        )
    for token in handoff.review_required_before:
        if token not in _HUMAN_REVIEW_TOKEN_ALLOWLIST:
            issues.append(
                _issue(
                    path="human_review_handoff.review_required_before",
                    code="human_review_token_not_in_allowlist",
                    message=(
                        f"review_required_before entry '{token}' is not in "
                        "the human-review token allowlist"
                    ),
                )
            )
    return issues


def validate_real_oss_license_workflow_packet(
    packet: OssLicenseWorkflowPacket, *, config_ref: str
) -> ConfigValidationReport:
    """Validate the planning packet deterministically.

    Every valid packet emits a deterministic
    ``live_workflow_not_implemented`` warning so callers cannot interpret
    schema validity as authority to clone, fetch, capture license text,
    or adjudicate. The validator performs no HTTP call, no credential
    lookup, no clone, no fetch, no license capture, and no adjudication.
    """

    issues: list[ConfigValidationIssue] = []

    if not _SLUG_PATTERN.fullmatch(packet.workflow_id):
        issues.append(
            _issue(
                path="workflow_id",
                code="invalid_workflow_id",
                message=(
                    "workflow_id must match ^[a-z][a-z0-9_-]{1,63}$"
                ),
            )
        )
    if not _SLUG_PATTERN.fullmatch(packet.operator_id):
        issues.append(
            _issue(
                path="operator_id",
                code="invalid_operator_id",
                message=(
                    "operator_id must match ^[a-z][a-z0-9_-]{1,63}$"
                ),
            )
        )
    if _is_unsafe_ref(packet.approval_ref):
        issues.append(
            _issue(
                path="approval_ref",
                code="unsafe_approval_ref",
                message=(
                    "approval_ref must be a docs/-relative path without "
                    "'..' traversal or absolute paths"
                ),
            )
        )

    if not packet.approved_repository_declarations:
        issues.append(
            _issue(
                path="approved_repository_declarations",
                code="missing_required_field",
                message=(
                    "at least one approved_repository_declarations entry is "
                    "required"
                ),
            )
        )

    for index, decl in enumerate(packet.approved_repository_declarations):
        issues.extend(_validate_declaration(decl, index))

    issues.extend(_validate_retention(packet.retention_policy))
    issues.extend(_validate_license_policy(packet.license_metadata_policy))
    issues.extend(_validate_source_ingestion(packet.source_ingestion_policy))
    issues.extend(_validate_human_review(packet.human_review_handoff))

    if packet.live_workflow_authorized:
        issues.append(
            _issue(
                path="live_workflow_authorized",
                code="live_workflow_authority_not_allowed",
                message=(
                    "live_workflow_authorized must be false; this milestone "
                    "is planning-only and does not authorize live execution"
                ),
            )
        )

    valid = not any(issue.severity == "error" for issue in issues)
    if valid:
        issues.append(
            _issue(
                path="*",
                code="live_workflow_not_implemented",
                severity="warning",
                message=(
                    "schema validity does not authorize clone, fetch, "
                    "license-text capture, license adjudication, raw source "
                    "archival, or any live workflow execution; the real OSS "
                    "comparison/license workflow remains planning-only until "
                    "a separately approved implementation lands"
                ),
            )
        )

    return ConfigValidationReport(
        config_ref=config_ref,
        schema_id=REAL_OSS_LICENSE_WORKFLOW_SCHEMA_ID,
        valid=valid,
        issues=issues,
    )


def _normalize(values) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(v for v in values if v is not None)))


def build_real_oss_license_workflow_report(
    *,
    packet: OssLicenseWorkflowPacket,
    date: str,
    current_head_short: str | None = None,
) -> OssLicenseWorkflowReport:
    if not _DATE_PATTERN.fullmatch(date):
        raise ValueError(f"invalid oss license workflow date: {date!r}")

    declared_repository_ids: list[str] = []
    declared_license_tags: list[str] = []
    unsafe_refs: set[str] = set()
    unsafe_repository_ids: list[str] = []

    for decl in packet.approved_repository_declarations:
        if not _SLUG_PATTERN.fullmatch(decl.repository_id):
            unsafe_repository_ids.append(decl.repository_id)
            continue
        declared_repository_ids.append(decl.repository_id)
        declared_license_tags.append(decl.license_tag_placeholder or "n/a")
        if _is_unsafe_ref(decl.operator_approval_ref):
            unsafe_refs.add(decl.operator_approval_ref)
        for ref in decl.local_fixture_refs:
            if _is_unsafe_ref(ref):
                unsafe_refs.add(ref)

    if _is_unsafe_ref(packet.approval_ref):
        unsafe_refs.add(packet.approval_ref)
    if _is_unsafe_ref(packet.human_review_handoff.review_inbox_ref):
        unsafe_refs.add(packet.human_review_handoff.review_inbox_ref)

    return OssLicenseWorkflowReport(
        date=date,
        current_head_short=current_head_short,
        workflow_id=packet.workflow_id,
        declared_repository_ids=_normalize(declared_repository_ids),
        declared_license_tags=_normalize(declared_license_tags),
        human_review_tokens=_normalize(
            packet.human_review_handoff.review_required_before
        ),
        unsafe_refs=_normalize(unsafe_refs),
        unsafe_repository_ids=_normalize(unsafe_repository_ids),
        declared_repository_count=len(set(declared_repository_ids)),
    )


def render_real_oss_license_workflow_markdown(
    report: OssLicenseWorkflowReport,
) -> str:
    lines: list[str] = []
    lines.append(
        f"# Real OSS License Workflow Report — {report.schema_id}"
    )
    lines.append("")
    lines.append(f"- schema_id: {report.schema_id}")
    lines.append(f"- date: {report.date}")
    lines.append(
        f"- current_head_short: {report.current_head_short or 'n/a'}"
    )
    lines.append(f"- workflow_id: {report.workflow_id}")
    lines.append(
        f"- declared_repository_count: {report.declared_repository_count}"
    )
    lines.append(f"- advisory_only: {str(report.advisory_only).lower()}")
    lines.append(
        f"- requires_human_review: "
        f"{str(report.requires_human_review).lower()}"
    )
    lines.append(
        f"- external_call_made: {str(report.external_call_made).lower()}"
    )
    lines.append(
        f"- mutation_performed: {str(report.mutation_performed).lower()}"
    )
    lines.append(
        "- raw_source_content_persisted: "
        f"{str(report.raw_source_content_persisted).lower()}"
    )
    lines.append(
        "- live_external_action_authorized: "
        f"{str(report.live_external_action_authorized).lower()}"
    )
    lines.append(
        f"- live_workflow_executed: "
        f"{str(report.live_workflow_executed).lower()}"
    )
    lines.append(
        f"- license_text_captured: "
        f"{str(report.license_text_captured).lower()}"
    )
    lines.append(
        f"- license_adjudicated: {str(report.license_adjudicated).lower()}"
    )
    lines.append(f"- allowed_actions: {report.allowed_actions}")
    lines.append("")

    def _section(title: str, values: tuple[str, ...]) -> None:
        lines.append(f"## {title}")
        if not values:
            lines.append("- (none)")
        else:
            for value in values:
                lines.append(f"- {value}")
        lines.append("")

    _section("Declared repository IDs", report.declared_repository_ids)
    _section("Declared license tags", report.declared_license_tags)
    _section("Human review tokens", report.human_review_tokens)
    _section("Unsafe refs", report.unsafe_refs)
    _section("Unsafe repository IDs", report.unsafe_repository_ids)

    return "\n".join(lines) + "\n"


def write_real_oss_license_workflow_report(
    *,
    instance_root: Path,
    date: str,
    workflow_id: str,
    report: OssLicenseWorkflowReport,
) -> dict[str, object]:
    if not _DATE_PATTERN.fullmatch(date):
        raise ValueError(
            f"invalid oss license workflow report date: {date!r}"
        )
    if not _SLUG_PATTERN.fullmatch(workflow_id):
        raise ValueError(
            f"invalid oss license workflow workflow_id: {workflow_id!r}"
        )
    rel_dir = f"{_PARTITION_PREFIX}/{date}"
    json_ref = f"{rel_dir}/{workflow_id}.json"
    md_ref = f"{rel_dir}/{workflow_id}.md"
    json_path = resolve_instance_runtime_ref(
        instance_root=instance_root, relative_ref=json_ref
    )
    md_path = resolve_instance_runtime_ref(
        instance_root=instance_root, relative_ref=md_ref
    )
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    md_path.write_text(
        render_real_oss_license_workflow_markdown(report), encoding="utf-8"
    )
    return {
        "schema_id": report.schema_id,
        "json_ref": json_ref,
        "markdown_ref": md_ref,
        "advisory_only": True,
        "requires_human_review": True,
        "external_call_made": False,
        "mutation_performed": False,
        "raw_source_content_persisted": False,
        "live_external_action_authorized": False,
        "live_workflow_executed": False,
        "license_text_captured": False,
        "license_adjudicated": False,
        "allowed_actions": "advisory_only",
    }


__all__ = [
    "REAL_OSS_LICENSE_WORKFLOW_SCHEMA_ID",
    "ApprovedRepositoryDeclaration",
    "HumanReviewHandoff",
    "LicenseMetadataPolicy",
    "OssLicenseWorkflowPacket",
    "OssLicenseWorkflowReport",
    "ProvenanceRecordSchema",
    "RetentionPolicy",
    "SourceIngestionPolicy",
    "build_real_oss_license_workflow_report",
    "render_real_oss_license_workflow_markdown",
    "validate_real_oss_license_workflow_packet",
    "write_real_oss_license_workflow_report",
]
