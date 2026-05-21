"""CLI tests for domain-general Hisys MVP boundary.

Traceability: HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001, HISYS-T-024,
HISYS-CON-010..012.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from hisys.cli.main import main
from hisys.connectors.claim_coverage_gate import ClaimCoverageGateBuilder
from hisys.connectors.claim_evidence_ledger import ClaimEvidenceLedgerBuilder
from hisys.connectors.claim_evidence_summary import ClaimEvidenceSummaryBuilder
from hisys.connectors.open_access_pdf import OpenAccessPdfConnector
from hisys.connectors.recommendation_claim_registry import RecommendationClaimRegistryBuilder
from hisys.connectors.pdf_evidence_promotion import PdfEvidencePromotionLoader
from hisys.connectors.pdf_quote_extractor import PdfQuoteExtractor
from hisys.operations.codebase_analysis import (
    build_codebase_inventory,
    build_codebase_scope_map,
    build_codebase_validation_plan,
    build_python_symbol_index,
    scan_codebase_risk_boundaries,
    write_codebase_inventory,
    write_codebase_risk_scan,
    write_codebase_scope_map,
    write_python_symbol_index,
)


def _write_domain_request(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "producer_id": "hermes",
                "status": "submitted",
                "request_id": "HISYS-REQ-RESEARCH-GAP-001",
                "domain": "research",
                "objective": "find research gap among formalisms for self-organizing structure",
                "sources": [
                    {
                        "source_id": "SRC-FORMALISM-FIXTURE-001",
                        "source_type": "fixture",
                        "ref": "fixture://formalism-gap",
                        "access_mode": "read_only",
                    }
                ],
                "user_focus": "Separate source evidence from interpreted gap statements.",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def test_codebase_map_freshness_review_cli_writes_report(tmp_path: Path, capsys) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    partition_dir = (
        instance_root
        / "runtime-boundary"
        / "codebase-analysis"
        / "20260518"
        / "REQ-CLI-FRESH"
    )
    partition_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "inventory.json",
        "symbol-index.json",
        "scope-map.json",
        "risk-scan.json",
    ):
        (partition_dir / name).write_text("{}\n", encoding="utf-8")

    result = main(
        [
            "codebase-map-freshness-review",
            "--instance",
            str(instance_root),
            "--date",
            "20260520",
            "--current-date",
            "2026-05-20",
            "--max-age-days",
            "30",
            "--current-head-short",
            "1cb2857",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "codebase map freshness report" in captured.out
    assert "external_call_made: false" in captured.out

    json_path = (
        instance_root
        / "runtime-boundary"
        / "codebase-map-freshness"
        / "20260520"
        / "freshness-report.json"
    )
    md_path = (
        instance_root
        / "runtime-boundary"
        / "codebase-map-freshness"
        / "20260520"
        / "freshness-report.md"
    )
    assert json_path.exists()
    assert md_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema_id"] == "hisys.codebase_map.freshness.v1"
    assert data["advisory_only"] is True
    assert data["current_date"] == "2026-05-20"
    assert data["max_age_days"] == 30
    assert data["current_head_short"] == "1cb2857"
    assert data["fresh_partitions"] == [
        "runtime-boundary/codebase-analysis/20260518/REQ-CLI-FRESH"
    ]


def test_change_impact_cli_writes_report(tmp_path: Path, capsys) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    repo_root = Path(__file__).resolve().parents[2]

    result = main(
        [
            "change-impact",
            "--instance",
            str(instance_root),
            "--date",
            "20260521",
            "--repo",
            str(repo_root),
            "--changed-ref",
            "docs/traceability/README.md",
            "--changed-ref",
            "src/hisys/agents/unrelated_helper.py",
            "--changed-ref",
            "runtime-boundary/codebase-analysis/20260520/REQ-X/inventory.json",
            "--changed-ref",
            "/etc/passwd",
            "--current-head-short",
            "7c4d5d0",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "change-impact report" in captured.out
    assert "external_call_made: false" in captured.out
    assert "allowed_actions: advisory_only" in captured.out

    json_path = (
        instance_root
        / "runtime-boundary"
        / "change-impact"
        / "20260521"
        / "impact-report.json"
    )
    md_path = (
        instance_root
        / "runtime-boundary"
        / "change-impact"
        / "20260521"
        / "impact-report.md"
    )
    assert json_path.exists()
    assert md_path.exists()

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema_id"] == "hisys.change_impact.v1"
    assert data["advisory_only"] is True
    assert data["external_call_made"] is False
    assert data["mutation_performed"] is False
    assert data["raw_source_content_persisted"] is False
    assert data["current_head_short"] == "7c4d5d0"
    assert data["changed_ref_count"] == 4
    assert "/etc/passwd" in data["unsafe_changed_refs"]
    assert (
        "runtime-boundary/codebase-analysis/20260520/REQ-X/inventory.json"
        in data["impacted_runtime_boundary_refs"]
    )
    assert (
        "docs/traceability/README.md"
        in data["impacted_design_or_interface_refs"]
    )
    assert "src/hisys/agents/unrelated_helper.py" in data["unmapped_changed_refs"]


def _architecture_coverage_payload() -> dict[str, object]:
    return {
        "schema_id": "hisys.traceability.coverage.v1",
        "unreferenced_requirements": ["HISYS-FR-DOM-001", "HISYS-FR-DOM-002"],
    }


def _architecture_freshness_payload() -> dict[str, object]:
    return {
        "schema_id": "hisys.codebase_map.freshness.v1",
        "stale_partitions": [
            "runtime-boundary/codebase-analysis/20260418/REQ-OLD",
        ],
    }


def _architecture_impact_payload() -> dict[str, object]:
    return {
        "schema_id": "hisys.change_impact.v1",
        "changed_ref_count": 3,
        "impacted_requirement_ids": ["HISYS-FR-DOM-001"],
        "impacted_design_or_interface_refs": ["docs/some-design.md"],
    }


def test_architecture_candidates_cli_writes_report(tmp_path: Path, capsys) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    coverage_path = tmp_path / "coverage.json"
    freshness_path = tmp_path / "freshness.json"
    impact_path = tmp_path / "impact.json"
    coverage_path.write_text(
        json.dumps(_architecture_coverage_payload()), encoding="utf-8"
    )
    freshness_path.write_text(
        json.dumps(_architecture_freshness_payload()), encoding="utf-8"
    )
    impact_path.write_text(
        json.dumps(_architecture_impact_payload()), encoding="utf-8"
    )

    result = main(
        [
            "architecture-candidates",
            "--instance",
            str(instance_root),
            "--date",
            "20260521",
            "--coverage-report",
            str(coverage_path),
            "--freshness-report",
            str(freshness_path),
            "--change-impact-report",
            str(impact_path),
            "--current-head-short",
            "50b7263",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "architecture-candidates report" in captured.out
    assert "candidate_count:" in captured.out
    assert "external_call_made: false" in captured.out
    assert "allowed_actions: advisory_only" in captured.out

    json_path = (
        instance_root
        / "runtime-boundary"
        / "architecture-candidates"
        / "20260521"
        / "architecture-candidates-report.json"
    )
    md_path = (
        instance_root
        / "runtime-boundary"
        / "architecture-candidates"
        / "20260521"
        / "architecture-candidates-report.md"
    )
    assert json_path.exists()
    assert md_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema_id"] == "hisys.architecture_candidates.v1"
    assert data["advisory_only"] is True
    assert data["requires_human_review"] is True
    assert data["external_call_made"] is False
    assert data["mutation_performed"] is False
    assert data["raw_source_content_persisted"] is False
    assert data["current_head_short"] == "50b7263"
    assert data["candidate_count"] > 0
    for candidate in data["candidates"]:
        assert candidate["recommendation_strength"] in (
            "advisory_candidate",
            "advisory_candidate_low_evidence",
        )


_CODE_ANALYSIS_FIXTURE_DIR = (
    Path(__file__).resolve().parent.parent
    / "fixtures"
    / "pass-contracts"
    / "code_analysis"
)


def _evaluate_code_analysis_coverage_payload() -> dict[str, object]:
    return {
        "schema_id": "hisys.traceability.coverage.v1",
        "requirement_count": 2,
        "covered_requirement_count": 2,
        "coverage_ratio": 1.0,
        "unreferenced_requirements": [],
        "orphan_test_ids": [],
    }


def test_evaluate_code_analysis_contract_cli_writes_artifact(
    tmp_path: Path, capsys
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    contract_path = (
        _CODE_ANALYSIS_FIXTURE_DIR / "traceability_coverage_review.json"
    )
    assert contract_path.is_file()
    coverage_path = tmp_path / "coverage.json"
    coverage_path.write_text(
        json.dumps(_evaluate_code_analysis_coverage_payload()), encoding="utf-8"
    )

    result = main(
        [
            "evaluate-code-analysis-contract",
            "--instance",
            str(instance_root),
            "--date",
            "20260521",
            "--contract-ref",
            str(contract_path),
            "--question-type",
            "traceability_coverage_review",
            "--coverage-report",
            str(coverage_path),
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "evaluate-code-analysis-contract evaluation" in captured.out
    assert "quality_gate: passed" in captured.out
    assert "blockers: none" in captured.out
    assert "external_call_made: false" in captured.out
    assert "mutation_performed: false" in captured.out
    assert "raw_source_content_persisted: false" in captured.out
    assert "allowed_actions: advisory_only" in captured.out
    assert (
        "contract_id: code_analysis_traceability_coverage_review_v0_1_candidate"
        in captured.out
    )
    assert "question_type: traceability_coverage_review" in captured.out

    json_path = (
        instance_root
        / "runtime-boundary"
        / "code-analysis-pass-contracts"
        / "20260521"
        / "code_analysis_traceability_coverage_review_v0_1_candidate-evaluation.json"
    )
    md_path = (
        instance_root
        / "runtime-boundary"
        / "code-analysis-pass-contracts"
        / "20260521"
        / "code_analysis_traceability_coverage_review_v0_1_candidate-evaluation.md"
    )
    assert json_path.exists()
    assert md_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert (
        data["schema_id"]
        == "hisys.code_analysis_pass_contract.evaluation.v1"
    )
    assert (
        data["contract_id"]
        == "code_analysis_traceability_coverage_review_v0_1_candidate"
    )
    assert data["quality_gate"] == "passed"
    assert data["blockers"] == []
    assert data["advisory_only"] is True
    assert data["requires_human_review"] is True
    assert data["external_call_made"] is False
    assert data["mutation_performed"] is False
    assert data["raw_source_content_persisted"] is False
    assert data["human_approval_ref"] is None


def test_evaluate_code_analysis_contract_cli_records_blockers_and_approval(
    tmp_path: Path, capsys
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    contract_path = (
        _CODE_ANALYSIS_FIXTURE_DIR / "change_impact_review.json"
    )
    change_impact_path = tmp_path / "change-impact.json"
    change_impact_path.write_text(
        json.dumps(
            {
                "schema_id": "hisys.change_impact.v1",
                "changed_ref_count": 1,
                "impacted_requirement_ids": ["HISYS-FR-DOM-001"],
                "impacted_test_id_or_refs": [],
                "impacted_design_or_interface_refs": [],
                "impacted_runtime_boundary_refs": [],
                "unmapped_changed_refs": [],
                "unsafe_changed_refs": [],
            }
        ),
        encoding="utf-8",
    )

    result = main(
        [
            "evaluate-code-analysis-contract",
            "--instance",
            str(instance_root),
            "--date",
            "20260521",
            "--contract-ref",
            str(contract_path),
            "--question-type",
            "change_impact_review",
            "--change-impact-report",
            str(change_impact_path),
            "--human-approval-ref",
            "APPROVAL-TEST-001",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "quality_gate: needs_more_evidence" in captured.out
    assert "blockers: contradiction_unchecked" in captured.out

    json_path = (
        instance_root
        / "runtime-boundary"
        / "code-analysis-pass-contracts"
        / "20260521"
        / "code_analysis_change_impact_review_v0_1_candidate-evaluation.json"
    )
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["quality_gate"] == "needs_more_evidence"
    assert data["blockers"] == ["contradiction_unchecked"]
    assert data["human_approval_ref"] == "APPROVAL-TEST-001"


def _subagent_evidence_task_payload() -> dict[str, object]:
    return {
        "schema_id": "hisys.subagent_evidence.task.v1",
        "task_id": "SUBEVID-TASK-CLI-001",
        "parent_request_id": "REQ-CLI-001",
        "objective": "Inspect bounded code-analysis refs for missing traceability anchors.",
        "repo_ref": "repos/hisys",
        "include_refs": ["src/hisys/contracts"],
        "exclude_refs": ["runtime-boundary/"],
        "allowed_read_only_tools": ["read_file", "search_files"],
        "expected_artifact_schema": "hisys.subagent_evidence.result.v1",
        "what_not_to_do": ["do not mutate files", "do not call network tools"],
        "advisory_only": True,
        "requires_human_review": True,
    }


def _subagent_evidence_result_payload() -> dict[str, object]:
    return {
        "schema_id": "hisys.subagent_evidence.result.v1",
        "task_id": "SUBEVID-TASK-CLI-001",
        "summary": "Two bounded refs inspected; no mutation performed.",
        "artifact_refs": ["runtime-boundary/subagent-evidence/20260521/result.json"],
        "source_refs": ["src/hisys/contracts/pass_registry.py"],
        "validation_suggestions": [
            "PYTHONPATH=src pytest tests/unit/test_pass_contract_evaluator.py -q"
        ],
        "blockers": [],
        "external_call_made": False,
        "mutation_performed": False,
        "raw_source_content_persisted": False,
        "parent_verification_required": True,
    }


def test_validate_subagent_evidence_packet_cli_accepts_task_and_result(
    tmp_path: Path, capsys
) -> None:
    task_path = tmp_path / "task.json"
    task_path.write_text(
        json.dumps(_subagent_evidence_task_payload()), encoding="utf-8"
    )
    result_path = tmp_path / "result.json"
    result_path.write_text(
        json.dumps(_subagent_evidence_result_payload()), encoding="utf-8"
    )

    exit_code = main(
        [
            "validate-subagent-evidence-packet",
            "--task",
            str(task_path),
            "--result",
            str(result_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "validate-subagent-evidence-packet: ok" in captured.out
    assert "task_id: SUBEVID-TASK-CLI-001" in captured.out
    assert "result_supplied: true" in captured.out
    assert "artifact_ref_count: 1" in captured.out
    assert "source_ref_count: 1" in captured.out
    assert "advisory_only: true" in captured.out
    assert "requires_human_review: true" in captured.out
    assert "external_call_made: false" in captured.out
    assert "mutation_performed: false" in captured.out
    assert "raw_source_content_persisted: false" in captured.out
    assert "allowed_actions: advisory_only" in captured.out


def test_validate_subagent_evidence_packet_cli_accepts_task_only(
    tmp_path: Path, capsys
) -> None:
    task_path = tmp_path / "task.json"
    task_path.write_text(
        json.dumps(_subagent_evidence_task_payload()), encoding="utf-8"
    )

    exit_code = main(
        [
            "validate-subagent-evidence-packet",
            "--task",
            str(task_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "validate-subagent-evidence-packet: ok" in captured.out
    assert "task_id: SUBEVID-TASK-CLI-001" in captured.out
    assert "result_supplied: false" in captured.out
    assert "artifact_ref_count: 0" in captured.out
    assert "source_ref_count: 0" in captured.out


def test_runtime_boundary_check_cli_writes_consistency_report(tmp_path: Path, capsys) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    safe_ref = "runtime-boundary/traceability-coverage/20260520/coverage-report.json"
    safe_md = "runtime-boundary/traceability-coverage/20260520/coverage-report.md"
    safe_json_path = instance_root / safe_ref
    safe_md_path = instance_root / safe_md
    safe_json_path.parent.mkdir(parents=True, exist_ok=True)
    safe_json_path.write_text(
        json.dumps(
            {
                "schema_id": "hisys.traceability.coverage.v1",
                "advisory_only": True,
                "requires_human_review": True,
                "external_call_made": False,
                "mutation_performed": False,
                "raw_source_content_persisted": False,
                "requirement_count": 0,
                "covered_requirement_count": 0,
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
    safe_md_path.write_text("# coverage\n- advisory_only: true\n", encoding="utf-8")

    result = main(
        [
            "runtime-boundary-check",
            "--instance",
            str(instance_root),
            "--date",
            "20260520",
            "--ref",
            safe_ref,
            "--ref",
            safe_md,
            "--ref",
            "runtime-boundary/codebase-analysis/20260520/REQ-MISSING/inventory.json",
            "--ref",
            "runtime-boundary/../escape.txt",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "runtime-boundary consistency report" in captured.out
    assert "external_call_made: false" in captured.out
    json_path = (
        instance_root
        / "runtime-boundary"
        / "runtime-boundary-consistency"
        / "20260520"
        / "consistency-report.json"
    )
    md_path = (
        instance_root
        / "runtime-boundary"
        / "runtime-boundary-consistency"
        / "20260520"
        / "consistency-report.md"
    )
    assert json_path.exists()
    assert md_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema_id"] == "hisys.runtime_boundary.consistency.v1"
    assert data["advisory_only"] is True
    assert data["requires_human_review"] is True
    assert data["external_call_made"] is False
    assert data["mutation_performed"] is False
    assert data["raw_source_content_persisted"] is False
    assert data["ok_ref_count"] == 2
    assert data["unsafe_refs"] == ["runtime-boundary/../escape.txt"]
    assert data["missing_files"] == [
        "runtime-boundary/codebase-analysis/20260520/REQ-MISSING/inventory.json"
    ]


def test_traceability_coverage_cli_writes_runtime_boundary_report(tmp_path: Path, capsys) -> None:
    result = main(
        [
            "traceability-coverage",
            "--instance",
            str(tmp_path),
            "--date",
            "20260520",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "traceability coverage report" in captured.out
    assert "external_call_made: false" in captured.out
    json_path = tmp_path / "runtime-boundary" / "traceability-coverage" / "20260520" / "coverage-report.json"
    md_path = tmp_path / "runtime-boundary" / "traceability-coverage" / "20260520" / "coverage-report.md"
    assert json_path.exists()
    assert md_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema_id"] == "hisys.traceability.coverage.v1"
    assert data["advisory_only"] is True
    assert data["requires_human_review"] is True
    assert data["external_call_made"] is False
    assert data["mutation_performed"] is False
    assert data["raw_source_content_persisted"] is False


def test_investigate_domain_writes_request_and_tool_result_boundary(tmp_path: Path, capsys) -> None:
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)

    result = main(
        [
            "investigate-domain",
            "--instance",
            str(tmp_path),
            "--request",
            str(request_path),
            "--date",
            "20260509",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "domain investigation run" in captured.out
    assert "domain: research" in captured.out
    boundary_dir = tmp_path / "runtime-boundary" / "domain-investigation" / "research" / "20260509"
    request_artifact = boundary_dir / "hisys-tool-request-HISYS-REQ-RESEARCH-GAP-001.json"
    result_artifact = boundary_dir / "hisys-tool-result-HISYS-REQ-RESEARCH-GAP-001.json"
    assert request_artifact.exists()
    assert result_artifact.exists()

    request_data = json.loads(request_artifact.read_text(encoding="utf-8"))
    tool_result = json.loads(result_artifact.read_text(encoding="utf-8"))
    assert request_data["constraints"] == {
        "credential_use_allowed": False,
        "external_calls_allowed": False,
        "max_rounds": 3,
        "mutation_allowed": False,
    }
    assert tool_result["status"] == "completed"
    assert tool_result["domain"] == "research"
    assert tool_result["external_call_made"] is False
    assert tool_result["mutation_performed"] is False
    assert tool_result["quality_gate"] == "passed"
    assert str(result_artifact.relative_to(tmp_path)) in tool_result["runtime_boundary_refs"]

    report = json.loads(
        (tmp_path / "reports" / "run-summaries" / "20260509" / "domain-investigation-report.json").read_text(
            encoding="utf-8"
        )
    )
    assert report["request_id"] == "HISYS-REQ-RESEARCH-GAP-001"
    assert report["domain"] == "research"
    assert report["tool_result_ref"] == str(result_artifact.relative_to(tmp_path))


def test_investigate_domain_research_gap_fixture_generates_alternatives(tmp_path: Path, capsys) -> None:
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)

    result = main(
        [
            "investigate-domain",
            "--instance",
            str(tmp_path),
            "--request",
            str(request_path),
            "--date",
            "20260509",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "status: completed" in captured.out
    boundary_dir = tmp_path / "runtime-boundary" / "domain-investigation" / "research" / "20260509"
    data_artifact = boundary_dir / "investigation-data-INV-HISYS-REQ-RESEARCH-GAP-001.json"
    alternatives_artifact = boundary_dir / "alternative-decision-set-ALTSET-HISYS-REQ-RESEARCH-GAP-001.json"
    domain_result_artifact = boundary_dir / "domain-investigation-result-DRESULT-HISYS-REQ-RESEARCH-GAP-001.json"
    tool_result_artifact = boundary_dir / "hisys-tool-result-HISYS-REQ-RESEARCH-GAP-001.json"
    assert data_artifact.exists()
    assert alternatives_artifact.exists()
    assert domain_result_artifact.exists()

    data = json.loads(data_artifact.read_text(encoding="utf-8"))
    alternatives = json.loads(alternatives_artifact.read_text(encoding="utf-8"))
    domain_result = json.loads(domain_result_artifact.read_text(encoding="utf-8"))
    tool_result = json.loads(tool_result_artifact.read_text(encoding="utf-8"))

    assert data["evidence_packages"][0]["evidence_type"] == "research_gap_matrix"
    assert "Dynamic Structure DEVS" in data["evidence_packages"][0]["summary"]
    assert any("source-access-ACCESS-HISYS-REQ-RESEARCH-GAP-001-fixture_publisher_page_reader.json" in ref for ref in data["evidence_packages"][0]["evidence_refs"])
    assert any("source-evidence-EVID-HISYS-REQ-RESEARCH-GAP-001-fixture_publisher_page_reader.json" in ref for ref in data["evidence_packages"][0]["evidence_refs"])
    assert alternatives["recommended_candidate_id"] == "CAND-HISYS-REQ-RESEARCH-GAP-001-SOS-DSDEVS"
    assert alternatives["candidates"][0]["candidate_type"] == "research_direction"
    assert "Self-organizing Dynamic Structure DEVS" in alternatives["candidates"][0]["claim"]
    assert domain_result["quality_gate"] == "passed"
    assert domain_result["recommended_alternative_id"] == "CAND-HISYS-REQ-RESEARCH-GAP-001-SOS-DSDEVS"
    assert tool_result["status"] == "completed"
    assert tool_result["recommended_alternative_id"] == "CAND-HISYS-REQ-RESEARCH-GAP-001-SOS-DSDEVS"
    assert tool_result["external_call_made"] is False
    assert tool_result["mutation_performed"] is False

    dars_dir = tmp_path / "runtime-boundary" / "dars" / "20260509"
    dars_request = dars_dir / "dars-request-DARSREQ-HISYS-REQ-RESEARCH-GAP-001.json"
    dars_response = dars_dir / "dars-response-DARSRESP-HISYS-REQ-RESEARCH-GAP-001.json"
    dars_trace = dars_dir / "dars-trace-DARSTRACE-DARSREQ-HISYS-REQ-RESEARCH-GAP-001.json"
    assert dars_request.exists()
    assert dars_response.exists()
    assert dars_trace.exists()
    assert str(dars_trace.relative_to(tmp_path)) in domain_result["dars_refs"]
    response = json.loads(dars_response.read_text(encoding="utf-8"))
    dars_request_payload = json.loads(dars_request.read_text(encoding="utf-8"))
    dars_trace_payload = json.loads(dars_trace.read_text(encoding="utf-8"))
    assert any("source-evidence-EVID-HISYS-REQ-RESEARCH-GAP-001-fixture_publisher_page_reader.json" in ref for ref in dars_request_payload["record_refs"]["runtime_boundary"])
    assert any("source-evidence-EVID-HISYS-REQ-RESEARCH-GAP-001-fixture_publisher_page_reader.json" in ref for ref in dars_trace_payload["evidence_refs"])
    assert response["producer"]["backend_kind"] == "loopback"
    assert response["producer"]["external_call_made"] is False
    assert response["boundary"]["action_taken"] == "none"
    assert response["boundary"]["external_side_effects_performed"] is False
    assert response["boundary"]["mutation_performed"] is False
    assert response["critique"]["recommended_actions"][0]["allowed_to_execute"] is False
    assert response["decision_trace"]["blocks_decision"] is False

    chief_dir = tmp_path / "runtime-boundary" / "chief-editor" / "research" / "20260509"
    chief_decision = chief_dir / "research-recommendation-review-CEDEC-HISYS-REQ-RESEARCH-GAP-001.json"
    assert chief_decision.exists()
    decision = json.loads(chief_decision.read_text(encoding="utf-8"))
    assert decision["decision_type"] == "research_recommendation_review"
    assert decision["status"] == "recommend_with_conditions"
    assert decision["recommended_candidate_id"] == "CAND-HISYS-REQ-RESEARCH-GAP-001-SOS-DSDEVS"
    assert decision["source_validation_status"] == "fixture_source_evidence_present"
    assert any("source-evidence-EVID-HISYS-REQ-RESEARCH-GAP-001-fixture_publisher_page_reader.json" in ref for ref in decision["source_evidence_refs"])
    assert "Validate fixture source evidence against live publisher pages before publication claims." in decision["conditions"]
    assert decision["dars_acceptance_decision"] == "accepted_as_conditions"
    assert decision["dars_accepted"] is True
    assert decision["accepted_dars_action_ids"] == ["RECACT-HISYS-REQ-RESEARCH-GAP-001-SOURCE-VALIDATION"]
    assert decision["dars_blocks_decision"] is False
    assert "Chief Editor accepted DARS advisory actions as non-executable conditions." in decision["conditions"]
    assert decision["action_taken"] == "none"
    assert decision["human_approval_required"] is True
    assert decision["external_call_made"] is False
    assert decision["mutation_performed"] is False


def test_investigate_domain_promotes_explicit_manual_pdf_evidence_refs(tmp_path: Path, capsys) -> None:
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)
    fixture = tmp_path / "manual-smoke.pdf"
    fixture.write_bytes(b"%PDF-1.7\nApproved manual smoke bytes.\n%%EOF\n")
    package = OpenAccessPdfConnector().collect_fixture(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        fixture_path=fixture,
        source_url="https://mdpi.com/fixture/manual-smoke.pdf",
        license_signal="open_access",
        output_root=tmp_path,
        yyyymmdd="20260509",
    )

    result = main(
        [
            "investigate-domain",
            "--instance",
            str(tmp_path),
            "--request",
            str(request_path),
            "--date",
            "20260509",
            "--promote-pdf-source-access-ref",
            package.access_ref,
            "--promote-pdf-source-evidence-ref",
            package.evidence_ref,
        ]
    )

    capsys.readouterr()
    assert result == 0
    boundary_dir = tmp_path / "runtime-boundary" / "domain-investigation" / "research" / "20260509"
    data_artifact = boundary_dir / "investigation-data-INV-HISYS-REQ-RESEARCH-GAP-001.json"
    data = json.loads(data_artifact.read_text(encoding="utf-8"))
    assert data["promoted_pdf_evidence_refs"] == [package.evidence_ref]
    assert package.access_ref in data["source_governance_refs"]
    assert package.evidence_ref in data["source_governance_refs"]
    assert package.evidence_ref in data["evidence_packages"][0]["evidence_refs"]
    dars_trace = json.loads(
        (tmp_path / "runtime-boundary" / "dars" / "20260509" / "dars-trace-DARSTRACE-DARSREQ-HISYS-REQ-RESEARCH-GAP-001.json").read_text(
            encoding="utf-8"
        )
    )
    assert package.evidence_ref in dars_trace["evidence_refs"]
    chief_decision = json.loads(
        (
            tmp_path
            / "runtime-boundary"
            / "chief-editor"
            / "research"
            / "20260509"
            / "research-recommendation-review-CEDEC-HISYS-REQ-RESEARCH-GAP-001.json"
        ).read_text(encoding="utf-8")
    )
    assert chief_decision["source_validation_status"] == "manual_pdf_evidence_promoted"
    assert chief_decision["promoted_pdf_evidence_refs"] == [package.evidence_ref]


def test_investigate_domain_preserves_explicit_pdf_quote_refs_without_strengthening_claims(
    tmp_path: Path, capsys
) -> None:
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)
    fixture = tmp_path / "manual-smoke.pdf"
    fixture.write_bytes(b"%PDF-1.7\nApproved manual quote bytes.\n%%EOF\n")
    package = OpenAccessPdfConnector().collect_fixture(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        fixture_path=fixture,
        source_url="https://mdpi.com/fixture/manual-quote.pdf",
        license_signal="open_access",
        output_root=tmp_path,
        yyyymmdd="20260509",
    )
    promoted = PdfEvidencePromotionLoader(root=tmp_path).promote(
        source_access_refs=[package.access_ref],
        source_evidence_refs=[package.evidence_ref],
    )
    quote_result = PdfQuoteExtractor(root=tmp_path).extract(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        promoted_pdf_evidence_refs=promoted.promoted_pdf_evidence_refs,
        yyyymmdd="20260509",
    )

    result = main(
        [
            "investigate-domain",
            "--instance",
            str(tmp_path),
            "--request",
            str(request_path),
            "--date",
            "20260509",
            "--promote-pdf-source-access-ref",
            package.access_ref,
            "--promote-pdf-source-evidence-ref",
            package.evidence_ref,
            "--source-quote-ref",
            quote_result.source_quote_refs[0],
        ]
    )

    capsys.readouterr()
    assert result == 0
    boundary_dir = tmp_path / "runtime-boundary" / "domain-investigation" / "research" / "20260509"
    data = json.loads((boundary_dir / "investigation-data-INV-HISYS-REQ-RESEARCH-GAP-001.json").read_text(encoding="utf-8"))
    assert data["source_quote_refs"] == quote_result.source_quote_refs
    assert quote_result.source_quote_refs[0] in data["evidence_packages"][0]["evidence_refs"]
    dars_trace = json.loads(
        (tmp_path / "runtime-boundary" / "dars" / "20260509" / "dars-trace-DARSTRACE-DARSREQ-HISYS-REQ-RESEARCH-GAP-001.json").read_text(
            encoding="utf-8"
        )
    )
    assert quote_result.source_quote_refs[0] in dars_trace["source_quote_refs"]
    chief_decision = json.loads(
        (
            tmp_path
            / "runtime-boundary"
            / "chief-editor"
            / "research"
            / "20260509"
            / "research-recommendation-review-CEDEC-HISYS-REQ-RESEARCH-GAP-001.json"
        ).read_text(encoding="utf-8")
    )
    assert chief_decision["source_quote_refs"] == quote_result.source_quote_refs
    assert chief_decision["source_validation_status"] == "manual_pdf_quotes_present"
    assert chief_decision["status"] == "recommend_with_conditions"
    assert "Keep novelty claims conditional after quote extraction." in chief_decision["conditions"]


def test_investigate_domain_preserves_claim_evidence_ledger_refs_without_strengthening_claims(
    tmp_path: Path, capsys
) -> None:
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)
    fixture = tmp_path / "manual-ledger.pdf"
    fixture.write_bytes(b"%PDF-1.7\nApproved manual ledger bytes.\n%%EOF\n")
    package = OpenAccessPdfConnector().collect_fixture(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        fixture_path=fixture,
        source_url="https://mdpi.com/fixture/manual-ledger.pdf",
        license_signal="open_access",
        output_root=tmp_path,
        yyyymmdd="20260509",
    )
    promoted = PdfEvidencePromotionLoader(root=tmp_path).promote(
        source_access_refs=[package.access_ref],
        source_evidence_refs=[package.evidence_ref],
    )
    quote_result = PdfQuoteExtractor(root=tmp_path).extract(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        promoted_pdf_evidence_refs=promoted.promoted_pdf_evidence_refs,
        yyyymmdd="20260509",
    )
    ledger_result = ClaimEvidenceLedgerBuilder(root=tmp_path).build(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        claim_id="CLAIM-HISYS-REQ-RESEARCH-GAP-001-DSDEVS",
        claim_text="Dynamic Structure DEVS is relevant to topology-changing simulation.",
        relation="support",
        rationale="The quote records structural change evidence but does not prove novelty.",
        source_quote_refs=quote_result.source_quote_refs,
        yyyymmdd="20260509",
    )

    result = main(
        [
            "investigate-domain",
            "--instance",
            str(tmp_path),
            "--request",
            str(request_path),
            "--date",
            "20260509",
            "--promote-pdf-source-access-ref",
            package.access_ref,
            "--promote-pdf-source-evidence-ref",
            package.evidence_ref,
            "--source-quote-ref",
            quote_result.source_quote_refs[0],
            "--claim-evidence-ledger-ref",
            ledger_result.claim_evidence_ledger_refs[0],
        ]
    )

    capsys.readouterr()
    assert result == 0
    boundary_dir = tmp_path / "runtime-boundary" / "domain-investigation" / "research" / "20260509"
    data = json.loads((boundary_dir / "investigation-data-INV-HISYS-REQ-RESEARCH-GAP-001.json").read_text(encoding="utf-8"))
    assert data["claim_evidence_ledger_refs"] == ledger_result.claim_evidence_ledger_refs
    assert ledger_result.claim_evidence_ledger_refs[0] in data["evidence_packages"][0]["evidence_refs"]
    dars_trace = json.loads(
        (tmp_path / "runtime-boundary" / "dars" / "20260509" / "dars-trace-DARSTRACE-DARSREQ-HISYS-REQ-RESEARCH-GAP-001.json").read_text(
            encoding="utf-8"
        )
    )
    assert ledger_result.claim_evidence_ledger_refs[0] in dars_trace["claim_evidence_ledger_refs"]
    chief_decision = json.loads(
        (
            tmp_path
            / "runtime-boundary"
            / "chief-editor"
            / "research"
            / "20260509"
            / "research-recommendation-review-CEDEC-HISYS-REQ-RESEARCH-GAP-001.json"
        ).read_text(encoding="utf-8")
    )
    assert chief_decision["claim_evidence_ledger_refs"] == ledger_result.claim_evidence_ledger_refs
    assert chief_decision["source_validation_status"] == "claim_evidence_ledger_present"
    assert chief_decision["status"] == "recommend_with_conditions"
    assert "Keep novelty claims conditional after claim-evidence ledger mapping." in chief_decision["conditions"]


def test_investigate_domain_preserves_claim_evidence_summary_refs_as_advisory_confidence(
    tmp_path: Path, capsys
) -> None:
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)
    fixture = tmp_path / "manual-summary.pdf"
    fixture.write_bytes(b"%PDF-1.7\nApproved manual summary bytes.\n%%EOF\n")
    package = OpenAccessPdfConnector().collect_fixture(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        fixture_path=fixture,
        source_url="https://mdpi.com/fixture/manual-summary.pdf",
        license_signal="open_access",
        output_root=tmp_path,
        yyyymmdd="20260509",
    )
    promoted = PdfEvidencePromotionLoader(root=tmp_path).promote(
        source_access_refs=[package.access_ref],
        source_evidence_refs=[package.evidence_ref],
    )
    quote_result = PdfQuoteExtractor(root=tmp_path).extract(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        promoted_pdf_evidence_refs=promoted.promoted_pdf_evidence_refs,
        yyyymmdd="20260509",
    )
    ledger_result = ClaimEvidenceLedgerBuilder(root=tmp_path).build(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        claim_id="CLAIM-HISYS-REQ-RESEARCH-GAP-001-DSDEVS",
        claim_text="Dynamic Structure DEVS is relevant to topology-changing simulation.",
        relation="support",
        rationale="The quote supports relevance, not novelty proof.",
        source_quote_refs=quote_result.source_quote_refs,
        yyyymmdd="20260509",
    )
    summary_result = ClaimEvidenceSummaryBuilder(root=tmp_path).build(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        claim_id="CLAIM-HISYS-REQ-RESEARCH-GAP-001-DSDEVS",
        claim_evidence_ledger_refs=ledger_result.claim_evidence_ledger_refs,
        yyyymmdd="20260509",
    )

    result = main(
        [
            "investigate-domain",
            "--instance",
            str(tmp_path),
            "--request",
            str(request_path),
            "--date",
            "20260509",
            "--promote-pdf-source-access-ref",
            package.access_ref,
            "--promote-pdf-source-evidence-ref",
            package.evidence_ref,
            "--source-quote-ref",
            quote_result.source_quote_refs[0],
            "--claim-evidence-ledger-ref",
            ledger_result.claim_evidence_ledger_refs[0],
            "--claim-evidence-summary-ref",
            summary_result.claim_evidence_summary_refs[0],
        ]
    )

    capsys.readouterr()
    assert result == 0
    boundary_dir = tmp_path / "runtime-boundary" / "domain-investigation" / "research" / "20260509"
    data = json.loads((boundary_dir / "investigation-data-INV-HISYS-REQ-RESEARCH-GAP-001.json").read_text(encoding="utf-8"))
    assert data["claim_evidence_summary_refs"] == summary_result.claim_evidence_summary_refs
    assert summary_result.claim_evidence_summary_refs[0] in data["evidence_packages"][0]["evidence_refs"]
    dars_trace = json.loads(
        (tmp_path / "runtime-boundary" / "dars" / "20260509" / "dars-trace-DARSTRACE-DARSREQ-HISYS-REQ-RESEARCH-GAP-001.json").read_text(
            encoding="utf-8"
        )
    )
    assert summary_result.claim_evidence_summary_refs[0] in dars_trace["claim_evidence_summary_refs"]
    chief_decision = json.loads(
        (
            tmp_path
            / "runtime-boundary"
            / "chief-editor"
            / "research"
            / "20260509"
            / "research-recommendation-review-CEDEC-HISYS-REQ-RESEARCH-GAP-001.json"
        ).read_text(encoding="utf-8")
    )
    assert chief_decision["claim_evidence_summary_refs"] == summary_result.claim_evidence_summary_refs
    assert chief_decision["source_validation_status"] == "claim_evidence_summary_present"
    assert chief_decision["advisory_confidence_only"] is True
    assert chief_decision["status"] == "recommend_with_conditions"
    assert "Keep confidence advisory after claim-evidence summary aggregation." in chief_decision["conditions"]


def test_investigate_domain_preserves_claim_coverage_gate_refs_as_conditional_manuscript_gate(
    tmp_path: Path, capsys
) -> None:
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)
    fixture = tmp_path / "manual-coverage.pdf"
    fixture.write_bytes(b"%PDF-1.7\nApproved manual coverage bytes.\n%%EOF\n")
    package = OpenAccessPdfConnector().collect_fixture(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        fixture_path=fixture,
        source_url="https://mdpi.com/fixture/manual-coverage.pdf",
        license_signal="open_access",
        output_root=tmp_path,
        yyyymmdd="20260509",
    )
    promoted = PdfEvidencePromotionLoader(root=tmp_path).promote(
        source_access_refs=[package.access_ref],
        source_evidence_refs=[package.evidence_ref],
    )
    quote_result = PdfQuoteExtractor(root=tmp_path).extract(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        promoted_pdf_evidence_refs=promoted.promoted_pdf_evidence_refs,
        yyyymmdd="20260509",
    )
    claim_id = "CLAIM-HISYS-REQ-RESEARCH-GAP-001-DSDEVS"
    ledger_result = ClaimEvidenceLedgerBuilder(root=tmp_path).build(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        claim_id=claim_id,
        claim_text="Dynamic Structure DEVS is relevant to topology-changing simulation.",
        relation="support",
        rationale="The quote supports relevance, not novelty proof.",
        source_quote_refs=quote_result.source_quote_refs,
        yyyymmdd="20260509",
    )
    summary_result = ClaimEvidenceSummaryBuilder(root=tmp_path).build(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        claim_id=claim_id,
        claim_evidence_ledger_refs=ledger_result.claim_evidence_ledger_refs,
        yyyymmdd="20260509",
    )
    gate_result = ClaimCoverageGateBuilder(root=tmp_path).build(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        required_claim_ids=[claim_id, "CLAIM-HISYS-REQ-RESEARCH-GAP-001-TOPOLOGY-BEHAVIOR"],
        claim_evidence_summary_refs=summary_result.claim_evidence_summary_refs,
        yyyymmdd="20260509",
    )

    result = main(
        [
            "investigate-domain",
            "--instance",
            str(tmp_path),
            "--request",
            str(request_path),
            "--date",
            "20260509",
            "--promote-pdf-source-access-ref",
            package.access_ref,
            "--promote-pdf-source-evidence-ref",
            package.evidence_ref,
            "--source-quote-ref",
            quote_result.source_quote_refs[0],
            "--claim-evidence-ledger-ref",
            ledger_result.claim_evidence_ledger_refs[0],
            "--claim-evidence-summary-ref",
            summary_result.claim_evidence_summary_refs[0],
            "--claim-coverage-gate-ref",
            gate_result.claim_coverage_gate_refs[0],
        ]
    )

    capsys.readouterr()
    assert result == 0
    boundary_dir = tmp_path / "runtime-boundary" / "domain-investigation" / "research" / "20260509"
    data = json.loads((boundary_dir / "investigation-data-INV-HISYS-REQ-RESEARCH-GAP-001.json").read_text(encoding="utf-8"))
    assert data["claim_coverage_gate_refs"] == gate_result.claim_coverage_gate_refs
    assert gate_result.claim_coverage_gate_refs[0] in data["evidence_packages"][0]["evidence_refs"]
    dars_trace = json.loads(
        (tmp_path / "runtime-boundary" / "dars" / "20260509" / "dars-trace-DARSTRACE-DARSREQ-HISYS-REQ-RESEARCH-GAP-001.json").read_text(
            encoding="utf-8"
        )
    )
    assert gate_result.claim_coverage_gate_refs[0] in dars_trace["claim_coverage_gate_refs"]
    chief_decision = json.loads(
        (
            tmp_path
            / "runtime-boundary"
            / "chief-editor"
            / "research"
            / "20260509"
            / "research-recommendation-review-CEDEC-HISYS-REQ-RESEARCH-GAP-001.json"
        ).read_text(encoding="utf-8")
    )
    assert chief_decision["claim_coverage_gate_refs"] == gate_result.claim_coverage_gate_refs
    assert chief_decision["source_validation_status"] == "claim_coverage_gate_present"
    assert chief_decision["manuscript_language_gate"] == "conditional_only"
    assert chief_decision["conditional_manuscript_language_only"] is True
    assert chief_decision["status"] == "recommend_with_conditions"
    assert "Keep manuscript-facing claims conditional after claim coverage gating." in chief_decision["conditions"]


def test_investigate_domain_preserves_recommendation_claim_registry_refs_as_conditional_lineage(
    tmp_path: Path, capsys
) -> None:
    request_path = tmp_path / "domain-request.json"
    _write_domain_request(request_path)
    registry_result = RecommendationClaimRegistryBuilder(root=tmp_path).build(
        request_id="HISYS-REQ-RESEARCH-GAP-001",
        recommendation_text="Recommend DSDEVS and topology/behavior co-evolution evaluation scenarios.",
        claim_texts=[
            "Self-organizing Dynamic Structure DEVS is the recommended research direction.",
            "Evaluation scenarios should demonstrate topology/behavior co-evolution.",
        ],
        yyyymmdd="20260509",
    )

    result = main(
        [
            "investigate-domain",
            "--instance",
            str(tmp_path),
            "--request",
            str(request_path),
            "--date",
            "20260509",
            "--recommendation-claim-registry-ref",
            registry_result.recommendation_claim_registry_refs[0],
        ]
    )

    capsys.readouterr()
    assert result == 0
    boundary_dir = tmp_path / "runtime-boundary" / "domain-investigation" / "research" / "20260509"
    data = json.loads((boundary_dir / "investigation-data-INV-HISYS-REQ-RESEARCH-GAP-001.json").read_text(encoding="utf-8"))
    assert data["recommendation_claim_registry_refs"] == registry_result.recommendation_claim_registry_refs
    assert registry_result.recommendation_claim_registry_refs[0] in data["evidence_packages"][0]["evidence_refs"]
    dars_trace = json.loads(
        (tmp_path / "runtime-boundary" / "dars" / "20260509" / "dars-trace-DARSTRACE-DARSREQ-HISYS-REQ-RESEARCH-GAP-001.json").read_text(
            encoding="utf-8"
        )
    )
    assert registry_result.recommendation_claim_registry_refs[0] in dars_trace["recommendation_claim_registry_refs"]
    chief_decision = json.loads(
        (
            tmp_path
            / "runtime-boundary"
            / "chief-editor"
            / "research"
            / "20260509"
            / "research-recommendation-review-CEDEC-HISYS-REQ-RESEARCH-GAP-001.json"
        ).read_text(encoding="utf-8")
    )
    assert chief_decision["recommendation_claim_registry_refs"] == registry_result.recommendation_claim_registry_refs
    assert chief_decision["source_validation_status"] == "recommendation_claim_registry_present"
    assert chief_decision["recommendation_claim_registry_conditional"] is True
    assert chief_decision["feeds_live_k_coverage_gates"] is True
    assert chief_decision["status"] == "recommend_with_conditions"
    assert "Run Live-K claim coverage gates before stronger manuscript-facing claims." in chief_decision["conditions"]


# ---------------------------------------------------------------------------
# M20.4 — investigate-domain --domain codebase fixture smoke.
# ---------------------------------------------------------------------------


def _seed_codebase_smoke_repo(repo: Path) -> None:
    (repo / "pkg").mkdir()
    (repo / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "pkg" / "mod.py").write_text(
        "def add(a, b):\n    return a + b\n", encoding="utf-8"
    )


def _materialize_complete_codebase_bundle_for_cli(
    *, instance_root: Path, repo: Path, date: str, request_id: str
) -> dict[str, str]:
    inventory = build_codebase_inventory(repo_root=repo)
    inv_ref = write_codebase_inventory(
        instance_root=instance_root,
        date=date,
        request_id=request_id,
        inventory=inventory,
    )["json_ref"]

    symbol_index = build_python_symbol_index(repo_root=repo)
    sym_ref = write_python_symbol_index(
        instance_root=instance_root,
        date=date,
        request_id=request_id,
        symbol_index=symbol_index,
    )["json_ref"]

    scope_map = build_codebase_scope_map(
        inventory=inventory, symbol_index=symbol_index
    )
    validation_plan = build_codebase_validation_plan(scope_map)
    scope_ref = write_codebase_scope_map(
        instance_root=instance_root,
        date=date,
        request_id=request_id,
        scope_map=scope_map,
        validation_plan=validation_plan,
    )["json_ref"]

    risk_scan = scan_codebase_risk_boundaries(repo_root=repo)
    risk_ref = write_codebase_risk_scan(
        instance_root=instance_root,
        date=date,
        request_id=request_id,
        scan=risk_scan,
    )["json_ref"]

    return {
        "inventory": inv_ref,
        "symbol_index": sym_ref,
        "scope_map": scope_ref,
        "validation_plan": (
            f"runtime-boundary/codebase-analysis/{date}/{request_id}/validation-plan.json"
        ),
        "risk_scan": risk_ref,
    }


def _write_codebase_smoke_request(
    path: Path, *, request_id: str, refs: dict[str, str]
) -> None:
    sources = [
        {
            "source_id": "SRC-INV",
            "source_type": "runtime_record",
            "ref": refs["inventory"],
            "access_mode": "read_only",
            "sensitivity": "public",
        },
        {
            "source_id": "SRC-SYM",
            "source_type": "runtime_record",
            "ref": refs["symbol_index"],
            "access_mode": "read_only",
            "sensitivity": "public",
        },
        {
            "source_id": "SRC-SCOPE",
            "source_type": "runtime_record",
            "ref": refs["scope_map"],
            "access_mode": "read_only",
            "sensitivity": "public",
        },
        {
            "source_id": "SRC-VALID",
            "source_type": "runtime_record",
            "ref": refs["validation_plan"],
            "access_mode": "read_only",
            "sensitivity": "public",
        },
        {
            "source_id": "SRC-RISK",
            "source_type": "runtime_record",
            "ref": refs["risk_scan"],
            "access_mode": "read_only",
            "sensitivity": "public",
        },
    ]
    path.write_text(
        json.dumps(
            {
                "producer_id": "hermes",
                "status": "submitted",
                "request_id": request_id,
                "domain": "codebase",
                "objective": "codebase: investigate-domain artifact-bridge smoke",
                "sources": sources,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def test_investigate_domain_codebase_smokes_local_bundle(
    tmp_path: Path, capsys
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_codebase_smoke_repo(repo)
    refs = _materialize_complete_codebase_bundle_for_cli(
        instance_root=instance_root,
        repo=repo,
        date="20260520",
        request_id="m20_4_smoke",
    )

    request_path = instance_root / "codebase-request.json"
    _write_codebase_smoke_request(
        request_path, request_id="HISYS-REQ-M20-4-SMOKE", refs=refs
    )

    exit_code = main(
        [
            "investigate-domain",
            "--instance",
            str(instance_root),
            "--request",
            str(request_path),
            "--date",
            "20260520",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "domain: codebase" in captured.out

    boundary_dir = (
        instance_root
        / "runtime-boundary"
        / "domain-investigation"
        / "codebase"
        / "20260520"
    )
    result_artifact = boundary_dir / "hisys-tool-result-HISYS-REQ-M20-4-SMOKE.json"
    assert result_artifact.exists()

    tool_result = json.loads(result_artifact.read_text(encoding="utf-8"))
    assert tool_result["domain"] == "codebase"
    assert tool_result["external_call_made"] is False
    assert tool_result["mutation_performed"] is False
    assert tool_result["requires_human_review"] is True
    assert tool_result["quality_gate"] == "passed"
    assert tool_result["status"] == "completed"

    domain_result_artifacts = list(boundary_dir.glob("domain-investigation-result-*.json"))
    assert len(domain_result_artifacts) == 1
    domain_payload = json.loads(domain_result_artifacts[0].read_text(encoding="utf-8"))
    codebase_packages = [
        pkg
        for pkg in domain_payload["investigation_data"]["evidence_packages"]
        if pkg["evidence_type"] == "codebase_analysis_bundle"
    ]
    assert len(codebase_packages) == 1
    package = codebase_packages[0]
    assert package["evidence_refs"] == [
        refs["inventory"],
        refs["symbol_index"],
        refs["scope_map"],
        refs["risk_scan"],
    ]
    assert package["external_call_made"] is False
    assert package["mutation_performed"] is False

    report_path = (
        instance_root
        / "reports"
        / "run-summaries"
        / "20260520"
        / "domain-investigation-report.json"
    )
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["request_id"] == "HISYS-REQ-M20-4-SMOKE"
    assert report["domain"] == "codebase"
    assert report["tool_result_ref"] == str(result_artifact.relative_to(instance_root))


def test_investigate_domain_codebase_materializes_current_artifact_repo(
    tmp_path: Path, capsys
) -> None:
    """M21: codebase domain request should run local source-inspection pipeline."""

    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_codebase_smoke_repo(repo)
    request_id = "HISYS-REQ-M21-CURRENT-ARTIFACT"

    request_path = instance_root / "codebase-current-artifact-request.json"
    request_path.write_text(
        json.dumps(
            {
                "producer_id": "hermes",
                "status": "submitted",
                "request_id": request_id,
                "domain": "codebase",
                "objective": "codebase: inspect current artifact repo",
                "sources": [
                    {
                        "source_id": "SRC-REPO",
                        "source_type": "current_artifact",
                        "ref": str(repo),
                        "access_mode": "read_only",
                        "sensitivity": "public",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "investigate-domain",
            "--instance",
            str(instance_root),
            "--request",
            str(request_path),
            "--date",
            "20260521",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "domain: codebase" in captured.out

    bundle_dir = (
        instance_root
        / "runtime-boundary"
        / "codebase-analysis"
        / "20260521"
        / request_id
    )
    for filename in (
        "inventory.json",
        "symbol-index.json",
        "scope-map.json",
        "validation-plan.json",
        "risk-scan.json",
        "source-inspection-decision.json",
    ):
        assert (bundle_dir / filename).exists()

    boundary_dir = (
        instance_root
        / "runtime-boundary"
        / "domain-investigation"
        / "codebase"
        / "20260521"
    )
    tool_result = json.loads(
        (boundary_dir / f"hisys-tool-result-{request_id}.json").read_text(
            encoding="utf-8"
        )
    )
    assert tool_result["quality_gate"] == "passed"

    domain_result_artifacts = list(boundary_dir.glob("domain-investigation-result-*.json"))
    assert len(domain_result_artifacts) == 1
    domain_payload = json.loads(domain_result_artifacts[0].read_text(encoding="utf-8"))
    codebase_packages = [
        pkg
        for pkg in domain_payload["investigation_data"]["evidence_packages"]
        if pkg["evidence_type"] == "codebase_analysis_bundle"
    ]
    assert len(codebase_packages) == 1
    assert codebase_packages[0]["evidence_refs"] == [
        f"runtime-boundary/codebase-analysis/20260521/{request_id}/inventory.json",
        f"runtime-boundary/codebase-analysis/20260521/{request_id}/symbol-index.json",
        f"runtime-boundary/codebase-analysis/20260521/{request_id}/scope-map.json",
        f"runtime-boundary/codebase-analysis/20260521/{request_id}/risk-scan.json",
    ]


def _portfolio_bundle_payload() -> dict[str, object]:
    return {
        "line_refs": [
            {
                "line_label": "M21",
                "artifact_refs": [
                    "docs/plans/m21-1-traceability-coverage-report-implementation-tasks.md",
                    "docs/plans/m21-6-change-impact-analyzer-implementation-tasks.md",
                ],
                "schema_ids": [
                    "hisys.traceability.coverage.v1",
                    "hisys.change_impact.v1",
                ],
                "quality_gate_refs": [
                    "tests/unit/test_traceability_coverage.py",
                    "tests/unit/test_change_impact.py",
                ],
                "implemented_surface_count": 9,
                "human_gated_surface_count": 2,
            },
            {
                "line_label": "DARS_PANEL_LOCAL_COMPLETION",
                "artifact_refs": [
                    "docs/reports/dars-panel-local-completion-audit.md",
                ],
                "schema_ids": ["hisys.dars_panel_readiness.v1"],
                "quality_gate_refs": [
                    "tests/unit/test_dars_critic_panel_runtime.py",
                ],
                "implemented_surface_count": 5,
                "human_gated_surface_count": 0,
            },
        ]
    }


def test_codebase_evidence_portfolio_cli_writes_report(tmp_path: Path, capsys) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(
        json.dumps(_portfolio_bundle_payload()), encoding="utf-8"
    )

    result = main(
        [
            "codebase-evidence-portfolio",
            "--instance",
            str(instance_root),
            "--date",
            "20260521",
            "--line-bundle",
            str(bundle_path),
            "--current-head-short",
            "86684f4",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "codebase-evidence-portfolio report" in captured.out
    assert "advisory_only: true" in captured.out
    assert "requires_human_review: true" in captured.out
    assert "external_call_made: false" in captured.out
    assert "mutation_performed: false" in captured.out
    assert "raw_source_content_persisted: false" in captured.out
    assert "allowed_actions: advisory_only" in captured.out
    assert "source_line_count: 2" in captured.out
    assert "implemented_surface_count: 14" in captured.out
    assert "human_gated_surface_count: 2" in captured.out

    json_path = (
        instance_root
        / "runtime-boundary"
        / "codebase-evidence-portfolio"
        / "20260521"
        / "portfolio-report.json"
    )
    md_path = (
        instance_root
        / "runtime-boundary"
        / "codebase-evidence-portfolio"
        / "20260521"
        / "portfolio-report.md"
    )
    assert json_path.exists()
    assert md_path.exists()

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema_id"] == "hisys.codebase_evidence_portfolio.v1"
    assert data["current_head_short"] == "86684f4"
    assert data["source_lines"] == ["DARS_PANEL_LOCAL_COMPLETION", "M21"]
    assert data["implemented_surface_count"] == 14
    assert data["human_gated_surface_count"] == 2
    assert "hisys.change_impact.v1" in data["schema_ids"]
    assert data["advisory_only"] is True


def test_codebase_evidence_portfolio_cli_rejects_missing_line_refs(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps({"not_line_refs": []}), encoding="utf-8")
    with pytest.raises(ValueError):
        main(
            [
                "codebase-evidence-portfolio",
                "--instance",
                str(instance_root),
                "--date",
                "20260521",
                "--line-bundle",
                str(bundle_path),
            ]
        )


def test_codebase_evidence_portfolio_cli_rejects_bad_date(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(
        json.dumps(
            {
                "line_refs": [
                    {
                        "line_label": "M21",
                        "artifact_refs": [
                            "docs/plans/m21-1-traceability-coverage-report-implementation-tasks.md"
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        main(
            [
                "codebase-evidence-portfolio",
                "--instance",
                str(instance_root),
                "--date",
                "2026-05-21",
                "--line-bundle",
                str(bundle_path),
            ]
        )


def test_codebase_evidence_portfolio_cli_records_unsafe_inputs(
    tmp_path: Path, capsys
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(
        json.dumps(
            {
                "line_refs": [
                    {
                        "line_label": "M21",
                        "artifact_refs": [
                            "/etc/passwd",
                            "../escape.md",
                            "docs/plans/m21-1-traceability-coverage-report-implementation-tasks.md",
                        ],
                        "schema_ids": ["hisys.traceability.coverage.v1"],
                    },
                    {
                        "line_label": "lowercase-not-allowed",
                        "artifact_refs": ["docs/should-not-leak.md"],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    result = main(
        [
            "codebase-evidence-portfolio",
            "--instance",
            str(instance_root),
            "--date",
            "20260521",
            "--line-bundle",
            str(bundle_path),
        ]
    )
    captured = capsys.readouterr()
    assert result == 0
    assert "unsafe_ref_count: 2" in captured.out
    assert "unsafe_line_label_count: 1" in captured.out
    json_path = (
        instance_root
        / "runtime-boundary"
        / "codebase-evidence-portfolio"
        / "20260521"
        / "portfolio-report.json"
    )
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert "/etc/passwd" in data["unsafe_refs"]
    assert "../escape.md" in data["unsafe_refs"]
    assert "lowercase-not-allowed" in data["unsafe_line_labels"]
    assert "docs/should-not-leak.md" not in data["artifact_refs"]


def _oss_comparison_bundle_payload() -> dict[str, object]:
    return {
        "local_line": {
            "line_label": "M21",
            "category_refs": [
                "architecture_candidates",
                "change_impact",
                "traceability_coverage",
            ],
            "portfolio_refs": [
                "docs/plans/m21-1-traceability-coverage-report-implementation-tasks.md",
            ],
            "implemented_surface_count": 9,
            "human_gated_surface_count": 2,
        },
        "approved_sources": [
            {
                "source_id": "understand-static-analysis",
                "source_name": "Approved static-analysis reference",
                "license_tag": "n/a",
                "category_refs": [
                    "architecture_candidates",
                    "change_impact",
                    "traceability_coverage",
                ],
                "approved_refs": [
                    "docs/plans/m23-advanced-codebase-adapter-integration-plan.md",
                ],
                "local_fixture_refs": [
                    "tests/fixtures/oss/approved/understand-static-analysis.json",
                ],
                "notes": "Local fixture descriptor only.",
            },
            {
                "source_id": "pylint-style-rules",
                "source_name": "Approved style/lint reference",
                "license_tag": "GPL-2.0-or-later",
                "category_refs": [
                    "code_analysis_pass_contract",
                    "style_conventions",
                ],
                "approved_refs": [
                    "docs/plans/m23-advanced-codebase-adapter-integration-plan.md",
                ],
                "local_fixture_refs": [
                    "tests/fixtures/oss/approved/pylint-style-rules.json",
                ],
                "notes": "Local fixture descriptor only.",
            },
        ],
    }


def test_oss_comparison_adapter_cli_writes_report(
    tmp_path: Path, capsys
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(
        json.dumps(_oss_comparison_bundle_payload()), encoding="utf-8"
    )

    result = main(
        [
            "oss-comparison-adapter",
            "--instance",
            str(instance_root),
            "--date",
            "20260522",
            "--bundle",
            str(bundle_path),
            "--current-head-short",
            "d610c53",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "oss-comparison-adapter report" in captured.out
    assert "compared_source_count: 2" in captured.out
    assert "advisory_only: true" in captured.out
    assert "requires_human_review: true" in captured.out
    assert "external_call_made: false" in captured.out
    assert "mutation_performed: false" in captured.out
    assert "raw_source_content_persisted: false" in captured.out
    assert "live_external_action_authorized: false" in captured.out
    assert "allowed_actions: advisory_only" in captured.out

    json_path = (
        instance_root
        / "runtime-boundary"
        / "oss-comparison"
        / "20260522"
        / "comparison-report.json"
    )
    md_path = (
        instance_root
        / "runtime-boundary"
        / "oss-comparison"
        / "20260522"
        / "comparison-report.md"
    )
    assert json_path.exists()
    assert md_path.exists()

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema_id"] == "hisys.oss_comparison_adapter.v1"
    assert data["current_head_short"] == "d610c53"
    assert data["local_line_label"] == "M21"
    assert data["compared_source_ids"] == [
        "pylint-style-rules",
        "understand-static-analysis",
    ]
    assert "traceability_coverage" in data["intersection_category_refs"]
    assert "style_conventions" in data["oss_only_category_refs"]
    assert data["advisory_only"] is True


def test_oss_comparison_adapter_cli_rejects_missing_local_line(
    tmp_path: Path,
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(
        json.dumps({"approved_sources": []}), encoding="utf-8"
    )
    with pytest.raises(ValueError):
        main(
            [
                "oss-comparison-adapter",
                "--instance",
                str(instance_root),
                "--date",
                "20260522",
                "--bundle",
                str(bundle_path),
            ]
        )


def test_oss_comparison_adapter_cli_rejects_bad_date(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(
        json.dumps(_oss_comparison_bundle_payload()), encoding="utf-8"
    )
    with pytest.raises(ValueError):
        main(
            [
                "oss-comparison-adapter",
                "--instance",
                str(instance_root),
                "--date",
                "2026-05-22",
                "--bundle",
                str(bundle_path),
            ]
        )


def test_oss_comparison_adapter_cli_records_unsafe_inputs(
    tmp_path: Path, capsys
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(
        json.dumps(
            {
                "local_line": {
                    "line_label": "M21",
                    "category_refs": ["traceability_coverage"],
                    "portfolio_refs": [
                        "/etc/passwd",
                        "../escape.md",
                        "docs/plans/m21-1-traceability-coverage-report-implementation-tasks.md",
                    ],
                    "implemented_surface_count": 1,
                },
                "approved_sources": [
                    {
                        "source_id": "UPPERCASE_SOURCE",
                        "category_refs": ["foo"],
                    },
                    {
                        "source_id": "approved-fixture",
                        "category_refs": [
                            "traceability_coverage",
                            "extra_topic",
                        ],
                        "approved_refs": ["../bad.md"],
                        "notes": "ok",
                    },
                    {
                        "source_id": "malformed-notes",
                        "category_refs": ["traceability_coverage"],
                        "notes": "\x00binary",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    result = main(
        [
            "oss-comparison-adapter",
            "--instance",
            str(instance_root),
            "--date",
            "20260522",
            "--bundle",
            str(bundle_path),
        ]
    )
    captured = capsys.readouterr()
    assert result == 0
    assert "compared_source_count: 1" in captured.out
    assert "unsafe_ref_count: 3" in captured.out
    assert "unsafe_source_id_count: 2" in captured.out

    json_path = (
        instance_root
        / "runtime-boundary"
        / "oss-comparison"
        / "20260522"
        / "comparison-report.json"
    )
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert "/etc/passwd" in data["unsafe_refs"]
    assert "../escape.md" in data["unsafe_refs"]
    assert "../bad.md" in data["unsafe_refs"]
    assert "UPPERCASE_SOURCE" in data["unsafe_source_ids"]
    assert "malformed-notes" in data["unsafe_source_ids"]
    assert "approved-fixture" in data["compared_source_ids"]
    assert "extra_topic" in data["oss_only_category_refs"]
    assert "foo" not in data["oss_only_category_refs"]


_LSP_CANNED_RUFF_PAYLOAD = json.dumps(
    [
        {
            "code": "F401",
            "message": "`os` imported but unused",
            "filename": "src/a.py",
            "location": {"row": 1, "column": 1},
            "end_location": {"row": 1, "column": 10},
        },
        {
            "code": "E501",
            "message": "Line too long (95 > 88)",
            "filename": "src/a.py",
            "location": {"row": 5, "column": 1},
            "end_location": {"row": 5, "column": 96},
        },
        {
            "code": "W292",
            "message": "No newline at end of file",
            "filename": "src/b.py",
            "location": {"row": 12, "column": 1},
            "end_location": {"row": 12, "column": 1},
        },
    ]
)


def _lsp_adapter_bundle_payload(workspace_root: Path) -> dict[str, object]:
    return {
        "workspace_root": str(workspace_root),
        "command": {
            "command_id": "ruff-check",
            "argv": ["ruff", "check", "--output-format=json", "src/"],
            "timeout_seconds": 30,
            "expected_exit_codes": [0, 1],
            "output_format": "ruff_json",
        },
        "target_refs": ["src/a.py", "src/b.py"],
        "command_allowlist": ["ruff"],
        "human_approval_ref": "docs/approvals/lsp-adapter-test.md",
    }


def test_lsp_adapter_cli_writes_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    workspace_root = instance_root / "workspace"
    workspace_root.mkdir()
    (workspace_root / "src").mkdir()
    (workspace_root / "src" / "a.py").write_text("", encoding="utf-8")
    (workspace_root / "src" / "b.py").write_text("", encoding="utf-8")
    bundle_path = tmp_path / "lsp-bundle.json"
    bundle_path.write_text(
        json.dumps(_lsp_adapter_bundle_payload(workspace_root)),
        encoding="utf-8",
    )

    fake_run = MagicMock()
    fake_run.return_value = subprocess.CompletedProcess(
        args=["ruff", "check", "--output-format=json", "src/"],
        returncode=1,
        stdout=_LSP_CANNED_RUFF_PAYLOAD,
        stderr="",
    )
    monkeypatch.setattr(subprocess, "run", fake_run)

    result = main(
        [
            "lsp-adapter",
            "--instance",
            str(instance_root),
            "--date",
            "20260522",
            "--bundle",
            str(bundle_path),
            "--current-head-short",
            "1874ad5",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "lsp-adapter report" in captured.out
    assert "command_id: ruff-check" in captured.out
    assert "output_format: ruff_json" in captured.out
    assert "subprocess_exit_code: 1" in captured.out
    assert "subprocess_timed_out: False" in captured.out
    assert "output_truncated: False" in captured.out
    assert "advisory_only: true" in captured.out
    assert "requires_human_review: true" in captured.out
    assert "external_call_made: false" in captured.out
    assert "mutation_performed: false" in captured.out
    assert "raw_source_content_persisted: false" in captured.out
    assert "live_external_action_authorized: false" in captured.out
    assert "allowed_actions: advisory_only" in captured.out

    json_path = (
        instance_root
        / "runtime-boundary"
        / "lsp-adapter"
        / "20260522"
        / "ruff-check"
        / "lsp-report.json"
    )
    md_path = (
        instance_root
        / "runtime-boundary"
        / "lsp-adapter"
        / "20260522"
        / "ruff-check"
        / "lsp-report.md"
    )
    assert json_path.exists()
    assert md_path.exists()

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema_id"] == "hisys.lsp_adapter.v1"
    assert data["current_head_short"] == "1874ad5"
    assert data["command_id"] == "ruff-check"
    assert data["output_format"] == "ruff_json"
    assert data["advisory_only"] is True
    assert data["raw_source_content_persisted"] is False
    assert data["live_external_action_authorized"] is False
    assert data["allowed_actions"] == "advisory_only"
    md_body = md_path.read_text(encoding="utf-8")
    for raw_message in (
        "`os` imported but unused",
        "Line too long (95 > 88)",
        "No newline at end of file",
    ):
        assert raw_message not in md_body
    fake_run.assert_called_once()
    called_kwargs = fake_run.call_args[1]
    assert called_kwargs["shell"] is False
    assert set(called_kwargs["env"].keys()) == {"PATH"}


def test_lsp_adapter_cli_rejects_missing_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    workspace_root = instance_root / "workspace"
    workspace_root.mkdir()
    bundle_path = tmp_path / "lsp-bundle.json"
    bundle_path.write_text(
        json.dumps(
            {
                "workspace_root": str(workspace_root),
                "command_allowlist": ["ruff"],
                "human_approval_ref": "docs/approvals/lsp-adapter-test.md",
            }
        ),
        encoding="utf-8",
    )
    fake_run = MagicMock()
    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(ValueError):
        main(
            [
                "lsp-adapter",
                "--instance",
                str(instance_root),
                "--date",
                "20260522",
                "--bundle",
                str(bundle_path),
            ]
        )
    fake_run.assert_not_called()


def test_lsp_adapter_cli_rejects_bad_date(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    workspace_root = instance_root / "workspace"
    workspace_root.mkdir()
    bundle_path = tmp_path / "lsp-bundle.json"
    bundle_path.write_text(
        json.dumps(_lsp_adapter_bundle_payload(workspace_root)),
        encoding="utf-8",
    )
    fake_run = MagicMock()
    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(ValueError):
        main(
            [
                "lsp-adapter",
                "--instance",
                str(instance_root),
                "--date",
                "2026-05-22",
                "--bundle",
                str(bundle_path),
            ]
        )
    fake_run.assert_not_called()


def test_lsp_adapter_cli_rejects_command_not_in_allowlist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    workspace_root = instance_root / "workspace"
    workspace_root.mkdir()
    bundle_path = tmp_path / "lsp-bundle.json"
    bundle_path.write_text(
        json.dumps(
            {
                "workspace_root": str(workspace_root),
                "command": {
                    "command_id": "rm-rf",
                    "argv": ["rm", "-rf", "/"],
                    "timeout_seconds": 30,
                    "output_format": "ruff_json",
                },
                "target_refs": [],
                "command_allowlist": ["ruff"],
                "human_approval_ref": "docs/approvals/lsp-adapter-test.md",
            }
        ),
        encoding="utf-8",
    )
    fake_run = MagicMock()
    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(ValueError, match="lsp_command_not_in_allowlist"):
        main(
            [
                "lsp-adapter",
                "--instance",
                str(instance_root),
                "--date",
                "20260522",
                "--bundle",
                str(bundle_path),
            ]
        )
    fake_run.assert_not_called()
