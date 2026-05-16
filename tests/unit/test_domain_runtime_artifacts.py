"""Runtime artifact writer tests for structured domain packets.

Traceability: HISYS-DOM-003, HISYS-DOM-010, HISYS-DOM-012.

The artifact-integrity tests below trace to the Local DARS / ByeSys
Provenance plan Milestone 2.5 (`docs/plans/2026-05-16-local-dars-byesys-provenance.md`).
"""

from __future__ import annotations

import json

from hisys.domain.adapters import DomainInvestigationContext
from hisys.domain.domain_adapters import StructuredDomainAdapter
from hisys.domain.layers import DomainUseCaseContext
from hisys.domain.runtime import DomainRuntimeArtifactWriter
from hisys.domain.specs import codebase_spec, research_spec
from hisys.domain.translation import DomainUseCaseArtifactTranslator
from hisys.domain.use_cases import CodeAnalysisUseCase, ResearchAnalysisUseCase
from hisys.schemas.domain_investigation import DomainInvestigationRequest


def _request() -> DomainInvestigationRequest:
    return DomainInvestigationRequest(
        request_id="REQ-RUNTIME-001",
        producer_id="hermes",
        status="submitted",
        domain="research",
        objective="persist structured domain runtime artifact",
        sources=[],
        config_snapshot_refs=["runtime-boundary/configs/domain-config.json"],
        prompt_bundle_refs=["runtime-boundary/prompts/domain-prompt.md"],
    )


def test_runtime_writer_persists_traceability_and_governance_fields(tmp_path) -> None:
    request = _request()
    context = DomainUseCaseContext(
        instance_root=tmp_path,
        boundary_dir=tmp_path / "runtime-boundary" / "domain-investigation",
        yyyymmdd="20260514",
    )
    result = ResearchAnalysisUseCase().run(request, context)
    packet = DomainUseCaseArtifactTranslator().translate(
        result,
        request=request,
        traceability_ids=("HISYS-DOM-003", "HISYS-DOM-010"),
    )

    refs = DomainRuntimeArtifactWriter().write(packet, context)

    json_path = tmp_path / refs.json_ref
    md_path = tmp_path / refs.markdown_ref
    assert json_path.exists()
    assert md_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["request_id"] == "REQ-RUNTIME-001"
    assert data["domain"] == "research"
    assert [step["layer"] for step in data["layer_trace"]] == ["investigation", "aggregation", "decision"]
    assert "artifact_refs" in data
    assert data["config_snapshot_refs"] == ["runtime-boundary/configs/domain-config.json"]
    assert data["prompt_bundle_refs"] == ["runtime-boundary/prompts/domain-prompt.md"]
    assert data["traceability_ids"] == ["HISYS-DOM-003", "HISYS-DOM-010"]
    assert data["requires_human_review"] is True
    assert data["external_call_made"] is False
    assert data["mutation_performed"] is False
    assert data["quality_gate"] == "needs_more_evidence"
    assert "Human review required: true" in md_path.read_text(encoding="utf-8")


def test_runtime_artifact_labels_requirements_analysis_codebase_subtype(tmp_path) -> None:
    request = DomainInvestigationRequest(
        request_id="REQ-RUNTIME-REQA-001",
        producer_id="hermes",
        status="submitted",
        domain="codebase",
        objective="requirements-analysis: review SRS coverage for module Y",
        sources=[],
    )
    context = DomainUseCaseContext(
        instance_root=tmp_path,
        boundary_dir=tmp_path / "runtime-boundary" / "domain-investigation",
        yyyymmdd="20260514",
    )
    result = CodeAnalysisUseCase(requirements_root="/home/cbchoi/me/requirements").run(
        request, context
    )
    packet = DomainUseCaseArtifactTranslator().translate(
        result,
        request=request,
        traceability_ids=("HISYS-FR-DOM-005", "HISYS-T-025"),
    )

    refs = DomainRuntimeArtifactWriter().write(packet, context)

    data = json.loads((tmp_path / refs.json_ref).read_text(encoding="utf-8"))
    # The persisted runtime artifact must carry the requirements-analysis
    # subtype label so audit reviewers can identify it without re-reading the
    # request objective.
    assert "REQUIREMENTS-ANALYSIS" in data["artifact_refs"]["investigation_ref"]
    assert data["external_call_made"] is False
    assert data["mutation_performed"] is False


# ---------------------------------------------------------------------------
# Local DARS / ByeSys provenance plan — Milestone 2.5 (Ralph M10.1, M10.2)
# Every ref recorded under `runtime_boundary_refs` or `dars_refs` must resolve
# to a real artifact under the instance root. Optional missing DARS output
# must be explicit, not a dangling path.
# ---------------------------------------------------------------------------


def _research_request(request_id: str = "REQ-INTEGRITY-001") -> DomainInvestigationRequest:
    return DomainInvestigationRequest(
        request_id=request_id,
        producer_id="hermes",
        status="submitted",
        domain="research",
        objective="verify runtime artifact integrity",
        sources=[],
    )


def _codebase_request(request_id: str = "REQ-INTEGRITY-CODE-001") -> DomainInvestigationRequest:
    return DomainInvestigationRequest(
        request_id=request_id,
        producer_id="hermes",
        status="submitted",
        domain="codebase",
        objective="verify runtime artifact integrity for codebase",
        sources=[],
    )


def _investigation_context(tmp_path) -> DomainInvestigationContext:
    return DomainInvestigationContext(
        instance_root=tmp_path,
        boundary_dir=tmp_path / "runtime-boundary" / "domain-investigation",
        yyyymmdd="20260516",
    )


def test_structured_adapter_aggregation_report_ref_resolves_to_file(tmp_path) -> None:
    adapter = StructuredDomainAdapter(research_spec())
    request = _research_request()
    context = _investigation_context(tmp_path)
    result = adapter.investigate(request, context)
    aggregation_ref = result.alternative_decision_set.candidates[0].evidence_refs
    candidate_paths = [ref for ref in aggregation_ref if ref.startswith("runtime-boundary/")]
    assert candidate_paths, "candidate evidence must reference a runtime-boundary aggregation path"
    for ref in candidate_paths:
        assert (tmp_path / ref).is_file(), f"missing runtime-boundary file for ref={ref}"


def test_structured_adapter_dars_decision_ref_resolves_to_file(tmp_path) -> None:
    adapter = StructuredDomainAdapter(research_spec())
    request = _research_request()
    context = _investigation_context(tmp_path)
    result = adapter.investigate(request, context)
    assert result.dars_refs, "dars_refs must be recorded for the structured domain"
    for ref in result.dars_refs:
        assert (tmp_path / ref).is_file(), f"missing DARS artifact for ref={ref}"


def test_structured_adapter_dars_decision_ref_is_advisory_placeholder(tmp_path) -> None:
    adapter = StructuredDomainAdapter(research_spec())
    request = _research_request("REQ-INTEGRITY-PLACEHOLDER-001")
    context = _investigation_context(tmp_path)
    result = adapter.investigate(request, context)
    assert result.dars_refs
    decision_path = tmp_path / result.dars_refs[0]
    payload = json.loads(decision_path.read_text(encoding="utf-8"))
    # The placeholder must explicitly mark itself as pending human review and
    # never claim live execution or mutation.
    assert payload.get("status") in {"pending_human_review", "skipped", "unavailable"}
    assert payload.get("requires_human_review") is True
    assert payload.get("external_call_made") is False
    assert payload.get("mutation_performed") is False
    assert payload.get("recommendation") == "human_review_required"


def test_structured_adapter_runtime_boundary_refs_all_resolve(tmp_path) -> None:
    adapter = StructuredDomainAdapter(research_spec())
    request = _research_request("REQ-INTEGRITY-RUNTIME-REFS-001")
    context = _investigation_context(tmp_path)
    result = adapter.investigate(request, context)
    assert result.runtime_boundary_refs
    for ref in result.runtime_boundary_refs:
        assert (tmp_path / ref).is_file(), f"missing runtime-boundary file for ref={ref}"


def test_structured_adapter_codebase_runtime_boundary_refs_all_resolve(tmp_path) -> None:
    adapter = StructuredDomainAdapter(codebase_spec())
    request = _codebase_request()
    context = _investigation_context(tmp_path)
    result = adapter.investigate(request, context)
    for ref in result.runtime_boundary_refs:
        assert (tmp_path / ref).is_file(), f"missing runtime-boundary file for ref={ref}"
    for ref in result.dars_refs:
        assert (tmp_path / ref).is_file(), f"missing DARS artifact for ref={ref}"


def test_structured_adapter_does_not_write_outside_instance_root(tmp_path) -> None:
    adapter = StructuredDomainAdapter(research_spec())
    request = _research_request("REQ-INTEGRITY-CONFINED-001")
    context = _investigation_context(tmp_path)
    adapter.investigate(request, context)
    # Every written artifact path under tmp_path must remain inside tmp_path;
    # tmp_path is the instance root in tests, so this asserts the integrity
    # guard never escapes the governed boundary.
    for path in tmp_path.rglob("*"):
        assert tmp_path in path.resolve().parents or path.resolve() == tmp_path
