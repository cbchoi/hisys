"""Altas subsystem service contracts.

Altas is responsible for evidence/source handle resolution and construction of
sensor-first evidence packages. This module contains pure frozen dataclasses
only; it does not perform resolution, contact providers, mutate state, publish,
or start subprocesses.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import ServiceInvocationEnvelope


@dataclass(frozen=True)
class AltasEvidenceResolutionRequest:
    """Request for future Altas evidence/source handle resolution."""

    envelope: ServiceInvocationEnvelope
    source_handles: tuple[str, ...]
    sensor_first: bool = True
    external_call_authorized: bool = False
    mutation_authorized: bool = False
    publication_authorized: bool = False


@dataclass(frozen=True)
class AltasResolvedSourceHandle:
    """Resolved source handle bound to an evidence reference."""

    handle: str
    evidence_ref: str
    sensor_first: bool = True
    resolution_notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class AltasEvidencePackage:
    """Bounded Altas evidence package contract."""

    package_id: str
    resolved_handles: tuple[AltasResolvedSourceHandle, ...]
    sensor_first: bool = True
    external_call_made: bool = False
    mutation_performed: bool = False
    publication_performed: bool = False
    requires_human_review: bool = True


__all__ = [
    "AltasEvidencePackage",
    "AltasEvidenceResolutionRequest",
    "AltasResolvedSourceHandle",
]
