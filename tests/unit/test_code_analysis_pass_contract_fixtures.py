"""M21.8.2 code-analysis pass-contract fixture sanity tests.

Traceability: HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001, HISYS-T-024.

These tests pin the five M21.8 PREP code-analysis question types under
``tests/fixtures/pass-contracts/code_analysis/``. They enforce candidate-only
status, no automatic promotion, no live side effects, only the existing
``minimum_evidence`` keys, only existing ``blocked_if`` reason codes, and a
deterministic match between each fixture's gate semantics and the M21.8.1
adapter output for representative payloads.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from hisys.contracts.evaluator import evaluate_pass_contract
from hisys.contracts.pass_registry import load_pass_contract_registry
from hisys.operations.code_analysis_pass_contract import (
    build_code_analysis_evidence_summary,
)

_FIXTURE_DIR = (
    Path(__file__).resolve().parent.parent
    / "fixtures"
    / "pass-contracts"
    / "code_analysis"
)

_EXPECTED_FIXTURES: tuple[tuple[str, str, str], ...] = (
    (
        "traceability_coverage_review.json",
        "traceability_coverage_review",
        "code_analysis_traceability_coverage_review_v0_1_candidate",
    ),
    (
        "runtime_boundary_consistency_review.json",
        "runtime_boundary_consistency_review",
        "code_analysis_runtime_boundary_consistency_review_v0_1_candidate",
    ),
    (
        "codebase_map_freshness_review.json",
        "codebase_map_freshness_review",
        "code_analysis_codebase_map_freshness_review_v0_1_candidate",
    ),
    (
        "change_impact_review.json",
        "change_impact_review",
        "code_analysis_change_impact_review_v0_1_candidate",
    ),
    (
        "architecture_candidate_review.json",
        "architecture_candidate_review",
        "code_analysis_architecture_candidate_review_v0_1_candidate",
    ),
)

_ALLOWED_MIN_EVIDENCE_KEYS = {
    "artifact_refs_required",
    "alternative_set_required",
    "claim_coverage_required",
    "contradiction_check_required",
    "dars_critique_required",
}

_ALLOWED_BLOCKED_IF = {
    "no_traceable_artifact_refs",
    "alternative_set_incomplete",
    "claim_coverage_incomplete",
    "contradiction_unchecked",
    "dars_critique_missing",
    "boundary_violation_detected",
    "human_approval_required",
}


def _clean_coverage_payload() -> dict[str, Any]:
    return {
        "schema_id": "hisys.traceability.coverage.v1",
        "requirement_count": 2,
        "covered_requirement_count": 2,
        "coverage_ratio": 1.0,
        "unreferenced_requirements": [],
        "orphan_test_ids": [],
    }


def _clean_freshness_payload() -> dict[str, Any]:
    return {
        "schema_id": "hisys.codebase_map.freshness.v1",
        "fresh_partitions": ["docs/runtime-boundary/A"],
        "stale_partitions": [],
        "incomplete_partitions": [],
        "unsafe_partitions": [],
    }


def _clean_change_impact_payload() -> dict[str, Any]:
    return {
        "schema_id": "hisys.change_impact.v1",
        "changed_ref_count": 1,
        "impacted_requirement_ids": ["HISYS-FR-DOM-001"],
        "impacted_test_id_or_refs": [],
        "impacted_design_or_interface_refs": [],
        "impacted_runtime_boundary_refs": [],
        "unmapped_changed_refs": [],
        "unsafe_changed_refs": [],
    }


def test_code_analysis_fixture_directory_exists():
    assert _FIXTURE_DIR.is_dir(), (
        f"missing M21.8.2 fixture directory: {_FIXTURE_DIR}"
    )


@pytest.mark.parametrize(
    ("filename", "question_type", "contract_id"), _EXPECTED_FIXTURES
)
def test_code_analysis_fixture_is_candidate_only(
    filename: str, question_type: str, contract_id: str
):
    path = _FIXTURE_DIR / filename
    assert path.is_file(), f"missing fixture: {path}"
    [entry] = load_pass_contract_registry(path)
    assert entry.contract_id == contract_id
    assert entry.domain == "code_analysis"
    assert entry.question_type == question_type
    assert entry.status == "candidate"
    assert entry.active is False
    assert entry.automatic_promotion_allowed is False
    assert entry.external_call_made is False
    assert entry.mutation_performed is False
    assert entry.publication_or_live_action_approved is False
    assert entry.human_approval_ref is None
    assert entry.promotion_gate == "human_reviewed_traceable_change"
    assert entry.review_refs == []


@pytest.mark.parametrize(
    ("filename", "question_type", "contract_id"), _EXPECTED_FIXTURES
)
def test_code_analysis_fixture_uses_only_recognized_taxonomy(
    filename: str, question_type: str, contract_id: str
):
    path = _FIXTURE_DIR / filename
    [entry] = load_pass_contract_registry(path)
    extra_keys = set(entry.minimum_evidence) - _ALLOWED_MIN_EVIDENCE_KEYS
    assert not extra_keys, f"unknown minimum_evidence keys: {sorted(extra_keys)}"
    for value in entry.minimum_evidence.values():
        assert isinstance(value, bool)
    invalid_codes = set(entry.blocked_if) - _ALLOWED_BLOCKED_IF
    assert not invalid_codes, (
        f"unknown blocked_if codes: {sorted(invalid_codes)}"
    )


def test_code_analysis_fixtures_cover_all_question_types():
    paths = sorted(_FIXTURE_DIR.glob("*.json"))
    question_types: set[str] = set()
    for path in paths:
        [entry] = load_pass_contract_registry(path)
        question_types.add(entry.question_type)
    assert question_types == {qt for _, qt, _ in _EXPECTED_FIXTURES}
    assert len(paths) == len(_EXPECTED_FIXTURES)


def test_traceability_coverage_review_passes_on_clean_payload():
    [entry] = load_pass_contract_registry(
        _FIXTURE_DIR / "traceability_coverage_review.json"
    )
    summary = build_code_analysis_evidence_summary(
        question_type="traceability_coverage_review",
        coverage_report=_clean_coverage_payload(),
    )
    result = evaluate_pass_contract(entry, summary)
    assert result.quality_gate == "passed"
    assert result.blockers == []
    assert result.external_call_made is False
    assert result.mutation_performed is False


def test_traceability_coverage_review_blocks_on_unreferenced_requirements():
    [entry] = load_pass_contract_registry(
        _FIXTURE_DIR / "traceability_coverage_review.json"
    )
    payload = _clean_coverage_payload()
    payload["unreferenced_requirements"] = ["HISYS-FR-DOM-099"]
    summary = build_code_analysis_evidence_summary(
        question_type="traceability_coverage_review",
        coverage_report=payload,
    )
    result = evaluate_pass_contract(entry, summary)
    assert result.quality_gate == "needs_more_evidence"
    assert "claim_coverage_incomplete" in result.blockers


def test_runtime_boundary_consistency_review_passes_on_clean_payload():
    [entry] = load_pass_contract_registry(
        _FIXTURE_DIR / "runtime_boundary_consistency_review.json"
    )
    summary = build_code_analysis_evidence_summary(
        question_type="runtime_boundary_consistency_review",
        boundary_report={
            "schema_id": "hisys.runtime_boundary.consistency.v1",
            "ok_ref_count": 3,
            "unsafe_refs": [],
            "missing_files": [],
            "malformed_json_refs": [],
            "missing_markdown_pair_refs": [],
            "missing_advisory_flag_refs": [],
            "outside_runtime_boundary_refs": [],
        },
    )
    result = evaluate_pass_contract(entry, summary)
    assert result.quality_gate == "passed"
    assert result.blockers == []


def test_runtime_boundary_consistency_review_fails_on_unsafe_refs():
    [entry] = load_pass_contract_registry(
        _FIXTURE_DIR / "runtime_boundary_consistency_review.json"
    )
    summary = build_code_analysis_evidence_summary(
        question_type="runtime_boundary_consistency_review",
        boundary_report={
            "schema_id": "hisys.runtime_boundary.consistency.v1",
            "ok_ref_count": 2,
            "unsafe_refs": ["runtime-boundary/bad/ref.json"],
            "missing_files": [],
            "malformed_json_refs": [],
            "missing_markdown_pair_refs": [],
            "missing_advisory_flag_refs": [],
            "outside_runtime_boundary_refs": [],
        },
    )
    result = evaluate_pass_contract(entry, summary)
    assert result.quality_gate == "failed"
    assert result.blockers == ["boundary_violation_detected"]


def test_codebase_map_freshness_review_passes_on_fresh_payload():
    [entry] = load_pass_contract_registry(
        _FIXTURE_DIR / "codebase_map_freshness_review.json"
    )
    summary = build_code_analysis_evidence_summary(
        question_type="codebase_map_freshness_review",
        freshness_report=_clean_freshness_payload(),
    )
    result = evaluate_pass_contract(entry, summary)
    assert result.quality_gate == "passed"
    assert result.blockers == []


def test_codebase_map_freshness_review_blocks_on_stale_partition():
    [entry] = load_pass_contract_registry(
        _FIXTURE_DIR / "codebase_map_freshness_review.json"
    )
    payload = _clean_freshness_payload()
    payload["stale_partitions"] = ["docs/runtime-boundary/B"]
    summary = build_code_analysis_evidence_summary(
        question_type="codebase_map_freshness_review",
        freshness_report=payload,
    )
    result = evaluate_pass_contract(entry, summary)
    assert result.quality_gate == "needs_more_evidence"
    assert "claim_coverage_incomplete" in result.blockers


def test_change_impact_review_passes_with_cross_signal_coverage():
    [entry] = load_pass_contract_registry(
        _FIXTURE_DIR / "change_impact_review.json"
    )
    summary = build_code_analysis_evidence_summary(
        question_type="change_impact_review",
        change_impact_report=_clean_change_impact_payload(),
        coverage_report=_clean_coverage_payload(),
    )
    result = evaluate_pass_contract(entry, summary)
    assert result.quality_gate == "passed"
    assert result.blockers == []


def test_change_impact_review_blocks_without_cross_signal_coverage():
    [entry] = load_pass_contract_registry(
        _FIXTURE_DIR / "change_impact_review.json"
    )
    summary = build_code_analysis_evidence_summary(
        question_type="change_impact_review",
        change_impact_report=_clean_change_impact_payload(),
    )
    result = evaluate_pass_contract(entry, summary)
    assert result.quality_gate == "needs_more_evidence"
    assert "contradiction_unchecked" in result.blockers


def test_architecture_candidate_review_passes_full_cross_signal():
    [entry] = load_pass_contract_registry(
        _FIXTURE_DIR / "architecture_candidate_review.json"
    )
    summary = build_code_analysis_evidence_summary(
        question_type="architecture_candidate_review",
        architecture_candidates_report={
            "schema_id": "hisys.architecture_candidates.v1",
            "candidates": [
                {
                    "summary": "alpha",
                    "rationale": "rationale alpha",
                    "supporting_refs": ["HISYS-FR-DOM-001"],
                },
                {
                    "summary": "beta",
                    "rationale": "rationale beta",
                    "supporting_refs": ["HISYS-FR-DOM-002"],
                },
            ],
        },
        coverage_report=_clean_coverage_payload(),
        freshness_report=_clean_freshness_payload(),
        change_impact_report=_clean_change_impact_payload(),
    )
    result = evaluate_pass_contract(entry, summary)
    assert result.quality_gate == "passed"
    assert result.blockers == []


def test_architecture_candidate_review_blocks_on_single_candidate():
    [entry] = load_pass_contract_registry(
        _FIXTURE_DIR / "architecture_candidate_review.json"
    )
    summary = build_code_analysis_evidence_summary(
        question_type="architecture_candidate_review",
        architecture_candidates_report={
            "schema_id": "hisys.architecture_candidates.v1",
            "candidates": [
                {
                    "summary": "alpha",
                    "rationale": "rationale alpha",
                    "supporting_refs": ["HISYS-FR-DOM-001"],
                }
            ],
        },
        coverage_report=_clean_coverage_payload(),
        freshness_report=_clean_freshness_payload(),
        change_impact_report=_clean_change_impact_payload(),
    )
    result = evaluate_pass_contract(entry, summary)
    assert result.quality_gate == "needs_more_evidence"
    assert "alternative_set_incomplete" in result.blockers
