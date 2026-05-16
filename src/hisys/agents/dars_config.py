"""DARS backend and role configuration validation.

Traceability: HISYS-FR-AGT-001..005, HISYS-T-019, HISYS-T-020,
HISYS-CON-010, HISYS-CON-011, HISYS-CON-012.

Local DARS endpoint policy implements the Local DARS / ByeSys Provenance
plan Milestone 1 (`docs/plans/2026-05-16-local-dars-byesys-provenance.md`).
"""

from __future__ import annotations

import ipaddress
import json
from typing import Any, Literal
from urllib.parse import urlsplit
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ..config.instance import InstanceRoot
from ..config.validation import ConfigValidationIssue, ConfigValidationReport, validate_config_document

DARS_SCHEMA_ID = "hisys.dars.config"
DARS_OUTPUT_CONTRACT = "DarsCritiqueRecord"
NON_LOOPBACK_BACKENDS = {"fixture_file", "mock_http", "openai_compatible", "cli_agent", "hermes_delegate"}
PROMPT_FIELD_NAMES = {"prompt", "objective", "focus", "instruction", "instructions", "summary", "description"}
LOCAL_ENDPOINT_HOSTNAMES = {"localhost"}
LOCAL_ENDPOINT_ALLOWED_SCHEMES = {"http", "https"}


class DarsPolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    allowed_actions: Literal["advisory_only"] = "advisory_only"
    require_human_approval_for_external_call: bool = True
    require_structured_output_schema: Literal["DarsCritiqueRecord"] = "DarsCritiqueRecord"
    allow_external_side_effects: bool = False
    max_runtime_seconds: int = Field(default=300, ge=1, le=3600)
    redact_markdown_outputs: bool = True


class DarsRolePrompt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objective: str
    focus: str | None = None


class DarsRoleSampling(BaseModel):
    model_config = ConfigDict(extra="forbid")

    temperature: float = Field(default=0.2, ge=0, le=1)
    top_p: float = Field(default=0.9, gt=0, le=1)
    max_output_tokens: int = Field(default=2000, ge=1, le=32000)


class DarsRoleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["devil_advocate", "risk_reviewer", "requirements_reviewer", "evidence_gap_reviewer"]
    profession: Literal["systems_safety_reviewer", "security_reviewer", "domain_scientist", "investment_risk_reviewer", "requirements_engineer"]
    stance: Literal["skeptical_but_constructive", "neutral_reviewer", "adversarial_reviewer"]
    strictness: Literal["low", "medium", "high"]
    creativity: Literal["low", "medium", "high"]
    verbosity: Literal["concise_structured", "detailed_structured"]
    critique_dimensions: list[Literal["unsupported_claims", "counterarguments", "risk_findings", "missing_evidence", "assumption_checks", "compliance_or_policy_gaps"]]
    prompt: DarsRolePrompt
    sampling: DarsRoleSampling = Field(default_factory=DarsRoleSampling)
    output_contract: Literal["DarsCritiqueRecord"] = "DarsCritiqueRecord"


class DarsBackendConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["loopback", "fixture_file", "mock_http", "openai_compatible", "cli_agent", "hermes_delegate"]
    enabled: bool = False
    mode: Literal["local_only", "local_network_only", "read_only", "external_api"]
    external_call_allowed: bool = False
    output_contract: Literal["DarsCritiqueRecord"] = "DarsCritiqueRecord"
    fixture_path: str | None = None
    endpoint: str | None = None
    model: str | None = None
    credential_ref: str | None = None
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    disallowed_tools: list[str] = Field(default_factory=list)


class DarsConfigSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default_backend: str
    policy: DarsPolicyConfig
    roles: dict[str, DarsRoleConfig]
    backends: dict[str, DarsBackendConfig]


class DarsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_id: Literal["hisys.dars.config"]
    schema_version: Literal["0.1.0"]
    config_id: str
    config_version: str
    owner: str
    status: Literal["draft", "active", "deprecated", "disabled"]
    classification: Literal["runtime_config", "harness_config", "test_config"]
    traceability: dict[str, list[str]]
    metadata: dict[str, Any] = Field(default_factory=dict)
    spec: DarsConfigSpec


def load_dars_config(instance: InstanceRoot) -> DarsConfig:
    path = instance.config_dir / "dars.json"
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    report = validate_dars_config_document(data, config_ref=str(path.relative_to(instance.root)))
    if not report.valid:
        messages = "; ".join(f"{issue.path}: {issue.code}" for issue in report.issues if issue.severity == "error")
        raise ValueError(f"invalid DARS config: {messages}")
    return DarsConfig.model_validate(data)


def validate_dars_config_document(data: dict[str, Any], *, config_ref: str) -> ConfigValidationReport:
    base = validate_config_document(data, config_ref=config_ref)
    issues = list(base.issues)
    try:
        config = DarsConfig.model_validate(data)
    except ValidationError as exc:
        issues.extend(_dars_issues_from_validation_error(exc, data))
        config = None

    spec = data.get("spec", {}) if isinstance(data, dict) else {}
    if isinstance(spec, dict):
        issues.extend(_policy_issues(data))
    if config is not None:
        issues.extend(_cross_field_issues(config))

    issues = _dedupe_issues(issues)
    return ConfigValidationReport(
        config_ref=config_ref,
        schema_id=str(data.get("schema_id", "")) if isinstance(data, dict) else "",
        valid=not any(issue.severity == "error" for issue in issues),
        issues=issues,
    )


def _dars_issues_from_validation_error(exc: ValidationError, data: dict[str, Any]) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    for error in exc.errors():
        path = ".".join(str(part) for part in error.get("loc", ()))
        error_type = str(error.get("type", "validation_error"))
        code = "validation_error"
        if error_type == "extra_forbidden":
            code = _extra_field_code(path)
        elif error_type == "literal_error":
            if path.endswith("output_contract") or path.endswith("require_structured_output_schema"):
                code = "invalid_output_contract"
            else:
                code = "invalid_enum_value"
        elif error_type in {"less_than_equal", "less_than", "greater_than", "greater_than_equal"} and ".sampling." in path:
            code = "invalid_sampling_bounds"
        elif error_type == "missing":
            code = "missing_required_field"
        issues.append(ConfigValidationIssue(path=path, code=code, message=str(error.get("msg", "validation error"))))
    issues.extend(_manual_sampling_issues(data))
    return issues


def _extra_field_code(path: str) -> str:
    leaf = path.rsplit(".", 1)[-1]
    if leaf in PROMPT_FIELD_NAMES:
        return "interpretive_text_outside_prompt"
    if leaf != "credential_ref" and any(marker in leaf.lower() for marker in ("api_key", "secret", "password", "credential")):
        return "raw_secret_value_not_allowed"
    return "unknown_field"


def _policy_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    spec = data.get("spec", {}) if isinstance(data, dict) else {}
    active_runtime_policy = (
        data.get("status") == "active"
        and isinstance(spec, dict)
        and isinstance(spec.get("policy"), dict)
        and spec["policy"].get("enabled") is True
    )
    backends = spec.get("backends", {}) if isinstance(spec, dict) else {}
    if isinstance(backends, dict):
        for backend_id, backend in backends.items():
            if not isinstance(backend, dict):
                continue
            path = f"spec.backends.{backend_id}"
            if backend.get("kind") != "loopback" and backend.get("enabled") is True and not active_runtime_policy:
                issues.append(
                    ConfigValidationIssue(
                        path=f"{path}.enabled",
                        code="non_loopback_backend_enabled_by_default",
                        message="non-loopback backends must be disabled in checked-in configuration",
                    )
                )
            if backend.get("output_contract") != DARS_OUTPUT_CONTRACT:
                issues.append(
                    ConfigValidationIssue(
                        path=f"{path}.output_contract",
                        code="invalid_output_contract",
                        message="DARS backends must output DarsCritiqueRecord",
                    )
                )
            if (
                backend.get("kind") == "openai_compatible"
                and backend.get("mode") == "local_network_only"
            ):
                code = _classify_local_endpoint(backend.get("endpoint"))
                if code is not None:
                    issues.append(
                        ConfigValidationIssue(
                            path=f"{path}.endpoint",
                            code=code,
                            message=_LOCAL_ENDPOINT_MESSAGES[code],
                        )
                    )
    roles = spec.get("roles", {})
    if isinstance(roles, dict):
        for role_id, role in roles.items():
            if isinstance(role, dict) and role.get("output_contract") != DARS_OUTPUT_CONTRACT:
                issues.append(
                    ConfigValidationIssue(
                        path=f"spec.roles.{role_id}.output_contract",
                        code="invalid_output_contract",
                        message="DARS roles must output DarsCritiqueRecord",
                    )
                )
    return issues


def _cross_field_issues(config: DarsConfig) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    if config.spec.default_backend not in config.spec.backends:
        issues.append(
            ConfigValidationIssue(
                path="spec.default_backend",
                code="unknown_default_backend",
                message="default_backend must reference an entry in spec.backends",
            )
        )
    for backend_id, backend in config.spec.backends.items():
        if backend.kind == "cli_agent" and (not backend.allowed_tools or not backend.disallowed_tools):
            issues.append(
                ConfigValidationIssue(
                    path=f"spec.backends.{backend_id}.allowed_tools",
                    code="missing_cli_tool_policy",
                    message="cli_agent backends must declare allowed_tools and disallowed_tools",
                )
            )
        if backend.external_call_allowed and not backend.credential_ref:
            issues.append(
                ConfigValidationIssue(
                    path=f"spec.backends.{backend_id}.credential_ref",
                    code="missing_credential_ref",
                    message="external-call backends must reference credentials without storing secret values",
                )
            )
    return issues


def _manual_sampling_issues(data: dict[str, Any]) -> list[ConfigValidationIssue]:
    issues: list[ConfigValidationIssue] = []
    roles = (((data.get("spec") or {}).get("roles") or {}) if isinstance(data, dict) else {})
    if not isinstance(roles, dict):
        return issues
    for role_id, role in roles.items():
        sampling = role.get("sampling") if isinstance(role, dict) else None
        if not isinstance(sampling, dict):
            continue
        temperature = sampling.get("temperature")
        if isinstance(temperature, (int, float)) and not 0 <= temperature <= 1:
            issues.append(
                ConfigValidationIssue(
                    path=f"spec.roles.{role_id}.sampling.temperature",
                    code="invalid_sampling_bounds",
                    message="temperature must be between 0 and 1",
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


_LOCAL_ENDPOINT_MESSAGES: dict[str, str] = {
    "missing_endpoint": "local openai_compatible backends must declare an endpoint",
    "missing_endpoint_host": "local openai_compatible endpoints must include a host",
    "unsupported_endpoint_scheme": "local openai_compatible endpoints must use http or https",
    "non_local_endpoint": "local openai_compatible endpoints must resolve to a loopback host",
}


def _classify_local_endpoint(endpoint: object) -> str | None:
    """Classify a local DARS endpoint as loopback-only or return a rejection code.

    Returns ``None`` when the endpoint is a valid localhost-only URL. Otherwise
    returns one of ``missing_endpoint``, ``missing_endpoint_host``,
    ``unsupported_endpoint_scheme``, or ``non_local_endpoint``. The classifier
    never performs DNS, sockets, or any other I/O — it is deterministic and
    relies only on :mod:`urllib.parse` and :mod:`ipaddress`.
    """

    if endpoint is None or endpoint == "":
        return "missing_endpoint"
    if not isinstance(endpoint, str):
        return "non_local_endpoint"
    try:
        parts = urlsplit(endpoint)
    except ValueError:
        return "non_local_endpoint"
    scheme = (parts.scheme or "").lower()
    if scheme not in LOCAL_ENDPOINT_ALLOWED_SCHEMES:
        return "unsupported_endpoint_scheme"
    # Reject userinfo tricks such as `http://localhost@evil.com/...` where the
    # authority that actually receives the request is the suffix host, not the
    # userinfo token.
    if parts.username or parts.password:
        return "non_local_endpoint"
    try:
        host = parts.hostname
    except ValueError:
        return "non_local_endpoint"
    if not host:
        return "missing_endpoint_host"
    host = host.lower()
    if host in LOCAL_ENDPOINT_HOSTNAMES:
        return None
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return "non_local_endpoint"
    if not address.is_loopback:
        return "non_local_endpoint"
    return None


def derive_local_backend_metadata(backend: DarsBackendConfig) -> dict[str, Any]:
    """Derive deterministic boundary metadata for a local DARS backend.

    Returns an empty mapping for non-local backends so downstream dispatch
    treats only ``openai_compatible`` + ``local_network_only`` backends as
    model-boundary callers.
    """

    if backend.kind == "openai_compatible" and backend.mode == "local_network_only":
        return {
            "endpoint_scope": "localhost_only",
            "model_boundary_required": True,
            "external_call_expected": False,
        }
    return {}


__all__ = [
    "DarsBackendConfig",
    "DarsConfig",
    "DarsConfigSpec",
    "derive_local_backend_metadata",
    "load_dars_config",
    "validate_dars_config_document",
]
