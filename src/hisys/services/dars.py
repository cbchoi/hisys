"""DARS subsystem service contracts.

DARS is responsible for adversarial critique and residual-risk surfacing. These
contracts are advisory-only pure data and do not authorize decisions,
subprocesses, mutation, live calls, or publication.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import ServiceInvocationEnvelope


@dataclass(frozen=True)
class DarsAdversarialCritique:
    """Advisory critique packet for residual-risk surfacing."""

    envelope: ServiceInvocationEnvelope
    critique_points: tuple[str, ...]
    residual_risks: tuple[str, ...]
    advisory_only: bool = True
    decision_authorized: bool = False
    mutation_authorized: bool = False
    publication_authorized: bool = False
    requires_human_review: bool = True


@dataclass(frozen=True)
class DarsResidualRisk:
    """Single residual-risk observation surfaced by DARS."""

    risk_id: str
    description: str
    evidence_refs: tuple[str, ...] = ()
    mitigation_notes: tuple[str, ...] = ()
    advisory_only: bool = True


__all__ = ["DarsAdversarialCritique", "DarsResidualRisk"]
