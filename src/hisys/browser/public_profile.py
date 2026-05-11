"""Public browser launch profile validation.

The public beta profile is intentionally narrower than the internal source
connector registry: it describes what may be exposed as public UX, while the
registry still governs actual connector dispatch.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

_REQUIRED_FORBIDDEN_ACTIONS = {
    "login",
    "credential_use",
    "form_submit",
    "upload",
    "purchase",
    "post",
    "mutation",
    "access_control_bypass",
}


class PublicBrowserProfile(BaseModel):
    """Safety envelope for public browser beta launches."""

    model_config = ConfigDict(extra="forbid")

    profile_id: str
    live_network_enabled: bool
    connector_id: Literal["playwright_read_only", "camoufox_read_only"]
    mode: Literal["read_only"]
    external_call_allowed: bool
    domain_decision_policy: Literal["orchestrator_decided", "static_allowlist"]
    allow_credentials: bool
    allow_mutation: bool
    fixture_mode_publicly_exposed: bool = False
    experimental_transports_enabled: bool = False
    transport_kind: Literal["playwright_live", "camoufox_live"] = "playwright_live"
    manual_smoke_env_var: str = "HISYS_ALLOW_BROWSER_SMOKE"
    max_source_urls: int = Field(default=10, ge=1, le=50)
    max_follow_links_per_source: int = Field(default=3, ge=0, le=10)
    navigation_timeout_ms: int = Field(default=20000, ge=1000, le=60000)
    allowed_url_schemes: list[Literal["https", "http"]] = Field(default_factory=lambda: ["https", "http"])
    forbidden_actions: list[str]

    @model_validator(mode="after")
    def enforce_public_safety(self) -> "PublicBrowserProfile":
        if not self.live_network_enabled:
            raise ValueError("public browser profile must enable live_network_enabled")
        if not self.external_call_allowed:
            raise ValueError("public browser profile must explicitly allow read-only external calls")
        if self.allow_credentials:
            raise ValueError("public browser profile must not allow credentials")
        if self.allow_mutation:
            raise ValueError("public browser profile must not allow mutation")
        if self.fixture_mode_publicly_exposed:
            raise ValueError("fixture mode must not be exposed in public profile")
        missing = _REQUIRED_FORBIDDEN_ACTIONS - set(self.forbidden_actions)
        if missing:
            raise ValueError(f"public browser profile missing forbidden actions: {sorted(missing)}")
        if self.connector_id == "camoufox_read_only" and not self.experimental_transports_enabled:
            raise ValueError("camoufox transport requires experimental_transports_enabled=true")
        expected_transport = "camoufox_live" if self.connector_id == "camoufox_read_only" else "playwright_live"
        if self.transport_kind != expected_transport:
            raise ValueError(f"transport_kind must be {expected_transport} for connector {self.connector_id}")
        return self


def load_public_browser_profile(path: str | Path) -> PublicBrowserProfile:
    """Load and validate a public browser profile YAML file."""

    raw: Any = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return PublicBrowserProfile.model_validate(raw)
