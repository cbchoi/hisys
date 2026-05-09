"""Common runtime configuration validation primitives.

Traceability: HISYS-FR-AGT-001..005, HISYS-T-019, HISYS-T-020,
HISYS-CON-010, HISYS-CON-011, HISYS-CON-012.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


KNOWN_SCHEMA_IDS = {"hisys.dars.config"}
SUPPORTED_SCHEMA_VERSIONS = {"0.1.0"}
_SECRET_KEY_RE = re.compile(r"(api[_-]?key|auth[_-]?token|access[_-]?token|secret|password|credential)", re.IGNORECASE)
_SECRET_VALUE_RE = re.compile(r"\b(?:sk|ghp|xox[baprs]|hf)_[A-Za-z0-9][A-Za-z0-9_-]{8,}\b|\bsk-[A-Za-z0-9][A-Za-z0-9_-]{8,}\b")


class ConfigValidationIssue(BaseModel):
    path: str
    severity: Literal["error", "warning"] = "error"
    code: str
    message: str


class ConfigValidationReport(BaseModel):
    config_ref: str
    schema_id: str = ""
    valid: bool
    issues: list[ConfigValidationIssue] = Field(default_factory=list)


class ConfigTraceability(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirements: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class ConfigEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_id: str
    schema_version: str
    config_id: str
    config_version: str
    owner: str
    status: Literal["draft", "active", "deprecated", "disabled"]
    classification: Literal["runtime_config", "harness_config", "test_config"]
    traceability: ConfigTraceability
    metadata: dict[str, Any] = Field(default_factory=dict)
    spec: dict[str, Any]


def validate_config_document(data: dict[str, Any], *, config_ref: str) -> ConfigValidationReport:
    """Validate the common Hisys configuration envelope.

    Domain-specific validators should call this first, then add schema-specific
    and cross-field policy issues.
    """

    schema_id = str(data.get("schema_id", "")) if isinstance(data, dict) else ""
    issues: list[ConfigValidationIssue] = []
    try:
        envelope = ConfigEnvelope.model_validate(data)
    except ValidationError as exc:
        issues.extend(_issues_from_validation_error(exc))
        envelope = None

    if schema_id and schema_id not in KNOWN_SCHEMA_IDS:
        issues.append(
            ConfigValidationIssue(
                path="schema_id",
                code="unknown_schema_id",
                message=f"unknown schema_id: {schema_id}",
            )
        )
    if isinstance(data, dict) and data.get("schema_version") not in SUPPORTED_SCHEMA_VERSIONS:
        issues.append(
            ConfigValidationIssue(
                path="schema_version",
                code="unsupported_schema_version",
                message="schema_version must be one of: 0.1.0",
            )
        )

    traceability = data.get("traceability", {}) if isinstance(data, dict) else {}
    if not isinstance(traceability, dict) or not traceability.get("requirements"):
        issues.append(
            ConfigValidationIssue(
                path="traceability.requirements",
                code="missing_traceability_requirements",
                message="traceability.requirements must be non-empty",
            )
        )
    if not isinstance(traceability, dict) or not traceability.get("constraints"):
        issues.append(
            ConfigValidationIssue(
                path="traceability.constraints",
                code="missing_traceability_constraints",
                message="traceability.constraints must be non-empty",
            )
        )

    issues.extend(_secret_issues(data))
    return ConfigValidationReport(
        config_ref=config_ref,
        schema_id=schema_id or (envelope.schema_id if envelope else ""),
        valid=not any(issue.severity == "error" for issue in issues),
        issues=_dedupe_issues(issues),
    )


def _issues_from_validation_error(exc: ValidationError) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    for error in exc.errors():
        path = _path(error.get("loc", ()))
        issue_type = str(error.get("type", "validation_error"))
        if issue_type == "extra_forbidden":
            code = "unknown_field"
        elif issue_type == "missing":
            code = "missing_required_field"
        elif issue_type == "literal_error":
            code = "invalid_enum_value"
        else:
            code = "validation_error"
        issues.append(ConfigValidationIssue(path=path, code=code, message=str(error.get("msg", "validation error"))))
    return issues


def _path(loc: tuple[Any, ...] | list[Any]) -> str:
    return ".".join(str(part) for part in loc) if loc else "$"


def _secret_issues(value: Any, *, path: str = "") -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            if key != "credential_ref" and _SECRET_KEY_RE.search(str(key)):
                issues.append(
                    ConfigValidationIssue(
                        path=child_path,
                        code="raw_secret_value_not_allowed",
                        message="raw secret-like fields are not allowed; use credential_ref",
                    )
                )
            issues.extend(_secret_issues(item, path=child_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            issues.extend(_secret_issues(item, path=f"{path}.{index}" if path else str(index)))
    elif isinstance(value, str) and _SECRET_VALUE_RE.search(value):
        issues.append(
            ConfigValidationIssue(
                path=path or "$",
                code="raw_secret_value_not_allowed",
                message="raw secret-like values are not allowed; use credential_ref",
            )
        )
    return issues


def _dedupe_issues(issues: list[ConfigValidationIssue]) -> list[ConfigValidationIssue]:
    seen: set[tuple[str, str]] = set()
    deduped: list[ConfigValidationIssue] = []
    for issue in issues:
        key = (issue.path, issue.code)
        if key not in seen:
            deduped.append(issue)
            seen.add(key)
    return deduped


__all__ = ["ConfigEnvelope", "ConfigValidationIssue", "ConfigValidationReport", "validate_config_document"]
