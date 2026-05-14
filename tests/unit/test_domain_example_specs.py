"""Tests for example structured-domain spec registration and precedence.

Traceability: HISYS-FR-DOM-001, HISYS-FR-DOM-002, HISYS-FR-DOM-003,
HISYS-FR-DOM-004, HISYS-FR-DOM-005, HISYS-T-025, HISYS-T-026, HISYS-T-027.
"""

from __future__ import annotations

from pathlib import Path

from hisys.cli.main import (
    _default_domain_adapter_registry,
    _ResearchGapDomainAdapter,
    _should_apply_research_gap_postprocessors,
)
from hisys.config import InstanceRoot
from hisys.domain.domain_adapters import StructuredDomainAdapter
from hisys.domain.specs import codebase_spec, research_spec
from hisys.domain.use_cases import CodeAnalysisUseCase, ResearchAnalysisUseCase
from hisys.schemas.domain_investigation import DomainInvestigationRequest


def _request(domain: str, objective: str, request_id: str = "REQ-EXAMPLE-001") -> DomainInvestigationRequest:
    return DomainInvestigationRequest.model_validate(
        {
            "producer_id": "hermes",
            "status": "submitted",
            "request_id": request_id,
            "domain": domain,
            "objective": objective,
            "sources": [
                {
                    "source_id": "SRC-LOCAL-FIXTURE",
                    "source_type": "current_artifact",
                    "ref": "artifact://local",
                    "access_mode": "read_only",
                }
            ],
        }
    )


def _instance(tmp_path: Path) -> InstanceRoot:
    return InstanceRoot(root=tmp_path)


def test_research_gap_objective_resolves_to_legacy_adapter(tmp_path: Path) -> None:
    registry = _default_domain_adapter_registry(instance=_instance(tmp_path))

    adapter = registry.resolve(
        _request("research", "find research gap among formalisms for self-organizing structure")
    )

    assert isinstance(adapter, _ResearchGapDomainAdapter)


def test_general_research_objective_resolves_to_research_structured_spec(tmp_path: Path) -> None:
    registry = _default_domain_adapter_registry(instance=_instance(tmp_path))

    adapter = registry.resolve(
        _request("research", "summarize research evidence for advisory review")
    )

    assert isinstance(adapter, StructuredDomainAdapter)
    assert adapter.spec.domain_id == "research"
    assert adapter.spec.use_case_factory is ResearchAnalysisUseCase


def test_codebase_request_resolves_to_codebase_structured_spec(tmp_path: Path) -> None:
    registry = _default_domain_adapter_registry(instance=_instance(tmp_path))

    adapter = registry.resolve(
        _request("codebase", "evaluate current codebase implementation evidence")
    )

    assert isinstance(adapter, StructuredDomainAdapter)
    assert adapter.spec.domain_id == "codebase"


def test_codebase_requirements_analysis_objective_resolves_to_codebase_spec(tmp_path: Path) -> None:
    registry = _default_domain_adapter_registry(instance=_instance(tmp_path))

    adapter = registry.resolve(
        _request("codebase", "requirements-analysis: review SRS coverage for module X")
    )

    assert isinstance(adapter, StructuredDomainAdapter)
    assert adapter.spec.domain_id == "codebase"


def test_structured_specs_skip_research_gap_postprocessors(tmp_path: Path) -> None:
    research_adapter = StructuredDomainAdapter(research_spec())
    codebase_adapter = StructuredDomainAdapter(codebase_spec())

    assert _should_apply_research_gap_postprocessors(research_adapter) is False
    assert _should_apply_research_gap_postprocessors(codebase_adapter) is False


def test_research_spec_factory_returns_research_analysis_use_case() -> None:
    spec = research_spec()

    assert spec.domain_id == "research"
    use_case = spec.use_case_factory()
    assert isinstance(use_case, ResearchAnalysisUseCase)


def test_codebase_spec_factory_returns_code_analysis_use_case() -> None:
    spec = codebase_spec()

    assert spec.domain_id == "codebase"
    use_case = spec.use_case_factory()
    assert isinstance(use_case, CodeAnalysisUseCase)
