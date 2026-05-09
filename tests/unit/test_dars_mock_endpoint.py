"""DARS mock endpoint adapter tests.

Traceability: HISYS-DARS-CONTRACT-001, HISYS-FR-AGT-001..005,
HISYS-T-019, HISYS-T-020, HISYS-CON-010..012.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.agents.dars_backend import DarsMockEndpointAdapter
from hisys.agents.dars_config import DarsConfig, load_dars_config, validate_dars_config_document
from hisys.agents.dars_dispatch import DarsDispatchGate
from hisys.config.instance import InstanceRoot
from tests.unit.test_dars_config import _minimal_dars_config


def _mock_config(*, enabled: bool = False, external_call_allowed: bool = False) -> DarsConfig:
    data = _minimal_dars_config()
    data["spec"]["backends"]["mock_endpoint"] = {
        "kind": "mock_http",
        "enabled": enabled,
        "mode": "local_network_only",
        "endpoint": "http://127.0.0.1:0/dars/mock",
        "external_call_allowed": external_call_allowed,
        "output_contract": "DarsCritiqueRecord",
    }
    return DarsConfig.model_validate(data)


def test_example_dars_config_declares_mock_endpoint_disabled_by_default(tmp_path: Path):
    example = Path("examples/instance/config/dars.json")
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "dars.json").write_text(example.read_text(encoding="utf-8"), encoding="utf-8")

    config = load_dars_config(InstanceRoot(tmp_path))

    backend = config.spec.backends["mock_endpoint"]
    assert backend.kind == "mock_http"
    assert backend.enabled is False
    assert backend.external_call_allowed is False
    assert backend.endpoint == "http://127.0.0.1:0/dars/mock"


def test_config_validation_rejects_enabled_mock_endpoint_in_checked_in_config():
    data = _minimal_dars_config()
    data["spec"]["backends"]["mock_endpoint"] = {
        "kind": "mock_http",
        "enabled": True,
        "mode": "local_network_only",
        "endpoint": "http://127.0.0.1:0/dars/mock",
        "external_call_allowed": False,
        "output_contract": "DarsCritiqueRecord",
    }

    report = validate_dars_config_document(data, config_ref="inline://mock-enabled")

    assert report.valid is False
    by_path = {issue.path: issue.code for issue in report.issues}
    assert by_path["spec.backends.mock_endpoint.enabled"] == "non_loopback_backend_enabled_by_default"


def test_mock_endpoint_adapter_refuses_blocked_dispatch_without_network(tmp_path: Path):
    config = _mock_config(enabled=False)
    decision = DarsDispatchGate(instance=InstanceRoot(tmp_path)).evaluate(
        yyyymmdd="20260509",
        request_id="DARSREQ-MOCK-001",
        config=config,
        backend_id="mock_endpoint",
        approval_ref=None,
    )

    assert decision.decision == "blocked"
    assert decision.reason_code == "backend_disabled"
    with pytest.raises(ValueError, match="dispatch decision is not allowed"):
        DarsMockEndpointAdapter(instance=InstanceRoot(tmp_path)).run(
            yyyymmdd="20260509",
            request_id="DARSREQ-MOCK-001",
            backend_config=config.spec.backends["mock_endpoint"],
            dispatch_decision=decision,
        )
    assert not list((tmp_path / "runtime-boundary" / "dars" / "20260509").glob("dars-response-*.json"))
