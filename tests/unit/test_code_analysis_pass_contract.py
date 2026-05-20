"""Tests for the M21.8 code-analysis pass-contract evidence adapter and writer.

This file pins the M21.8.1.A boundary invariants for two question types:
``traceability_coverage_review`` and ``runtime_boundary_consistency_review``.
The remaining three question types declared in the M21.8 PREP doc raise
``NotImplementedError`` until follow-up increments add their mapping rules.

Traceability: HISYS-FR-DOM-001..006, HISYS-DARS-CONTRACT-001, HISYS-T-024.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.contracts.evaluator import EvidenceSummary, PassContractEvaluationResult
from hisys.operations.code_analysis_pass_contract import (
    build_code_analysis_evidence_summary,
    write_code_analysis_pass_contract_evaluation,
)


def _m21_1_coverage_payload() -> dict[str, object]:
    return {
        "schema_id": "hisys.traceability.coverage.v1",
        "requirement_count": 3,
        "covered_requirement_count": 3,
        "coverage_ratio": 1.0,
        "unreferenced_requirements": [],
        "orphan_test_ids": [],
    }


def _m21_3_consistency_payload_clean() -> dict[str, object]:
    return {
        "schema_id": "hisys.runtime_boundary.consistency.v1",
        "ok_ref_count": 4,
        "unsafe_refs": [],
        "missing_files": [],
        "malformed_json_refs": [],
        "missing_markdown_pair_refs": [],
        "missing_advisory_flag_refs": [],
        "outside_runtime_boundary_refs": [],
    }


def _m21_3_consistency_payload_unsafe() -> dict[str, object]:
    return {
        "schema_id": "hisys.runtime_boundary.consistency.v1",
        "ok_ref_count": 2,
        "unsafe_refs": ["/etc/passwd"],
        "missing_files": ["runtime-boundary/codebase-analysis/20260520/REQ/missing.json"],
        "malformed_json_refs": [],
        "missing_markdown_pair_refs": [],
        "missing_advisory_flag_refs": [],
        "outside_runtime_boundary_refs": ["../../escape.json"],
    }


def test_build_code_analysis_evidence_summary_maps_m21_1_payload_to_artifact_refs() -> None:
    summary = build_code_analysis_evidence_summary(
        question_type="traceability_coverage_review",
        coverage_report=_m21_1_coverage_payload(),
    )
    assert isinstance(summary, EvidenceSummary)
    assert summary.artifact_refs == ["hisys.traceability.coverage.v1"]
    assert summary.claims_covered is True
    assert summary.boundary_violation_detected is False
    assert summary.alternative_count == 0
    assert summary.dars_critique_refs == []
    assert summary.consequential_use is False
    assert summary.human_approval_ref is None


def test_build_code_analysis_evidence_summary_flags_uncovered_requirements() -> None:
    payload = _m21_1_coverage_payload()
    payload["unreferenced_requirements"] = ["HISYS-FR-X-001"]
    summary = build_code_analysis_evidence_summary(
        question_type="traceability_coverage_review",
        coverage_report=payload,
    )
    assert summary.claims_covered is False
    assert summary.boundary_violation_detected is False


def test_build_code_analysis_evidence_summary_requires_coverage_for_traceability_review() -> None:
    with pytest.raises(ValueError, match="coverage_report"):
        build_code_analysis_evidence_summary(
            question_type="traceability_coverage_review",
            coverage_report=None,
        )


def test_build_code_analysis_evidence_summary_marks_boundary_violation_on_unsafe_refs() -> None:
    summary = build_code_analysis_evidence_summary(
        question_type="runtime_boundary_consistency_review",
        boundary_report=_m21_3_consistency_payload_unsafe(),
    )
    assert summary.boundary_violation_detected is True
    assert summary.claims_covered is False
    assert "/etc/passwd" in summary.artifact_refs
    assert "../../escape.json" in summary.artifact_refs


def test_build_code_analysis_evidence_summary_passes_clean_consistency_review() -> None:
    summary = build_code_analysis_evidence_summary(
        question_type="runtime_boundary_consistency_review",
        boundary_report=_m21_3_consistency_payload_clean(),
    )
    assert summary.boundary_violation_detected is False
    assert summary.claims_covered is True
    assert summary.artifact_refs == ["hisys.runtime_boundary.consistency.v1"]


def test_build_code_analysis_evidence_summary_requires_boundary_for_consistency_review() -> None:
    with pytest.raises(ValueError, match="boundary_report"):
        build_code_analysis_evidence_summary(
            question_type="runtime_boundary_consistency_review",
            boundary_report=None,
        )


@pytest.mark.parametrize(
    "question_type",
    [
        "codebase_map_freshness_review",
        "change_impact_review",
        "architecture_candidate_review",
    ],
)
def test_build_code_analysis_evidence_summary_defers_other_question_types(
    question_type: str,
) -> None:
    with pytest.raises(NotImplementedError, match=question_type):
        build_code_analysis_evidence_summary(question_type=question_type)


def test_build_code_analysis_evidence_summary_rejects_unknown_question_type() -> None:
    with pytest.raises(ValueError, match="unknown_review"):
        build_code_analysis_evidence_summary(question_type="unknown_review")


def test_write_code_analysis_pass_contract_evaluation_round_trips_advisory_flags(
    tmp_path: Path,
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    result = PassContractEvaluationResult(
        contract_id="code_analysis_traceability_coverage_review_v0_1_candidate",
        quality_gate="passed",
        blockers=[],
    )
    written = write_code_analysis_pass_contract_evaluation(
        instance_root=instance_root,
        date="20260521",
        contract_id=result.contract_id,
        result=result,
        human_approval_ref=None,
    )
    json_path = (
        instance_root
        / "runtime-boundary"
        / "code-analysis-pass-contracts"
        / "20260521"
        / f"{result.contract_id}-evaluation.json"
    )
    md_path = (
        instance_root
        / "runtime-boundary"
        / "code-analysis-pass-contracts"
        / "20260521"
        / f"{result.contract_id}-evaluation.md"
    )
    assert json_path.exists()
    assert md_path.exists()
    assert written["json_ref"].endswith(f"{result.contract_id}-evaluation.json")
    assert written["markdown_ref"].endswith(f"{result.contract_id}-evaluation.md")
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["schema_id"] == "hisys.code_analysis_pass_contract.evaluation.v1"
    assert payload["contract_id"] == result.contract_id
    assert payload["quality_gate"] == "passed"
    assert payload["advisory_only"] is True
    assert payload["requires_human_review"] is True
    assert payload["external_call_made"] is False
    assert payload["mutation_performed"] is False
    assert payload["raw_source_content_persisted"] is False
    assert payload["human_approval_ref"] is None


def test_write_code_analysis_pass_contract_evaluation_records_human_approval_ref(
    tmp_path: Path,
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    result = PassContractEvaluationResult(
        contract_id="code_analysis_runtime_boundary_consistency_review_v0_1_candidate",
        quality_gate="human_approval_required",
        blockers=["human_approval_required"],
    )
    write_code_analysis_pass_contract_evaluation(
        instance_root=instance_root,
        date="20260521",
        contract_id=result.contract_id,
        result=result,
        human_approval_ref="APPROVAL-CA-20260521-001",
    )
    json_path = (
        instance_root
        / "runtime-boundary"
        / "code-analysis-pass-contracts"
        / "20260521"
        / f"{result.contract_id}-evaluation.json"
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["human_approval_ref"] == "APPROVAL-CA-20260521-001"


def test_write_code_analysis_pass_contract_evaluation_rejects_non_yyyymmdd_date(
    tmp_path: Path,
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    result = PassContractEvaluationResult(
        contract_id="any",
        quality_gate="passed",
        blockers=[],
    )
    with pytest.raises(ValueError, match="20260521-01"):
        write_code_analysis_pass_contract_evaluation(
            instance_root=instance_root,
            date="20260521-01",
            contract_id=result.contract_id,
            result=result,
        )
