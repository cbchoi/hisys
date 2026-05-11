import json

from hisys.connectors.playwright_browser import PlaywrightBrowserConnector


class EmptySecurityRiskTransport:
    def fetch(self, url: str):
        return (200, "Cybersecurity risk", "")


def test_playwright_connector_persists_blocked_or_empty_page_without_crashing(tmp_path):
    connector = PlaywrightBrowserConnector(transport=EmptySecurityRiskTransport())

    package = connector.collect_live(
        request_id="HISYS-REQ-SECURITY-BLOCK-001",
        source_url="https://blocked.example/security-risk",
        output_root=tmp_path,
        yyyymmdd="20260511",
    )

    evidence = json.loads((tmp_path / package.evidence_ref).read_text(encoding="utf-8"))
    assert evidence["quoted_text"] == "[no visible text captured; page may be empty, blocked, or unavailable]"
    assert evidence["confidence"] == "low"
    assert "empty_or_blocked_page" in evidence["uncertainty"]
    access = json.loads((tmp_path / package.access_ref).read_text(encoding="utf-8"))
    assert access["external_call_made"] is True
    assert access["title"] == "Cybersecurity risk"
