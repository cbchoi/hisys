"""Focused unit tests for the M21.7 architecture candidate generator.

The generator is pure and advisory only: callers supply already-trusted
M21.1/M21.4/M21.6 dict payloads, and the generator emits bounded
``ArchitectureCandidate`` records labeled only as ``advisory_candidate`` or
``advisory_candidate_low_evidence``. Imperative wording such as
``recommended``, ``required``, ``approved``, ``must``, ``next step``, or
``should`` must never appear in any candidate ``summary`` / ``rationale``
field; this is pinned by ``test_*_rejects_imperative_wording``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.operations.architecture_candidates import (
    ArchitectureCandidateInputs,
    build_architecture_candidate_report,
    write_architecture_candidate_report,
)


def _coverage_payload() -> dict:
    return {
        "schema_id": "hisys.traceability.coverage.v1",
        "advisory_only": True,
        "requires_human_review": True,
        "external_call_made": False,
        "mutation_performed": False,
        "raw_source_content_persisted": False,
        "requirement_count": 3,
        "covered_requirement_count": 1,
        "coverage_ratio": 0.3333,
        "unreferenced_requirements": ["HISYS-FR-DOM-002", "HISYS-NFR-MNT-001"],
        "orphan_test_ids": [],
    }


def _freshness_payload() -> dict:
    return {
        "schema_id": "hisys.codebase_map.freshness.v1",
        "advisory_only": True,
        "requires_human_review": True,
        "external_call_made": False,
        "mutation_performed": False,
        "raw_source_content_persisted": False,
        "current_date": "2026-05-21",
        "max_age_days": 30,
        "current_head_short": "3297909",
        "fresh_partitions": [],
        "stale_partitions": [
            "runtime-boundary/codebase-analysis/20260301/REQ-OLD"
        ],
        "incomplete_partitions": [],
        "unsafe_partitions": [],
    }


def _impact_payload() -> dict:
    return {
        "schema_id": "hisys.change_impact.v1",
        "advisory_only": True,
        "requires_human_review": True,
        "external_call_made": False,
        "mutation_performed": False,
        "raw_source_content_persisted": False,
        "current_head_short": "3297909",
        "changed_ref_count": 5,
        "impacted_requirement_ids": ["HISYS-FR-DOM-001", "HISYS-FR-DOM-002"],
        "impacted_test_id_or_refs": [],
        "impacted_design_or_interface_refs": [
            "docs/traceability/README.md",
            "src/hisys/schemas/domain_adapter.py",
        ],
        "impacted_runtime_boundary_refs": [],
        "unmapped_changed_refs": ["src/hisys/agents/unrelated_helper.py"],
        "unsafe_changed_refs": [],
    }


_FORBIDDEN_IMPERATIVE_TOKENS = (
    "recommended",
    "required",
    "approved",
    "must",
    "next step",
    "should",
)


def test_build_architecture_candidate_report_produces_bounded_candidates(
    tmp_path: Path,
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()

    inputs = ArchitectureCandidateInputs(
        instance_root=instance_root,
        coverage_report=_coverage_payload(),
        freshness_report=_freshness_payload(),
        change_impact_report=_impact_payload(),
        current_head_short="3297909",
    )

    report = build_architecture_candidate_report(inputs=inputs)

    assert report.schema_id == "hisys.architecture_candidates.v1"
    assert report.advisory_only is True
    assert report.requires_human_review is True
    assert report.external_call_made is False
    assert report.mutation_performed is False
    assert report.raw_source_content_persisted is False
    assert report.current_head_short == "3297909"
    assert report.candidate_count == len(report.candidates)

    kinds = [c.kind for c in report.candidates]
    assert "coverage_gap" in kinds
    assert "freshness_drift" in kinds
    assert "change_impact_concentration" in kinds
    assert "cross_signal_alignment" in kinds

    for candidate in report.candidates:
        assert candidate.recommendation_strength in (
            "advisory_candidate",
            "advisory_candidate_low_evidence",
        )
        lowered_summary = candidate.summary.lower()
        lowered_rationale = candidate.rationale.lower()
        for forbidden in _FORBIDDEN_IMPERATIVE_TOKENS:
            assert forbidden not in lowered_summary
            assert forbidden not in lowered_rationale


def test_write_architecture_candidate_report_persists_safe_refs(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    inputs = ArchitectureCandidateInputs(
        instance_root=instance_root,
        coverage_report=_coverage_payload(),
        freshness_report=None,
        change_impact_report=None,
    )
    report = build_architecture_candidate_report(inputs=inputs)
    refs = write_architecture_candidate_report(
        instance_root=instance_root, date="20260521", report=report
    )
    assert refs["json_ref"] == (
        "runtime-boundary/architecture-candidates/20260521/"
        "architecture-candidates-report.json"
    )
    assert refs["markdown_ref"] == (
        "runtime-boundary/architecture-candidates/20260521/"
        "architecture-candidates-report.md"
    )
    assert refs["external_call_made"] is False
    assert refs["mutation_performed"] is False
    assert refs["raw_source_content_persisted"] is False
    json_path = instance_root / refs["json_ref"]
    md_path = instance_root / refs["markdown_ref"]
    assert json_path.is_file()
    assert md_path.is_file()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["schema_id"] == "hisys.architecture_candidates.v1"
    assert payload["advisory_only"] is True


def test_build_architecture_candidate_report_rejects_imperative_wording(
    tmp_path: Path,
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    inputs = ArchitectureCandidateInputs(
        instance_root=instance_root,
        coverage_report=_coverage_payload(),
        freshness_report=_freshness_payload(),
        change_impact_report=_impact_payload(),
    )
    report = build_architecture_candidate_report(inputs=inputs)
    assert report.candidate_count > 0
    for candidate in report.candidates:
        lowered_summary = candidate.summary.lower()
        lowered_rationale = candidate.rationale.lower()
        for forbidden in _FORBIDDEN_IMPERATIVE_TOKENS:
            assert forbidden not in lowered_summary
            assert forbidden not in lowered_rationale


def test_build_architecture_candidate_report_handles_missing_inputs(
    tmp_path: Path,
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    inputs = ArchitectureCandidateInputs(
        instance_root=instance_root,
        coverage_report=None,
        freshness_report=None,
        change_impact_report=None,
    )
    report = build_architecture_candidate_report(inputs=inputs)
    assert report.candidate_count == 0
    assert report.candidates == ()


def test_write_architecture_candidate_report_rejects_bad_date(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    inputs = ArchitectureCandidateInputs(
        instance_root=instance_root,
        coverage_report=None,
        freshness_report=None,
        change_impact_report=None,
    )
    report = build_architecture_candidate_report(inputs=inputs)
    with pytest.raises(ValueError):
        write_architecture_candidate_report(
            instance_root=instance_root, date="2026-05-21", report=report
        )
