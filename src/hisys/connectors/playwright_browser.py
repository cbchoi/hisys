"""Governed read-only Playwright browser source collector.

Traceability: HISYS-FR-INV-001..006, HISYS-T-024, HISYS-CON-010..012,
HISYS-CON-022..023.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Protocol

from .live_source_evidence import SourceAccessRecord, SourceEvidenceItem


class BrowserTransport(Protocol):
    """Read-only browser transport contract."""

    def fetch(self, url: str) -> tuple[int, str, str]:
        """Return ``(http_status, title, visible_text)`` for a read-only page visit."""


@dataclass(frozen=True)
class PlaywrightBrowserEvidencePackage:
    """Persisted browser source evidence refs."""

    access_record: SourceAccessRecord
    evidence_items: list[SourceEvidenceItem]
    access_ref: str
    evidence_ref: str


class PlaywrightBrowserConnector:
    """Collect company/publisher page text through a governed read-only browser."""

    connector_id = "playwright_read_only"

    def __init__(self, *, transport: BrowserTransport | None = None) -> None:
        self._transport = transport

    def collect_fixture(
        self,
        *,
        request_id: str,
        source_url: str,
        fixture_html: Path,
        output_root: Path,
        yyyymmdd: str,
    ) -> PlaywrightBrowserEvidencePackage:
        """Collect a local HTML fixture using the same evidence shape as browser visits."""

        html = fixture_html.read_text(encoding="utf-8")
        title, text = _extract_html_title_and_text(html)
        return self._persist_page(
            request_id=request_id,
            source_url=source_url,
            http_status=200,
            title=title or fixture_html.stem,
            visible_text=text,
            output_root=output_root,
            yyyymmdd=yyyymmdd,
            transport_kind="playwright_fixture",
        )

    def collect_live(
        self,
        *,
        request_id: str,
        source_url: str,
        output_root: Path,
        yyyymmdd: str,
    ) -> PlaywrightBrowserEvidencePackage:
        """Collect one URL through injected transport or Playwright sync runtime."""

        transport = self._transport or PlaywrightSyncTransport()
        http_status, title, visible_text = transport.fetch(source_url)
        return self._persist_page(
            request_id=request_id,
            source_url=source_url,
            http_status=http_status,
            title=title,
            visible_text=visible_text,
            output_root=output_root,
            yyyymmdd=yyyymmdd,
            transport_kind="playwright_live",
        )

    def _persist_page(
        self,
        *,
        request_id: str,
        source_url: str,
        http_status: int,
        title: str,
        visible_text: str,
        output_root: Path,
        yyyymmdd: str,
        transport_kind: str,
    ) -> PlaywrightBrowserEvidencePackage:
        normalized_text = _normalize_visible_text(visible_text)
        digest = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
        access_id = f"ACCESS-{request_id}-{self.connector_id}"
        evidence_id = f"EVID-{request_id}-{self.connector_id}"
        access_ref = f"runtime-boundary/source-connectors/{yyyymmdd}/source-access-{access_id}.json"
        evidence_ref = f"runtime-boundary/source-connectors/{yyyymmdd}/source-evidence-{evidence_id}.json"
        access = SourceAccessRecord(
            access_id=access_id,
            request_id=request_id,
            connector_id=self.connector_id,
            source_url=source_url,
            accessed_at=f"{yyyymmdd}T00:00:00Z",
            http_status=http_status,
            content_type="text/html",
            title=title or source_url,
            license_signal="unknown",
            sha256=digest,
            external_call_made=True,
            policy_refs=["docs/use-cases/live-research-connectors.md"],
        )
        evidence = SourceEvidenceItem(
            evidence_id=evidence_id,
            access_ref=access_ref,
            quoted_text=normalized_text[:1200],
            interpretation=(
                "Read-only Playwright browser collection captured visible page text from a company/publisher source "
                "for downstream actual-data investigation."
            ),
            claim_type="source_evidence",
            confidence="medium",
            uncertainty=(
                f"Browser transport kind={transport_kind}; extracted visible text requires downstream corroboration "
                "before Chief Editor acceptance."
            ),
        )
        output_dir = output_root / "runtime-boundary" / "source-connectors" / yyyymmdd
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_root / access_ref).write_text(_json_dump(access), encoding="utf-8")
        (output_root / evidence_ref).write_text(_json_dump(evidence), encoding="utf-8")
        return PlaywrightBrowserEvidencePackage(
            access_record=access,
            evidence_items=[evidence],
            access_ref=access_ref,
            evidence_ref=evidence_ref,
        )


class PlaywrightUnavailableError(RuntimeError):
    """Raised when Playwright runtime is requested but not installed/ready."""


class PlaywrightSyncTransport:
    """Minimal read-only Playwright sync transport."""

    def fetch(self, url: str) -> tuple[int, str, str]:
        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:  # pragma: no cover - environment dependent
            raise PlaywrightUnavailableError("playwright is not installed; use --browser-fixture-html or install playwright browsers") from exc
        with sync_playwright() as playwright:  # pragma: no cover - environment dependent
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                response = page.goto(url, wait_until="domcontentloaded", timeout=20000)
                title = page.title()
                text = page.locator("body").inner_text(timeout=10000)
                status = int(response.status) if response is not None else 200
                return status, title, text
            finally:
                browser.close()


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self._in_title = False
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._ignored_depth += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._ignored_depth:
            self._ignored_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        if self._in_title:
            self.title_parts.append(data)
        else:
            self.text_parts.append(data)


def _extract_html_title_and_text(html: str) -> tuple[str, str]:
    parser = _VisibleTextParser()
    parser.feed(html)
    return _normalize_visible_text(" ".join(parser.title_parts)), _normalize_visible_text(" ".join(parser.text_parts))


def _normalize_visible_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _json_dump(record: SourceAccessRecord | SourceEvidenceItem) -> str:
    return json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


__all__ = [
    "BrowserTransport",
    "PlaywrightBrowserConnector",
    "PlaywrightBrowserEvidencePackage",
    "PlaywrightSyncTransport",
    "PlaywrightUnavailableError",
]
