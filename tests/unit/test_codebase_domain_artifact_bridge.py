"""M20.1: codebase request can reference local artifact bundle.

Traceability: HISYS-FR-DOM-001..006, M20.1, M20.2, M20.3.
"""

from __future__ import annotations

from pathlib import Path

from hisys.domain.adapters import DomainInvestigationContext
from hisys.domain.domain_adapters import StructuredDomainAdapter
from hisys.domain.layers import DomainUseCaseContext
from hisys.domain.specs import codebase_spec
from hisys.domain.use_cases import CodeInvestigationLayer
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
from hisys.schemas.domain_investigation import (
    DomainInvestigationRequest,
    DomainInvestigationResult,
    DomainSourceRef,
)


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


# ---------------------------------------------------------------------------
# M20.3 — complete local bundle enriches DomainInvestigationResult.
# ---------------------------------------------------------------------------


def _seed_review_repo(repo: Path) -> None:
    (repo / "pkg").mkdir()
    (repo / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "pkg" / "mod.py").write_text(
        "def add(a, b):\n    return a + b\n", encoding="utf-8"
    )


def _materialize_complete_bundle(
    instance_root: Path, repo: Path, *, date: str, request_id: str
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

    validation_ref = (
        f"runtime-boundary/codebase-analysis/{date}/{request_id}/validation-plan.json"
    )

    return {
        "inventory": inv_ref,
        "symbol_index": sym_ref,
        "scope_map": scope_ref,
        "validation_plan": validation_ref,
        "risk_scan": risk_ref,
    }


def _run_codebase_domain_result(
    *,
    request: DomainInvestigationRequest,
    instance_root: Path,
    yyyymmdd: str = "20260520",
) -> DomainInvestigationResult:
    context = DomainInvestigationContext(
        instance_root=instance_root,
        boundary_dir=instance_root / "runtime-boundary" / "domain-investigation",
        yyyymmdd=yyyymmdd,
    )
    adapter = StructuredDomainAdapter(codebase_spec())
    return adapter.investigate(request, context)


def test_codebase_domain_result_enriches_complete_local_bundle(tmp_path: Path) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    _seed_review_repo(repo)
    refs = _materialize_complete_bundle(
        instance_root, repo, date="20260520", request_id="m20_3_fixture"
    )

    request = _build_codebase_request_with_id(
        request_id="REQ-M20-3",
        refs=[
            ("SRC-INV", refs["inventory"]),
            ("SRC-SYM", refs["symbol_index"]),
            ("SRC-SCOPE", refs["scope_map"]),
            ("SRC-VALID", refs["validation_plan"]),
            ("SRC-RISK", refs["risk_scan"]),
        ],
    )

    result = _run_codebase_domain_result(request=request, instance_root=instance_root)

    assert result.quality_gate == "passed"
    assert result.requires_human_review is True
    assert result.external_call_made is False
    assert result.mutation_performed is False
    assert "approved" not in result.recommendation_summary.lower()

    codebase_packages = [
        pkg
        for pkg in result.investigation_data.evidence_packages
        if pkg.evidence_type == "codebase_analysis_bundle"
    ]
    assert len(codebase_packages) == 1
    package = codebase_packages[0]
    assert package.evidence_refs == [
        refs["inventory"],
        refs["symbol_index"],
        refs["scope_map"],
        refs["risk_scan"],
    ]
    assert package.external_call_made is False
    assert package.mutation_performed is False


def test_codebase_domain_result_maps_incomplete_bundle_refs_to_needs_more_evidence(
    tmp_path: Path,
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()

    # Four real role refs, validation_plan omitted -> work-product gate
    # is needs_more_evidence; loader is not called.
    request = _build_codebase_request_with_id(
        request_id="REQ-M20-3-INCOMPLETE",
        refs=[
            ("SRC-INV", "runtime-boundary/codebase-analysis/20260520/REQ-M20-3-INCOMPLETE/inventory.json"),
            ("SRC-SYM", "runtime-boundary/codebase-analysis/20260520/REQ-M20-3-INCOMPLETE/symbol-index.json"),
            ("SRC-SCOPE", "runtime-boundary/codebase-analysis/20260520/REQ-M20-3-INCOMPLETE/scope-map.json"),
            ("SRC-RISK", "runtime-boundary/codebase-analysis/20260520/REQ-M20-3-INCOMPLETE/risk-scan.json"),
        ],
    )

    result = _run_codebase_domain_result(request=request, instance_root=instance_root)

    assert result.quality_gate == "needs_more_evidence"
    assert result.requires_human_review is True
    assert result.external_call_made is False
    assert result.mutation_performed is False
    codebase_packages = [
        pkg
        for pkg in result.investigation_data.evidence_packages
        if pkg.evidence_type == "codebase_analysis_bundle"
    ]
    assert len(codebase_packages) == 1
    package = codebase_packages[0]
    assert any("missing role: validation_plan" in lim for lim in package.limitations)


def test_codebase_domain_result_maps_unreadable_complete_bundle_to_needs_more_evidence(
    tmp_path: Path,
) -> None:
    instance_root = tmp_path / "instance"
    instance_root.mkdir()

    # Five role refs satisfy the work-product gate (`candidate_complete`),
    # but no files exist on disk -> loader raises FileNotFoundError and
    # the adapter downgrades the result.
    request = _build_codebase_request_with_id(
        request_id="REQ-M20-3-UNREADABLE",
        refs=[
            ("SRC-INV", "runtime-boundary/codebase-analysis/20260520/REQ-M20-3-UNREADABLE/inventory.json"),
            ("SRC-SYM", "runtime-boundary/codebase-analysis/20260520/REQ-M20-3-UNREADABLE/symbol-index.json"),
            ("SRC-SCOPE", "runtime-boundary/codebase-analysis/20260520/REQ-M20-3-UNREADABLE/scope-map.json"),
            ("SRC-VALID", "runtime-boundary/codebase-analysis/20260520/REQ-M20-3-UNREADABLE/validation-plan.json"),
            ("SRC-RISK", "runtime-boundary/codebase-analysis/20260520/REQ-M20-3-UNREADABLE/risk-scan.json"),
        ],
    )

    result = _run_codebase_domain_result(request=request, instance_root=instance_root)

    assert result.quality_gate == "needs_more_evidence"
    assert result.requires_human_review is True
    assert result.external_call_made is False
    assert result.mutation_performed is False
    codebase_packages = [
        pkg
        for pkg in result.investigation_data.evidence_packages
        if pkg.evidence_type == "codebase_analysis_bundle"
    ]
    assert len(codebase_packages) == 1
    package = codebase_packages[0]
    assert any("unreadable" in lim for lim in package.limitations)


def _build_codebase_request_with_id(
    *, request_id: str, refs: list[tuple[str, str]]
) -> DomainInvestigationRequest:
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
        request_id=request_id,
        domain="codebase",
        objective="codebase: artifact-bridge-enrichment",
        sources=sources,
    )
