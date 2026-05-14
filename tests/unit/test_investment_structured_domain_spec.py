"""RED tests for the investment structured-domain spec acceptance boundary.

Traceability: HISYS-FR-DOM-006, HISYS-FR-DOM-003, HISYS-FR-DOM-004,
HISYS-T-028, HISYS-T-026, HISYS-T-027.

These tests lock the governance/safety boundary for `investment_spec` and
`InvestmentAnalysisUseCase` before any implementation lands. They are the M3.1
RED tests in the domain-adapter Ralph loop control plan.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.cli.main import _default_domain_adapter_registry, _ResearchGapDomainAdapter
from hisys.config import InstanceRoot
from hisys.domain.adapters import DomainInvestigationContext
from hisys.domain.domain_adapters import DomainAdapterSpec, StructuredDomainAdapter
from hisys.domain.specs import investment_spec
from hisys.domain.use_cases import InvestmentAnalysisUseCase
from hisys.schemas.domain_investigation import (
    DomainInvestigationRequest,
    DomainInvestigationResult,
    HisysToolResult,
)


def _request(
    *,
    request_id: str = "REQ-INVEST-001",
    objective: str = "advisory review of S&P 500 valuation evidence",
) -> DomainInvestigationRequest:
    return DomainInvestigationRequest.model_validate(
        {
            "producer_id": "hermes",
            "status": "submitted",
            "request_id": request_id,
            "domain": "investment",
            "objective": objective,
            "sources": [
                {
                    "source_id": "IDP-CLI-SP500-001",
                    "source_type": "current_artifact",
                    "ref": "runtime-boundary/investment-decisions/20260512/IDP-CLI-SP500-001.json",
                    "access_mode": "read_only",
                },
                {
                    "source_id": "IW-POLICY-CLI-SP500-BALANCED-001",
                    "source_type": "current_artifact",
                    "ref": "runtime-boundary/investment-decisions/20260512/IW-POLICY-CLI-SP500-BALANCED-001.json",
                    "access_mode": "read_only",
                },
            ],
            "config_snapshot_refs": ["config://investment-weight-policy-balanced"],
        }
    )


def _context(tmp_path: Path) -> DomainInvestigationContext:
    boundary_dir = tmp_path / "runtime-boundary" / "domain-investigation"
    boundary_dir.mkdir(parents=True, exist_ok=True)
    return DomainInvestigationContext(
        instance_root=tmp_path,
        boundary_dir=boundary_dir,
        yyyymmdd="20260514",
    )


def test_investment_spec_returns_domain_adapter_spec_with_canonical_id() -> None:
    spec = investment_spec()

    assert isinstance(spec, DomainAdapterSpec)
    assert spec.domain_id == "investment"
    assert "investment" in spec.aliases


def test_investment_spec_uses_investment_analysis_use_case() -> None:
    spec = investment_spec()
    use_case = spec.use_case_factory()

    assert isinstance(use_case, InvestmentAnalysisUseCase)


def test_investment_spec_traceability_includes_governance_anchors() -> None:
    spec = investment_spec()

    assert "HISYS-FR-DOM-006" in spec.traceability_ids
    assert "HISYS-T-028" in spec.traceability_ids


def test_investment_spec_safety_policy_marks_advisory_only() -> None:
    spec = investment_spec()

    # The advisory-only safety policy is an explicit contract that this
    # structured-domain path must not authorize live action or mutation.
    assert "advisory" in spec.safety_policy.lower()


def test_investment_structured_adapter_returns_bridgeable_result(tmp_path: Path) -> None:
    adapter = StructuredDomainAdapter(investment_spec())

    result = adapter.investigate(_request(), _context(tmp_path))

    assert isinstance(result, DomainInvestigationResult)
    assert result.domain == "investment"
    tool_result = HisysToolResult.from_domain_result(result)
    assert tool_result.domain == "investment"
    assert tool_result.external_call_made is False
    assert tool_result.mutation_performed is False
    assert tool_result.requires_human_review is True


def test_investment_structured_adapter_preserves_safety_defaults(tmp_path: Path) -> None:
    adapter = StructuredDomainAdapter(investment_spec())

    result = adapter.investigate(_request(), _context(tmp_path))

    assert result.requires_human_review is True
    assert result.external_call_made is False
    assert result.mutation_performed is False


def test_investment_structured_adapter_quality_gate_defaults_needs_more_evidence(tmp_path: Path) -> None:
    adapter = StructuredDomainAdapter(investment_spec())

    result = adapter.investigate(_request(), _context(tmp_path))

    assert result.quality_gate == "needs_more_evidence"


def test_investment_structured_adapter_projects_packet_and_policy_refs(tmp_path: Path) -> None:
    adapter = StructuredDomainAdapter(investment_spec())

    result = adapter.investigate(_request(), _context(tmp_path))

    evidence = result.investigation_data.evidence_packages[0]
    # Packet and weight-policy refs supplied via request sources must flow
    # through to the bridged investigation evidence as source refs.
    assert "IDP-CLI-SP500-001" in evidence.source_refs
    assert "IW-POLICY-CLI-SP500-BALANCED-001" in evidence.source_refs


def test_investment_structured_adapter_recommendation_carries_safety_phrases(tmp_path: Path) -> None:
    adapter = StructuredDomainAdapter(investment_spec())

    result = adapter.investigate(_request(), _context(tmp_path))

    summary = result.recommendation_summary.lower()
    assert "not financial advice" in summary
    assert "no autonomous execution" in summary


def test_investment_structured_adapter_runtime_artifact_records_governance_flags(tmp_path: Path) -> None:
    adapter = StructuredDomainAdapter(investment_spec())
    context = _context(tmp_path)

    result = adapter.investigate(_request(), context)

    json_refs = [ref for ref in result.runtime_boundary_refs if ref.endswith(".json")]
    assert json_refs, f"expected JSON runtime artifact in {result.runtime_boundary_refs}"
    artifact_path = tmp_path / json_refs[0]
    record = json.loads(artifact_path.read_text(encoding="utf-8"))
    summary = record["recommendation_summary"].lower()
    # The runtime artifact must surface execution / publication governance
    # flags so audit reviewers can confirm advisory-only handling.
    assert "execution_authorized=false" in summary
    assert "publication_or_live_action_approved=false" in summary
    assert record["requires_human_review"] is True
    assert record["external_call_made"] is False
    assert record["mutation_performed"] is False


def test_investment_domain_resolves_through_default_registry(tmp_path: Path) -> None:
    registry = _default_domain_adapter_registry(instance=InstanceRoot(root=tmp_path))

    adapter = registry.resolve(_request())

    assert isinstance(adapter, StructuredDomainAdapter)
    assert adapter.spec.domain_id == "investment"


def test_investment_registration_preserves_research_gap_precedence(tmp_path: Path) -> None:
    registry = _default_domain_adapter_registry(instance=InstanceRoot(root=tmp_path))

    research_gap_request = DomainInvestigationRequest.model_validate(
        {
            "producer_id": "hermes",
            "status": "submitted",
            "request_id": "REQ-INVEST-RES-GAP-001",
            "domain": "research",
            "objective": "find research gap among formalisms for self-organizing structure",
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

    adapter = registry.resolve(research_gap_request)

    # The investment spec must not displace the legacy research-gap adapter
    # for formalism-gap research objectives.
    assert isinstance(adapter, _ResearchGapDomainAdapter)


def test_investment_structured_adapter_does_not_authorize_execution(tmp_path: Path) -> None:
    adapter = StructuredDomainAdapter(investment_spec())
    context = _context(tmp_path)

    result = adapter.investigate(_request(), context)

    json_refs = [ref for ref in result.runtime_boundary_refs if ref.endswith(".json")]
    artifact_path = tmp_path / json_refs[0]
    record = json.loads(artifact_path.read_text(encoding="utf-8"))
    summary = record["recommendation_summary"]
    # Negative assertions guard against accidental flag inversion: the
    # advisory-only adapter must never claim authorization or live action.
    assert "execution_authorized=true" not in summary
    assert "publication_or_live_action_approved=true" not in summary
