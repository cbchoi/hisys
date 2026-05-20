"""Focused unit tests for the M21.6 change-impact analyzer.

The analyzer is pure and advisory only: callers supply a bounded list of
changed file refs plus an existing :class:`TraceabilityAnchors` value, and the
analyzer maps each ref to impacted requirement IDs, test IDs/refs,
design/interface refs, runtime-boundary refs, or unmapped/unsafe partitions.
These tests pin the classification vocabulary, the writer invariants, and the
unsafe-ref rejection path.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.operations.change_impact import (
    ChangeImpactRequest,
    build_change_impact_report,
    write_change_impact_report,
)
from hisys.operations.traceability_coverage import TraceabilityAnchors


def _seed_anchors() -> TraceabilityAnchors:
    requirement_ids = ("HISYS-FR-DOM-001", "HISYS-FR-DOM-002", "HISYS-NFR-MNT-001")
    design_requirement_refs = {
        "HISYS-FR-DOM-001": ("docs/traceability/README.md",),
        "HISYS-FR-DOM-002": ("docs/traceability/README.md",),
    }
    interface_requirement_refs = {
        "HISYS-FR-DOM-001": ("src/hisys/schemas/domain_adapter.py",),
        "HISYS-NFR-MNT-001": ("src/hisys/schemas/runtime_boundary.py",),
    }
    test_requirement_refs = {
        "HISYS-FR-DOM-001": ("tests/integration/test_trace_path.py",),
    }
    test_ids = ("tests/integration/test_trace_path.py",)
    test_requirement_links = {
        "tests/integration/test_trace_path.py": (
            "HISYS-FR-DOM-001",
            "HISYS-FR-DOM-002",
        ),
    }
    return TraceabilityAnchors(
        requirement_ids=requirement_ids,
        design_requirement_refs=design_requirement_refs,
        interface_requirement_refs=interface_requirement_refs,
        test_requirement_refs=test_requirement_refs,
        test_ids=test_ids,
        test_requirement_links=test_requirement_links,
    )


def test_build_change_impact_report_classifies_changed_refs(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    anchors = _seed_anchors()

    request = ChangeImpactRequest(
        instance_root=instance_root,
        repo_root=repo_root,
        changed_file_refs=(
            "src/hisys/schemas/domain_adapter.py",
            "docs/traceability/README.md",
            "tests/integration/test_trace_path.py",
            "runtime-boundary/codebase-analysis/20260520/REQ-X/inventory.json",
            "src/hisys/agents/unrelated_helper.py",
            "/etc/passwd",
            "runtime-boundary/../escape.txt",
        ),
        current_head_short="2d8d4ac",
    )

    report = build_change_impact_report(request=request, anchors=anchors)

    assert report.schema_id == "hisys.change_impact.v1"
    assert report.advisory_only is True
    assert report.requires_human_review is True
    assert report.external_call_made is False
    assert report.mutation_performed is False
    assert report.raw_source_content_persisted is False
    assert report.current_head_short == "2d8d4ac"
    assert report.changed_ref_count == 7

    assert "HISYS-FR-DOM-001" in report.impacted_requirement_ids
    assert "HISYS-FR-DOM-002" in report.impacted_requirement_ids
    # NFR-MNT-001 is only linked via src/hisys/schemas/runtime_boundary.py, which
    # is NOT in the changed list; the schema_adapter.py edit only impacts FR-DOM-001.
    assert "HISYS-NFR-MNT-001" not in report.impacted_requirement_ids

    assert "tests/integration/test_trace_path.py" in report.impacted_test_id_or_refs
    assert (
        "docs/traceability/README.md"
        in report.impacted_design_or_interface_refs
    )
    assert (
        "src/hisys/schemas/domain_adapter.py"
        in report.impacted_design_or_interface_refs
    )
    assert (
        "runtime-boundary/codebase-analysis/20260520/REQ-X/inventory.json"
        in report.impacted_runtime_boundary_refs
    )
    assert "src/hisys/agents/unrelated_helper.py" in report.unmapped_changed_refs
    assert "/etc/passwd" in report.unsafe_changed_refs
    assert "runtime-boundary/../escape.txt" in report.unsafe_changed_refs


def test_write_change_impact_report_persists_safe_refs(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    anchors = _seed_anchors()

    request = ChangeImpactRequest(
        instance_root=instance_root,
        repo_root=repo_root,
        changed_file_refs=("docs/traceability/README.md",),
    )
    report = build_change_impact_report(request=request, anchors=anchors)
    refs = write_change_impact_report(
        instance_root=instance_root, date="20260521", report=report
    )

    assert refs["json_ref"] == (
        "runtime-boundary/change-impact/20260521/impact-report.json"
    )
    assert refs["markdown_ref"] == (
        "runtime-boundary/change-impact/20260521/impact-report.md"
    )
    assert refs["external_call_made"] is False
    assert refs["mutation_performed"] is False
    assert refs["raw_source_content_persisted"] is False

    json_path = instance_root / refs["json_ref"]
    md_path = instance_root / refs["markdown_ref"]
    assert json_path.is_file()
    assert md_path.is_file()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["schema_id"] == "hisys.change_impact.v1"
    assert payload["advisory_only"] is True
    assert payload["requires_human_review"] is True
    assert payload["external_call_made"] is False
    assert payload["mutation_performed"] is False
    assert payload["raw_source_content_persisted"] is False
    assert "HISYS-FR-DOM-001" in payload["impacted_requirement_ids"]


def test_build_change_impact_report_rejects_unsafe_refs(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    anchors = _seed_anchors()

    request = ChangeImpactRequest(
        instance_root=instance_root,
        repo_root=repo_root,
        changed_file_refs=(
            "/etc/passwd",
            "../escape",
            "subdir/../escape.py",
            "ok/path.py",
        ),
    )
    report = build_change_impact_report(request=request, anchors=anchors)

    assert "/etc/passwd" in report.unsafe_changed_refs
    assert "../escape" in report.unsafe_changed_refs
    assert "subdir/../escape.py" in report.unsafe_changed_refs
    assert "ok/path.py" in report.unmapped_changed_refs
    assert report.impacted_requirement_ids == ()


def test_write_change_impact_report_rejects_bad_date(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    anchors = _seed_anchors()
    request = ChangeImpactRequest(
        instance_root=instance_root,
        repo_root=repo_root,
        changed_file_refs=(),
    )
    report = build_change_impact_report(request=request, anchors=anchors)
    with pytest.raises(ValueError):
        write_change_impact_report(
            instance_root=instance_root, date="2026-05-21", report=report
        )


def test_build_change_impact_report_empty_changed_list(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    anchors = _seed_anchors()
    request = ChangeImpactRequest(
        instance_root=instance_root,
        repo_root=repo_root,
        changed_file_refs=(),
    )
    report = build_change_impact_report(request=request, anchors=anchors)
    assert report.changed_ref_count == 0
    assert report.impacted_requirement_ids == ()
    assert report.impacted_test_id_or_refs == ()
    assert report.impacted_design_or_interface_refs == ()
    assert report.impacted_runtime_boundary_refs == ()
    assert report.unmapped_changed_refs == ()
    assert report.unsafe_changed_refs == ()
