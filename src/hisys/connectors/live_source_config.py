"""Live source connector registry configuration.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field


class LiveSourceConnectorSafetyError(ValueError):
    """Raised when live source connector config violates Hisys safety policy."""


class LiveSearchPolicy(BaseModel):
    """Global policy controlling live network connector eligibility."""

    live_network_enabled: bool = False
    require_human_approval_for_external_call: bool = True
    allow_credentials: bool = False
    allow_mutation: bool = False
    require_allowlist: bool = True
    require_provenance_record: bool = True


class SourceConnectorConfig(BaseModel):
    """Configuration for one live or fixture source connector."""

    model_config = ConfigDict(extra="forbid")

    connector_id: str
    connector_type: Literal[
        "web_search",
        "metadata_search",
        "pdf_fetch",
        "local_file",
        "playwright_read_only",
        "selenium_read_only",
        "fixture",
        "llm_read_only",
    ]
    enabled: bool = False
    mode: str = "dry_run"
    external_call_allowed: bool = False
    domain_decision_policy: Literal["static_allowlist", "orchestrator_decided"] = "static_allowlist"
    requires_human_approval: bool = True
    approval_policy_ref: str | None = None
    allowed_domains: list[str] = Field(default_factory=list)
    disallowed_domains: list[str] = Field(default_factory=list)
    forbidden_actions: list[str] = Field(
        default_factory=lambda: [
            "login",
            "credential_use",
            "form_submit",
            "upload",
            "purchase",
            "post",
            "mutation",
        ]
    )
    output_schema: Literal["EvidencePackage", "SourceAccessRecord"] = "EvidencePackage"
    credential_ref: str | None = None
    manual_smoke_only: bool = False
    manual_smoke_env_var: str | None = None
    smoke_test_in_ci: bool = False


class SourceConnectorRegistry(BaseModel):
    """Root registry for governed source connectors."""

    model_config = ConfigDict(extra="forbid")

    default_mode: Literal["fixture_only", "dry_run", "read_only"] = "fixture_only"
    policy: LiveSearchPolicy = Field(default_factory=LiveSearchPolicy)
    connectors: dict[str, SourceConnectorConfig] = Field(default_factory=dict)

    @classmethod
    def model_validate(cls, obj: Any, *args: Any, **kwargs: Any) -> "SourceConnectorRegistry":  # type: ignore[override]
        registry = super().model_validate(obj, *args, **kwargs)
        registry._enforce_safety()
        return registry

    def _enforce_safety(self) -> None:
        if self.policy.allow_credentials:
            raise LiveSourceConnectorSafetyError("live source connectors must not allow credentials by default")
        if self.policy.allow_mutation:
            raise LiveSourceConnectorSafetyError("live source connectors must not allow mutation")
        for name, connector in self.connectors.items():
            if name != connector.connector_id:
                raise LiveSourceConnectorSafetyError("connector registry key must match connector_id")
            if connector.mode not in {"fixture_only", "dry_run", "read_only", "local_only"}:
                raise LiveSourceConnectorSafetyError("connector mode must be read_only or safer")
            if connector.credential_ref:
                raise LiveSourceConnectorSafetyError("credential_ref is not allowed in checked live source registry baseline")
            if connector.smoke_test_in_ci:
                raise LiveSourceConnectorSafetyError("manual smoke connectors must not run in CI")
            if connector.manual_smoke_only and not connector.manual_smoke_env_var:
                raise LiveSourceConnectorSafetyError("manual smoke connectors require manual_smoke_env_var")
            if connector.external_call_allowed and connector.enabled and not self.policy.live_network_enabled:
                raise LiveSourceConnectorSafetyError("live_network_enabled must be true before enabled external connectors")
            if connector.external_call_allowed and connector.requires_human_approval and not connector.approval_policy_ref:
                raise LiveSourceConnectorSafetyError("external connectors requiring approval need approval_policy_ref")
            if (
                connector.external_call_allowed
                and self.policy.require_allowlist
                and not connector.allowed_domains
                and connector.domain_decision_policy != "orchestrator_decided"
            ):
                raise LiveSourceConnectorSafetyError("external connectors require allowed_domains")
            forbidden = set(connector.forbidden_actions)
            missing_forbidden = {"login", "credential_use", "form_submit", "upload", "purchase", "post"} - forbidden
            if missing_forbidden:
                raise LiveSourceConnectorSafetyError(
                    f"connector {connector.connector_id} missing forbidden actions: {sorted(missing_forbidden)}"
                )


def load_source_connector_registry(path: str | Path) -> SourceConnectorRegistry:
    """Load a governed source connector registry from YAML."""

    config_path = Path(path)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return SourceConnectorRegistry.model_validate(raw)
