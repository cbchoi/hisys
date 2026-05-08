"""Example runtime instance smoke tests.

Traceability: HISYS-RUNTIME-DIR-001, HISYS-HARNESS-GUIDE-001,
HISYS-D-015, HISYS-D-016, HISYS-T-001, HISYS-T-002.
"""

from __future__ import annotations

from pathlib import Path

from hisys.config import InstanceRoot, load_source_registry


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples" / "instance"


def test_example_instance_has_minimum_runtime_scaffold():
    required = [
        "config/source-registry.yaml",
        "config/web-compliance/SRC-WEB-RSS-001.yaml",
        "config/hermes-scope.yaml",
        "templates/collection/research-topic-search-template.md",
        "harness/guidelines/README.md",
        "harness/guidelines/investigator.md",
        "harness/guidelines/hermes.md",
        "harness/guidelines/source-governance.md",
        "harness/guidelines/audit-and-traceability.md",
        "harness/scenarios/hardware-anomaly.yaml",
        "harness/scenarios/source-failure-isolation.yaml",
        "secrets/README.md",
    ]
    missing = [path for path in required if not (EXAMPLE / path).exists()]
    assert missing == []


def test_example_instance_registry_is_loadable_and_collectable():
    registry = load_source_registry(InstanceRoot(EXAMPLE))

    assert registry.assert_collectable("SRC-HW-MOCK-001").source_type == "hardware_sensor"
    assert registry.assert_collectable("SRC-WEB-RSS-001").source_type == "web_news"
    assert registry.assert_collectable("SRC-HERMES-TOOL-001").source_type == "hermes_tool"
