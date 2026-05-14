"""Bridge contract tests for structured domain use-case results.

Traceability: HISYS-DOM-003, HISYS-DOM-009, HISYS-DOM-010, HISYS-DOM-012.
"""

from __future__ import annotations

from hisys.domain.translation import DomainUseCaseArtifactTranslator, build_domain_investigation_result
from hisys.domain.use_cases import ResearchAnalysisUseCase
from hisys.schemas.domain_investigation import DomainInvestigationRequest, HisysToolResult
from hisys.domain.layers import DomainUseCaseContext


def _request() -> DomainInvestigationRequest:
    return DomainInvestigationRequest(
        request_id="REQ-BRIDGE-001",
        producer_id="hermes",
        status="submitted",
        domain="research",
        objective="bridge structured research use case result",
        sources=[],
        config_snapshot_refs=["runtime-boundary/configs/domain-config.json"],
        prompt_bundle_refs=["runtime-boundary/prompts/domain-prompt.md"],
    )


def test_use_case_result_bridges_to_domain_investigation_result(tmp_path) -> None:
    request = _request()
    use_case_result = ResearchAnalysisUseCase().run(
        request,
        DomainUseCaseContext(instance_root=tmp_path, boundary_dir=tmp_path / "runtime-boundary", yyyymmdd="20260514"),
    )

    packet = DomainUseCaseArtifactTranslator().translate(
        use_case_result,
        request=request,
        traceability_ids=("HISYS-DOM-003", "HISYS-DOM-010"),
    )
    result = build_domain_investigation_result(
        packet,
        request,
        runtime_boundary_refs=["runtime-boundary/domain-investigation/research/20260514/domain-use-case-result-REQ-BRIDGE-001.json"],
    )
    tool_result = HisysToolResult.from_domain_result(result)

    assert result.investigation_data.hisys_mode.level == "stone"
    assert result.investigation_data.request_id == request.request_id
    assert result.alternative_decision_set.request_id == request.request_id
    assert result.recommendation_summary == packet.recommendation_summary
    assert tool_result.quality_gate == result.quality_gate
    assert tool_result.runtime_boundary_refs == result.runtime_boundary_refs


def test_bridge_preserves_governance_flags_and_human_review(tmp_path) -> None:
    request = _request()
    use_case_result = ResearchAnalysisUseCase().run(
        request,
        DomainUseCaseContext(instance_root=tmp_path, boundary_dir=tmp_path / "runtime-boundary", yyyymmdd="20260514"),
    )

    packet = DomainUseCaseArtifactTranslator().translate(
        use_case_result,
        request=request,
        traceability_ids=("HISYS-DOM-009", "HISYS-DOM-012"),
    )
    result = build_domain_investigation_result(packet, request, runtime_boundary_refs=[])
    tool_result = HisysToolResult.from_domain_result(result)

    assert packet.requires_human_review is True
    assert result.requires_human_review is True
    assert tool_result.requires_human_review is True
    assert result.external_call_made is False
    assert result.mutation_performed is False
    assert tool_result.external_call_made is False
    assert tool_result.mutation_performed is False
    assert packet.traceability_ids == ("HISYS-DOM-009", "HISYS-DOM-012")
