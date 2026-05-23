"""DARS bounded unattended standing approval policy validator.

R5 introduces a finite standing approval policy for unattended advisory dry-run
rehearsal. The validator is declarative and local-only: it performs no provider
call, no credential lookup, no network access, and does not activate a standing
approval. Even a valid policy emits a deterministic warning so callers cannot
interpret schema validity as live or unattended action authority.

Traceability:

- HISYS-FR-DARS-CP-013, HISYS-T-DARS-CP-015
- DARS-LIVE-RELEASE-R5-UNATTENDED-PREP
- docs/runbooks/dars-unattended-advisory-operation.md
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from hisys.config.validation import ConfigValidationIssue, ConfigValidationReport


STANDING_APPROVAL_POLICY_SCHEMA_ID = "hisys.dars.standing_approval_policy"
STANDING_APPROVAL_POLICY_SCHEMA_VERSION = "0.1.0"

_ALLOWED_PREP_REQUEST_CLASSES = ("dars_live_provider_advisory_dry_run",)
_REQUIRED_STRING_FIELDS = (
    "policy_id",
    "approval_ref",
    "operator_id",
    "post_run_reviewer_ref",
    "valid_from",
    "expires_at",
    "cost_budget_ref",
    "kill_switch_ref",
    "audit_ledger_ref",
    "audit_retention_ref",
    "redaction_policy_ref",
)
_REQUIRED_POSITIVE_INT_FIELDS = (
    "max_runs",
    "max_runs_per_hour",
    "max_prompt_bytes_per_run",
    "max_output_bytes_per_run",
    "rate_limit_per_minute",
    "max_critics_per_run",
    "max_parallel_critics",
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
_SECRET_FIELD_EXEMPT = {
    "approval_ref",
    "cost_budget_ref",
    "redaction_policy_ref",
    "kill_switch_ref",
    "audit_retention_ref",
    "audit_ledger_ref",
    "alert_on_failure_ref",
    "secret_scan_hit",
}
_SECRET_VALUE_PREFIXES = ("sk-", "sk_", "ghp_", "xoxb-", "xoxp-", "hf_")
_SAFE_VALUE_PREFIXES = ("sk-fake", "hf_fake", "ghp_fake", "xoxb-fake")


def validate_standing_approval_policy(
    data: dict[str, Any],
    *,
    config_ref: str,
    now: str | datetime | None = None,
) -> ConfigValidationReport:
    """Validate a DARS unattended standing approval policy.

    Validity means the policy is well-formed for bounded dry-run rehearsal. It
    does not authorize a live provider/model call or activate unattended action.
    """

    issues: list[ConfigValidationIssue] = []
    issues.extend(_raw_secret_issues(data))
    issues.extend(_required_field_issues(data))
    issues.extend(_request_class_issues(data))
    issues.extend(_provider_ref_issues(data))
    issues.extend(_bounded_int_issues(data))
    issues.extend(_kill_switch_issues(data))
    issues.extend(_audit_issues(data))
    issues.extend(_authority_issues(data))
    issues.extend(_circuit_breaker_issues(data))
    issues.extend(_validity_window_issues(data, now=now))

    issues = _dedupe_issues(issues)
    valid = not any(issue.severity == "error" for issue in issues)
    if valid:
        issues.append(
            ConfigValidationIssue(
                path="*",
                severity="warning",
                code="standing_approval_does_not_authorize_live_action_by_itself",
                message=(
                    "standing approval schema validity does not authorize live"
                    " provider/model calls, credential lookup, or unattended"
                    " action; R5 ACTION requires a separate human-gated canary"
                    " decision packet"
                ),
            )
        )
    return ConfigValidationReport(
        config_ref=config_ref,
        schema_id=STANDING_APPROVAL_POLICY_SCHEMA_ID,
        valid=valid,
        issues=issues,
    )


def _required_field_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    for field in _REQUIRED_STRING_FIELDS:
        value = data.get(field)
        if not isinstance(value, str) or not value:
            code = "missing_required_field"
            if field == "kill_switch_ref":
                code = "kill_switch_ref_missing"
            elif field == "audit_retention_ref":
                code = "audit_retention_ref_missing"
            elif field in {
                "cost_budget_ref",
                "max_runs",
                "max_runs_per_hour",
                "rate_limit_per_minute",
                "max_prompt_bytes_per_run",
                "max_output_bytes_per_run",
            }:
                code = "budget_or_rate_caps_missing"
            issues.append(
                ConfigValidationIssue(
                    path=field,
                    code=code,
                    message=f"standing approval policy must declare {field}",
                )
            )
    return issues


def _request_class_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    classes = data.get("request_class_allowlist")
    if not isinstance(classes, list) or not classes:
        return [
            ConfigValidationIssue(
                path="request_class_allowlist",
                code="request_class_allowlist_missing",
                message="standing approval must declare a non-empty request_class_allowlist",
            )
        ]
    issues: list[ConfigValidationIssue] = []
    for index, value in enumerate(classes):
        if value not in _ALLOWED_PREP_REQUEST_CLASSES:
            issues.append(
                ConfigValidationIssue(
                    path=f"request_class_allowlist[{index}]",
                    code="request_class_not_allowed_for_prep",
                    message=(
                        "R5 PREP permits only dars_live_provider_advisory_dry_run;"
                        " live canary request classes remain HUMAN-GATED ACTION"
                    ),
                )
            )
    return issues


def _provider_ref_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    for field in ("provider_policy_refs", "activation_packet_refs"):
        refs = data.get(field)
        if not isinstance(refs, list) or not refs or not all(
            isinstance(ref, str) and ref for ref in refs
        ):
            issues.append(
                ConfigValidationIssue(
                    path=field,
                    code="missing_required_field",
                    message=f"standing approval policy must declare non-empty {field}",
                )
            )
    return issues


def _bounded_int_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    for field in _REQUIRED_POSITIVE_INT_FIELDS:
        value = data.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            issues.append(
                ConfigValidationIssue(
                    path=field,
                    code="budget_or_rate_caps_missing",
                    message=f"{field} must be a positive integer",
                )
            )
    if isinstance(data.get("max_parallel_critics"), int) and isinstance(
        data.get("max_critics_per_run"), int
    ):
        if int(data["max_parallel_critics"]) > int(data["max_critics_per_run"]):
            issues.append(
                ConfigValidationIssue(
                    path="max_parallel_critics",
                    code="budget_or_rate_caps_missing",
                    message="max_parallel_critics cannot exceed max_critics_per_run",
                )
            )
    return issues


def _kill_switch_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    if data.get("kill_switch_required") is True:
        return []
    return [
        ConfigValidationIssue(
            path="kill_switch_required",
            code="kill_switch_ref_missing",
            message="standing approval must set kill_switch_required=true",
        )
    ]


def _audit_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    if isinstance(data.get("audit_ledger_ref"), str) and data.get("audit_ledger_ref"):
        return []
    return [
        ConfigValidationIssue(
            path="audit_ledger_ref",
            code="audit_ledger_ref_missing",
            message="standing approval must declare audit_ledger_ref",
        )
    ]


def _authority_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    if data.get("requires_post_run_human_review") is not True:
        issues.append(
            ConfigValidationIssue(
                path="requires_post_run_human_review",
                code="post_run_human_review_required",
                message="requires_post_run_human_review must remain true",
            )
        )
    for field in ("mutation_allowed", "publication_allowed", "external_action_allowed"):
        if data.get(field) is not False:
            issues.append(
                ConfigValidationIssue(
                    path=field,
                    code="unattended_authority_rejected",
                    message=(
                        "standing unattended policy may not grant mutation,"
                        " publication, or external action authority"
                    ),
                )
            )
    if data.get("advisory_only") is not True:
        issues.append(
            ConfigValidationIssue(
                path="advisory_only",
                code="unattended_authority_rejected",
                message="standing approval must remain advisory_only=true",
            )
        )
    return issues


def _circuit_breaker_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    breakers = data.get("circuit_breakers")
    if not isinstance(breakers, dict) or not breakers:
        return [
            ConfigValidationIssue(
                path="circuit_breakers",
                code="circuit_breakers_missing",
                message="standing approval must declare circuit_breakers",
            )
        ]
    required = (
        "max_consecutive_failures",
        "cost_threshold_ref",
        "secret_scan_hit",
        "output_redaction_failure",
        "policy_mismatch",
        "kill_switch_activation",
    )
    issues: list[ConfigValidationIssue] = []
    for field in required:
        if field not in breakers:
            issues.append(
                ConfigValidationIssue(
                    path=f"circuit_breakers.{field}",
                    code="circuit_breakers_missing",
                    message=f"circuit_breakers must declare {field}",
                )
            )
    return issues


def _validity_window_issues(
    data: dict[str, Any], *, now: str | datetime | None
) -> list[ConfigValidationIssue]:
    valid_from = _parse_datetime(data.get("valid_from"))
    expires_at = _parse_datetime(data.get("expires_at"))
    current = _parse_datetime(now) if now is not None else datetime.now(timezone.utc)
    if valid_from is None or expires_at is None or current is None:
        return [
            ConfigValidationIssue(
                path="valid_from/expires_at",
                code="invalid_validity_window",
                message="valid_from, expires_at, and now must be ISO datetimes",
            )
        ]
    if expires_at <= valid_from or current < valid_from or current > expires_at:
        return [
            ConfigValidationIssue(
                path="valid_from/expires_at",
                code="standing_approval_not_active",
                message="standing approval policy is not active for the supplied time",
            )
        ]
    return []


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _raw_secret_issues(data: Any) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []

    def visit(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                key_text = str(key)
                lowered = key_text.lower()
                child_path = f"{path}.{key_text}" if path else key_text
                if key_text not in _SECRET_FIELD_EXEMPT and any(
                    marker in lowered for marker in _SECRET_FIELD_MARKERS
                ):
                    issues.append(
                        ConfigValidationIssue(
                            path=child_path,
                            code="raw_secret_field_rejected",
                            message="standing approval policy must not contain raw secret fields",
                        )
                    )
                visit(nested, child_path)
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                visit(nested, f"{path}[{index}]")
        elif isinstance(value, str):
            lowered = value.lower()
            if lowered.startswith(_SECRET_VALUE_PREFIXES) or "bearer " in lowered:
                issues.append(
                    ConfigValidationIssue(
                        path=path,
                        code="raw_secret_value_rejected",
                        message="standing approval policy must not contain raw secret-looking values",
                    )
                )

    visit(data, "")
    return issues


def _dedupe_issues(
    issues: list[ConfigValidationIssue],
) -> list[ConfigValidationIssue]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[ConfigValidationIssue] = []
    for issue in issues:
        key = (issue.path, issue.code, issue.severity)
        if key not in seen:
            seen.add(key)
            deduped.append(issue)
    return deduped


__all__ = [
    "STANDING_APPROVAL_POLICY_SCHEMA_ID",
    "STANDING_APPROVAL_POLICY_SCHEMA_VERSION",
    "validate_standing_approval_policy",
]
