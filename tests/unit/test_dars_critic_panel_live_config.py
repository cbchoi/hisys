"""Tests for controlled live DARS panel activation packets."""

from pydantic import ValidationError

from hisys.agents.dars_panel_live_config import (
    LiveDarsPanelActivationPacket,
    validate_live_dars_panel_activation_packet,
)


def _valid_packet_data() -> dict[str, object]:
    return {
        "activation_id": "DARS-LIVE-ACT-20260520-001",
        "approval_ref": "APPROVAL-DARS-LIVE-20260520-001",
        "operator_id": "operator:cbchoi",
        "approved_endpoint_scope": "localhost_only",
        "allowed_actions": "advisory_only",
        "human_approved": True,
        "expires_at": "2026-05-21T00:00:00Z",
        "requested_backend_id": "local_openai_compatible",
        "requested_adapter_class": "local_model",
    }


def test_live_panel_activation_requires_human_approval_ref() -> None:
    data = _valid_packet_data()
    data.pop("approval_ref")

    report = validate_live_dars_panel_activation_packet(data, config_ref="inline://missing-approval")

    assert report.valid is False
    assert any(issue.path == "approval_ref" and issue.code == "missing_required_field" for issue in report.issues)


def test_live_panel_activation_accepts_localhost_advisory_packet() -> None:
    packet = LiveDarsPanelActivationPacket.model_validate(_valid_packet_data())
    report = validate_live_dars_panel_activation_packet(packet.model_dump(mode="json"), config_ref="inline://valid")

    assert report.valid is True
    assert report.issues == []
    assert packet.model_boundary_authorized is True
    assert packet.live_external_action_authorized is False
    assert packet.mutation_authorized is False


def test_live_panel_activation_rejects_remote_scope_and_mutation_authority() -> None:
    data = _valid_packet_data()
    data["approved_endpoint_scope"] = "external_api"
    data["allowed_actions"] = "mutation_allowed"

    report = validate_live_dars_panel_activation_packet(data, config_ref="inline://remote")

    codes = {issue.code for issue in report.issues}
    assert report.valid is False
    assert "invalid_endpoint_scope" in codes
    assert "invalid_allowed_actions" in codes


def test_live_panel_activation_rejects_raw_secret_fields() -> None:
    data = _valid_packet_data()
    data["api_key"] = "sk-testvalue123456789"

    report = validate_live_dars_panel_activation_packet(data, config_ref="inline://secret")

    assert report.valid is False
    assert any(issue.code == "raw_secret_value_not_allowed" for issue in report.issues)


def test_live_panel_activation_model_validation_forbids_extra_secret_fields() -> None:
    data = _valid_packet_data()
    data["password"] = "never-store-this"

    try:
        LiveDarsPanelActivationPacket.model_validate(data)
    except ValidationError as exc:
        assert exc.errors()[0]["type"] == "extra_forbidden"
    else:  # pragma: no cover - explicit failure clarity
        raise AssertionError("raw secret-like extra field was accepted")
