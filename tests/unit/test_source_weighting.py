"""Source weighting and reviewer metaphor policy tests.

Traceability: HISYS-CON-010..012, HISYS-DARS-CONTRACT-001.

Evidence-sufficiency tests trace to the Local DARS / ByeSys Provenance
plan Milestones 4 and 5 (`docs/plans/2026-05-16-local-dars-byesys-provenance.md`).
"""

from __future__ import annotations

import pytest

from hisys.provenance.source_weighting import (
    BYESYS_SOURCE_ID,
    EvidenceSufficiencyVerdict,
    claim_has_sufficient_non_byesys_evidence,
    reviewer_metaphor_alias,
    source_evidence_weight,
)


def test_byesys_source_has_zero_weight():
    assert source_evidence_weight(source_id="ByeSys", configured_weight=0.8) == 0.0
    assert source_evidence_weight(source_id="byesys", configured_weight=1.0) == 0.0


def test_non_byesys_source_preserves_configured_weight():
    assert source_evidence_weight(source_id="doi:10.1234/example", configured_weight=0.7) == 0.7
    assert source_evidence_weight(source_id="internal:obsidian:claim-001", configured_weight=0.5) == 0.5


def test_reviewer_metaphor_alias_maps_chief_editor_to_jeweler_and_dars_terms_to_devil():
    assert reviewer_metaphor_alias("Chief Editor") == "Jeweler"
    assert reviewer_metaphor_alias("chief_editor") == "Jeweler"
    assert reviewer_metaphor_alias("Devil") == "Devil"
    assert reviewer_metaphor_alias("DARS devil") == "Devil"
    assert reviewer_metaphor_alias("dars_devil") == "Devil"
    assert reviewer_metaphor_alias("dars_reviewer") == "Devil"
    assert reviewer_metaphor_alias("Appraiser") == "Devil"
    assert BYESYS_SOURCE_ID == "ByeSys"


# ---------------------------------------------------------------------------
# Local DARS / ByeSys provenance plan — Milestones 4..5 (Ralph M11.1, M11.2)
# Evidence sufficiency must ignore ByeSys contributions so a claim supported
# only by generated/unsupported synthesis cannot pass the Jeweler review gate.
# ---------------------------------------------------------------------------


def test_claim_with_only_byesys_evidence_fails_sufficiency_gate():
    verdict = claim_has_sufficient_non_byesys_evidence(
        source_weights=[
            {"source_id": "ByeSys", "evidential_weight": 0.9},
            {"source_id": "byesys", "evidential_weight": 1.0},
        ],
        minimum_weight=0.5,
    )
    assert isinstance(verdict, EvidenceSufficiencyVerdict)
    assert verdict.sufficient is False
    assert verdict.contributing_weight == 0.0
    assert "ByeSys" in verdict.reason or "byesys" in verdict.reason.lower()


def test_claim_with_mixed_evidence_keeps_non_byesys_contributions():
    verdict = claim_has_sufficient_non_byesys_evidence(
        source_weights=[
            {"source_id": "doi:10.1234/example", "evidential_weight": 0.7},
            {"source_id": "ByeSys", "evidential_weight": 1.0},
        ],
        minimum_weight=0.5,
    )
    assert verdict.sufficient is True
    assert verdict.contributing_weight == pytest.approx(0.7)


def test_claim_with_low_non_byesys_weight_fails_sufficiency_gate():
    verdict = claim_has_sufficient_non_byesys_evidence(
        source_weights=[
            {"source_id": "internal:obsidian:claim-002", "evidential_weight": 0.2},
        ],
        minimum_weight=0.5,
    )
    assert verdict.sufficient is False
    assert verdict.contributing_weight == pytest.approx(0.2)


def test_sufficiency_gate_normalizes_byesys_weight_even_when_configured_high():
    # A misconfigured weight on a ByeSys source must not slip through; the
    # gate enforces the ByeSys-zero invariant via source_evidence_weight.
    verdict = claim_has_sufficient_non_byesys_evidence(
        source_weights=[
            {"source_id": "ByeSys", "evidential_weight": 0.95},
            {"source_id": "doi:10.1234/example", "evidential_weight": 0.4},
        ],
        minimum_weight=0.5,
    )
    assert verdict.sufficient is False
    # The byesys contribution must be reported as 0.0 not 0.95.
    assert verdict.contributing_weight == pytest.approx(0.4)


def test_sufficiency_gate_accepts_no_minimum_weight():
    verdict = claim_has_sufficient_non_byesys_evidence(
        source_weights=[
            {"source_id": "internal:obsidian:claim-003", "evidential_weight": 0.1},
        ],
        minimum_weight=0.0,
    )
    assert verdict.sufficient is True


def test_sufficiency_gate_rejects_empty_evidence():
    verdict = claim_has_sufficient_non_byesys_evidence(source_weights=[], minimum_weight=0.5)
    assert verdict.sufficient is False
    assert verdict.contributing_weight == 0.0
