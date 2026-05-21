"""DARS backend activation packet validator tests.

Traceability: M-DARS-BE-1, docs/plans/dars-live-backend-implementation-plan.md.
"""

from __future__ import annotations

from typing import Any

from hisys.agents.dars_backend_activation import validate_dars_backend_activation_packet


def _valid_packet_data(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "activation_id": "DARS-BE-ACT-20260521-001",
        "backend_id": "local_llm_dars",
        "backend_kind": "openai_compatible",
        "endpoint_scope": "localhost_only",
        "allowed_actions": "advisory_only",
        "human_approved": True,
        "approval_ref": "APPROVAL-DARS-BE-20260521-001",
        "expires_at": "2026-05-22T00:00:00Z",
    }
    data.update(overrides)
    return data


def _issue_codes(report: Any) -> set[str]:
    return {issue.code for issue in report.issues}


def test_backend_activation_accepts_minimal_localhost_advisory_packet():
    report = validate_dars_backend_activation_packet(
        _valid_packet_data(),
        config_ref="inline://valid-localhost",
        now="2026-05-21T00:00:00Z",
    )

    assert report.valid is True
    assert _issue_codes(report) == set()


def test_backend_activation_rejects_external_provider_without_policy_packet():
    report = validate_dars_backend_activation_packet(
        _valid_packet_data(
            backend_id="external-openai",
            endpoint_scope="external_api",
        ),
        config_ref="inline://external",
        now="2026-05-21T00:00:00Z",
    )

    assert report.valid is False
    assert "external_backend_requires_remote_policy_packet" in _issue_codes(report)


def test_backend_activation_rejects_expired_packet_deterministically():
    report = validate_dars_backend_activation_packet(
        _valid_packet_data(expires_at="2026-05-20T00:00:00Z"),
        config_ref="inline://expired",
        now="2026-05-21T00:00:00Z",
    )

    assert report.valid is False
    assert "activation_expired" in _issue_codes(report)


def test_backend_activation_rejects_secret_like_fields_and_values():
    data = _valid_packet_data()
    data["api_key"] = "sk-testvalue123456789"

    report = validate_dars_backend_activation_packet(
        data,
        config_ref="inline://secret",
        now="2026-05-21T00:00:00Z",
    )

    assert report.valid is False
    assert "raw_secret_value_not_allowed" in _issue_codes(report)


def test_backend_activation_rejects_invalid_allowed_actions():
    report = validate_dars_backend_activation_packet(
        _valid_packet_data(allowed_actions="execute_mutations"),
        config_ref="inline://mutation",
        now="2026-05-21T00:00:00Z",
    )

    assert report.valid is False
    assert "invalid_allowed_actions" in _issue_codes(report)


def test_backend_activation_rejects_missing_approval_ref():
    report = validate_dars_backend_activation_packet(
        _valid_packet_data(approval_ref=""),
        config_ref="inline://missing-approval",
        now="2026-05-21T00:00:00Z",
    )

    assert report.valid is False
    assert "missing_approval_ref" in _issue_codes(report)


def test_backend_activation_requires_human_approval():
    report = validate_dars_backend_activation_packet(
        _valid_packet_data(human_approved=False),
        config_ref="inline://not-approved",
        now="2026-05-21T00:00:00Z",
    )

    assert report.valid is False
    assert "human_approval_required" in _issue_codes(report)


def test_backend_activation_rejects_invalid_endpoint_scope():
    report = validate_dars_backend_activation_packet(
        _valid_packet_data(endpoint_scope="public_internet"),
        config_ref="inline://bad-scope",
        now="2026-05-21T00:00:00Z",
    )

    assert report.valid is False
    assert "invalid_endpoint_scope" in _issue_codes(report)
