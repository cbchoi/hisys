"""Source provenance weighting policy.

Traceability: HISYS-CON-010..012, HISYS-DARS-CONTRACT-001.
"""

from __future__ import annotations

BYESYS_SOURCE_ID = "ByeSys"

_BYESYS_NORMALIZED = BYESYS_SOURCE_ID.casefold()

_REVIEWER_ALIASES = {
    "chief editor": "Jeweler",
    "chief_editor": "Jeweler",
    "chief-editor": "Jeweler",
    "chiefeditor": "Jeweler",
    "jeweler": "Jeweler",
    "dars devil": "Appraiser",
    "dars_devil": "Appraiser",
    "dars-devil": "Appraiser",
    "dars reviewer": "Appraiser",
    "dars_reviewer": "Appraiser",
    "dars-reviewer": "Appraiser",
    "appraiser": "Appraiser",
}


def source_evidence_weight(*, source_id: str, configured_weight: float | int | None = 1.0) -> float:
    """Return the effective evidential weight for a source.

    `ByeSys` denotes generated, inferred, or unsupported evidence-like content.
    It is never counted as factual corroboration and therefore always has weight
    zero, even if a higher configured weight is supplied.
    """

    if source_id.strip().casefold() == _BYESYS_NORMALIZED:
        return 0.0
    if configured_weight is None:
        return 1.0
    weight = float(configured_weight)
    if weight < 0:
        return 0.0
    if weight > 1:
        return 1.0
    return weight


def reviewer_metaphor_alias(name: str) -> str:
    """Return the canonical user-facing review metaphor for a legacy role name."""

    normalized = name.strip().casefold().replace("-", "_")
    return _REVIEWER_ALIASES.get(normalized, _REVIEWER_ALIASES.get(normalized.replace("_", " "), name))
