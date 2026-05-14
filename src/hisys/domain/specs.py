"""Example structured-domain specs for the Hisys domain adapter registry.

Traceability: HISYS-FR-DOM-001, HISYS-FR-DOM-002, HISYS-FR-DOM-003,
HISYS-FR-DOM-004, HISYS-FR-DOM-005, HISYS-T-025, HISYS-T-026, HISYS-T-027.
"""

from __future__ import annotations

from typing import Iterable

from hisys.domain.domain_adapters import DomainAdapterSpec
from hisys.domain.runtime import DomainRuntimeArtifactWriter
from hisys.domain.translation import DomainUseCaseArtifactTranslator
from hisys.domain.use_cases import (
    CodeAnalysisUseCase,
    InvestmentAnalysisUseCase,
    ResearchAnalysisUseCase,
)


class DuplicateDomainSpecError(ValueError):
    """Raised when registered specs collide on canonical domain or alias."""

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

_INVESTMENT_TRACEABILITY_IDS = (
    "HISYS-FR-DOM-003",
    "HISYS-FR-DOM-004",
    "HISYS-FR-DOM-006",
    "HISYS-T-026",
    "HISYS-T-027",
    "HISYS-T-028",
)


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


def investment_spec() -> DomainAdapterSpec:
    """Advisory-only structured spec for the investment domain migration.

    The spec reuses the existing investment packet/dry-run/operator-review CLI
    as the system of record and never authorizes live execution, publication,
    credential use, or external mutation. The recommendation surfaced by this
    spec is advisory, requires human review, and explicitly carries the
    `execution_authorized=false` and `publication_or_live_action_approved=false`
    governance flags so audit reviewers can confirm the boundary without
    re-resolving the underlying investment packet.
    """

    return DomainAdapterSpec(
        domain_id="investment",
        aliases=("investment",),
        use_case_factory=InvestmentAnalysisUseCase,
        translator=DomainUseCaseArtifactTranslator(),
        artifact_writer=DomainRuntimeArtifactWriter(),
        traceability_ids=_INVESTMENT_TRACEABILITY_IDS,
        safety_policy="advisory_only_no_live_action",
    )


def validate_spec_collisions(specs: Iterable[DomainAdapterSpec]) -> None:
    """Reject duplicate canonical domains or aliases across registered specs.

    Validation is deterministic and local: it never touches the filesystem or
    network. The first collision is reported with the offending name so domain
    developers can fix the spec definition before registry construction.
    """

    claimed_names: dict[str, str] = {}

    for spec in specs:
        candidates: list[tuple[str, str]] = [("domain_id", spec.domain_id)]
        # An alias that equals the spec's own canonical domain is harmless
        # redundancy; only cross-spec collisions are rejected.
        candidates.extend(
            ("alias", alias) for alias in spec.aliases if alias != spec.domain_id
        )
        for kind, name in candidates:
            if name in claimed_names:
                raise DuplicateDomainSpecError(
                    f"Domain spec collision on {kind} {name!r}: "
                    f"already registered by {claimed_names[name]!r}; rename or remove the alias."
                )
            claimed_names[name] = spec.domain_id


__all__ = [
    "DEFAULT_REQUIREMENTS_ROOT",
    "DuplicateDomainSpecError",
    "codebase_spec",
    "investment_spec",
    "research_spec",
    "validate_spec_collisions",
]
