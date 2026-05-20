from __future__ import annotations

import json

from hisys.operations.traceability_coverage import (
    TraceabilityAnchors,
    build_traceability_coverage_report,
    write_traceability_coverage_report,
)


def test_traceability_coverage_reports_unreferenced_requirements() -> None:
    anchors = TraceabilityAnchors(
        requirement_ids=("HISYS-FR-001", "HISYS-FR-002"),
        design_requirement_refs={"HISYS-FR-001": ("SDD-MOD-001",)},
        interface_requirement_refs={},
        test_requirement_refs={"HISYS-FR-001": ("STD-TC-001",)},
        test_ids=("STD-TC-001", "STD-TC-ORPHAN",),
        test_requirement_links={"STD-TC-001": ("HISYS-FR-001",)},
    )

    report = build_traceability_coverage_report(anchors)

    assert report.requirement_count == 2
    assert report.covered_requirement_count == 1
    assert report.unreferenced_requirements == ("HISYS-FR-002",)
    assert report.orphan_test_ids == ("STD-TC-ORPHAN",)
    assert report.coverage_ratio == 0.5
    assert report.advisory_only is True
    assert report.requires_human_review is True


def test_traceability_coverage_writer_persists_bounded_runtime_artifacts(tmp_path) -> None:
    report = build_traceability_coverage_report(
        TraceabilityAnchors(
            requirement_ids=("HISYS-FR-001",),
            design_requirement_refs={"HISYS-FR-001": ("SDD-MOD-001",)},
            test_requirement_refs={"HISYS-FR-001": ("STD-TC-001",)},
            test_ids=("STD-TC-001",),
            test_requirement_links={"STD-TC-001": ("HISYS-FR-001",)},
        )
    )

    refs = write_traceability_coverage_report(
        instance_root=tmp_path, date="20260520", report=report
    )

    json_path = tmp_path / refs["json_ref"]
    markdown_path = tmp_path / refs["markdown_ref"]
    payload = json.loads(json_path.read_text())
    markdown = markdown_path.read_text()
    assert refs["json_ref"] == "runtime-boundary/traceability-coverage/20260520/coverage-report.json"
    assert payload["raw_source_content_persisted"] is False
    assert payload["external_call_made"] is False
    assert payload["mutation_performed"] is False
    assert "advisory_only: true" in markdown
    assert "raw_source_content_persisted: false" in markdown
