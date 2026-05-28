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


__all__ = [
    "DarsCritiqueRecord",
    "DarsCritiqueReport",
    "DarsRequestEnvelope",
    "DarsResponseEnvelope",
    "DarsRuntime",
    "DarsSubsystemManifest",
    "get_dars_subsystem_manifest",
]
