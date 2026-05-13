"""Domain investigation adapter dispatch primitives.

Traceability: HISYS-FR-INV-001..006, HISYS-CON-010..012.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, TypeVar

from hisys.schemas.domain_investigation import DomainInvestigationRequest


DomainResultT = TypeVar("DomainResultT")


@dataclass(frozen=True)
class DomainInvestigationContext:
    """Read-only execution context shared by domain-specific adapters.

    The context carries runtime refs and optional evidence refs without making the
    adapter responsible for CLI parsing. Adapters must preserve the caller's
    no-mutation/no-publication boundary and write only governed runtime artifacts
    through the command workflow.
    """

    instance_root: Path
    boundary_dir: Path
    yyyymmdd: str
    promoted_pdf_evidence: object | None = None
    source_quote_refs: list[str] = field(default_factory=list)
    claim_evidence_ledger_refs: list[str] = field(default_factory=list)
    claim_evidence_summary_refs: list[str] = field(default_factory=list)
    claim_coverage_gate_refs: list[str] = field(default_factory=list)
    recommendation_claim_registry_refs: list[str] = field(default_factory=list)
    live_source_access_refs: list[str] = field(default_factory=list)
    live_source_evidence_refs: list[str] = field(default_factory=list)


class DomainInvestigationAdapter(Protocol[DomainResultT]):
    """Protocol for one domain-specific investigation implementation."""

    def supports(self, request: DomainInvestigationRequest) -> bool:
        """Return true when this adapter owns the request."""

    def investigate(
        self,
        request: DomainInvestigationRequest,
        context: DomainInvestigationContext,
    ) -> DomainResultT:
        """Build the domain investigation result for a supported request."""


class DomainAdapterRegistry:
    """Ordered registry for domain-specific investigation adapters."""

    def __init__(self, adapters: list[DomainInvestigationAdapter[DomainResultT]] | None = None) -> None:
        self._adapters: list[DomainInvestigationAdapter[DomainResultT]] = list(adapters or [])

    def register(self, adapter: DomainInvestigationAdapter[DomainResultT]) -> None:
        self._adapters.append(adapter)

    def resolve(self, request: DomainInvestigationRequest) -> DomainInvestigationAdapter[DomainResultT] | None:
        for adapter in self._adapters:
            if adapter.supports(request):
                return adapter
        return None

    def investigate(
        self,
        request: DomainInvestigationRequest,
        context: DomainInvestigationContext,
    ) -> DomainResultT | None:
        adapter = self.resolve(request)
        if adapter is None:
            return None
        return adapter.investigate(request, context)


__all__ = [
    "DomainAdapterRegistry",
    "DomainInvestigationAdapter",
    "DomainInvestigationContext",
]
