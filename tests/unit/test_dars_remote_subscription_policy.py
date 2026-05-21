"""DARS remote subscription policy packet validator tests.

Traceability: M-DARS-BE-5, docs/plans/dars-live-backend-implementation-plan.md.
"""

from __future__ import annotations

from typing import Any

from hisys.agents.dars_remote_subscription_policy import (
    validate_dars_remote_subscription_policy_packet,
)


def _valid_policy_data(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "policy_id": "DARS-RS-POL-20260521-001",
        "approval_ref": "APPROVAL-DARS-RS-20260521-001",
        "operator_id": "operator:cbchoi",
        "provider_id": "claude",
        "access_mode": "subscription",
        "subscription_account_ref": "vault://dars/claude/subscription-001",
        "adapter_class": "claude_subscription",
        "redaction_policy_ref": "redaction://dars/no-raw-source",
        "egress_scope": "subscription_only",
        "max_session_or_token_budget": 100000,
        "expires_at": "2026-06-21T00:00:00Z",
        "revocation_ref": "revocation://dars/claude/subscription-001",
        "audit_required": True,
    }
    data.update(overrides)
    return data


def _issue_codes(report: Any) -> set[str]:
    return {issue.code for issue in report.issues}


def _error_codes(report: Any) -> set[str]:
    return {issue.code for issue in report.issues if issue.severity == "error"}


def test_remote_subscription_policy_accepts_minimal_claude_packet():
    report = validate_dars_remote_subscription_policy_packet(
        _valid_policy_data(),
        config_ref="inline://valid-claude",
        now="2026-05-21T00:00:00Z",
    )

    assert report.valid is True
    assert _error_codes(report) == set()


def test_remote_subscription_policy_accepts_codex_provider():
    report = validate_dars_remote_subscription_policy_packet(
        _valid_policy_data(provider_id="codex", adapter_class="codex_subscription"),
        config_ref="inline://valid-codex",
        now="2026-05-21T00:00:00Z",
    )

    assert report.valid is True


def test_remote_subscription_policy_rejects_non_allowlisted_provider():
    report = validate_dars_remote_subscription_policy_packet(
        _valid_policy_data(provider_id="gemini", adapter_class="gemini_subscription"),
        config_ref="inline://gemini",
        now="2026-05-21T00:00:00Z",
    )

    assert report.valid is False
    assert "provider_not_allowlisted" in _issue_codes(report)


def test_remote_subscription_policy_rejects_grok_provider():
    report = validate_dars_remote_subscription_policy_packet(
        _valid_policy_data(provider_id="grok", adapter_class="grok_subscription"),
        config_ref="inline://grok",
        now="2026-05-21T00:00:00Z",
    )

    assert report.valid is False
    assert "provider_not_allowlisted" in _issue_codes(report)


def test_remote_subscription_policy_rejects_generic_openai_provider():
    report = validate_dars_remote_subscription_policy_packet(
        _valid_policy_data(
            provider_id="openai_generic",
            adapter_class="openai_generic_subscription",
        ),
        config_ref="inline://openai-generic",
        now="2026-05-21T00:00:00Z",
    )

    assert report.valid is False
    assert "provider_not_allowlisted" in _issue_codes(report)


def test_remote_subscription_policy_rejects_pay_per_call_access_mode():
    report = validate_dars_remote_subscription_policy_packet(
        _valid_policy_data(access_mode="api_key"),
        config_ref="inline://api-key-access",
        now="2026-05-21T00:00:00Z",
    )

    assert report.valid is False
    assert "invalid_access_mode" in _issue_codes(report)


def test_remote_subscription_policy_rejects_adapter_class_mismatch():
    report = validate_dars_remote_subscription_policy_packet(
        _valid_policy_data(provider_id="claude", adapter_class="codex_subscription"),
        config_ref="inline://mismatch",
        now="2026-05-21T00:00:00Z",
    )

    assert report.valid is False
    assert "adapter_class_mismatch" in _issue_codes(report)


def test_remote_subscription_policy_rejects_raw_secret_fields():
    data = _valid_policy_data()
    data["api_key"] = "sk-testvalue123456789"

    report = validate_dars_remote_subscription_policy_packet(
        data,
        config_ref="inline://secret",
        now="2026-05-21T00:00:00Z",
    )

    assert report.valid is False
    assert "raw_secret_value_not_allowed" in _issue_codes(report)


def test_remote_subscription_policy_rejects_endpoint_url_field():
    data = _valid_policy_data()
    data["endpoint_url"] = "https://anthropic.example/v1/messages"

    report = validate_dars_remote_subscription_policy_packet(
        data,
        config_ref="inline://endpoint-url",
        now="2026-05-21T00:00:00Z",
    )

    assert report.valid is False
    assert "endpoint_url_not_allowed_for_subscription" in _issue_codes(report)


def test_remote_subscription_policy_requires_audit_true():
    report = validate_dars_remote_subscription_policy_packet(
        _valid_policy_data(audit_required=False),
        config_ref="inline://no-audit",
        now="2026-05-21T00:00:00Z",
    )

    assert report.valid is False
    assert "audit_required_must_be_true" in _issue_codes(report)


def test_remote_subscription_policy_rejects_expired_packet_deterministically():
    report = validate_dars_remote_subscription_policy_packet(
        _valid_policy_data(expires_at="2026-05-20T00:00:00Z"),
        config_ref="inline://expired",
        now="2026-05-21T00:00:00Z",
    )

    assert report.valid is False
    assert "policy_expired" in _issue_codes(report)


def test_remote_subscription_policy_requires_subscription_account_ref():
    report = validate_dars_remote_subscription_policy_packet(
        _valid_policy_data(subscription_account_ref=""),
        config_ref="inline://no-account",
        now="2026-05-21T00:00:00Z",
    )

    assert report.valid is False
    assert "missing_subscription_account_ref" in _issue_codes(report)


def test_remote_subscription_policy_rejects_mutation_or_publication_authority():
    data = _valid_policy_data()
    data["mutation_authorized"] = True

    report = validate_dars_remote_subscription_policy_packet(
        data,
        config_ref="inline://mutation",
        now="2026-05-21T00:00:00Z",
    )

    assert report.valid is False
    assert "mutation_authority_not_allowed" in _issue_codes(report)


def test_remote_subscription_policy_blocks_remote_dispatch_until_explicit_implementation():
    """The packet is preparation only; even a valid packet must not authorize
    remote dispatch. The validator surface declares this invariant via the
    ``remote_dispatch_blocked`` derived flag in the report metadata.
    """

    report = validate_dars_remote_subscription_policy_packet(
        _valid_policy_data(),
        config_ref="inline://valid-claude",
        now="2026-05-21T00:00:00Z",
    )

    assert report.valid is True
    # The report must explicitly record that even a valid policy packet does
    # not authorize remote dispatch.
    assert any(
        issue.code == "remote_dispatch_not_implemented" and issue.severity == "warning"
        for issue in report.issues
    )
