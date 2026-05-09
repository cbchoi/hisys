"""DARS dispatch gate tests.

Traceability: HISYS-DARS-CONTRACT-001, HISYS-FR-AGT-001..005,
HISYS-T-019, HISYS-T-020, HISYS-T-024, HISYS-CON-010..012.
"""

from __future__ import annotations

import json
from pathlib import Path

from hisys.agents.dars_config import DarsConfig
from hisys.agents.dars_dispatch import DarsDispatchGate
from hisys.config.instance import InstanceRoot
from tests.unit.test_dars_config import _minimal_dars_config


def _config_with_fixture_backend_enabled() -> DarsConfig:
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


def _config_with_external_backend() -> DarsConfig:
    data = _minimal_dars_config()
    data["spec"]["backends"]["remote_dars"] = {
        "kind": "openai_compatible",
        "enabled": True,
        "mode": "external_api",
        "endpoint": "https://example.invalid/v1/chat/completions",
        "model": "example-model",
        "credential_ref": "vault://dars/example",
        "external_call_allowed": True,
        "output_contract": "DarsCritiqueRecord",
    }
    return DarsConfig.model_validate(data)


def test_dars_dispatch_gate_allows_local_loopback_and_records_boundary(tmp_path: Path):
    config = DarsConfig.model_validate(_minimal_dars_config())

    decision = DarsDispatchGate(instance=InstanceRoot(tmp_path)).evaluate(
        yyyymmdd="20260509",
        request_id="DARSREQ-DISPATCH-001",
        config=config,
        backend_id="loopback_placeholder",
        approval_ref=None,
    )

    assert decision.decision == "allowed"
    assert decision.backend_id == "loopback_placeholder"
    assert decision.backend_kind == "loopback"
    assert decision.external_call_made is False
    assert decision.mutation_performed is False
    assert decision.action_taken == "none"
    assert decision.allowed_actions == "advisory_only"

    record_path = tmp_path / "runtime-boundary" / "dars" / "20260509" / "dars-dispatch-decision-DARSREQ-DISPATCH-001.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record["decision"] == "allowed"
    assert record["reason_code"] == "loopback_backend_allowed"
    assert record["external_call_requested"] is False


def test_dars_dispatch_gate_blocks_disabled_backend_and_records_reason(tmp_path: Path):
    config = DarsConfig.model_validate(_minimal_dars_config())

    decision = DarsDispatchGate(instance=InstanceRoot(tmp_path)).evaluate(
        yyyymmdd="20260509",
        request_id="DARSREQ-DISPATCH-002",
        config=config,
        backend_id="claude_dars",
        approval_ref=None,
    )

    assert decision.decision == "blocked"
    assert decision.reason_code == "backend_disabled"
    assert "disabled" in decision.reason
    assert decision.external_call_made is False
    assert decision.action_taken == "none"

    record_path = tmp_path / "runtime-boundary" / "dars" / "20260509" / "dars-dispatch-decision-DARSREQ-DISPATCH-002.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record["decision"] == "blocked"
    assert record["backend_id"] == "claude_dars"
    assert record["reason_code"] == "backend_disabled"


def test_dars_dispatch_gate_blocks_external_backend_without_explicit_approval(tmp_path: Path):
    config = _config_with_external_backend()

    decision = DarsDispatchGate(instance=InstanceRoot(tmp_path)).evaluate(
        yyyymmdd="20260509",
        request_id="DARSREQ-DISPATCH-003",
        config=config,
        backend_id="remote_dars",
        approval_ref=None,
    )

    assert decision.decision == "blocked"
    assert decision.reason_code == "external_call_requires_approval"
    assert decision.external_call_requested is True
    assert decision.external_call_made is False
    assert decision.action_taken == "none"


def test_dars_dispatch_gate_allows_enabled_local_fixture_without_external_call(tmp_path: Path):
    config = _config_with_fixture_backend_enabled()

    decision = DarsDispatchGate(instance=InstanceRoot(tmp_path)).evaluate(
        yyyymmdd="20260509",
        request_id="DARSREQ-DISPATCH-004",
        config=config,
        backend_id="fixture_file",
        approval_ref=None,
    )

    assert decision.decision == "allowed"
    assert decision.reason_code == "local_backend_allowed"
    assert decision.backend_kind == "fixture_file"
    assert decision.external_call_requested is False
    assert decision.external_call_made is False
