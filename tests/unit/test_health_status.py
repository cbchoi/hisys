"""Operator health status hardening tests.

Traceability: HISYS-FR-ADM-004, HISYS-T-006, HISYS-T-020, HISYS-T-023.
"""

from __future__ import annotations

from pathlib import Path

from hisys.operations.health import collect_health_status


def test_collect_health_status_reports_runtime_dirs_and_disabled_connectors(tmp_path: Path) -> None:
    instance = tmp_path / "instance"
    (instance / "config").mkdir(parents=True)
    (instance / "config" / "source-registry.yaml").write_text("sources: []\n", encoding="utf-8")
    (instance / "data").mkdir()
    (instance / "reports").mkdir()

    report = collect_health_status(instance)

    assert report.overall_status == "degraded"
    by_id = {component.component_id: component for component in report.components}
    assert by_id["runtime.config"].status == "ok"
    assert by_id["runtime.data"].status == "ok"
    assert by_id["runtime.runtime-boundary"].status == "missing"
    assert by_id["connectors.alert_delivery"].status == "disabled"
    assert by_id["connectors.alert_delivery"].metadata["live_delivery_permitted"] is False
    assert by_id["connectors.dars"].status == "loopback_placeholder"
    assert by_id["connectors.dars"].metadata["external_call_made"] is False


def test_collect_health_status_is_ok_when_required_runtime_dirs_exist(tmp_path: Path) -> None:
    instance = tmp_path / "instance"
    for name in ["config", "data", "reports", "runtime-boundary"]:
        (instance / name).mkdir(parents=True, exist_ok=True)
    (instance / "config" / "source-registry.yaml").write_text("sources: []\n", encoding="utf-8")

    report = collect_health_status(instance)

    assert report.overall_status == "ok"
    assert report.required_operator_action == "none"
