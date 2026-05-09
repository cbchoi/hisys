"""DARS fixture backend tests.

Traceability: HISYS-DARS-CONTRACT-001, HISYS-FR-AGT-001..005,
HISYS-T-019, HISYS-T-020, HISYS-T-024, HISYS-CON-010..012.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hisys.agents.dars_backend import DarsFixtureBackend
from hisys.agents.dars_config import DarsConfig
from hisys.agents.dars_dispatch import DarsDispatchGate
from hisys.config.instance import InstanceRoot
from tests.unit.test_dars_config import _minimal_dars_config
from tests.unit.test_dars_protocol import _valid_response_payload


def _fixture_config() -> DarsConfig:
    data = _minimal_dars_config()
    data["spec"]["backends"]["fixture_file"] = {
        "kind": "fixture_file",
        "enabled": True,
        "mode": "local_only",
        "fixture_path": "harness/fixtures/dars/critique-response.json",
        "external_call_allowed": False,
        "output_contract": "DarsCritiqueRecord",
    }
    return DarsConfig.model_validate(data)


def test_fixture_backend_loads_valid_response_and_records_runtime_boundary(tmp_path: Path):
    instance = InstanceRoot(tmp_path)
    fixture_path = tmp_path / "harness" / "fixtures" / "dars" / "critique-response.json"
    fixture_path.parent.mkdir(parents=True)
    payload = _valid_response_payload()
    payload["request_id"] = "DARSREQ-FIXTURE-001"
    payload["response_id"] = "DARSRESP-FIXTURE-001"
    fixture_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    config = _fixture_config()
    decision = DarsDispatchGate(instance=instance).evaluate(
        yyyymmdd="20260509",
        request_id="DARSREQ-FIXTURE-001",
        config=config,
        backend_id="fixture_file",
        approval_ref=None,
    )

    response = DarsFixtureBackend(instance=instance).run(
        yyyymmdd="20260509",
        request_id="DARSREQ-FIXTURE-001",
        backend_config=config.spec.backends["fixture_file"],
        dispatch_decision=decision,
    )

    assert response.response_id == "DARSRESP-FIXTURE-001"
    assert response.request_id == "DARSREQ-FIXTURE-001"
    assert response.producer.backend_kind == "loopback"
    assert response.boundary.action_taken == "none"
    response_path = tmp_path / "runtime-boundary" / "dars" / "20260509" / "dars-response-DARSRESP-FIXTURE-001.json"
    response_record = json.loads(response_path.read_text(encoding="utf-8"))
    assert response_record["schema_id"] == "hisys.dars.response"
    assert response_record["request_id"] == "DARSREQ-FIXTURE-001"
    assert (tmp_path / "runtime-boundary" / "dars" / "20260509" / "dars-response-DARSRESP-FIXTURE-001.md").exists()


def test_fixture_backend_rejects_blocked_dispatch_decision(tmp_path: Path):
    instance = InstanceRoot(tmp_path)
    data = _minimal_dars_config()
    data["spec"]["backends"]["fixture_file"] = {
        "kind": "fixture_file",
        "enabled": False,
        "mode": "local_only",
        "fixture_path": "harness/fixtures/dars/critique-response.json",
        "external_call_allowed": False,
        "output_contract": "DarsCritiqueRecord",
    }
    config = DarsConfig.model_validate(data)
    decision = DarsDispatchGate(instance=instance).evaluate(
        yyyymmdd="20260509",
        request_id="DARSREQ-FIXTURE-BLOCKED",
        config=config,
        backend_id="fixture_file",
        approval_ref=None,
    )

    with pytest.raises(ValueError, match="dispatch decision is not allowed"):
        DarsFixtureBackend(instance=instance).run(
            yyyymmdd="20260509",
            request_id="DARSREQ-FIXTURE-BLOCKED",
            backend_config=config.spec.backends["fixture_file"],
            dispatch_decision=decision,
        )


def test_fixture_backend_rejects_request_id_mismatch(tmp_path: Path):
    instance = InstanceRoot(tmp_path)
    fixture_path = tmp_path / "harness" / "fixtures" / "dars" / "critique-response.json"
    fixture_path.parent.mkdir(parents=True)
    payload = _valid_response_payload()
    payload["request_id"] = "DARSREQ-OTHER"
    fixture_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    config = _fixture_config()
    decision = DarsDispatchGate(instance=instance).evaluate(
        yyyymmdd="20260509",
        request_id="DARSREQ-EXPECTED",
        config=config,
        backend_id="fixture_file",
        approval_ref=None,
    )

    with pytest.raises(ValueError, match="request_id mismatch"):
        DarsFixtureBackend(instance=instance).run(
            yyyymmdd="20260509",
            request_id="DARSREQ-EXPECTED",
            backend_config=config.spec.backends["fixture_file"],
            dispatch_decision=decision,
        )
