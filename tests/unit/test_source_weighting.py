"""Source weighting and reviewer metaphor policy tests.

Traceability: HISYS-CON-010..012, HISYS-DARS-CONTRACT-001.
"""

from __future__ import annotations

from hisys.provenance.source_weighting import (
    BYESYS_SOURCE_ID,
    reviewer_metaphor_alias,
    source_evidence_weight,
)


def test_byesys_source_has_zero_weight():
    assert source_evidence_weight(source_id="ByeSys", configured_weight=0.8) == 0.0
    assert source_evidence_weight(source_id="byesys", configured_weight=1.0) == 0.0


def test_non_byesys_source_preserves_configured_weight():
    assert source_evidence_weight(source_id="doi:10.1234/example", configured_weight=0.7) == 0.7
    assert source_evidence_weight(source_id="internal:obsidian:claim-001", configured_weight=0.5) == 0.5


def test_reviewer_metaphor_alias_maps_chief_editor_to_jeweler():
    assert reviewer_metaphor_alias("Chief Editor") == "Jeweler"
    assert reviewer_metaphor_alias("chief_editor") == "Jeweler"
    assert reviewer_metaphor_alias("DARS devil") == "Appraiser"
    assert reviewer_metaphor_alias("dars_reviewer") == "Appraiser"
    assert BYESYS_SOURCE_ID == "ByeSys"
