"""Tests for three-layer domain use-case design.

Traceability: HISYS-FR-INV-001..006, HISYS-DARS-CONTRACT-001, HISYS-CON-010..012.
"""

from __future__ import annotations

from pathlib import Path

from hisys.domain.layers import DomainUseCaseContext
from hisys.domain.use_cases import CodeAnalysisUseCase, ResearchAnalysisUseCase
from hisys.schemas.domain_investigation import DomainInvestigationRequest


def _request(domain: str, objective: str) -> DomainInvestigationRequest:
    return DomainInvestigationRequest.model_validate(
        {
            "producer_id": "hermes",
            "status": "submitted",
            "request_id": f"REQ-{domain.upper()}-3LAYER-001",
            "domain": domain,
            "objective": objective,
            "sources": [
                {
                    "source_id": "SRC-LOCAL-ME-VAULT",
                    "source_type": "current_artifact",
                    "ref": "/home/cbchoi/me",
                    "access_mode": "read_only",
                }
            ],
            "user_focus": "Use investigation, aggregation, and decision layers.",
        }
    )


def _context(tmp_path: Path) -> DomainUseCaseContext:
    return DomainUseCaseContext(
        instance_root=tmp_path,
        boundary_dir=tmp_path / "runtime-boundary" / "domain-investigation" / "research" / "20260514",
        yyyymmdd="20260514",
    )


def test_research_use_case_runs_investigation_aggregation_decision_layers(tmp_path: Path) -> None:
    use_case = ResearchAnalysisUseCase()

    result = use_case.run(
        _request("research", "analyze research topic evidence"),
        _context(tmp_path),
    )

    assert [step.layer for step in result.layer_trace] == ["investigation", "aggregation", "decision"]
    assert result.investigation.scope == "research"
    assert result.investigation.local_search_targets == ["/home/cbchoi/me"]
    assert "publisher_source" in result.investigation.data_source_targets
    assert result.aggregation.report_type == "memo_aggregation_report"
    assert result.aggregation.input_memo_refs == result.investigation.memo_refs
    assert result.decision.decision_engine == "DARS"
    assert result.decision.input_report_ref == result.aggregation.report_ref
    assert result.external_call_made is False
    assert result.mutation_performed is False


def test_code_use_case_uses_local_me_vault_and_local_requirements_sources(tmp_path: Path) -> None:
    use_case = CodeAnalysisUseCase(requirements_root="/work/project/requirements")

    result = use_case.run(
        _request("codebase", "analyze source code requirements and design evidence"),
        _context(tmp_path),
    )

    assert [step.layer for step in result.layer_trace] == ["investigation", "aggregation", "decision"]
    assert result.investigation.scope == "codebase"
    assert result.investigation.local_search_targets == ["/home/cbchoi/me", "/work/project/requirements"]
    assert result.investigation.data_source_targets == ["local_requirements_folder"]
    assert result.aggregation.report_type == "memo_aggregation_report"
    assert result.decision.decision_engine == "DARS"
    assert result.decision.decision_type == "code_evaluation_review"
    assert result.external_call_made is False
    assert result.mutation_performed is False
