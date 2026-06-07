"""Judge subsystem service contracts.

Judge is responsible for rubric scoring and bounded decision packets behind a
human-review gate. These contracts are pure frozen dataclasses and do not start
subprocesses, mutate state, publish, push remotely, or remove human review.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from . import ServiceInvocationEnvelope

JudgeBoundedDecision = Literal[
    "human_review_required",
    "needs_more_evidence",
    "reject",
    "advisory_pass",
]


@dataclass(frozen=True)
class JudgeRubricScore:
    """Single rubric score with bounded rationale."""

    rubric_id: str
    score: float
    rationale: str
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class JudgeBoundedDecisionPacket:
    """Human-review-gated Judge decision packet."""

    envelope: ServiceInvocationEnvelope
    rubric_scores: tuple[JudgeRubricScore, ...]
    decision: JudgeBoundedDecision
    rationale: str = ""
    human_review_required: bool = True
    mutation_authorized: bool = False
    publication_authorized: bool = False
    remote_push_authorized: bool = False
    live_action_authorized: bool = False


__all__ = [
    "JudgeBoundedDecision",
    "JudgeBoundedDecisionPacket",
    "JudgeRubricScore",
]
