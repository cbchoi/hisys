"""Regression tests for post-M4 Ralph risk resolution.

Traceability: HISYS-FR-DOM-004, HISYS-FR-DOM-005, HISYS-FR-DOM-006,
HISYS-T-025, HISYS-T-027, HISYS-T-028.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from hisys.domain.adapters import DomainInvestigationContext
from hisys.domain.domain_adapters import StructuredDomainAdapter
from hisys.domain.layers import DomainUseCaseContext
from hisys.domain.runtime import DomainRuntimeArtifactWriter
from hisys.domain.specs import codebase_spec, investment_spec
from hisys.domain.translation import DomainUseCaseArtifactTranslator
from hisys.domain.use_cases import CodeAnalysisUseCase
from hisys.schemas.domain_investigation import DomainInvestigationRequest

TRACEABILITY_README = Path("docs/traceability/README.md")


def _investment_request() -> DomainInvestigationRequest:
    return DomainInvestigationRequest.model_validate(
        {
            "producer_id": "hermes",
            "status": "submitted",
            "request_id": "REQ-RISK-INV-001",
            "domain": "investment",
            "objective": "advisory investment review over existing packet artifacts",
            "sources": [
                {
                    "source_id": "IDP-RISK-001",
                    "source_type": "current_artifact",
                    "ref": "runtime-boundary/investment-decisions/IDP-RISK-001.json",
                    "access_mode": "read_only",
                }
            ],
        }
    )


def _codebase_request(objective: str) -> DomainInvestigationRequest:
    return DomainInvestigationRequest.model_validate(
        {
            "producer_id": "hermes",
            "status": "submitted",
            "request_id": "REQ-RISK-CODE-001",
            "domain": "codebase",
            "objective": objective,
            "sources": [],
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


def test_traceability_summary_uses_unique_hisys_t_028_owner() -> None:
    text = TRACEABILITY_README.read_text(encoding="utf-8")

    t028_increment_owner_rows = [
        line
        for line in text.splitlines()
        if line.startswith("| Investment structured-domain adapter migration |")
        and re.search(r"\bHISYS-T-028\b(?!-)", line)
    ]

    assert len(t028_increment_owner_rows) == 1
    assert "| HISYS-T-028 Selenium read-only research harness |" not in text
    assert "HISYS-T-028-SEL Selenium read-only research harness" in text


def test_investment_runtime_artifact_has_typed_governance_flags(tmp_path: Path) -> None:
    adapter = StructuredDomainAdapter(investment_spec())

    result = adapter.investigate(_investment_request(), _context(tmp_path))

    json_refs = [ref for ref in result.runtime_boundary_refs if ref.endswith(".json")]
    record = json.loads((tmp_path / json_refs[0]).read_text(encoding="utf-8"))
    assert record["governance_flags"] == {
        "execution_authorized": False,
        "publication_or_live_action_approved": False,
        "autonomous_execution_allowed": False,
        "credential_use_allowed": False,
        "live_external_action_allowed": False,
    }


def test_requirements_analysis_runtime_artifact_has_typed_domain_subtype(tmp_path: Path) -> None:
    request = _codebase_request("requirements-analysis: check SRS and SDD coverage")
    context = DomainUseCaseContext(
        instance_root=tmp_path,
        boundary_dir=tmp_path / "runtime-boundary" / "domain-investigation",
        yyyymmdd="20260514",
    )
    result = CodeAnalysisUseCase(requirements_root="/controlled/requirements").run(request, context)
    packet = DomainUseCaseArtifactTranslator().translate(
        result,
        request=request,
        traceability_ids=("HISYS-FR-DOM-005", "HISYS-T-025"),
    )

    refs = DomainRuntimeArtifactWriter().write(packet, context)

    record = json.loads((tmp_path / refs.json_ref).read_text(encoding="utf-8"))
    assert record["domain_subtype"] == "requirements-analysis"
    assert record["artifact_refs"]["investigation_ref"].endswith("REQUIREMENTS-ANALYSIS")


def test_requirements_analysis_classifier_accepts_explicit_objective_marker(tmp_path: Path) -> None:
    adapter = StructuredDomainAdapter(codebase_spec())
    request = _codebase_request("[requirements-analysis] check verifiability of SRS clauses")

    result = adapter.investigate(request, _context(tmp_path))

    json_refs = [ref for ref in result.runtime_boundary_refs if ref.endswith(".json")]
    record = json.loads((tmp_path / json_refs[0]).read_text(encoding="utf-8"))
    assert record["domain_subtype"] == "requirements-analysis"
