"""Tests for guarding research-specific domain postprocessing.

Traceability: HISYS-DOM-003, HISYS-DOM-010, HISYS-DOM-012.
"""

from __future__ import annotations

from hisys.cli.main import _ResearchGapDomainAdapter, _should_apply_research_gap_postprocessors


class _StructuredLikeAdapter:
    pass


def test_research_gap_adapter_keeps_research_specific_postprocessors(tmp_path) -> None:
    adapter = _ResearchGapDomainAdapter(instance=object())  # type: ignore[arg-type]

    assert _should_apply_research_gap_postprocessors(adapter) is True


def test_structured_domain_adapter_skips_research_specific_postprocessors() -> None:
    assert _should_apply_research_gap_postprocessors(_StructuredLikeAdapter()) is False
