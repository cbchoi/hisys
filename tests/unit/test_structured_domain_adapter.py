"""Tests for the generic structured domain adapter/spec seam.

Traceability: HISYS-DOM-001, HISYS-DOM-003, HISYS-DOM-010, HISYS-DOM-012.
"""

from __future__ import annotations

from hisys.domain.adapters import DomainInvestigationContext
from hisys.domain.domain_adapters import DomainAdapterSpec, StructuredDomainAdapter, build_use_case_context
from hisys.domain.runtime import DomainRuntimeArtifactWriter
from hisys.domain.translation import DomainUseCaseArtifactTranslator
from hisys.domain.use_cases import ResearchAnalysisUseCase
from hisys.schemas.domain_investigation import DomainInvestigationRequest, DomainInvestigationResult


def _request(domain: str = "research") -> DomainInvestigationRequest:
    return DomainInvestigationRequest(
        request_id="REQ-STRUCTURED-001",
        producer_id="hermes",
        status="submitted",
        domain=domain,
        objective="structured adapter fake spec request",
        sources=[],
        config_snapshot_refs=["runtime-boundary/configs/domain-config.json"],
        prompt_bundle_refs=["runtime-boundary/prompts/domain-prompt.md"],
    )


def _context(tmp_path) -> DomainInvestigationContext:
    return DomainInvestigationContext(
        instance_root=tmp_path,
        boundary_dir=tmp_path / "runtime-boundary" / "domain-investigation",
        yyyymmdd="20260514",
    )


def _spec() -> DomainAdapterSpec:
    return DomainAdapterSpec(
        domain_id="research",
        aliases=("research",),
        use_case_factory=ResearchAnalysisUseCase,
        translator=DomainUseCaseArtifactTranslator(),
        artifact_writer=DomainRuntimeArtifactWriter(),
        traceability_ids=("HISYS-DOM-003", "HISYS-DOM-010"),
        safety_policy="read_only_advisory",
    )


def test_build_use_case_context_preserves_runtime_boundary(tmp_path) -> None:
    context = _context(tmp_path)

    use_case_context = build_use_case_context(context)

    assert use_case_context.instance_root == context.instance_root
    assert use_case_context.boundary_dir == context.boundary_dir
    assert use_case_context.yyyymmdd == context.yyyymmdd


def test_structured_domain_adapter_supports_spec_domain(tmp_path) -> None:
    adapter = StructuredDomainAdapter(_spec())

    assert adapter.supports(_request("research")) is True
    assert adapter.supports(_request("codebase")) is False


def test_structured_domain_adapter_returns_existing_domain_result_schema(tmp_path) -> None:
    adapter = StructuredDomainAdapter(_spec())

    result = adapter.investigate(_request("research"), _context(tmp_path))

    assert isinstance(result, DomainInvestigationResult)
    assert result.request_id == "REQ-STRUCTURED-001"
    assert result.domain == "research"
    assert result.investigation_data.hisys_mode.level == "stone"
    assert result.requires_human_review is True
    assert result.external_call_made is False
    assert result.mutation_performed is False
    assert any(ref.endswith("domain-use-case-result-REQ-STRUCTURED-001.json") for ref in result.runtime_boundary_refs)
