"""Focused unit tests for the M21.3 runtime-boundary consistency checker.

The checker is pure and advisory only: it reads bounded refs under
``runtime-boundary/`` through the existing safe chokepoint, classifies each
into a small issue vocabulary, and writes a JSON/Markdown report under
``runtime-boundary/runtime-boundary-consistency/<YYYYMMDD>/``. These tests pin
the safe-ref accept path, the unsafe/missing/malformed reject paths, and the
writer invariants.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.operations.runtime_boundary_consistency import (
    build_runtime_boundary_consistency_report,
    write_runtime_boundary_consistency_report,
)


def _seed_complete_traceability_coverage_artifact(instance_root: Path) -> tuple[str, str]:
    json_ref = "runtime-boundary/traceability-coverage/20260520/coverage-report.json"
    md_ref = "runtime-boundary/traceability-coverage/20260520/coverage-report.md"
    json_path = instance_root / json_ref
    md_path = instance_root / md_ref
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(
            {
                "schema_id": "hisys.traceability.coverage.v1",
                "advisory_only": True,
                "requires_human_review": True,
                "external_call_made": False,
                "mutation_performed": False,
                "raw_source_content_persisted": False,
                "requirement_count": 1,
                "covered_requirement_count": 1,
                "coverage_ratio": 1.0,
                "unreferenced_requirements": [],
                "orphan_test_ids": [],
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    md_path.write_text("# coverage\n- advisory_only: true\n", encoding="utf-8")
    return json_ref, md_ref


def test_runtime_boundary_consistency_flags_missing_and_unsafe_refs(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    json_ref, md_ref = _seed_complete_traceability_coverage_artifact(instance_root)

    report = build_runtime_boundary_consistency_report(
        instance_root=instance_root,
        candidate_refs=(
            json_ref,
            md_ref,
            "runtime-boundary/codebase-analysis/20260520/REQ-MISSING/inventory.json",
            "runtime-boundary/../escape.txt",
            "reports/run-summaries/20260520/domain-investigation-report.json",
        ),
    )

    assert report.schema_id == "hisys.runtime_boundary.consistency.v1"
    assert report.advisory_only is True
    assert report.requires_human_review is True
    assert report.external_call_made is False
    assert report.mutation_performed is False
    assert report.raw_source_content_persisted is False
    assert report.ok_ref_count == 2
    assert report.unsafe_refs == ("runtime-boundary/../escape.txt",)
    assert report.missing_files == (
        "runtime-boundary/codebase-analysis/20260520/REQ-MISSING/inventory.json",
    )
    assert report.malformed_json_refs == ()
    assert report.missing_markdown_pair_refs == ()
    assert report.missing_advisory_flag_refs == ()
    assert report.outside_runtime_boundary_refs == (
        "reports/run-summaries/20260520/domain-investigation-report.json",
    )


def test_runtime_boundary_consistency_flags_malformed_and_missing_markdown_pair(
    tmp_path: Path,
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()

    malformed_ref = "runtime-boundary/traceability-coverage/20260520/coverage-report.json"
    malformed_path = instance_root / malformed_ref
    malformed_path.parent.mkdir(parents=True, exist_ok=True)
    malformed_path.write_text("{not-json", encoding="utf-8")

    missing_pair_ref = (
        "runtime-boundary/codebase-analysis/20260520/REQ-M21-3-PAIR/inventory.json"
    )
    missing_pair_path = instance_root / missing_pair_ref
    missing_pair_path.parent.mkdir(parents=True, exist_ok=True)
    missing_pair_path.write_text(
        json.dumps(
            {
                "schema_id": "hisys.codebase.inventory",
                "advisory_only": True,
                "requires_human_review": True,
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    no_flag_ref = (
        "runtime-boundary/codebase-analysis/20260520/REQ-M21-3-FLAG/symbol-index.json"
    )
    no_flag_path = instance_root / no_flag_ref
    no_flag_path.parent.mkdir(parents=True, exist_ok=True)
    no_flag_path.write_text(
        json.dumps({"schema_id": "hisys.codebase.symbol_index"}, sort_keys=True, indent=2)
        + "\n",
        encoding="utf-8",
    )

    report = build_runtime_boundary_consistency_report(
        instance_root=instance_root,
        candidate_refs=(malformed_ref, missing_pair_ref, no_flag_ref),
    )

    assert report.malformed_json_refs == (malformed_ref,)
    assert report.missing_markdown_pair_refs == (missing_pair_ref,)
    assert report.missing_advisory_flag_refs == (no_flag_ref,)
    assert report.ok_ref_count == 0


def test_write_runtime_boundary_consistency_report_persists_safe_refs(
    tmp_path: Path,
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()

    report = build_runtime_boundary_consistency_report(
        instance_root=instance_root, candidate_refs=()
    )
    refs = write_runtime_boundary_consistency_report(
        instance_root=instance_root, date="20260520", report=report
    )

    expected_json_ref = (
        "runtime-boundary/runtime-boundary-consistency/20260520/consistency-report.json"
    )
    expected_md_ref = (
        "runtime-boundary/runtime-boundary-consistency/20260520/consistency-report.md"
    )
    assert refs["json_ref"] == expected_json_ref
    assert refs["markdown_ref"] == expected_md_ref
    assert refs["advisory_only"] is True
    assert refs["requires_human_review"] is True
    assert refs["external_call_made"] is False
    assert refs["mutation_performed"] is False
    assert refs["raw_source_content_persisted"] is False

    json_path = instance_root / expected_json_ref
    md_path = instance_root / expected_md_ref
    assert json_path.is_file()
    assert md_path.is_file()

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema_id"] == "hisys.runtime_boundary.consistency.v1"
    assert data["advisory_only"] is True
    assert data["mutation_performed"] is False
    md_text = md_path.read_text(encoding="utf-8")
    assert "advisory_only: true" in md_text
    assert "external_call_made: false" in md_text


def test_build_runtime_boundary_consistency_report_rejects_traversal(
    tmp_path: Path,
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    report = build_runtime_boundary_consistency_report(
        instance_root=instance_root,
        candidate_refs=(
            "runtime-boundary/../escape.txt",
            "runtime-boundary//evil/../leak.json",
        ),
    )
    assert set(report.unsafe_refs) == {
        "runtime-boundary/../escape.txt",
        "runtime-boundary//evil/../leak.json",
    }
    assert report.ok_ref_count == 0
    assert report.missing_files == ()


def test_write_runtime_boundary_consistency_report_rejects_invalid_date(
    tmp_path: Path,
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    report = build_runtime_boundary_consistency_report(
        instance_root=instance_root, candidate_refs=()
    )
    try:
        write_runtime_boundary_consistency_report(
            instance_root=instance_root, date="2026-05-20", report=report
        )
    except ValueError as exc:
        assert "invalid" in str(exc).lower()
    else:  # pragma: no cover - defensive
        raise AssertionError("expected ValueError for non-YYYYMMDD date")
