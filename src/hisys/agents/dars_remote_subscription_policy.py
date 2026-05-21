"""DARS remote subscription policy packet validator.

M-DARS-BE-5 defines a schema and fail-closed validator for future
Codex/Claude subscription-backed DARS providers. The validator never
implements remote dispatch — even a valid packet emits a deterministic
``remote_dispatch_not_implemented`` warning so consumers cannot mistake
schema validity for live authority.

Traceability: docs/plans/dars-live-backend-implementation-plan.md (M-DARS-BE-5).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from hisys.config.validation import ConfigValidationIssue, ConfigValidationReport


DARS_REMOTE_SUBSCRIPTION_POLICY_SCHEMA_ID = "hisys.dars.remote_subscription_policy"
DARS_REMOTE_SUBSCRIPTION_POLICY_SCHEMA_VERSION = "0.1.0"

_ALLOWED_PROVIDERS = ("codex", "claude")
_PROVIDER_TO_ADAPTER_CLASS = {
    "codex": "codex_subscription",
    "claude": "claude_subscription",
}
_ALLOWED_ACCESS_MODE = "subscription"
_REQUIRED_STRING_FIELDS = (
    "policy_id",
    "approval_ref",
    "operator_id",
    "provider_id",
    "access_mode",
    "subscription_account_ref",
    "adapter_class",
    "redaction_policy_ref",
    "egress_scope",
    "expires_at",
    "revocation_ref",
)
_SECRET_FIELD_MARKERS = (
    "api_key",
    "apikey",
    "auth_token",
    "access_token",
    "secret",
    "password",
    "credential",
    "token",
)
_SECRET_VALUE_PREFIXES = ("sk-", "sk_", "ghp_", "xoxb-", "xoxp-", "hf_")
_FORBIDDEN_ENDPOINT_FIELDS = (
    "endpoint",
    "endpoint_url",
    "base_url",
    "api_url",
    "api_base",
)


def validate_dars_remote_subscription_policy_packet(
    data: dict[str, Any],
    *,
    config_ref: str,
    now: str | datetime | None = None,
) -> ConfigValidationReport:
    """Validate a Codex/Claude subscription policy packet deterministically.

    Even a fully valid packet emits a deterministic
    ``remote_dispatch_not_implemented`` warning so callers cannot interpret
    schema validity as live authority. The validator performs no HTTP call,
    no credential lookup, and no provider dispatch.
    """

    issues: list[ConfigValidationIssue] = []
    issues.extend(_raw_secret_issues(data))
    issues.extend(_forbidden_endpoint_issues(data))
    issues.extend(_required_field_issues(data))
    issues.extend(_provider_issues(data))
    issues.extend(_access_mode_issues(data))
    issues.extend(_adapter_class_issues(data))
    issues.extend(_audit_required_issues(data))
    issues.extend(_subscription_account_issues(data))
    issues.extend(_mutation_authority_issues(data))
    issues.extend(_expiry_issues(data, now=now))

    issues = _dedupe_issues(issues)

    valid = not any(issue.severity == "error" for issue in issues)
    if valid:
        issues.append(
            ConfigValidationIssue(
                path="*",
                severity="warning",
                code="remote_dispatch_not_implemented",
                message=(
                    "schema validity does not authorize remote dispatch; remote"
                    " Codex/Claude subscription dispatch remains fail-closed"
                    " until a later separately approved implementation lands"
                ),
            )
        )
    return ConfigValidationReport(
        config_ref=config_ref,
        schema_id=DARS_REMOTE_SUBSCRIPTION_POLICY_SCHEMA_ID,
        valid=valid,
        issues=issues,
    )


def _required_field_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    for field in _REQUIRED_STRING_FIELDS:
        value = data.get(field)
        if not isinstance(value, str) or not value:
            code = (
                "missing_subscription_account_ref"
                if field == "subscription_account_ref"
                else "missing_required_field"
            )
            issues.append(
                ConfigValidationIssue(
                    path=field,
                    code=code,
                    message=f"remote subscription policy must declare {field}",
                )
            )
    return issues


def _provider_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    provider = data.get("provider_id")
    if not isinstance(provider, str) or not provider:
        return []
    if provider not in _ALLOWED_PROVIDERS:
        return [
            ConfigValidationIssue(
                path="provider_id",
                code="provider_not_allowlisted",
                message=(
                    "remote subscription policy provider_id must be 'codex' or"
                    " 'claude'; raw API-key, arbitrary OpenAI/Anthropic-compatible,"
                    " Gemini, Grok, local-proxy, and custom-HTTP providers are"
                    " out of scope"
                ),
            )
        ]
    return []


def _access_mode_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    access_mode = data.get("access_mode")
    if access_mode == _ALLOWED_ACCESS_MODE:
        return []
    return [
        ConfigValidationIssue(
            path="access_mode",
            code="invalid_access_mode",
            message=(
                "remote DARS must use access_mode=subscription; pay-per-call,"
                " api_key, and provider-token modes are out of scope"
            ),
        )
    ]


def _adapter_class_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    provider = data.get("provider_id")
    adapter = data.get("adapter_class")
    if (
        isinstance(provider, str)
        and provider in _PROVIDER_TO_ADAPTER_CLASS
        and isinstance(adapter, str)
        and adapter != _PROVIDER_TO_ADAPTER_CLASS[provider]
    ):
        return [
            ConfigValidationIssue(
                path="adapter_class",
                code="adapter_class_mismatch",
                message=(
                    "adapter_class must match provider_id: codex_subscription"
                    " for codex; claude_subscription for claude"
                ),
            )
        ]
    return []


def _audit_required_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    if data.get("audit_required") is True:
        return []
    return [
        ConfigValidationIssue(
            path="audit_required",
            code="audit_required_must_be_true",
            message="remote subscription policy must declare audit_required=true",
        )
    ]


def _subscription_account_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    # Already covered by `_required_field_issues` but kept as a dedicated rule
    # so a future relaxation of required-field handling cannot accidentally
    # weaken the subscription_account_ref invariant.
    value = data.get("subscription_account_ref")
    if isinstance(value, str) and value:
        return []
    return [
        ConfigValidationIssue(
            path="subscription_account_ref",
            code="missing_subscription_account_ref",
            message=(
                "remote subscription policy must reference a"
                " subscription_account_ref (e.g. vault://) and never inline a"
                " raw token"
            ),
        )
    ]


def _mutation_authority_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    forbidden_true_flags = (
        "mutation_authorized",
        "publication_authorized",
        "tool_authority_granted",
        "browser_authority_granted",
        "search_authority_granted",
    )
    issues: list[ConfigValidationIssue] = []
    for flag in forbidden_true_flags:
        if data.get(flag) is True:
            issues.append(
                ConfigValidationIssue(
                    path=flag,
                    code="mutation_authority_not_allowed",
                    message=(
                        f"remote subscription policy must not grant {flag};"
                        " advisory-only is the only allowed authority"
                    ),
                )
            )
    return issues


def _expiry_issues(
    data: dict[str, Any], *, now: str | datetime | None
) -> list[ConfigValidationIssue]:
    expires_at = data.get("expires_at")
    if not isinstance(expires_at, str) or not expires_at:
        return []
    try:
        expires_dt = _parse_iso8601(expires_at)
    except ValueError:
        return [
            ConfigValidationIssue(
                path="expires_at",
                code="invalid_expires_at",
                message="expires_at must be ISO-8601",
            )
        ]
    if now is None:
        return []
    try:
        now_dt = _coerce_now(now)
    except ValueError:
        return [
            ConfigValidationIssue(
                path="expires_at",
                code="invalid_expires_at",
                message="now must be ISO-8601 or datetime",
            )
        ]
    if expires_dt <= now_dt:
        return [
            ConfigValidationIssue(
                path="expires_at",
                code="policy_expired",
                message="remote subscription policy packet has expired",
            )
        ]
    return []


def _raw_secret_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    for key, value in data.items():
        if key in {
            "approval_ref",
            "subscription_account_ref",
            "revocation_ref",
            "max_session_or_token_budget",
        }:
            continue
        key_lower = key.lower().replace("-", "_")
        if any(marker in key_lower for marker in _SECRET_FIELD_MARKERS):
            issues.append(
                ConfigValidationIssue(
                    path=key,
                    code="raw_secret_value_not_allowed",
                    message=(
                        "remote subscription policy packets must not contain raw"
                        " secret or credential fields; reference vault entries"
                        " through subscription_account_ref instead"
                    ),
                )
            )
            continue
        if isinstance(value, str) and value.startswith(_SECRET_VALUE_PREFIXES):
            issues.append(
                ConfigValidationIssue(
                    path=key,
                    code="raw_secret_value_not_allowed",
                    message=(
                        "remote subscription policy packets must not contain raw"
                        " secret-looking values"
                    ),
                )
            )
    return issues


def _forbidden_endpoint_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    for field in _FORBIDDEN_ENDPOINT_FIELDS:
        if field in data:
            issues.append(
                ConfigValidationIssue(
                    path=field,
                    code="endpoint_url_not_allowed_for_subscription",
                    message=(
                        "remote subscription policy must not declare arbitrary"
                        " endpoint URLs; subscription access is mediated"
                        " through subscription_account_ref"
                    ),
                )
            )
    return issues


def _parse_iso8601(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _coerce_now(now: str | datetime) -> datetime:
    if isinstance(now, datetime):
        if now.tzinfo is None:
            return now.replace(tzinfo=timezone.utc)
        return now
    return _parse_iso8601(now)


def _dedupe_issues(issues: list[ConfigValidationIssue]) -> list[ConfigValidationIssue]:
    deduped: list[ConfigValidationIssue] = []
    seen: set[tuple[str, str, str]] = set()
    for issue in issues:
        key = (issue.path, issue.code, issue.severity)
        if key not in seen:
            deduped.append(issue)
            seen.add(key)
    return deduped


__all__ = [
    "DARS_REMOTE_SUBSCRIPTION_POLICY_SCHEMA_ID",
    "DARS_REMOTE_SUBSCRIPTION_POLICY_SCHEMA_VERSION",
    "validate_dars_remote_subscription_policy_packet",
]
