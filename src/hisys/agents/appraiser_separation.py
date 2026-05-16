"""Shared DARS Devil-separation guard.

Hisys preserves DARS/Devil as advisory-only and separate from Chief
Editor / Jeweler decision authority (HISYS-DARS-CONTRACT-001). This module
centralises the policy: which intents are advisory, which are authority, and
how non-dispatch DARS paths (backends, adapters, protocol consumers) must
fail-closed when a request, response, or dispatch decision represents a
forbidden authority intent.

The dispatch gate, fixture backend, and mock endpoint adapter all consult
this module so the policy cannot be bypassed by alternate code paths.

Traceability: HISYS-DARS-CONTRACT-001, HISYS-FR-AGT-001..005,
HISYS-SCHEMA-001, HISYS-CON-010, HISYS-CON-011, HISYS-CON-012.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..schemas.lapidary_governance import AppraiserSeparationPolicy

ADVISORY_INTENTS: frozenset[str] = frozenset(
    {"advisory_critique", "return_findings", "return_recommendations"}
)
AUTHORITY_INTENTS: frozenset[str] = frozenset(
    {"approve_decision", "execute_action", "publish_output"}
)
DEFAULT_APPRAISER_POLICY_REF = "APPRAISER-POLICY-DEFAULT"

POLICY_VIOLATION_REASON_CODE = "appraiser_separation_policy_violation"


@dataclass(frozen=True)
class AppraiserSeparationVerdict:
    """Result of evaluating an intent against the Devil-separation policy."""

    decision: Literal["allowed", "blocked"]
    reason_code: str
    reason: str
    intent: str
    policy_ref: str


class AppraiserSeparationViolation(ValueError):
    """Raised when a DARS path attempts a non-advisory authority intent.

    Carries the verdict so callers can persist policy-violation evidence
    (e.g. runtime-boundary validation reports) before propagating the error.
    """

    def __init__(self, verdict: AppraiserSeparationVerdict) -> None:
        super().__init__(verdict.reason)
        self.verdict = verdict

    @property
    def decision(self) -> Literal["allowed", "blocked"]:
        return self.verdict.decision

    @property
    def reason_code(self) -> str:
        return self.verdict.reason_code

    @property
    def intent(self) -> str:
        return self.verdict.intent

    @property
    def policy_ref(self) -> str:
        return self.verdict.policy_ref


def resolve_policy_ref(policy: AppraiserSeparationPolicy | None) -> str:
    """Return the policy id to record on a verdict, defaulting when omitted."""

    return policy.policy_id if policy is not None else DEFAULT_APPRAISER_POLICY_REF


def classify_intent(
    intent: str,
    *,
    appraiser_policy: AppraiserSeparationPolicy | None = None,
) -> AppraiserSeparationVerdict:
    """Classify an intent against the advisory-only Devil policy.

    Any intent not present in :data:`ADVISORY_INTENTS` is fail-closed and
    rejected as an Devil-separation policy violation. Unknown intents
    (typos, new authority intents added by callers without policy review) are
    treated as authority intents to preserve the fail-closed boundary.
    """

    policy_ref = resolve_policy_ref(appraiser_policy)
    if intent in ADVISORY_INTENTS:
        return AppraiserSeparationVerdict(
            decision="allowed",
            reason_code="advisory_intent",
            reason="Intent is within the DARS advisory-only scope.",
            intent=intent,
            policy_ref=policy_ref,
        )
    reason = (
        "DARS/Devil is advisory-only and may not be dispatched for "
        f"authority intent {intent!r}; refer to {policy_ref}."
    )
    return AppraiserSeparationVerdict(
        decision="blocked",
        reason_code=POLICY_VIOLATION_REASON_CODE,
        reason=reason,
        intent=intent,
        policy_ref=policy_ref,
    )


def enforce_advisory_intent(
    intent: str,
    *,
    appraiser_policy: AppraiserSeparationPolicy | None = None,
) -> AppraiserSeparationVerdict:
    """Raise :class:`AppraiserSeparationViolation` when ``intent`` is non-advisory.

    Use this at non-dispatch DARS boundaries (backends, adapters, future
    runtime hooks) so a forged dispatch decision or an alternate code path
    cannot route an authority intent past the Devil-separation policy.
    """

    verdict = classify_intent(intent, appraiser_policy=appraiser_policy)
    if verdict.decision == "blocked":
        raise AppraiserSeparationViolation(verdict)
    return verdict


__all__ = [
    "ADVISORY_INTENTS",
    "AUTHORITY_INTENTS",
    "DEFAULT_APPRAISER_POLICY_REF",
    "POLICY_VIOLATION_REASON_CODE",
    "AppraiserSeparationVerdict",
    "AppraiserSeparationViolation",
    "classify_intent",
    "enforce_advisory_intent",
    "resolve_policy_ref",
]
