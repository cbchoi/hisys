"""Controlled live DARS panel activation-packet validation.

M-CP-LIVE-1 keeps this surface local and declarative. It validates a human
activation packet for a localhost-only model boundary but performs no HTTP call,
credential lookup, model invocation, publication, mutation, or remote action.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, computed_field

from hisys.config.validation import ConfigValidationIssue, ConfigValidationReport


LIVE_DARS_PANEL_ACTIVATION_SCHEMA_ID = "hisys.dars.panel.live.activation"
LIVE_DARS_PANEL_ACTIVATION_SCHEMA_VERSION = "0.1.0"
_ALLOWED_ENDPOINT_SCOPE = "localhost_only"
_ALLOWED_ACTIONS = "advisory_only"
_ALLOWED_ADAPTER_CLASS = "local_model"
_SECRET_FIELD_MARKERS = (
    "api_key",
    "apikey",
    "auth_token",
    "access_token",
    "secret",
    "password",
    "credential",
)
_SECRET_VALUE_PREFIXES = ("sk-", "sk_", "ghp_", "xoxb-", "xoxp-", "hf_")


class LiveDarsPanelActivationPacket(BaseModel):
    """Human-scoped activation packet for localhost-only DARS panel work."""

    model_config = ConfigDict(extra="forbid")

    activation_id: str = Field(min_length=1)
    approval_ref: str = Field(min_length=1)
    operator_id: str = Field(min_length=1)
    approved_endpoint_scope: Literal["localhost_only"] = "localhost_only"
    allowed_actions: Literal["advisory_only"] = "advisory_only"
    human_approved: Literal[True] = True
    expires_at: str = Field(min_length=1)
    requested_backend_id: str = Field(min_length=1)
    requested_adapter_class: Literal["local_model"] = "local_model"

    @computed_field  # type: ignore[misc]
    @property
    def model_boundary_authorized(self) -> bool:
        return True

    @computed_field  # type: ignore[misc]
    @property
    def live_external_action_authorized(self) -> bool:
        return False

    @computed_field  # type: ignore[misc]
    @property
    def mutation_authorized(self) -> bool:
        return False

    @computed_field  # type: ignore[misc]
    @property
    def requires_human_review(self) -> bool:
        return True

    @computed_field  # type: ignore[misc]
    @property
    def external_call_made(self) -> bool:
        return False


def validate_live_dars_panel_activation_packet(
    data: dict[str, Any], *, config_ref: str
) -> ConfigValidationReport:
    """Validate an activation packet without crossing a model/network boundary."""

    issues: list[ConfigValidationIssue] = []
    issues.extend(_raw_secret_issues(data))
    model_data = dict(data)
    issues.extend(_derived_boundary_field_issues(model_data))
    try:
        LiveDarsPanelActivationPacket.model_validate(model_data)
    except ValidationError as exc:
        issues.extend(_issues_from_validation_error(exc))
    issues.extend(_semantic_policy_issues(data))
    issues = _dedupe_issues(issues)
    return ConfigValidationReport(
        config_ref=config_ref,
        schema_id=LIVE_DARS_PANEL_ACTIVATION_SCHEMA_ID,
        valid=not any(issue.severity == "error" for issue in issues),
        issues=issues,
    )


def _issues_from_validation_error(exc: ValidationError) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    for error in exc.errors():
        path = ".".join(str(part) for part in error.get("loc", ()))
        error_type = str(error.get("type", "validation_error"))
        code = "validation_error"
        if error_type == "missing":
            code = "missing_required_field"
        elif error_type == "extra_forbidden":
            code = _extra_field_code(path)
        elif error_type == "literal_error":
            if path == "approved_endpoint_scope":
                code = "invalid_endpoint_scope"
            elif path == "allowed_actions":
                code = "invalid_allowed_actions"
            elif path == "requested_adapter_class":
                code = "invalid_adapter_class"
            elif path == "human_approved":
                code = "activation_not_human_approved"
            else:
                code = "invalid_enum_value"
        elif error_type == "string_too_short":
            code = "missing_required_field"
        issues.append(
            ConfigValidationIssue(
                path=path,
                code=code,
                message=str(error.get("msg", "validation error")),
            )
        )
    return issues


def _semantic_policy_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    if data.get("approved_endpoint_scope") != _ALLOWED_ENDPOINT_SCOPE:
        issues.append(
            ConfigValidationIssue(
                path="approved_endpoint_scope",
                code="invalid_endpoint_scope",
                message="live DARS panel activation is limited to localhost_only endpoints",
            )
        )
    if data.get("allowed_actions") != _ALLOWED_ACTIONS:
        issues.append(
            ConfigValidationIssue(
                path="allowed_actions",
                code="invalid_allowed_actions",
                message="live DARS panel activation must remain advisory_only",
            )
        )
    if data.get("requested_adapter_class") != _ALLOWED_ADAPTER_CLASS:
        issues.append(
            ConfigValidationIssue(
                path="requested_adapter_class",
                code="invalid_adapter_class",
                message="M-CP-LIVE-1 only authorizes a local_model adapter class",
            )
        )
    if data.get("human_approved") is not True:
        issues.append(
            ConfigValidationIssue(
                path="human_approved",
                code="activation_not_human_approved",
                message="activation packet must record explicit human approval",
            )
        )
    return issues


def _derived_boundary_field_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    expected = {
        "model_boundary_authorized": True,
        "live_external_action_authorized": False,
        "mutation_authorized": False,
        "requires_human_review": True,
        "external_call_made": False,
    }
    issues: list[ConfigValidationIssue] = []
    for key, expected_value in expected.items():
        if key not in data:
            continue
        actual = data.pop(key)
        if actual is not expected_value:
            issues.append(
                ConfigValidationIssue(
                    path=key,
                    code="invalid_boundary_flag",
                    message=f"derived boundary flag {key} must be {expected_value!r}",
                )
            )
    return issues


def _raw_secret_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    for key, value in data.items():
        key_lower = key.lower().replace("-", "_")
        if any(marker in key_lower for marker in _SECRET_FIELD_MARKERS):
            issues.append(
                ConfigValidationIssue(
                    path=key,
                    code="raw_secret_value_not_allowed",
                    message="activation packets must not contain raw secrets or credential fields",
                )
            )
            continue
        if isinstance(value, str) and value.startswith(_SECRET_VALUE_PREFIXES):
            issues.append(
                ConfigValidationIssue(
                    path=key,
                    code="raw_secret_value_not_allowed",
                    message="activation packets must not contain raw secret-looking values",
                )
            )
    return issues


def _extra_field_code(path: str) -> str:
    key_lower = path.lower().replace("-", "_")
    if any(marker in key_lower for marker in _SECRET_FIELD_MARKERS):
        return "raw_secret_value_not_allowed"
    return "unknown_field"


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
    "LIVE_DARS_PANEL_ACTIVATION_SCHEMA_ID",
    "LIVE_DARS_PANEL_ACTIVATION_SCHEMA_VERSION",
    "LiveDarsPanelActivationPacket",
    "validate_live_dars_panel_activation_packet",
]
