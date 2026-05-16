"""Source provenance weighting policy.

Traceability: HISYS-CON-010..012, HISYS-DARS-CONTRACT-001.

The evidence-sufficiency gate implements the Local DARS / ByeSys Provenance
plan Milestone 5: a claim must be supported by non-ByeSys evidence whose
combined weight meets a minimum threshold before Jeweler review accepts it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

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


def is_byesys_source(source_id: str) -> bool:
    """Return True when the source identifier is the ByeSys provenance label."""

    return source_id.strip().casefold() == _BYESYS_NORMALIZED


def source_evidence_weight(*, source_id: str, configured_weight: float | int | None = 1.0) -> float:
    """Return the effective evidential weight for a source.

    `ByeSys` denotes generated, inferred, or unsupported evidence-like content.
    It is never counted as factual corroboration and therefore always has weight
    zero, even if a higher configured weight is supplied.
    """

    if is_byesys_source(source_id):
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


@dataclass(frozen=True)
class EvidenceSufficiencyVerdict:
    """Result of an evidence sufficiency check against the ByeSys-zero policy."""

    sufficient: bool
    contributing_weight: float
    minimum_weight: float
    byesys_present: bool
    reason: str


def claim_has_sufficient_non_byesys_evidence(
    *,
    source_weights: Iterable[Mapping[str, object]],
    minimum_weight: float,
) -> EvidenceSufficiencyVerdict:
    """Evaluate evidence sufficiency while ignoring any ByeSys contribution.

    `source_weights` accepts an iterable of mappings, each carrying at least
    `source_id` and an optional `evidential_weight`. ByeSys contributions are
    normalized to zero before the threshold check so generated/unsupported
    synthesis can never satisfy the gate on its own.
    """

    contributing = 0.0
    byesys_present = False
    has_any = False
    for entry in source_weights:
        has_any = True
        raw_source_id = entry.get("source_id", "")
        source_id = str(raw_source_id) if raw_source_id is not None else ""
        configured = entry.get("evidential_weight", 1.0)
        weight = source_evidence_weight(source_id=source_id, configured_weight=configured)
        if is_byesys_source(source_id):
            byesys_present = True
            continue
        contributing += weight

    if not has_any:
        reason = "no evidence records were provided"
    elif contributing >= minimum_weight:
        reason = "non-ByeSys contributions meet the minimum weight"
    elif byesys_present and contributing == 0.0:
        reason = "ByeSys-only evidence cannot satisfy the sufficiency gate"
    else:
        reason = "non-ByeSys contributing weight is below the minimum"

    return EvidenceSufficiencyVerdict(
        sufficient=contributing >= minimum_weight and has_any,
        contributing_weight=contributing,
        minimum_weight=minimum_weight,
        byesys_present=byesys_present,
        reason=reason,
    )
