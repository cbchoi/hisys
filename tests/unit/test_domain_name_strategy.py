"""Domain naming strategy tests for structured example adapters.

Traceability: HISYS-DOM-005, HISYS-DOM-006, HISYS-DOM-012.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from hisys.schemas.domain_investigation import DomainInvestigationRequest


def test_codebase_is_canonical_development_domain() -> None:
    request = DomainInvestigationRequest(
        request_id="REQ-domain-name-codebase",
        producer_id="hermes",
        status="submitted",
        domain="codebase",
        objective="development/codebase evaluation",
        sources=[],
    )

    assert request.domain == "codebase"


def test_development_is_not_direct_domain_without_prevalidation_alias() -> None:
    with pytest.raises(ValidationError):
        DomainInvestigationRequest(
            request_id="REQ-domain-name-development",
            producer_id="hermes",
            status="submitted",
            domain="development",
            objective="development/codebase evaluation",
            sources=[],
        )


def test_requirements_analysis_uses_codebase_objective_for_first_loop() -> None:
    request = DomainInvestigationRequest(
        request_id="REQ-domain-name-requirements",
        producer_id="hermes",
        status="submitted",
        domain="codebase",
        objective="requirements-analysis: identify ambiguity conflict gap unverifiable statements",
        sources=[],
    )

    assert request.domain == "codebase"
    assert "requirements-analysis" in request.objective


def test_domain_strategy_is_documented() -> None:
    doc = Path("docs/use-cases/hermes-hisys-domain-tool.md").read_text(encoding="utf-8")

    assert "Domain Naming Strategy for Example Specs" in doc
    assert "canonical domain is `codebase`" in doc
    assert "`development` is not accepted as a direct `DomainName`" in doc
    assert "requirements-analysis uses `domain=\"codebase\"`" in doc
