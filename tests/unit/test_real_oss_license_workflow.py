"""Tests for the M24 real OSS comparison/license workflow planning validator.

The validator/builder/writer is planning-only. It does not clone, fetch,
search, inspect, archive, or adjudicate any real external repository or
license. Every valid packet emits a standing
``live_workflow_not_implemented`` warning so schema validity is never
authority to act.
"""

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
    render_real_oss_license_workflow_markdown,
    validate_real_oss_license_workflow_packet,
    write_real_oss_license_workflow_report,
)


_CONFIG_REF = "docs/plans/m24-real-oss-comparison-license-workflow-prep-tasks.md"


def _placeholder_declaration(**overrides: object) -> ApprovedRepositoryDeclaration:
    base = ApprovedRepositoryDeclaration(
        repository_id="placeholder-ref-impl",
        repository_label="Placeholder reference implementation",
        repository_url_placeholder="placeholder://approved-ref-impl",
        commit_or_tag_placeholder="placeholder-commit-0000000",
        operator_approval_ref=(
            "docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.39.md"
        ),
        approval_timestamp_placeholder="placeholder-20260522",
        license_tag_placeholder="MIT",
        local_fixture_refs=(
            "tests/fixtures/oss/approved/placeholder-ref-impl.json",
        ),
        notes="Placeholder only; no real upstream repository is referenced.",
    )
    if overrides:
        return base.model_copy(update=overrides)
    return base


def _valid_packet(**overrides: object) -> OssLicenseWorkflowPacket:
    base = OssLicenseWorkflowPacket(
        workflow_id="placeholder-m24-planning",
        approval_ref=(
            "docs/milestone-bootstrap/documents/readiness_decision_record_v0.0.39.md"
        ),
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
            review_inbox_ref=(
                "docs/runbooks/m24-real-oss-license-workflow-review.md"
            ),
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
    if overrides:
        return base.model_copy(update=overrides)
    return base


def _has_code(report, code: str) -> bool:
    return any(issue.code == code for issue in report.issues)


def _error_codes(report) -> tuple[str, ...]:
    return tuple(issue.code for issue in report.issues if issue.severity == "error")


def test_valid_packet_emits_standing_not_implemented_warning() -> None:
    report = validate_real_oss_license_workflow_packet(
        _valid_packet(), config_ref=_CONFIG_REF
    )
    assert report.schema_id == "hisys.oss_license_workflow.v1"
    assert report.valid is True
    assert _error_codes(report) == ()
    assert any(
        issue.severity == "warning"
        and issue.code == "live_workflow_not_implemented"
        for issue in report.issues
    )


@pytest.mark.parametrize(
    "url_override",
    [
        "https://github.com/example/repo",
        "http://example.com/repo",
        "git@github.com:example/repo.git",
        "git://gitlab.com/example/repo",
        "git+ssh://gitlab.com/example/repo",
        "git+https://github.com/example/repo",
        "ssh://git@bitbucket.org/example/repo",
        "ftp://example.com/repo",
        "gopher://example.com/repo",
        "file:///tmp/repo",
        "pkg:pypi/example@1.0.0",
        "oci://registry.example.com/repo",
    ],
)
def test_real_url_schemes_rejected(url_override: str) -> None:
    bad_decl = _placeholder_declaration(repository_url_placeholder=url_override)
    packet = _valid_packet(approved_repository_declarations=(bad_decl,))
    report = validate_real_oss_license_workflow_packet(
        packet, config_ref=_CONFIG_REF
    )
    assert _has_code(report, "real_repository_url_not_allowed_in_planning")
    assert report.valid is False


@pytest.mark.parametrize(
    "host_token",
    [
        "github.com",
        "gitlab.com",
        "bitbucket.org",
        "sourceforge.net",
        "pypi.org",
        "npmjs.com",
        "crates.io",
        "rubygems.org",
        "huggingface.co",
        "gitee.com",
        "codeberg.org",
        "kernel.org",
    ],
)
def test_real_url_hosts_rejected(host_token: str) -> None:
    bad_decl = _placeholder_declaration(
        repository_url_placeholder=f"placeholder://{host_token}/repo"
    )
    packet = _valid_packet(approved_repository_declarations=(bad_decl,))
    report = validate_real_oss_license_workflow_packet(
        packet, config_ref=_CONFIG_REF
    )
    assert _has_code(report, "real_repository_url_not_allowed_in_planning")


def test_placeholder_url_must_start_with_placeholder_scheme() -> None:
    bad_decl = _placeholder_declaration(
        repository_url_placeholder="example://approved-ref-impl"
    )
    packet = _valid_packet(approved_repository_declarations=(bad_decl,))
    report = validate_real_oss_license_workflow_packet(
        packet, config_ref=_CONFIG_REF
    )
    assert _has_code(report, "real_repository_url_not_allowed_in_planning")


def test_live_workflow_authority_rejected() -> None:
    packet = _valid_packet(live_workflow_authorized=True)
    report = validate_real_oss_license_workflow_packet(
        packet, config_ref=_CONFIG_REF
    )
    assert _has_code(report, "live_workflow_authority_not_allowed")
    assert report.valid is False


def test_license_text_capture_rejected() -> None:
    packet = _valid_packet(
        license_metadata_policy=LicenseMetadataPolicy(
            allowed_license_tags=("MIT",),
            forbid_license_text_capture=False,
        )
    )
    report = validate_real_oss_license_workflow_packet(
        packet, config_ref=_CONFIG_REF
    )
    assert _has_code(report, "license_text_capture_not_allowed_in_planning")


def test_license_adjudication_claim_rejected() -> None:
    packet = _valid_packet(
        license_metadata_policy=LicenseMetadataPolicy(
            allowed_license_tags=("MIT",),
            forbid_license_adjudication_claim=False,
        )
    )
    report = validate_real_oss_license_workflow_packet(
        packet, config_ref=_CONFIG_REF
    )
    assert _has_code(report, "license_adjudication_claim_not_allowed_in_planning")


def test_license_human_review_required_must_be_true() -> None:
    packet = _valid_packet(
        license_metadata_policy=LicenseMetadataPolicy(
            allowed_license_tags=("MIT",),
            human_review_required=False,
        )
    )
    report = validate_real_oss_license_workflow_packet(
        packet, config_ref=_CONFIG_REF
    )
    assert _has_code(report, "license_human_review_required_must_be_true")


def test_license_tag_not_in_allowlist_rejected() -> None:
    bad_decl = _placeholder_declaration(license_tag_placeholder="Proprietary")
    packet = _valid_packet(approved_repository_declarations=(bad_decl,))
    report = validate_real_oss_license_workflow_packet(
        packet, config_ref=_CONFIG_REF
    )
    assert _has_code(report, "license_tag_not_in_allowlist")


def test_automated_cleanup_rejected() -> None:
    packet = _valid_packet(
        retention_policy=RetentionPolicy(
            cache_directory_placeholder="placeholder-cache-dir/m24",
            max_age_days=30,
            cleanup_command_placeholder="placeholder-cleanup-script",
            cleanup_responsibility="automated_cleanup",
        )
    )
    report = validate_real_oss_license_workflow_packet(
        packet, config_ref=_CONFIG_REF
    )
    assert _has_code(report, "automated_cleanup_not_allowed")


def test_retention_max_age_out_of_range_rejected() -> None:
    packet = _valid_packet(
        retention_policy=RetentionPolicy(
            cache_directory_placeholder="placeholder-cache-dir/m24",
            max_age_days=0,
            cleanup_command_placeholder="placeholder-cleanup-script",
            cleanup_responsibility="operator_run_manually",
        )
    )
    report = validate_real_oss_license_workflow_packet(
        packet, config_ref=_CONFIG_REF
    )
    assert _has_code(report, "invalid_retention_max_age")


def test_cache_directory_must_use_placeholder_prefix() -> None:
    packet = _valid_packet(
        retention_policy=RetentionPolicy(
            cache_directory_placeholder="/tmp/m24-cache",
            max_age_days=30,
            cleanup_command_placeholder="placeholder-cleanup-script",
            cleanup_responsibility="operator_run_manually",
        )
    )
    report = validate_real_oss_license_workflow_packet(
        packet, config_ref=_CONFIG_REF
    )
    assert _has_code(report, "invalid_cache_directory_placeholder")


def test_automated_source_ingestion_rejected() -> None:
    packet = _valid_packet(
        source_ingestion_policy=SourceIngestionPolicy(
            allowed_in_product_artifacts=("category_refs",),
            ingestion_responsibility="automated_ingestion",
        )
    )
    report = validate_real_oss_license_workflow_packet(
        packet, config_ref=_CONFIG_REF
    )
    assert _has_code(report, "automated_source_ingestion_not_allowed")


def test_source_ingestion_disallowed_category_rejected() -> None:
    packet = _valid_packet(
        source_ingestion_policy=SourceIngestionPolicy(
            allowed_in_product_artifacts=(
                "category_refs",
                "raw_source_body",
            ),
            ingestion_responsibility="operator_run_manually",
        )
    )
    report = validate_real_oss_license_workflow_packet(
        packet, config_ref=_CONFIG_REF
    )
    assert _has_code(report, "source_ingestion_category_not_in_allowlist")


def test_source_ingestion_forbid_flags_must_be_true() -> None:
    packet = _valid_packet(
        source_ingestion_policy=SourceIngestionPolicy(
            allowed_in_product_artifacts=(
                "category_refs",
                "license_tags",
                "placeholder_url",
                "repository_id",
            ),
            ingestion_responsibility="operator_run_manually",
            forbid_raw_source_archival=False,
        )
    )
    report = validate_real_oss_license_workflow_packet(
        packet, config_ref=_CONFIG_REF
    )
    assert _has_code(report, "raw_source_archival_not_allowed_in_planning")


def test_human_review_handoff_required() -> None:
    packet = _valid_packet(
        human_review_handoff=HumanReviewHandoff(
            review_owner="placeholder-reviewer",
            review_inbox_ref=(
                "docs/runbooks/m24-real-oss-license-workflow-review.md"
            ),
            review_required_before=(),
        )
    )
    report = validate_real_oss_license_workflow_packet(
        packet, config_ref=_CONFIG_REF
    )
    assert _has_code(report, "human_review_handoff_required")


def test_human_review_token_not_in_allowlist_rejected() -> None:
    packet = _valid_packet(
        human_review_handoff=HumanReviewHandoff(
            review_owner="placeholder-reviewer",
            review_inbox_ref=(
                "docs/runbooks/m24-real-oss-license-workflow-review.md"
            ),
            review_required_before=("ad_hoc_request",),
        )
    )
    report = validate_real_oss_license_workflow_packet(
        packet, config_ref=_CONFIG_REF
    )
    assert _has_code(report, "human_review_token_not_in_allowlist")


def test_workflow_id_must_match_slug_pattern() -> None:
    packet = _valid_packet(workflow_id="Invalid Workflow ID")
    report = validate_real_oss_license_workflow_packet(
        packet, config_ref=_CONFIG_REF
    )
    assert _has_code(report, "invalid_workflow_id")


def test_repository_id_must_match_slug_pattern() -> None:
    bad_decl = _placeholder_declaration(repository_id="Bad Repo ID")
    packet = _valid_packet(approved_repository_declarations=(bad_decl,))
    report = validate_real_oss_license_workflow_packet(
        packet, config_ref=_CONFIG_REF
    )
    assert _has_code(report, "invalid_repository_id")


def test_unsafe_operator_approval_ref_collected() -> None:
    bad_decl = _placeholder_declaration(
        operator_approval_ref="/etc/passwd"
    )
    packet = _valid_packet(approved_repository_declarations=(bad_decl,))
    report = validate_real_oss_license_workflow_packet(
        packet, config_ref=_CONFIG_REF
    )
    assert _has_code(report, "unsafe_operator_approval_ref")


def test_notes_overlong_rejected() -> None:
    bad_decl = _placeholder_declaration(notes="x" * 1025)
    packet = _valid_packet(approved_repository_declarations=(bad_decl,))
    report = validate_real_oss_license_workflow_packet(
        packet, config_ref=_CONFIG_REF
    )
    assert _has_code(report, "notes_too_long")


def test_notes_with_control_characters_rejected() -> None:
    bad_decl = _placeholder_declaration(notes="bad\x00content")
    packet = _valid_packet(approved_repository_declarations=(bad_decl,))
    report = validate_real_oss_license_workflow_packet(
        packet, config_ref=_CONFIG_REF
    )
    assert _has_code(report, "notes_contains_control_characters")


def test_secret_like_notes_rejected() -> None:
    marker_field = "api" + "_key"
    bad_decl = _placeholder_declaration(
        notes=f"{marker_field}=FAKE_AKIAEXAMPLEEXAMPLE placeholder"
    )
    packet = _valid_packet(approved_repository_declarations=(bad_decl,))
    report = validate_real_oss_license_workflow_packet(
        packet, config_ref=_CONFIG_REF
    )
    assert _has_code(report, "raw_secret_value_not_allowed")


def test_at_least_one_declaration_required() -> None:
    packet = _valid_packet(approved_repository_declarations=())
    report = validate_real_oss_license_workflow_packet(
        packet, config_ref=_CONFIG_REF
    )
    assert _has_code(report, "missing_required_field")


def test_build_report_aggregates_declared_metadata() -> None:
    packet = _valid_packet()
    report = build_real_oss_license_workflow_report(
        packet=packet,
        date="20260522",
        current_head_short="1b053a7",
    )
    assert isinstance(report, OssLicenseWorkflowReport)
    assert report.schema_id == "hisys.oss_license_workflow.v1"
    assert report.date == "20260522"
    assert report.current_head_short == "1b053a7"
    assert report.workflow_id == "placeholder-m24-planning"
    assert report.declared_repository_ids == ("placeholder-ref-impl",)
    assert report.declared_license_tags == ("MIT",)
    assert report.human_review_tokens == (
        "license_adjudication",
        "license_text_capture",
        "live_workflow_execution",
        "network_fetch",
        "raw_source_archival",
        "repository_clone",
    )
    assert report.declared_repository_count == 1
    assert report.unsafe_refs == ()
    assert report.unsafe_repository_ids == ()
    assert report.advisory_only is True
    assert report.requires_human_review is True
    assert report.external_call_made is False
    assert report.mutation_performed is False
    assert report.raw_source_content_persisted is False
    assert report.live_external_action_authorized is False
    assert report.live_workflow_executed is False
    assert report.license_text_captured is False
    assert report.license_adjudicated is False
    assert report.allowed_actions == "advisory_only"


def test_build_report_collects_unsafe_repository_id() -> None:
    bad_decl = _placeholder_declaration(repository_id="Bad Repo")
    packet = _valid_packet(approved_repository_declarations=(bad_decl,))
    report = build_real_oss_license_workflow_report(
        packet=packet, date="20260522", current_head_short=None
    )
    assert "Bad Repo" in report.unsafe_repository_ids
    assert report.declared_repository_ids == ()
    assert report.declared_repository_count == 0


def test_build_report_collects_unsafe_refs() -> None:
    bad_decl = _placeholder_declaration(
        local_fixture_refs=("/etc/passwd", "../escape.json"),
        operator_approval_ref="docs/approvals/m24.md",
    )
    packet = _valid_packet(approved_repository_declarations=(bad_decl,))
    report = build_real_oss_license_workflow_report(
        packet=packet, date="20260522", current_head_short=None
    )
    assert "../escape.json" in report.unsafe_refs
    assert "/etc/passwd" in report.unsafe_refs


def test_build_report_rejects_bad_date() -> None:
    with pytest.raises(ValueError, match="invalid"):
        build_real_oss_license_workflow_report(
            packet=_valid_packet(),
            date="2026-05-22",
            current_head_short=None,
        )


def test_writer_round_trip(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    packet = _valid_packet()
    report = build_real_oss_license_workflow_report(
        packet=packet, date="20260522", current_head_short="1b053a7"
    )
    refs = write_real_oss_license_workflow_report(
        instance_root=instance_root,
        date="20260522",
        workflow_id=packet.workflow_id,
        report=report,
    )
    assert refs["schema_id"] == "hisys.oss_license_workflow.v1"
    expected_json_ref = (
        "runtime-boundary/oss-license-workflow/20260522/"
        "placeholder-m24-planning.json"
    )
    expected_md_ref = (
        "runtime-boundary/oss-license-workflow/20260522/"
        "placeholder-m24-planning.md"
    )
    assert refs["json_ref"] == expected_json_ref
    assert refs["markdown_ref"] == expected_md_ref
    assert refs["advisory_only"] is True
    assert refs["live_workflow_executed"] is False
    payload = json.loads(
        (instance_root / expected_json_ref).read_text(encoding="utf-8")
    )
    assert payload["schema_id"] == "hisys.oss_license_workflow.v1"
    assert payload["live_workflow_executed"] is False
    assert payload["license_text_captured"] is False
    assert payload["license_adjudicated"] is False
    md_body = (instance_root / expected_md_ref).read_text(encoding="utf-8")
    assert "hisys.oss_license_workflow.v1" in md_body
    assert "live_workflow_executed: false" in md_body


def test_writer_rejects_bad_date(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    report = build_real_oss_license_workflow_report(
        packet=_valid_packet(), date="20260522", current_head_short=None
    )
    with pytest.raises(ValueError, match="invalid"):
        write_real_oss_license_workflow_report(
            instance_root=instance_root,
            date="not-a-date",
            workflow_id="placeholder-m24-planning",
            report=report,
        )


def test_writer_rejects_bad_workflow_id(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    report = build_real_oss_license_workflow_report(
        packet=_valid_packet(), date="20260522", current_head_short=None
    )
    with pytest.raises(ValueError, match="invalid"):
        write_real_oss_license_workflow_report(
            instance_root=instance_root,
            date="20260522",
            workflow_id="Bad Workflow",
            report=report,
        )


def test_markdown_render_contains_advisory_flags() -> None:
    report = build_real_oss_license_workflow_report(
        packet=_valid_packet(),
        date="20260522",
        current_head_short="1b053a7",
    )
    md = render_real_oss_license_workflow_markdown(report)
    for line in (
        "schema_id: hisys.oss_license_workflow.v1",
        "advisory_only: true",
        "requires_human_review: true",
        "external_call_made: false",
        "mutation_performed: false",
        "raw_source_content_persisted: false",
        "live_external_action_authorized: false",
        "live_workflow_executed: false",
        "license_text_captured: false",
        "license_adjudicated: false",
        "allowed_actions: advisory_only",
    ):
        assert line in md
