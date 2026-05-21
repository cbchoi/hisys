"""M23 approved-OSS comparison adapter tests.

Caller-supplied descriptors only; no network, no clone, no package install,
no subprocess, no `.git/` access, no system clock, no raw OSS source bodies.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.operations.oss_comparison_adapter import (
    ApprovedOssSource,
    LocalCodebaseLine,
    OssComparisonRequest,
    build_oss_comparison_report,
    write_oss_comparison_report,
)


def _m21_local_line() -> LocalCodebaseLine:
    return LocalCodebaseLine(
        line_label="M21",
        category_refs=(
            "architecture_candidates",
            "change_impact",
            "code_analysis_pass_contract",
            "codebase_map_freshness",
            "runtime_boundary_consistency",
            "subagent_evidence_collector_protocol",
            "traceability_coverage",
        ),
        portfolio_refs=(
            "docs/plans/m21-1-traceability-coverage-report-implementation-tasks.md",
            "docs/plans/m21-6-change-impact-analyzer-implementation-tasks.md",
            "docs/plans/m21-7-architecture-candidate-generator-implementation-tasks.md",
        ),
        implemented_surface_count=9,
        human_gated_surface_count=2,
    )


def _approved_oss_understand() -> ApprovedOssSource:
    return ApprovedOssSource(
        source_id="understand-static-analysis",
        source_name="Approved static-analysis reference",
        license_tag="n/a",
        category_refs=(
            "architecture_candidates",
            "change_impact",
            "traceability_coverage",
        ),
        approved_refs=(
            "docs/plans/m23-advanced-codebase-adapter-integration-plan.md",
        ),
        local_fixture_refs=(
            "tests/fixtures/oss/approved/understand-static-analysis.json",
        ),
        notes="Local fixture descriptor only; no upstream content fetched.",
    )


def _approved_oss_pylint() -> ApprovedOssSource:
    return ApprovedOssSource(
        source_id="pylint-style-rules",
        source_name="Approved style/lint reference",
        license_tag="GPL-2.0-or-later",
        category_refs=(
            "code_analysis_pass_contract",
            "runtime_boundary_consistency",
            "style_conventions",
        ),
        approved_refs=(
            "docs/plans/m23-advanced-codebase-adapter-integration-plan.md",
        ),
        local_fixture_refs=(
            "tests/fixtures/oss/approved/pylint-style-rules.json",
        ),
        notes="Local fixture descriptor only.",
    )


def test_build_oss_comparison_aggregates_local_line_and_approved_sources(
    tmp_path: Path,
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    request = OssComparisonRequest(
        instance_root=instance_root,
        date="20260522",
        local_line=_m21_local_line(),
        approved_sources=(_approved_oss_understand(), _approved_oss_pylint()),
        current_head_short="70ae484",
    )

    report = build_oss_comparison_report(request=request)

    assert report.schema_id == "hisys.oss_comparison_adapter.v1"
    assert report.date == "20260522"
    assert report.current_head_short == "70ae484"
    assert report.local_line_label == "M21"
    assert report.compared_source_ids == (
        "pylint-style-rules",
        "understand-static-analysis",
    )
    assert report.compared_source_license_tags == ("GPL-2.0-or-later", "n/a")
    assert report.compared_source_count == 2
    assert "traceability_coverage" in report.intersection_category_refs
    assert "code_analysis_pass_contract" in report.intersection_category_refs
    assert (
        "subagent_evidence_collector_protocol"
        in report.local_only_category_refs
    )
    assert "style_conventions" in report.oss_only_category_refs
    assert report.union_category_count >= 8
    assert report.unsafe_refs == ()
    assert report.unsafe_source_ids == ()
    assert report.unsafe_line_labels == ()
    assert report.advisory_only is True
    assert report.requires_human_review is True
    assert report.external_call_made is False
    assert report.mutation_performed is False
    assert report.raw_source_content_persisted is False
    assert report.live_external_action_authorized is False
    assert report.allowed_actions == "advisory_only"


def test_write_oss_comparison_persists_safe_refs(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    request = OssComparisonRequest(
        instance_root=instance_root,
        date="20260522",
        local_line=_m21_local_line(),
        approved_sources=(_approved_oss_understand(),),
    )
    report = build_oss_comparison_report(request=request)
    refs = write_oss_comparison_report(
        instance_root=instance_root, date="20260522", report=report
    )
    assert refs["json_ref"] == (
        "runtime-boundary/oss-comparison/20260522/comparison-report.json"
    )
    assert refs["markdown_ref"] == (
        "runtime-boundary/oss-comparison/20260522/comparison-report.md"
    )
    assert refs["external_call_made"] is False
    assert refs["allowed_actions"] == "advisory_only"
    json_path = instance_root / refs["json_ref"]
    md_path = instance_root / refs["markdown_ref"]
    assert json_path.exists()
    assert md_path.exists()


def test_build_oss_comparison_rejects_unsafe_refs_and_ids(
    tmp_path: Path,
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    request = OssComparisonRequest(
        instance_root=instance_root,
        date="20260522",
        local_line=LocalCodebaseLine(
            line_label="M21",
            category_refs=("traceability_coverage",),
            portfolio_refs=(
                "docs/plans/m22-codebase-evidence-portfolio-implementation-tasks.md",
                "../escape.md",
                "/etc/passwd",
            ),
            implemented_surface_count=1,
        ),
        approved_sources=(
            ApprovedOssSource(
                source_id="UPPERCASE_SOURCE",
                source_name="invalid id",
                category_refs=("foo",),
            ),
            ApprovedOssSource(
                source_id="approved-fixture",
                category_refs=("traceability_coverage", "extra_topic"),
                approved_refs=("../bad.md",),
                local_fixture_refs=(
                    "tests/fixtures/oss/approved/foo.json",
                ),
                notes="ok",
            ),
            ApprovedOssSource(
                source_id="malformed-notes",
                category_refs=("traceability_coverage",),
                notes="\x00binary",
            ),
        ),
    )
    report = build_oss_comparison_report(request=request)
    assert report.local_line_label == "M21"
    assert "UPPERCASE_SOURCE" in report.unsafe_source_ids
    assert "malformed-notes" in report.unsafe_source_ids
    assert "approved-fixture" in report.compared_source_ids
    assert "/etc/passwd" in report.unsafe_refs
    assert "../escape.md" in report.unsafe_refs
    assert "../bad.md" in report.unsafe_refs
    assert "extra_topic" in report.oss_only_category_refs
    assert "foo" not in report.oss_only_category_refs


def test_build_oss_comparison_rejects_unsafe_line_label(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    request = OssComparisonRequest(
        instance_root=instance_root,
        date="20260522",
        local_line=LocalCodebaseLine(
            line_label="lowercase-not-allowed",
            category_refs=("traceability_coverage",),
        ),
        approved_sources=(_approved_oss_understand(),),
    )
    report = build_oss_comparison_report(request=request)
    assert "lowercase-not-allowed" in report.unsafe_line_labels
    assert report.local_category_refs == ()
    assert report.intersection_category_refs == ()
    assert report.local_only_category_refs == ()


def test_build_oss_comparison_rejects_bad_date(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    request = OssComparisonRequest(
        instance_root=instance_root,
        date="2026-05-22",
        local_line=_m21_local_line(),
        approved_sources=(_approved_oss_understand(),),
    )
    with pytest.raises(ValueError):
        build_oss_comparison_report(request=request)


def test_write_oss_comparison_rejects_bad_date(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    request = OssComparisonRequest(
        instance_root=instance_root,
        date="20260522",
        local_line=_m21_local_line(),
        approved_sources=(_approved_oss_understand(),),
    )
    report = build_oss_comparison_report(request=request)
    with pytest.raises(ValueError):
        write_oss_comparison_report(
            instance_root=instance_root,
            date="2026-05-22",
            report=report,
        )


_FIXTURE_DIR = (
    Path(__file__).resolve().parents[1] / "fixtures" / "oss-comparison"
)


def _load_golden_bundle() -> dict[str, object]:
    return json.loads(
        (_FIXTURE_DIR / "m23_local_oss_bundle.json").read_text(encoding="utf-8")
    )


def _expected_golden_json() -> str:
    return (_FIXTURE_DIR / "expected" / "comparison-report.json").read_text(
        encoding="utf-8"
    )


def _expected_golden_markdown() -> str:
    return (_FIXTURE_DIR / "expected" / "comparison-report.md").read_text(
        encoding="utf-8"
    )


def test_oss_comparison_adapter_golden_round_trip(tmp_path: Path) -> None:
    bundle = _load_golden_bundle()
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    local_line = LocalCodebaseLine(**bundle["local_line"])
    approved_sources = tuple(
        ApprovedOssSource(**raw) for raw in bundle["approved_sources"]
    )
    request = OssComparisonRequest(
        instance_root=instance_root,
        date=bundle["date"],
        local_line=local_line,
        approved_sources=approved_sources,
        current_head_short=bundle["current_head_short"],
    )
    report = build_oss_comparison_report(request=request)
    write_oss_comparison_report(
        instance_root=instance_root, date=bundle["date"], report=report
    )

    json_path = (
        instance_root
        / "runtime-boundary"
        / "oss-comparison"
        / bundle["date"]
        / "comparison-report.json"
    )
    md_path = (
        instance_root
        / "runtime-boundary"
        / "oss-comparison"
        / bundle["date"]
        / "comparison-report.md"
    )
    assert json_path.read_text(encoding="utf-8") == _expected_golden_json()
    assert md_path.read_text(encoding="utf-8") == _expected_golden_markdown()
