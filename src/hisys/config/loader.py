"""Runtime configuration loaders.

Traceability: HISYS-D-015, HISYS-D-016, HISYS-RUNTIME-DIR-001,
HISYS-FR-SRC-001..005, HISYS-T-001, HISYS-T-002.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ..registry import SourceRegistry
from ..schemas import SourceRegistryEntry, WebComplianceReview
from .instance import InstanceRoot


def _read_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_source_registry(instance: InstanceRoot) -> SourceRegistry:
    """Load SourceRegistryEntry and WebComplianceReview YAML files.

    Expected paths:
    - ``config/source-registry.yaml`` with top-level ``sources`` list.
    - ``config/web-compliance/*.yaml`` with one review per file.
    """

    source_path = instance.config_dir / "source-registry.yaml"
    data = _read_yaml(source_path)
    registry = SourceRegistry()
    registry.register_many(SourceRegistryEntry(**item) for item in data.get("sources", []))

    compliance_dir = instance.config_dir / "web-compliance"
    if compliance_dir.exists():
        for review_path in sorted(compliance_dir.glob("*.yaml")):
            registry.add_web_review(WebComplianceReview(**_read_yaml(review_path)))
    return registry


__all__ = ["load_source_registry"]
