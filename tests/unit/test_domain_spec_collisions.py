"""Tests for structured-domain spec collision validation.

Traceability: HISYS-FR-DOM-001, HISYS-FR-DOM-002, HISYS-NFR-MNT-001,
HISYS-T-025.
"""

from __future__ import annotations

import pytest

from hisys.domain.domain_adapters import DomainAdapterSpec
from hisys.domain.runtime import DomainRuntimeArtifactWriter
from hisys.domain.specs import (
    DuplicateDomainSpecError,
    codebase_spec,
    research_spec,
    validate_spec_collisions,
)
from hisys.domain.translation import DomainUseCaseArtifactTranslator
from hisys.domain.use_cases import ResearchAnalysisUseCase


def _fake_spec(domain_id: str, aliases: tuple[str, ...] = ()) -> DomainAdapterSpec:
    return DomainAdapterSpec(
        domain_id=domain_id,
        aliases=aliases,
        use_case_factory=ResearchAnalysisUseCase,
        translator=DomainUseCaseArtifactTranslator(),
        artifact_writer=DomainRuntimeArtifactWriter(),
        traceability_ids=("HISYS-FR-DOM-001",),
    )


def test_validate_spec_collisions_accepts_disjoint_specs() -> None:
    validate_spec_collisions([research_spec(), codebase_spec()])


def test_validate_spec_collisions_rejects_duplicate_canonical_domain() -> None:
    duplicate = _fake_spec("research", aliases=())

    with pytest.raises(DuplicateDomainSpecError) as exc:
        validate_spec_collisions([research_spec(), duplicate])

    assert "research" in str(exc.value)


def test_validate_spec_collisions_rejects_alias_colliding_with_other_canonical_domain() -> None:
    other = _fake_spec("custom", aliases=("research",))

    with pytest.raises(DuplicateDomainSpecError) as exc:
        validate_spec_collisions([research_spec(), other])

    assert "research" in str(exc.value)


def test_validate_spec_collisions_rejects_alias_duplicated_across_specs() -> None:
    first = _fake_spec("alpha", aliases=("shared",))
    second = _fake_spec("beta", aliases=("shared",))

    with pytest.raises(DuplicateDomainSpecError) as exc:
        validate_spec_collisions([first, second])

    assert "shared" in str(exc.value)
