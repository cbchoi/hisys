"""M20.1: codebase request can reference local artifact bundle.

Traceability: HISYS-FR-DOM-001..006, M20.1.
"""

from __future__ import annotations

from pathlib import Path

from hisys.domain.layers import DomainUseCaseContext
from hisys.domain.use_cases import CodeInvestigationLayer
from hisys.schemas.domain_investigation import DomainInvestigationRequest, DomainSourceRef


def _build_codebase_request(*, refs: list[tuple[str, str]]) -> DomainInvestigationRequest:
    sources = [
        DomainSourceRef(
            source_id=source_id,
            source_type="runtime_record",
            ref=ref,
            sensitivity="public",
        )
        for source_id, ref in refs
    ]
    return DomainInvestigationRequest(
        producer_id="hermes",
        status="submitted",
        request_id="REQ-M20-1",
        domain="codebase",
        objective="codebase: artifact-bridge-acceptance",
        sources=sources,
    )


def _context(tmp_path: Path) -> DomainUseCaseContext:
    return DomainUseCaseContext(
        instance_root=tmp_path,
        boundary_dir=tmp_path / "runtime-boundary" / "domain-investigation" / "codebase" / "20260520",
        yyyymmdd="20260520",
    )


def test_code_investigation_layer_surfaces_codebase_artifact_refs(tmp_path: Path) -> None:
    request = _build_codebase_request(
        refs=[
            ("SRC-INV", "runtime-boundary/codebase-analysis/20260520/REQ-M20-1/inventory.json"),
            ("SRC-SYM", "runtime-boundary/codebase-analysis/20260520/REQ-M20-1/symbol-index.json"),
            ("SRC-INV-DUP", "runtime-boundary/codebase-analysis/20260520/REQ-M20-1/inventory.json"),
            ("SRC-UP", "runtime-boundary/codebase-analysis/20260520/../escape.json"),
            ("SRC-EVD", "memo://REQ-M20-1/local-research-memos"),
        ],
    )

    layer = CodeInvestigationLayer(requirements_root=str(tmp_path / "requirements"))
    work_product = layer.investigate(request=request, context=_context(tmp_path))

    assert work_product.codebase_artifact_refs == [
        "runtime-boundary/codebase-analysis/20260520/REQ-M20-1/inventory.json",
        "runtime-boundary/codebase-analysis/20260520/REQ-M20-1/symbol-index.json",
    ]
    assert "SRC-EVD" in work_product.evidence_refs
    assert "SRC-UP" in work_product.evidence_refs
    for codebase_ref in work_product.codebase_artifact_refs:
        assert codebase_ref not in work_product.evidence_refs
    assert "SRC-INV" not in work_product.evidence_refs
    assert "SRC-SYM" not in work_product.evidence_refs
    assert "SRC-INV-DUP" not in work_product.evidence_refs


def test_code_investigation_layer_returns_empty_artifact_refs_when_none_present(tmp_path: Path) -> None:
    request = _build_codebase_request(
        refs=[("SRC-EVD", "memo://REQ-M20-1/local-code-and-requirements-memos")],
    )

    layer = CodeInvestigationLayer(requirements_root=str(tmp_path / "requirements"))
    work_product = layer.investigate(request=request, context=_context(tmp_path))

    assert work_product.codebase_artifact_refs == []
    assert "SRC-EVD" in work_product.evidence_refs


def test_code_investigation_layer_records_incomplete_bundle_missing_evidence(tmp_path: Path) -> None:
    request = _build_codebase_request(
        refs=[
            ("SRC-INV", "runtime-boundary/codebase-analysis/20260520/REQ-M20-2/inventory.json"),
            ("SRC-SYM", "runtime-boundary/codebase-analysis/20260520/REQ-M20-2/symbol-index.json"),
        ],
    )

    layer = CodeInvestigationLayer(requirements_root=str(tmp_path / "requirements"))
    work_product = layer.investigate(request=request, context=_context(tmp_path))

    assert work_product.codebase_bundle_gate == "needs_more_evidence"
    assert work_product.codebase_missing_evidence == ["risk_scan", "scope_map", "validation_plan"]
    assert work_product.requires_human_review is True


def test_code_investigation_layer_marks_complete_bundle_candidate_complete(tmp_path: Path) -> None:
    request = _build_codebase_request(
        refs=[
            ("SRC-INV", "runtime-boundary/codebase-analysis/20260520/REQ-M20-2/inventory.json"),
            ("SRC-SYM", "runtime-boundary/codebase-analysis/20260520/REQ-M20-2/symbol-index.json"),
            ("SRC-SCOPE", "runtime-boundary/codebase-analysis/20260520/REQ-M20-2/scope-map.json"),
            ("SRC-VALID", "runtime-boundary/codebase-analysis/20260520/REQ-M20-2/validation-plan.json"),
            ("SRC-RISK", "runtime-boundary/codebase-analysis/20260520/REQ-M20-2/risk-scan.json"),
        ],
    )

    layer = CodeInvestigationLayer(requirements_root=str(tmp_path / "requirements"))
    work_product = layer.investigate(request=request, context=_context(tmp_path))

    assert work_product.codebase_bundle_gate == "candidate_complete"
    assert work_product.codebase_missing_evidence == []
    assert work_product.requires_human_review is True
