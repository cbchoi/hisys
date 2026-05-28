"""DARS subsystem public seam.

This package is a minimal subsystem-level entry point for the Hisys
``Altas + DARS + Judge`` role split. It re-exports the existing bounded DARS
advisory seams without moving implementation or changing legacy import paths
under :mod:`hisys.agents.*`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from hisys.agents.dars import DarsCritiqueRecord, DarsCritiqueReport, DarsRuntime
from hisys.agents.dars_protocol import DarsRequestEnvelope, DarsResponseEnvelope


@dataclass(frozen=True)
class DarsSubsystemManifest:
    """Machine-readable DARS subsystem role and authority boundary."""

    role: Literal["dars"] = "dars"
    responsibility: Literal["developmental opposition/advisory critique"] = (
        "developmental opposition/advisory critique"
    )
    advisory_only: Literal[True] = True
    requires_human_review: Literal[True] = True
    live_external_action_authorized: Literal[False] = False
    completion_upgrade_claimed: Literal[False] = False
    raw_provider_api_readiness: Literal[False] = False
    adapter_native_readiness: Literal[False] = False
    bounded_unattended_advisory_operation_ready: Literal[False] = False


def get_dars_subsystem_manifest() -> DarsSubsystemManifest:
    """Return the current DARS subsystem manifest without side effects."""

    return DarsSubsystemManifest()


@dataclass(frozen=True)
class DarsSubsystemInvocationMode:
    """A documented Hisys invocation mode that DARS participates in.

    Mirrors the invocation-mode record in
    ``docs/design/hisys-subsystem-architecture.md`` for the modes that involve
    DARS. The other documented modes (``altas-only`` and ``judge-only``) do
    not run DARS and are intentionally not represented here.
    """

    mode_id: Literal["dars-only", "full-loop"]
    description: str
    dars_role: Literal["sole_subsystem", "developmental_opposition_stage"]
    advisory_only: Literal[True] = True
    requires_human_review: Literal[True] = True


def get_dars_subsystem_invocation_modes() -> tuple[
    DarsSubsystemInvocationMode, ...
]:
    """Return the documented invocation modes that DARS participates in.

    Returns the ``dars-only`` standalone advisory mode and the ``full-loop``
    composition stage. The returned tuple is ordered and stable so callers can
    rely on positional access for the standalone mode and the composed stage.
    """

    return (
        DarsSubsystemInvocationMode(
            mode_id="dars-only",
            description="developmental opposition and advisory critique",
            dars_role="sole_subsystem",
        ),
        DarsSubsystemInvocationMode(
            mode_id="full-loop",
            description="Altas -> DARS -> Judge",
            dars_role="developmental_opposition_stage",
        ),
    )


__all__ = [
    "DarsCritiqueRecord",
    "DarsCritiqueReport",
    "DarsRequestEnvelope",
    "DarsResponseEnvelope",
    "DarsRuntime",
    "DarsSubsystemInvocationMode",
    "DarsSubsystemManifest",
    "get_dars_subsystem_invocation_modes",
    "get_dars_subsystem_manifest",
]
