"""Generic structured domain adapter/spec seam.

Traceability: HISYS-DOM-001, HISYS-DOM-003, HISYS-DOM-010, HISYS-DOM-012.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from hisys.domain.adapters import DomainInvestigationContext
from hisys.domain.layers import DomainUseCase, DomainUseCaseContext
from hisys.domain.runtime import DomainRuntimeArtifactWriter
from hisys.domain.translation import DomainUseCaseArtifactTranslator, build_domain_investigation_result
from hisys.schemas.domain_investigation import DomainInvestigationRequest, DomainInvestigationResult


class DomainUseCaseFactory(Protocol):
    def __call__(self) -> DomainUseCase:
        ...


@dataclass(frozen=True)
class DomainAdapterSpec:
    """Configuration for one example domain over the shared structured adapter."""

    domain_id: str
    aliases: tuple[str, ...]
    use_case_factory: Callable[[], DomainUseCase]
    translator: DomainUseCaseArtifactTranslator
    artifact_writer: DomainRuntimeArtifactWriter
    traceability_ids: tuple[str, ...]
    safety_policy: str = "read_only_advisory"


def build_use_case_context(context: DomainInvestigationContext) -> DomainUseCaseContext:
    """Map adapter-facing context to layer-facing context without inventing paths."""

    return DomainUseCaseContext(
        instance_root=context.instance_root,
        boundary_dir=context.boundary_dir,
        yyyymmdd=context.yyyymmdd,
    )


class StructuredDomainAdapter:
    """Shared adapter implementation for example domain specs."""

    def __init__(self, spec: DomainAdapterSpec) -> None:
        self.spec = spec

    def supports(self, request: DomainInvestigationRequest) -> bool:
        return request.domain == self.spec.domain_id or request.domain in self.spec.aliases

    def investigate(
        self,
        request: DomainInvestigationRequest,
        context: DomainInvestigationContext,
    ) -> DomainInvestigationResult:
        use_case_context = build_use_case_context(context)
        use_case = self.spec.use_case_factory()
        use_case_result = use_case.run(request, use_case_context)
        packet = self.spec.translator.translate(
            use_case_result,
            request=request,
            traceability_ids=self.spec.traceability_ids,
        )
        refs = self.spec.artifact_writer.write(packet, use_case_context)
        return build_domain_investigation_result(
            packet,
            request,
            runtime_boundary_refs=[str(refs.json_ref), str(refs.markdown_ref)],
        )


__all__ = ["DomainAdapterSpec", "StructuredDomainAdapter", "build_use_case_context"]
