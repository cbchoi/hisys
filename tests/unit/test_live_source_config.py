"""Tests for live source connector registry governance.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hisys.connectors.live_source_config import (
    LiveSourceConnectorSafetyError,
    SourceConnectorRegistry,
    load_source_connector_registry,
)


def test_live_source_connector_registry_loads_disabled_connectors(tmp_path: Path):
    config_path = tmp_path / "source-connectors.yaml"
    config_path.write_text(
        """
default_mode: fixture_only
policy:
  live_network_enabled: false
  require_human_approval_for_external_call: true
connectors:
  publisher_web_search:
    connector_id: publisher_web_search
    connector_type: web_search
    enabled: false
    mode: read_only
    external_call_allowed: false
    requires_human_approval: true
    allowed_domains:
      - arxiv.org
    forbidden_actions:
      - login
      - form_submit
      - upload
      - purchase
      - post
      - credential_use
    output_schema: EvidencePackage
""".strip(),
        encoding="utf-8",
    )

    registry = load_source_connector_registry(config_path)

    assert registry.default_mode == "fixture_only"
    connector = registry.connectors["publisher_web_search"]
    assert connector.enabled is False
    assert connector.external_call_allowed is False
    assert connector.requires_human_approval is True
    assert connector.allowed_domains == ["arxiv.org"]
    assert "form_submit" in connector.forbidden_actions


def test_live_source_connector_registry_rejects_enabled_external_without_live_policy():
    with pytest.raises(LiveSourceConnectorSafetyError, match="live_network_enabled"):
        SourceConnectorRegistry.model_validate(
            {
                "policy": {"live_network_enabled": False},
                "connectors": {
                    "publisher_web_search": {
                        "connector_id": "publisher_web_search",
                        "connector_type": "web_search",
                        "enabled": True,
                        "mode": "read_only",
                        "external_call_allowed": True,
                        "requires_human_approval": True,
                        "approval_policy_ref": "POLICY-LIVE-001",
                        "allowed_domains": ["arxiv.org"],
                    }
                },
            }
        )


def test_live_source_connector_registry_rejects_mutating_modes():
    with pytest.raises(LiveSourceConnectorSafetyError, match="read_only"):
        SourceConnectorRegistry.model_validate(
            {
                "policy": {"live_network_enabled": True},
                "connectors": {
                    "unsafe_connector": {
                        "connector_id": "unsafe_connector",
                        "connector_type": "web_search",
                        "enabled": False,
                        "mode": "write",
                        "external_call_allowed": False,
                    }
                },
            }
        )
