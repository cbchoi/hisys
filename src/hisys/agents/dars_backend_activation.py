"""DARS backend activation packet validation.

M-DARS-BE-1 keeps this surface local and declarative. It validates an operator
activation packet that authorizes a DARS backend boundary crossing (typically a
localhost-only `openai_compatible` model) but performs no HTTP call, credential
lookup, model invocation, publication, mutation, or remote action.

Traceability: docs/plans/dars-live-backend-implementation-plan.md (M-DARS-BE-1).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from hisys.config.validation import ConfigValidationIssue, ConfigValidationReport


DARS_BACKEND_ACTIVATION_SCHEMA_ID = "hisys.dars.backend.activation"
DARS_BACKEND_ACTIVATION_SCHEMA_VERSION = "0.1.0"

_ALLOWED_ENDPOINT_SCOPES = ("localhost_only", "external_api")
_ALLOWED_ACTIONS = "advisory_only"
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

_REQUIRED_STRING_FIELDS = (
    "activation_id",
    "backend_id",
    "backend_kind",
    "endpoint_scope",
    "allowed_actions",
    "expires_at",
)


def validate_dars_backend_activation_packet(
    data: dict[str, Any],
    *,
    config_ref: str,
    now: str | datetime | None = None,
) -> ConfigValidationReport:
    """Validate a DARS backend activation packet deterministically.

    The validator never opens a network/model boundary, never reads credentials,
    and never persists state. It returns a deterministic
    :class:`ConfigValidationReport` whose issue codes follow the M-DARS-BE-1
    contract.
    """

    issues: list[ConfigValidationIssue] = []
    issues.extend(_raw_secret_issues(data))
    issues.extend(_required_field_issues(data))
    issues.extend(_endpoint_scope_issues(data))
    issues.extend(_allowed_actions_issues(data))
    issues.extend(_approval_ref_issues(data))
    issues.extend(_human_approval_issues(data))
    issues.extend(_expiry_issues(data, now=now))
    issues.extend(_remote_policy_issues(data))

    issues = _dedupe_issues(issues)
    return ConfigValidationReport(
        config_ref=config_ref,
        schema_id=DARS_BACKEND_ACTIVATION_SCHEMA_ID,
        valid=not any(issue.severity == "error" for issue in issues),
        issues=issues,
    )


def _required_field_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    for field in _REQUIRED_STRING_FIELDS:
        value = data.get(field)
        if not isinstance(value, str) or not value:
            issues.append(
                ConfigValidationIssue(
                    path=field,
                    code="missing_required_field",
                    message=f"backend activation packet must declare {field}",
                )
            )
    return issues


def _endpoint_scope_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    scope = data.get("endpoint_scope")
    if not isinstance(scope, str) or not scope:
        return []
    if scope not in _ALLOWED_ENDPOINT_SCOPES:
        return [
            ConfigValidationIssue(
                path="endpoint_scope",
                code="invalid_endpoint_scope",
                message=(
                    "endpoint_scope must be 'localhost_only' or 'external_api'"
                ),
            )
        ]
    return []


def _allowed_actions_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    value = data.get("allowed_actions")
    if value == _ALLOWED_ACTIONS:
        return []
    return [
        ConfigValidationIssue(
            path="allowed_actions",
            code="invalid_allowed_actions",
            message="backend activation packet must declare allowed_actions=advisory_only",
        )
    ]


def _approval_ref_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    approval_ref = data.get("approval_ref")
    if isinstance(approval_ref, str) and approval_ref:
        return []
    return [
        ConfigValidationIssue(
            path="approval_ref",
            code="missing_approval_ref",
            message="backend activation packet must reference a non-empty approval_ref",
        )
    ]


def _human_approval_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    if data.get("human_approved") is True:
        return []
    return [
        ConfigValidationIssue(
            path="human_approved",
            code="human_approval_required",
            message="backend activation packet must record explicit human approval",
        )
    ]


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
                code="activation_expired",
                message="backend activation packet has expired",
            )
        ]
    return []


def _remote_policy_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    if data.get("endpoint_scope") != "external_api":
        return []
    policy_ref = data.get("remote_policy_packet_ref")
    if isinstance(policy_ref, str) and policy_ref:
        return []
    return [
        ConfigValidationIssue(
            path="remote_policy_packet_ref",
            code="external_backend_requires_remote_policy_packet",
            message=(
                "external_api endpoint_scope requires a remote_policy_packet_ref"
                " describing the Codex/Claude subscription policy"
            ),
        )
    ]


def _raw_secret_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    for key, value in data.items():
        if key == "approval_ref":
            continue
        key_lower = key.lower().replace("-", "_")
        if any(marker in key_lower for marker in _SECRET_FIELD_MARKERS):
            issues.append(
                ConfigValidationIssue(
                    path=key,
                    code="raw_secret_value_not_allowed",
                    message=(
                        "backend activation packets must not contain raw secret or"
                        " credential fields"
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
                        "backend activation packets must not contain raw secret-looking"
                        " values"
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
    seen: set[tuple[str, str]] = set()
    for issue in issues:
        key = (issue.path, issue.code)
        if key not in seen:
            deduped.append(issue)
            seen.add(key)
    return deduped


__all__ = [
    "DARS_BACKEND_ACTIVATION_SCHEMA_ID",
    "DARS_BACKEND_ACTIVATION_SCHEMA_VERSION",
    "validate_dars_backend_activation_packet",
]
