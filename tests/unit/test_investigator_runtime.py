"""Investigator runtime skeleton tests.

Traceability: HISYS-INST-INV-001, HISYS-D-015, HISYS-D-016,
HISYS-FR-INV-001..006, HISYS-T-007, HISYS-T-008.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.config import InstanceRoot
from hisys.investigator import InvestigatorRuntime
from hisys.registry import SourceRegistry


def test_investigator_collect_run_writes_observation_and_audit(
    tmp_path: Path,
    hardware_source,
    hardware_adapter,
):
    registry = SourceRegistry()
    registry.register(hardware_source)
    runtime = InvestigatorRuntime(
        registry=registry,
        adapters={"SRC-HW-MOCK-001": hardware_adapter},
        instance=InstanceRoot(tmp_path),
        collector_id="investigator-test",
    )

    report = runtime.collect_run(["SRC-HW-MOCK-001"], yyyymmdd="20260508")

    assert report.requested_source_ids == ["SRC-HW-MOCK-001"]
    assert report.skipped_source_ids == []
    assert len(report.collected_observation_refs) == 1
    obs_id = report.collected_observation_refs[0]
    obs_path = tmp_path / "data" / "raw-observations" / "20260508" / f"{obs_id}.json"
    assert obs_path.exists()
    obs_data = json.loads(obs_path.read_text(encoding="utf-8"))
    assert obs_data["source_id"] == "SRC-HW-MOCK-001"
    assert obs_data["usage_constraints"] == ["test_only"]
    audit_path = tmp_path / "data" / "audit" / "20260508" / "AUDIT-20260508.jsonl"
    assert audit_path.exists()
    assert report.audit_event_refs


def test_investigator_refuses_unregistered_source_without_blocking_registered(
    tmp_path: Path,
    hardware_source,
    hardware_adapter,
):
    registry = SourceRegistry()
    registry.register(hardware_source)
    runtime = InvestigatorRuntime(
        registry=registry,
        adapters={"SRC-HW-MOCK-001": hardware_adapter},
        instance=InstanceRoot(tmp_path),
        collector_id="investigator-test",
    )

    report = runtime.collect_run(["SRC-MISSING-001", "SRC-HW-MOCK-001"], yyyymmdd="20260508")

    assert report.skipped_source_ids == ["SRC-MISSING-001"]
    assert len(report.collected_observation_refs) == 1
    assert "SRC-MISSING-001" in report.adapter_errors
