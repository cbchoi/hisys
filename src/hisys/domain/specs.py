"""Example structured-domain specs for the Hisys domain adapter registry.

Traceability: HISYS-FR-DOM-001, HISYS-FR-DOM-002, HISYS-FR-DOM-003,
HISYS-FR-DOM-004, HISYS-FR-DOM-005, HISYS-T-025, HISYS-T-026, HISYS-T-027.
"""

from __future__ import annotations

from hisys.domain.domain_adapters import DomainAdapterSpec
from hisys.domain.runtime import DomainRuntimeArtifactWriter
from hisys.domain.translation import DomainUseCaseArtifactTranslator
from hisys.domain.use_cases import CodeAnalysisUseCase, ResearchAnalysisUseCase

# Read-only default search ref. Concrete instances may override the requirements
# root through a future spec factory parameter; the value is recorded only as a
# governed evidence ref, never resolved as a live filesystem path.
DEFAULT_REQUIREMENTS_ROOT = "/home/cbchoi/me/requirements"

_RESEARCH_TRACEABILITY_IDS = (
    "HISYS-FR-DOM-001",
    "HISYS-FR-DOM-002",
    "HISYS-FR-DOM-003",
    "HISYS-FR-DOM-004",
    "HISYS-FR-DOM-005",
    "HISYS-T-025",
    "HISYS-T-026",
    "HISYS-T-027",
)

_CODEBASE_TRACEABILITY_IDS = _RESEARCH_TRACEABILITY_IDS


def research_spec() -> DomainAdapterSpec:
    """Example structured spec covering general research investigation."""

    return DomainAdapterSpec(
        domain_id="research",
        aliases=("research",),
        use_case_factory=ResearchAnalysisUseCase,
        translator=DomainUseCaseArtifactTranslator(),
        artifact_writer=DomainRuntimeArtifactWriter(),
        traceability_ids=_RESEARCH_TRACEABILITY_IDS,
        safety_policy="read_only_advisory",
    )


def _build_code_analysis_use_case() -> CodeAnalysisUseCase:
    return CodeAnalysisUseCase(requirements_root=DEFAULT_REQUIREMENTS_ROOT)


def codebase_spec() -> DomainAdapterSpec:
    """Example structured spec covering codebase evaluation use cases."""

    return DomainAdapterSpec(
        domain_id="codebase",
        aliases=("codebase",),
        use_case_factory=_build_code_analysis_use_case,
        translator=DomainUseCaseArtifactTranslator(),
        artifact_writer=DomainRuntimeArtifactWriter(),
        traceability_ids=_CODEBASE_TRACEABILITY_IDS,
        safety_policy="read_only_advisory",
    )


__all__ = ["DEFAULT_REQUIREMENTS_ROOT", "codebase_spec", "research_spec"]
