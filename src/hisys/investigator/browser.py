"""Disabled-by-default Selenium/browser research harness.

Traceability: HISYS-T-028, HISYS-T-027, HISYS-CON-022..023, HISYS-D-015,
HISYS-DATA-002.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
import hashlib
import re

from pydantic import BaseModel, Field

from .research import ClaimRecord, EvidenceItem, EvidencePackage, ResearchTask


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
        path = local_file_from_task(task)
        if not path.exists() or not path.is_file():
            raise BrowserAgentSafetyError(f"local browser fixture not found: {path}")
        html = path.read_text(encoding="utf-8")
        title = _extract_title(html)
        text = _html_to_text(html)
        digest = hashlib.sha256(html.encode("utf-8")).hexdigest()
        evidence = EvidenceItem(
            evidence_id=f"EV-{task.task_id}-BROWSER-001",
            task_id=task.task_id,
            agent_id=self.agent_id,
            path=str(path),
            title=title,
            quoted_text=text[:500],
            retrieved_at="2026-05-08T00:00:00Z",
            content_hash=f"sha256:{digest}",
        )
        claim = ClaimRecord(
            claim_id=f"CLAIM-{task.task_id}-BROWSER-001",
            text=f"Local static browser fixture provides read-only evidence for: {task.question}",
            confidence=0.75,
            evidence_refs=[evidence.evidence_id],
        )
        return EvidencePackage(
            package_id=f"EPKG-{task.task_id}-BROWSER",
            task_id=task.task_id,
            agent_id=self.agent_id,
            agent_type="selenium_read_only",
            claims=[claim],
            evidence=[evidence],
            actions_taken=["read_local_static_html"],
        )


def local_file_from_task(task: ResearchTask) -> Path:
    """Return a local fixture path from a browser task query."""

    target = task.query or ""
    parsed = urlparse(target)
    if parsed.scheme == "file":
        return Path(parsed.path)
    return Path(target)



def _extract_title(html: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return "Untitled browser evidence"
    return _collapse_ws(_strip_tags(match.group(1)))


def _html_to_text(html: str) -> str:
    body = re.sub(r"<script.*?</script>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    body = re.sub(r"<style.*?</style>", " ", body, flags=re.IGNORECASE | re.DOTALL)
    return _collapse_ws(_strip_tags(body))


def _strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", value)


def _collapse_ws(value: str) -> str:
    return " ".join(value.split())
