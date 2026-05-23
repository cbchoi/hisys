"""DARS live-provider policy packet validator.

DARS-LIVE-RELEASE-R1-POLICY introduces the controlled live-provider policy
contract. The validator accepts only credential *references* (e.g.
``env://...`` or ``secret-manager-ref://...``); it never reads a credential,
opens a socket, calls a provider, or activates live dispatch. Even a fully
valid packet emits a deterministic
``live_provider_dispatch_not_authorized_by_policy_alone`` warning so callers
cannot interpret schema validity as live authority.

Traceability:

- HISYS-FR-DARS-CP-009, HISYS-T-DARS-CP-011
- docs/plans/dars-panel-live-provider-unattended-release-final-plan.md (R1)
- docs/runbooks/dars-codex-subscription-executor-runbook.md
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from hisys.config.validation import ConfigValidationIssue, ConfigValidationReport


LIVE_PROVIDER_POLICY_SCHEMA_ID = "hisys.dars.live_provider_policy"
LIVE_PROVIDER_POLICY_SCHEMA_VERSION = "0.1.0"

_ALLOWED_PROVIDERS = ("codex", "claude")
_ALLOWED_PROVIDER_KINDS = ("subscription", "managed_subscription", "vendor_managed")
_ALLOWED_ACTIONS = "advisory_only"
_ALLOWED_CREDENTIAL_REF_SCHEMES = (
    "env://",
    "secret-manager-ref://",
    "vault://",
    "subscription-account-ref://",
    "keychain-ref://",
)
_ALLOWED_CREDENTIAL_REF_KINDS = (
    "env",
    "secret-manager",
    "vault",
    "subscription-account",
    "keychain",
)
_REQUIRED_STRING_FIELDS = (
    "policy_id",
    "approval_ref",
    "operator_id",
    "provider_id",
    "provider_kind",
    "model_id",
    "credential_ref",
    "credential_ref_kind",
    "endpoint_ref",
    "allowed_actions",
    "cost_budget_ref",
    "expires_at",
    "redaction_policy_ref",
)
_REQUIRED_BOOL_FIELDS = (
    "external_call_allowed",
    "mutation_allowed",
    "publication_allowed",
    "requires_human_review",
    "audit_required",
)
_REQUIRED_POSITIVE_INT_FIELDS = (
    "max_prompt_bytes",
    "max_output_bytes",
    "rate_limit_per_minute",
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
    "authorization",
    "bearer",
)
_RAW_SECRET_FIELD_EXEMPT = {
    "approval_ref",
    "cost_budget_ref",
    "credential_ref",
    "credential_ref_kind",
    "redaction_policy_ref",
    "revocation_ref",
}
_SECRET_VALUE_PREFIXES = ("sk-", "sk_", "ghp_", "xoxb-", "xoxp-", "hf_")


def validate_live_provider_policy_packet(
    data: dict[str, Any],
    *,
    config_ref: str,
    now: str | datetime | None = None,
) -> ConfigValidationReport:
    """Validate a live-provider policy packet deterministically.

    The validator performs no HTTP call, no credential lookup, and no provider
    dispatch. Even a valid packet only authorizes a *future* gated live call
    behind activation + approval + transport gates implemented in R2 and later.
    """

    issues: list[ConfigValidationIssue] = []
    issues.extend(_raw_secret_issues(data))
    issues.extend(_required_field_issues(data))
    issues.extend(_provider_issues(data))
    issues.extend(_provider_kind_issues(data))
    issues.extend(_allowed_actions_issues(data))
    issues.extend(_credential_ref_issues(data))
    issues.extend(_authority_flag_issues(data))
    issues.extend(_bounded_int_issues(data))
    issues.extend(_expiry_issues(data, now=now))

    issues = _dedupe_issues(issues)

    valid = not any(issue.severity == "error" for issue in issues)
    if valid:
        issues.append(
            ConfigValidationIssue(
                path="*",
                severity="warning",
                code="live_provider_dispatch_not_authorized_by_policy_alone",
                message=(
                    "schema validity does not authorize live provider dispatch;"
                    " a live provider call still requires the R2 fail-closed"
                    " adapter, an activation packet, a decision packet, and a"
                    " reviewed runbook gate"
                ),
            )
        )
    return ConfigValidationReport(
        config_ref=config_ref,
        schema_id=LIVE_PROVIDER_POLICY_SCHEMA_ID,
        valid=valid,
        issues=issues,
    )


def _required_field_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    for field in _REQUIRED_STRING_FIELDS:
        value = data.get(field)
        if not isinstance(value, str) or not value:
            code = (
                "missing_credential_ref"
                if field in {"credential_ref", "credential_ref_kind"}
                else "missing_required_field"
            )
            issues.append(
                ConfigValidationIssue(
                    path=field,
                    code=code,
                    message=f"live provider policy must declare {field}",
                )
            )
    for field in _REQUIRED_BOOL_FIELDS:
        if not isinstance(data.get(field), bool):
            issues.append(
                ConfigValidationIssue(
                    path=field,
                    code="missing_required_field",
                    message=f"live provider policy must declare {field}",
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
                    "live provider policy provider_id must be 'codex' or"
                    " 'claude'; arbitrary OpenAI-compatible, Gemini, Grok,"
                    " local-proxy, and custom-HTTP providers are out of"
                    " scope for R1"
                ),
            )
        ]
    return []


def _provider_kind_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    kind = data.get("provider_kind")
    if not isinstance(kind, str) or not kind:
        return []
    if kind not in _ALLOWED_PROVIDER_KINDS:
        return [
            ConfigValidationIssue(
                path="provider_kind",
                code="invalid_provider_kind",
                message=(
                    "live provider policy provider_kind must be one of "
                    + ", ".join(_ALLOWED_PROVIDER_KINDS)
                ),
            )
        ]
    return []


def _allowed_actions_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    actions = data.get("allowed_actions")
    if actions == _ALLOWED_ACTIONS:
        return []
    if not isinstance(actions, str) or not actions:
        return []
    return [
        ConfigValidationIssue(
            path="allowed_actions",
            code="invalid_allowed_actions",
            message="live provider policy allowed_actions must remain advisory_only",
        )
    ]


def _credential_ref_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    ref = data.get("credential_ref")
    kind = data.get("credential_ref_kind")
    if isinstance(ref, str) and ref:
        if not ref.startswith(_ALLOWED_CREDENTIAL_REF_SCHEMES):
            issues.append(
                ConfigValidationIssue(
                    path="credential_ref",
                    code="invalid_credential_ref_scheme",
                    message=(
                        "credential_ref must use one of the controlled schemes: "
                        + ", ".join(_ALLOWED_CREDENTIAL_REF_SCHEMES)
                    ),
                )
            )
    if isinstance(kind, str) and kind and kind not in _ALLOWED_CREDENTIAL_REF_KINDS:
        issues.append(
            ConfigValidationIssue(
                path="credential_ref_kind",
                code="invalid_credential_ref_kind",
                message=(
                    "credential_ref_kind must be one of "
                    + ", ".join(_ALLOWED_CREDENTIAL_REF_KINDS)
                ),
            )
        )
    return issues


def _authority_flag_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    if data.get("mutation_allowed") is True:
        issues.append(
            ConfigValidationIssue(
                path="mutation_allowed",
                code="mutation_authority_not_allowed",
                message=(
                    "live provider policy must not grant mutation authority;"
                    " advisory_only is the only allowed scope"
                ),
            )
        )
    if data.get("publication_allowed") is True:
        issues.append(
            ConfigValidationIssue(
                path="publication_allowed",
                code="mutation_authority_not_allowed",
                message=(
                    "live provider policy must not grant publication authority;"
                    " advisory_only is the only allowed scope"
                ),
            )
        )
    if data.get("external_call_allowed") is False:
        issues.append(
            ConfigValidationIssue(
                path="external_call_allowed",
                code="external_call_must_be_allowed",
                message=(
                    "live provider policy must set external_call_allowed=true;"
                    " a policy that disables external calls cannot authorize a"
                    " future live call"
                ),
            )
        )
    if data.get("requires_human_review") is False:
        issues.append(
            ConfigValidationIssue(
                path="requires_human_review",
                code="requires_human_review_must_be_true",
                message=(
                    "live provider policy must preserve requires_human_review=true;"
                    " removing human review requires a separately approved policy"
                    " change"
                ),
            )
        )
    return issues


def _bounded_int_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    for field in _REQUIRED_POSITIVE_INT_FIELDS:
        value = data.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            if field == "max_prompt_bytes":
                code = "max_prompt_bytes_must_be_positive"
            elif field == "max_output_bytes":
                code = "max_output_bytes_must_be_positive"
            else:
                code = "rate_limit_must_be_positive"
            issues.append(
                ConfigValidationIssue(
                    path=field,
                    code=code,
                    message=f"live provider policy {field} must be a positive integer",
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
                message="live provider policy packet has expired",
            )
        ]
    return []


def _raw_secret_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    for key, value in data.items():
        if key in _RAW_SECRET_FIELD_EXEMPT:
            if isinstance(value, str) and value.startswith(_SECRET_VALUE_PREFIXES):
                issues.append(
                    ConfigValidationIssue(
                        path=key,
                        code="raw_secret_value_not_allowed",
                        message=(
                            "live provider policy must not contain raw"
                            " secret-looking values; use a controlled reference"
                            " scheme (env://, secret-manager-ref://, vault://,"
                            " subscription-account-ref://, keychain-ref://)"
                        ),
                    )
                )
            continue
        key_lower = key.lower().replace("-", "_")
        if any(marker in key_lower for marker in _SECRET_FIELD_MARKERS):
            issues.append(
                ConfigValidationIssue(
                    path=key,
                    code="raw_secret_value_not_allowed",
                    message=(
                        "live provider policy packets must not declare raw"
                        " secret or credential fields; reference credentials"
                        " through credential_ref/credential_ref_kind only"
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
                        "live provider policy packets must not contain raw"
                        " secret-looking values"
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
    "LIVE_PROVIDER_POLICY_SCHEMA_ID",
    "LIVE_PROVIDER_POLICY_SCHEMA_VERSION",
    "validate_live_provider_policy_packet",
]
