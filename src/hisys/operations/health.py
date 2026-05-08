"""Operator-visible runtime health status checks.

Traceability: HISYS-FR-ADM-004, HISYS-T-006, HISYS-T-020, HISYS-T-023,
HISYS-FR-AGT-004, HISYS-DARS-CONTRACT-001.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

HealthState = Literal["ok", "degraded"]
ComponentState = Literal["ok", "missing", "disabled", "loopback_placeholder"]

REQUIRED_RUNTIME_DIRS = ("config", "data", "reports", "runtime-boundary")


class HealthComponent(BaseModel):
    """One operator-visible Hisys health component."""

    component_id: str
    status: ComponentState
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class HealthStatusReport(BaseModel):
    """Summary health report for local Hisys runtime readiness."""

    overall_status: HealthState
    required_operator_action: str
    components: list[HealthComponent]


def _runtime_dir_component(instance_root: Path, directory_name: str) -> HealthComponent:
    path = instance_root / directory_name
    exists = path.is_dir()
    return HealthComponent(
        component_id=f"runtime.{directory_name}",
        status="ok" if exists else "missing",
        message=(
            f"required runtime directory exists: {directory_name}"
            if exists
            else f"required runtime directory missing: {directory_name}"
        ),
        metadata={"path": str(path), "required": True},
    )


def _connector_components() -> list[HealthComponent]:
    return [
        HealthComponent(
            component_id="connectors.alert_delivery",
            status="disabled",
            message="live alert delivery connector is intentionally disabled until explicitly approved",
            metadata={
                "live_delivery_permitted": False,
                "external_action_permitted": False,
                "operator_action": "keep disabled unless a future controlled live-connector increment is approved",
            },
        ),
        HealthComponent(
            component_id="connectors.dars",
            status="loopback_placeholder",
            message="DARS integration is runtime-local loopback/advisory only",
            metadata={
                "external_call_made": False,
                "allowed_actions": "advisory_only",
                "operator_action": "replace only through a future controlled DARS adapter increment",
            },
        ),
    ]


def collect_health_status(instance_root: str | Path) -> HealthStatusReport:
    """Collect a local health report without live external probes or side effects."""

    root = Path(instance_root).resolve()
    runtime_components = [_runtime_dir_component(root, name) for name in REQUIRED_RUNTIME_DIRS]
    components = [*runtime_components, *_connector_components()]
    missing_components = [component for component in runtime_components if component.status == "missing"]
    if missing_components:
        action = "create missing runtime directories before production operation"
        overall: HealthState = "degraded"
    else:
        action = "none"
        overall = "ok"
    return HealthStatusReport(
        overall_status=overall,
        required_operator_action=action,
        components=components,
    )


__all__ = ["HealthComponent", "HealthStatusReport", "collect_health_status"]
