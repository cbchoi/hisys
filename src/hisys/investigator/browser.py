"""Disabled-by-default Selenium/browser research harness.

Traceability: HISYS-T-028, HISYS-T-027, HISYS-CON-022..023, HISYS-D-015,
HISYS-DATA-002.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from .research import EvidencePackage, ResearchTask


class BrowserAgentSafetyError(ValueError):
    """Raised when a browser research task violates read-only safety gates."""


class BrowserAgentConfig(BaseModel):
    """Runtime safety config for the browser research adapter."""

    enabled: bool = False
    read_only: bool = True
    max_pages: int = 5
    max_depth: int = 1
    allowed_domains: list[str] = Field(default_factory=list)
    forbidden_actions: list[str] = Field(
        default_factory=lambda: [
            "login",
            "post",
            "form_submit",
            "upload",
            "purchase",
            "credential_use",
        ]
    )


class SeleniumReadOnlyAgent:
    """Read-only browser evidence adapter, disabled until harnesses pass."""

    agent_id = "selenium-read-only-agent"
    agent_type = "selenium_read_only"
    output_schema = "EvidencePackage"

    def __init__(self, config: BrowserAgentConfig | None = None) -> None:
        self.config = config or BrowserAgentConfig()

    def run(self, task: ResearchTask, *, requested_actions: list[str] | None = None) -> EvidencePackage:
        self._validate_task(task, requested_actions=requested_actions or [])
        return self._read_static_fixture(task)

    def _validate_task(self, task: ResearchTask, *, requested_actions: list[str]) -> None:
        if not self.config.enabled:
            raise BrowserAgentSafetyError("selenium_read_only agent is disabled")
        if not self.config.read_only:
            raise BrowserAgentSafetyError("selenium_read_only agent requires read_only=true")
        forbidden = set(self.config.forbidden_actions) | set(task.disallowed_actions)
        blocked = sorted(set(requested_actions) & forbidden)
        if blocked:
            raise BrowserAgentSafetyError(f"browser task requested forbidden actions: {blocked}")
        target = task.query or ""
        parsed = urlparse(target)
        if parsed.scheme in {"http", "https"}:
            if parsed.hostname not in set(self.config.allowed_domains):
                raise BrowserAgentSafetyError(f"browser domain not allowed: {parsed.hostname}")
        elif parsed.scheme not in {"file", ""}:
            raise BrowserAgentSafetyError(f"browser URL scheme not allowed: {parsed.scheme}")

    def _read_static_fixture(self, task: ResearchTask) -> EvidencePackage:
        raise BrowserAgentSafetyError("static browser fixture extraction is not implemented until HISYS-T-028 Task 7")


def local_file_from_task(task: ResearchTask) -> Path:
    """Return a local fixture path from a browser task query."""

    target = task.query or ""
    parsed = urlparse(target)
    if parsed.scheme == "file":
        return Path(parsed.path)
    return Path(target)
