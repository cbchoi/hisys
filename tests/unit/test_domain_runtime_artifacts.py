"""Runtime artifact writer tests for structured domain packets.

Traceability: HISYS-DOM-003, HISYS-DOM-010, HISYS-DOM-012.
"""

from __future__ import annotations

import json

from hisys.domain.layers import DomainUseCaseContext
from hisys.domain.runtime import DomainRuntimeArtifactWriter
from hisys.domain.translation import DomainUseCaseArtifactTranslator
from hisys.domain.use_cases import ResearchAnalysisUseCase
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
