"""DARS live-provider policy packet validator tests.

Traceability: HISYS-FR-DARS-CP-009, HISYS-T-DARS-CP-011,
DARS-LIVE-RELEASE-R1-POLICY,
docs/plans/dars-panel-live-provider-unattended-release-final-plan.md.

These tests exercise only the local validator. They never read credentials,
open sockets, call a provider, or activate live dispatch.
"""

from __future__ import annotations

from typing import Any

from hisys.agents.dars_live_provider_policy import (
    LIVE_PROVIDER_POLICY_SCHEMA_ID,
    LIVE_PROVIDER_POLICY_SCHEMA_VERSION,
    validate_live_provider_policy_packet,
)


def _valid_policy_data(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "policy_id": "DARS-LP-POL-20260523-001",
        "approval_ref": "APPROVAL-DARS-LP-20260523-001",
        "operator_id": "operator:cbchoi",
        "provider_id": "claude",
        "provider_kind": "subscription",
        "model_id": "claude-opus-4-7",
        "credential_ref": "env://HISYS_DARS_PROVIDER_TOKEN",
        "credential_ref_kind": "env",
        "endpoint_ref": "subscription://claude/default",
        "allowed_actions": "advisory_only",
        "external_call_allowed": True,
        "mutation_allowed": False,
        "publication_allowed": False,
        "requires_human_review": True,
        "max_prompt_bytes": 4096,
        "max_output_bytes": 4096,
        "rate_limit_per_minute": 30,
        "cost_budget_ref": "budget://dars/live-provider/2026-05",
        "expires_at": "2026-06-23T00:00:00Z",
        "redaction_policy_ref": "policy://hisys/dars/live-provider-redaction-v1",
        "audit_required": True,
    }
    data.update(overrides)
    return data


def _issue_codes(report: Any) -> set[str]:
    return {issue.code for issue in report.issues}


def _error_codes(report: Any) -> set[str]:
    return {issue.code for issue in report.issues if issue.severity == "error"}


def test_live_provider_policy_schema_constants_are_stable():
    assert LIVE_PROVIDER_POLICY_SCHEMA_ID == "hisys.dars.live_provider_policy"
    assert LIVE_PROVIDER_POLICY_SCHEMA_VERSION == "0.1.0"


def test_live_provider_policy_accepts_credential_reference_only():
    report = validate_live_provider_policy_packet(
        _valid_policy_data(),
        config_ref="inline://valid-claude",
        now="2026-05-23T00:00:00Z",
    )

    assert report.valid is True
    assert _error_codes(report) == set()
    assert report.schema_id == LIVE_PROVIDER_POLICY_SCHEMA_ID


def test_live_provider_policy_rejects_raw_secret_fields():
    # Test fixture values are prefixed with FAKE_/fixture- per
    # hisys.security.secret_scan.SAFE_VALUE_PREFIXES so the secret scanner
    # does not flag the deliberately secret-shaped inputs that exercise the
    # policy validator's raw-secret rejection paths.
    raw_secret_payloads: list[dict[str, object]] = [
        _valid_policy_data(api_key="FAKE_not_a_real_secret_value"),
        _valid_policy_data(token="FAKE_not_a_real_token_value"),
        _valid_policy_data(password="FAKE_not_a_real_password"),
        _valid_policy_data(authorization="FAKE_not_a_real_bearer_value"),
        _valid_policy_data(provider_token_value="FAKE_not_a_real_provider_token"),
        _valid_policy_data(credential_ref="sk-" + "fake_credential_ref_value"),
        _valid_policy_data(credential_ref="hf_" + "fake_credential_ref_value"),
    ]
    for payload in raw_secret_payloads:
        report = validate_live_provider_policy_packet(
            payload,
            config_ref="inline://raw-secret",
            now="2026-05-23T00:00:00Z",
        )
        assert report.valid is False, payload
        assert "raw_secret_value_not_allowed" in _error_codes(report), payload


def test_live_provider_policy_rejects_missing_credential_reference():
    payload = _valid_policy_data()
    payload.pop("credential_ref")
    payload.pop("credential_ref_kind")
    report = validate_live_provider_policy_packet(
        payload,
        config_ref="inline://no-credential-ref",
        now="2026-05-23T00:00:00Z",
    )

    assert report.valid is False
    assert "missing_credential_ref" in _error_codes(report)


def test_live_provider_policy_rejects_unknown_credential_ref_scheme():
    report = validate_live_provider_policy_packet(
        _valid_policy_data(credential_ref="https://example.com/token"),
        config_ref="inline://http-credential-ref",
        now="2026-05-23T00:00:00Z",
    )

    assert report.valid is False
    assert "invalid_credential_ref_scheme" in _error_codes(report)


def test_live_provider_policy_rejects_mutation_or_publication_authority():
    for flag in ("mutation_allowed", "publication_allowed"):
        report = validate_live_provider_policy_packet(
            _valid_policy_data(**{flag: True}),
            config_ref="inline://mutation-flag",
            now="2026-05-23T00:00:00Z",
        )
        assert report.valid is False, flag
        assert "mutation_authority_not_allowed" in _error_codes(report), flag


def test_live_provider_policy_rejects_non_advisory_allowed_actions():
    report = validate_live_provider_policy_packet(
        _valid_policy_data(allowed_actions="autonomous_decision"),
        config_ref="inline://autonomous-actions",
        now="2026-05-23T00:00:00Z",
    )

    assert report.valid is False
    assert "invalid_allowed_actions" in _error_codes(report)


def test_live_provider_policy_rejects_disabled_external_call_or_human_review():
    payloads = [
        _valid_policy_data(external_call_allowed=False),
        _valid_policy_data(requires_human_review=False),
    ]
    expected_codes = {
        "external_call_must_be_allowed",
        "requires_human_review_must_be_true",
    }
    for payload in payloads:
        report = validate_live_provider_policy_packet(
            payload,
            config_ref="inline://gate-flag",
            now="2026-05-23T00:00:00Z",
        )
        assert report.valid is False, payload
        assert expected_codes & _error_codes(report), payload


def test_live_provider_policy_rejects_unbounded_prompt_output_or_rate_limit():
    payloads = [
        _valid_policy_data(max_prompt_bytes=0),
        _valid_policy_data(max_output_bytes=0),
        _valid_policy_data(rate_limit_per_minute=0),
        _valid_policy_data(max_prompt_bytes=-10),
    ]
    expected_codes = {
        "max_prompt_bytes_must_be_positive",
        "max_output_bytes_must_be_positive",
        "rate_limit_must_be_positive",
    }
    for payload in payloads:
        report = validate_live_provider_policy_packet(
            payload,
            config_ref="inline://unbounded",
            now="2026-05-23T00:00:00Z",
        )
        assert report.valid is False, payload
        assert expected_codes & _error_codes(report), payload


def test_live_provider_policy_rejects_expired_packet():
    report = validate_live_provider_policy_packet(
        _valid_policy_data(expires_at="2025-01-01T00:00:00Z"),
        config_ref="inline://expired",
        now="2026-05-23T00:00:00Z",
    )

    assert report.valid is False
    assert "policy_expired" in _error_codes(report)


def test_live_provider_policy_rejects_non_allowlisted_provider():
    report = validate_live_provider_policy_packet(
        _valid_policy_data(provider_id="gemini"),
        config_ref="inline://gemini",
        now="2026-05-23T00:00:00Z",
    )

    assert report.valid is False
    assert "provider_not_allowlisted" in _error_codes(report)


def test_live_provider_policy_rejects_missing_approval_or_cost_budget_ref():
    payloads = [
        _valid_policy_data(approval_ref=""),
        _valid_policy_data(cost_budget_ref=""),
    ]
    for payload in payloads:
        report = validate_live_provider_policy_packet(
            payload,
            config_ref="inline://missing-ref",
            now="2026-05-23T00:00:00Z",
        )
        assert report.valid is False, payload
        assert "missing_required_field" in _error_codes(report), payload


def test_live_provider_policy_emits_dispatch_warning_even_when_valid():
    report = validate_live_provider_policy_packet(
        _valid_policy_data(),
        config_ref="inline://warning",
        now="2026-05-23T00:00:00Z",
    )

    assert report.valid is True
    warning_codes = {
        issue.code for issue in report.issues if issue.severity == "warning"
    }
    assert "live_provider_dispatch_not_authorized_by_policy_alone" in warning_codes
