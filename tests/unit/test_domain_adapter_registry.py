"""Tests for domain-adaptive investigation adapter dispatch.

Traceability: HISYS-FR-INV-001..006, HISYS-CON-010..012.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hisys.domain.adapters import DomainAdapterRegistry, DomainInvestigationContext
from hisys.schemas.domain_investigation import DomainInvestigationRequest


@dataclass
class _FakeResult:
    result_id: str


class _FakeAdapter:
    def __init__(self, domain: str, result_id: str) -> None:
        self.domain = domain
        self.result_id = result_id
        self.seen_context: DomainInvestigationContext | None = None

    def supports(self, request: DomainInvestigationRequest) -> bool:
        return request.domain == self.domain

    def investigate(self, request: DomainInvestigationRequest, context: DomainInvestigationContext) -> _FakeResult:
        self.seen_context = context
        return _FakeResult(result_id=self.result_id)


def _request(domain: str = "codebase") -> DomainInvestigationRequest:
    return DomainInvestigationRequest.model_validate(
        {
            "producer_id": "hermes",
            "status": "submitted",
            "request_id": "REQ-DOMAIN-ADAPTER-001",
            "domain": domain,
            "objective": "Evaluate domain-specific Hisys use case.",
            "sources": [
                {
                    "source_id": "SRC-001",
                    "source_type": "current_artifact",
                    "ref": "artifact://local",
                    "access_mode": "read_only",
                }
            ],
        }
    )


def _context(tmp_path: Path) -> DomainInvestigationContext:
    return DomainInvestigationContext(
        instance_root=tmp_path,
        boundary_dir=tmp_path / "runtime-boundary" / "domain-investigation" / "codebase" / "20260514",
        yyyymmdd="20260514",
        promoted_pdf_evidence=None,
        source_quote_refs=[],
        claim_evidence_ledger_refs=[],
        claim_evidence_summary_refs=[],
        claim_coverage_gate_refs=[],
        recommendation_claim_registry_refs=[],
        live_source_access_refs=[],
        live_source_evidence_refs=[],
    )


def test_registry_dispatches_to_first_adapter_that_supports_request(tmp_path: Path) -> None:
    ignored = _FakeAdapter("research", "ignored")
    selected = _FakeAdapter("codebase", "selected")
    registry = DomainAdapterRegistry([ignored, selected])

    result = registry.investigate(_request("codebase"), _context(tmp_path))

    assert result == _FakeResult(result_id="selected")
    assert ignored.seen_context is None
    assert selected.seen_context is not None
    assert selected.seen_context.yyyymmdd == "20260514"


def test_registry_returns_none_when_no_domain_adapter_supports_request(tmp_path: Path) -> None:
    registry = DomainAdapterRegistry([_FakeAdapter("research", "ignored")])

    result = registry.investigate(_request("codebase"), _context(tmp_path))

    assert result is None
